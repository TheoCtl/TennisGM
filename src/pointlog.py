"""
pointlog.py - Highlights system.

Every point simulated in a tournament match is rated out of 100 based on:
  * its duration (rally length)
  * the variety and the quality of the shots played (power, placement, specials)
  * its importance in the match (break point, set point, set/match winning point)

The 10 best points of each match are kept in `data/pointlog.json`, together with
every shot (type, power, precision, direction), the ball coordinates and the
score at that moment of the match.

The file holds every match of the *current week*; it is wiped whenever the game
advances to a new week.
"""

import json
import math
import os

POINTLOG_PATH = os.path.join('data', 'pointlog.json')

TOP_N = 10

SPECIAL_SHOTS = {'dropshot', 'volley', 'lift', 'slice'}

# Bonus given to the point-winning shot (spectacular shots score higher)
WINNING_SHOT_BONUS = {
    'dropshot': 4.0,
    'volley': 2.0,
    'lift': 3.0,
    'slice': 1.0,
    'forehand': 2.0,
    'backhand': 2.0,
    'serve': 0.5,
}

EMPTY_MATCH_STATS = {
    'aces': 0, 'breaks': 0, 'forehand_winners': 0, 'backhand_winners': 0,
    'dropshot_winners': 0, 'volley_winners': 0, 'lift_winners': 0, 'slice_winners': 0,
}


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def round_name(round_idx, num_rounds):
    """Human readable name of a round (0-based index)."""
    from_end = num_rounds - round_idx
    if from_end == 1:
        return "Final"
    if from_end == 2:
        return "Semifinal"
    if from_end == 3:
        return "Quarterfinal"
    if from_end == 4:
        return "Round of 16"
    if from_end == 5:
        return "Round of 32"
    if from_end == 6:
        return "Round of 64"
    if from_end == 7:
        return "Round of 128"
    return "Round %d" % (round_idx + 1)


def _effective_shots(events):
    """Return the shot events of a point, dropping the duplicated final shot.

    The engine emits the winning ball twice (once as the shot, once as the
    `is_final` marker) - the second one always has the same hitter as the
    previous event, exactly like the check made by the match viewer.
    """
    shots = []
    for ev in events:
        if ev.get('type') != 'shot':
            continue
        if shots and ev.get('hitter_id') == shots[-1].get('hitter_id'):
            continue
        shots.append(ev)
    return shots


def _shot_info(shot):
    bp = (shot.get('ball_positions') or [{}])[0]
    power = bp.get('power', 50)
    precision = bp.get('precision')
    try:
        power = float(power)
    except (TypeError, ValueError):
        power = 50.0
    try:
        precision = float(precision) if precision is not None else None
    except (TypeError, ValueError):
        precision = None
    return power, precision


# ----------------------------------------------------------------------
# Rating
# ----------------------------------------------------------------------
def rate_point(events, meta=None):
    """Rate a single point out of 100. Returns (rating, breakdown)."""
    meta = meta or {}
    shots = _effective_shots(events)
    summary = next((e for e in events if e.get('type') == 'point_summary'), {}) or {}

    rally = summary.get('rally_length') or len(shots)

    # --- 1. Duration (0 - 25) ------------------------------------------
    # 1 shot -> 0, 3 -> 10, 5 -> 18, 8 -> 26, 12 -> 32, 20+ -> ~25
    duration = 25.0 * (1.0 - math.exp(-max(0, rally - 1) / 6.0))

    # --- 2. Variety (0 - 35) -------------------------------------------
    rally_types = [s.get('shot_type') for s in shots if s.get('shot_type') != 'serve']
    distinct = set(t for t in rally_types if t)
    specials = distinct & SPECIAL_SHOTS

    variety = 5.0 * len(distinct) + 3.0 * len(specials)

    # Changing direction (cross <-> straight) makes a rally livelier
    directions = [
        (s.get('ball_positions') or [{}])[0].get('direction')
        for s in shots
    ]
    switches = sum(
        1 for a, b in zip(directions, directions[1:])
        if a and b and a != b
    )
    variety += min(6.0, switches * 1.2)
    variety = min(35.0, variety)

    # --- 3. Quality of the shots (0 - 40) ------------------------------
    qualities = []
    for s in shots:
        power, precision = _shot_info(s)
        # precision 50 = middle of the court, 0/100 = along the lines
        placement = 50.0 if precision is None else min(100.0, abs(precision - 50.0) * 2.0)
        qualities.append(0.55 * min(100.0, max(0.0, power)) + 0.45 * placement)

    if qualities:
        mean_q = sum(qualities) / len(qualities)
        best_q = max(qualities)
        quality = 40.0 * ((0.65 * mean_q + 0.40 * best_q) / 100.0)
    else:
        quality = 0.0

    winning_shot = summary.get('winning_shot')
    if summary.get('is_ace'):
        quality += 1.0
    else:
        quality += WINNING_SHOT_BONUS.get(winning_shot, 0.0)
    quality = min(40.0, quality)

    rating = duration + variety + quality

    # NB: the point that wins the match is rated exactly like any other one.
    # It is force-picked into the match highlights by build_match_points(), but
    # it only makes the tournament highlights if its rating earns it.
    rating = max(0.0, min(100.0, rating))

    breakdown = {
        'duration': round(duration, 1),
        'variety': round(variety, 1),
        'quality': round(quality, 1),
        'rally': rally,
    }
    return round(rating, 1), breakdown


# ----------------------------------------------------------------------
# Building the record of a match
# ----------------------------------------------------------------------
def _blank_score(score_ev):
    return {
        'type': 'score',
        'sets': [],
        'current_set': {'player1': 0, 'player2': 0},
        'player1_name': (score_ev or {}).get('player1_name', 'Player 1'),
        'player2_name': (score_ev or {}).get('player2_name', 'Player 2'),
        'match_stats': {
            'player1': dict(EMPTY_MATCH_STATS),
            'player2': dict(EMPTY_MATCH_STATS),
        },
    }


def build_match_points(point_events, ctx, top_n=TOP_N):
    """Rate every point of a match and return the `top_n` best ones.

    The returned list is sorted chronologically (as needed by the match
    highlights). Each record embeds everything needed to replay the point.
    """
    records = []
    prev_score = None

    for order, pt in enumerate(point_events or []):
        events = pt.get('events') or []
        if not events:
            continue
        score_ev = next((e for e in events if e.get('type') == 'score'), None)
        summary = next((e for e in events if e.get('type') == 'point_summary'), {}) or {}
        meta = pt.get('meta') or {}

        rating, breakdown = rate_point(events, meta)

        records.append({
            'order': order,
            'rating': rating,
            'breakdown': breakdown,
            'events': events,
            'score_before': prev_score or _blank_score(score_ev),
            'score_after': score_ev or _blank_score(score_ev),
            'winner_id': summary.get('winner_id'),
            'winning_shot': summary.get('winning_shot'),
            'rally_length': summary.get('rally_length', breakdown['rally']),
            'won_set': bool(meta.get('won_set')),
            'won_match': bool(meta.get('won_match')),
            # match context (needed by the tournament highlights, where every
            # point may come from a different match)
            'tournament_id': ctx.get('tournament_id'),
            'tournament_name': ctx.get('tournament_name'),
            'round_idx': ctx.get('round_idx'),
            'round_name': ctx.get('round_name'),
            'match_idx': ctx.get('match_idx'),
            'surface': ctx.get('surface'),
            'player1_id': ctx.get('player1_id'),
            'player2_id': ctx.get('player2_id'),
            'player1_name': ctx.get('player1_name'),
            'player2_name': ctx.get('player2_name'),
        })

        prev_score = score_ev

    by_rating = sorted(records, key=lambda r: (-r['rating'], r['order']))
    best = by_rating[:top_n]

    # The point that wins the match always belongs to the match highlights,
    # however dull it was: if its rating did not earn it a spot, it takes the
    # place of the weakest point selected. Its rating is left untouched, so it
    # still has to earn its way into the tournament highlights.
    match_point = next((r for r in records if r['won_match']), None)
    if match_point is not None and match_point not in best and top_n > 0:
        best[-1] = match_point           # by_rating order -> last is the weakest

    best.sort(key=lambda r: r['order'])

    # Only the points we keep are stored: shrink their float noise so the file
    # stays small (a full week of tournaments means hundreds of matches).
    for rec in best:
        _compact_events(rec['events'])
    return best


def _compact_events(events):
    """Round the floats of an event list (imperceptible, ~40% smaller on disk)."""
    for ev in events:
        for bp in ev.get('ball_positions', []) or []:
            for key in ('x', 'y', 'power', 'precision'):
                val = bp.get(key)
                if isinstance(val, float):
                    bp[key] = round(val, 1)
        stamina = ev.get('stamina')
        if isinstance(stamina, dict):
            for k, v in stamina.items():
                if isinstance(v, float):
                    stamina[k] = round(v, 3)
    return events


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------
class PointLog:
    """Stores the 10 best points of every match played during the current week."""

    def __init__(self, path=POINTLOG_PATH):
        self.path = path
        self.year = None
        self.week = None
        self.matches = {}      # match_key -> {'info': {...}, 'points': [...]}
        self._dirty = False
        self.load()

    # -- keys ----------------------------------------------------------
    @staticmethod
    def match_key(tournament_id, round_idx, match_idx):
        return "%s|%s|%s" % (tournament_id, round_idx, match_idx)

    # -- io ------------------------------------------------------------
    def load(self):
        try:
            with open(self.path, 'r') as f:
                data = json.load(f)
            self.year = data.get('year')
            self.week = data.get('week')
            self.matches = data.get('matches', {}) or {}
            for entry in self.matches.values():
                for rec in entry.get('points', []):
                    _normalize_events(rec.get('events') or [])
        except (IOError, OSError, ValueError):
            self.year = None
            self.week = None
            self.matches = {}

    def save(self):
        try:
            directory = os.path.dirname(self.path)
            if directory and not os.path.isdir(directory):
                os.makedirs(directory)
            payload = {
                'year': self.year,
                'week': self.week,
                'matches': self.matches,
            }
            with open(self.path, 'w') as f:
                json.dump(payload, f, separators=(',', ':'))
            self._dirty = False
        except (IOError, OSError, TypeError, ValueError):
            # Never let the highlights break the game
            pass

    def flush(self):
        """Write to disk only if something changed."""
        if self._dirty:
            self.save()

    # -- week management ------------------------------------------------
    def reset(self, year, week):
        """Wipe every stored point (called when the game advances one week)."""
        self.matches = {}
        self.year = year
        self.week = week
        self._dirty = True
        self.save()

    def ensure_week(self, year, week):
        """Reset the log if it belongs to another week (e.g. after loading a save)."""
        if self.year != year or self.week != week:
            self.reset(year, week)

    # -- recording ------------------------------------------------------
    def record_match(self, key, info, points):
        if not points:
            return
        self.matches[key] = {'info': info, 'points': points}
        self._dirty = True

    # -- reading --------------------------------------------------------
    def has_match(self, key):
        entry = self.matches.get(key)
        return bool(entry and entry.get('points'))

    def get_match_points(self, key):
        """The 10 best points of a match, in chronological order."""
        entry = self.matches.get(key)
        if not entry:
            return []
        points = list(entry.get('points', []))
        points.sort(key=lambda r: r.get('order', 0))
        return points

    def get_match_info(self, key):
        entry = self.matches.get(key)
        return dict(entry.get('info', {})) if entry else {}

    def has_tournament(self, tournament_id):
        return bool(self.get_tournament_points(tournament_id))

    def get_tournament_points(self, tournament_id, top_n=TOP_N):
        """The 10 best points of a whole tournament, from the lowest to the
        highest rating (a proper highlights countdown)."""
        pool = []
        for entry in self.matches.values():
            info = entry.get('info', {})
            if info.get('tournament_id') != tournament_id:
                continue
            pool.extend(entry.get('points', []))

        pool.sort(key=lambda r: (
            -r.get('rating', 0),
            r.get('round_idx', 0),
            r.get('order', 0),
        ))
        best = pool[:top_n]
        # Countdown: worst of the ten first, best last
        best.sort(key=lambda r: (
            r.get('rating', 0),
            -r.get('round_idx', 0),
            -r.get('order', 0),
        ))
        return best


def _normalize_events(events):
    """JSON turns integer dict keys into strings: restore usable stamina keys."""
    for ev in events:
        stamina = ev.get('stamina')
        if isinstance(stamina, dict):
            fixed = {}
            for k, v in stamina.items():
                fixed[k] = v
                if isinstance(k, str):
                    try:
                        fixed[int(k)] = v
                    except ValueError:
                        pass
            ev['stamina'] = fixed
    return events
