"""
Commentary generator for match visualization.

Produces short, varied text lines after each point based on rich context:
winner/loser names, shot type, rally length, score situation, player
archetypes, skill levels, tournament round, etc.
"""
import random

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _first_name(full_name: str) -> str:
    """Return the first name (everything before the last space)."""
    parts = full_name.split()
    return parts[0] if parts else full_name


def _last_name(full_name: str) -> str:
    """Return the last name (last token)."""
    parts = full_name.split()
    return parts[-1] if parts else full_name


def _is_center_y(ball_y: float) -> bool:
    """True when the ball landed near the centre of the court (unforced-error zone)."""
    return 220 <= ball_y <= 380


def _top_skill(player: dict) -> str:
    """Return the name of the player's highest-rated skill."""
    skills = player.get("skills", {})
    if not skills:
        return "game"
    return max(skills, key=lambda k: skills[k])


def _skill_value(player: dict, skill: str) -> int:
    return player.get("skills", {}).get(skill, 50)


# ---------------------------------------------------------------------------
# Template banks – keyed by *situation*.
# Each template is a format-string that may use:
#   {w}     = winner full name       {wf} = winner first name
#   {wl}    = winner last name
#   {l}     = loser full name        {lf} = loser first name
#   {ll}    = loser last name
#   {shot}  = winning shot label (e.g. "forehand", "backhand")
#   {rally} = rally length (int)
# ---------------------------------------------------------------------------

_ACE_TEMPLATES = [
    "ACE! {wl} fires an untouchable serve!",
    "An ace from {w}! {ll} could only watch.",
    "Thundering ace from {wl}!",
    "{wl} paints the line with an ace!",
    "Boom! Ace from {w}. {lf} had no chance.",
    "That serve was too quick for {ll}. Ace!",
    "A bullet serve from {wl} — ace!",
    "Superb serving! Ace for {wf}!",
    "{wl} sends one down the T — ace!",
    "Unstoppable serve from {wl} for the ace!",
    "Right on the line! Ace, {wl}!",
    "{lf} is left flat-footed — ace {wl}!",
    "Pure power from {wl}! Another ace in the bank.",
    "No answer from {ll} — {wl} aces it.",
    "{wl} goes wide with the serve — ace!",
    "The serve from {wl} is just too good!",
    "{wl} with a commanding ace down the middle!",
    "Another big serve from {wl}. {lf} couldn't react in time.",
]

_FOREHAND_WINNER_CENTER = [
    "{ll} puts a ball right in {wl}'s strike zone — and pays for it. Forehand winner!",
    "A loose shot from {ll} and {wl} punishes it with the forehand.",
    "Easy pickings — {wl} tees off on a weak ball. Forehand winner.",
    "{ll} gifts {wl} a short ball and gets burned.",
    "{wl} steps in and crushes the forehand. {ll} should have done better with that placement.",
    "Not enough depth from {ll}, and {wl} makes them pay.",
    "A comfortable forehand winner for {wl} — that ball was asking for it.",
    "{wl} swings freely on a ball that sat up. Forehand winner.",
]

_BACKHAND_WINNER_CENTER = [
    "{ll} feeds {wl}'s backhand — costly mistake. Winner!",
    "A loose reply from {ll} and {wl} cracks a backhand winner.",
    "{wl} makes it look easy — backhand winner off a weak ball from {ll}.",
    "Poor placement from {ll}. {wl} dispatches the backhand without breaking a sweat.",
    "That ball from {ll} was too central — {wl}'s backhand takes care of business.",
    "{wl} capitalises on {ll}'s error in placement. Backhand winner.",
    "The ball sat up for {wl} — clean backhand winner.",
    "{wl} punishes the short backhand from {ll}. Clean winner.",
]

_FOREHAND_WINNER = [
    "Forehand winner from {wl}! Beautiful shot.",
    "{wl} unleashes a devastating forehand!",
    "What a forehand! {wl} finds the corner.",
    "{wf} cracks a forehand down the line!",
    "{wl} with a blistering forehand winner!",
    "Clinical forehand from {wl} — {ll} had no answer.",
    "Incredible forehand from {wl}! Right on the line.",
    "{wl} rips the forehand cross-court for a winner!",
    "{lf} is stretched wide — {wl} finishes with the forehand.",
    "{wl} paints the line with an unplayable forehand.",
    "A venomous forehand from {wl} wraps up the point.",
    "{wl} threads the forehand past a diving {ll}!",
    "Jaw-dropping forehand from {wl}!",
    "Full swing from {wl} — forehand winner, clean as a whistle.",
    "{wl} goes for the forehand and nails it.",
    "Inside-out forehand from {wl} — world class!",
    "Textbook forehand winner from {wl}.",
    "The pace on that forehand from {wl} was exceptional.",
    "{wl} finds a passing forehand angle that {ll} can't cover.",
    "{wl}'s forehand fires deep into the corner. No chance for {ll}.",
]

_BACKHAND_WINNER = [
    "Backhand winner from {wl}! Superb technique.",
    "{wl} fires a backhand cross-court winner!",
    "Stunning backhand from {wl}!",
    "{lf} can't reach {wl}'s backhand. Winner!",
    "A gorgeous backhand down the line from {wl}!",
    "Clinical backhand from {wl} — untouchable.",
    "{wl} produces a sublime backhand winner.",
    "Immaculate backhand from {wl} to wrap up the point!",
    "The backhand from {wl} is pure class.",
    "{wl} slices a backhand winner past {ll}!",
    "{wl} wrong-foots {ll} with a sneaky backhand.",
    "Full extension from {wl} — backhand winner!",
    "What hands! {wl} turns defense into a backhand winner.",
    "{wl} catches {lf} going the wrong way — backhand winner.",
    "{wl} steps in and tattoos the backhand for a winner.",
    "Precise backhand from {wl} — right on the corner.",
    "{wl} finds the open court with a stunning backhand.",
]

_DROPSHOT_WINNER = [
    "Brilliant dropshot from {wl}! {ll} couldn't get there.",
    "{wl} with a delicate touch — dropshot winner!",
    "What finesse! {wl} plays a perfect dropshot.",
    "{ll} is caught flat-footed by {wl}'s dropshot!",
    "A cheeky dropshot from {wl} catches {ll} off guard!",
    "{wl} disguises the dropshot beautifully. Winner!",
    "Exquisite touch from {wl}! The dropshot just dies over the net.",
    "{lf} sprints forward but can't reach the dropshot.",
    "The softest of touches from {wl} — dropshot winner.",
    "{wl} reads the situation perfectly — dropshot into empty court!",
    "Vintage dropshot from {wl}! {ll} is stranded at the baseline.",
    "That drop was disguised as a drive — genius from {wl}.",
    "{wl} with the velvet touch! Dropshot winner.",
]

_VOLLEY_WINNER = [
    "{wl} comes to the net and puts the volley away!",
    "Crisp volley from {wl}! Point over.",
    "{wl} finishes at the net with a punching volley!",
    "What reflexes! {wl} dispatches the volley.",
    "{wl} moves forward and executes a perfect volley!",
    "Net play pays off for {wl} — volley winner!",
    "{ll} tries to pass but {wl} cuts it off at the net!",
    "Aggressive net play from {wl}! Volley winner.",
    "{wl} is commanding at the net — easy volley winner.",
    "{wl} reads the return and punches the volley into the open court!",
    "Instinctive volley from {wl}!",
    "Textbook serve and volley from {wl} — point sealed at the net.",
    "{wl} closes the net and {ll} has nowhere to go.",
]

# Unforced errors: when the ball lands center, the "loser" messed up
_UNFORCED_ERROR_FH = [
    "Unforced error from {ll}! The forehand goes wide.",
    "{ll} pushes the forehand long. Free point for {wl}.",
    "Loose forehand from {ll} — unforced error.",
    "{ll} misjudges the forehand. It drifts into the net.",
    "Sloppy forehand from {ll}. {wl} takes the point.",
    "{ll} overcooks the forehand. Error.",
    "That forehand from {ll} was ill-advised — right into the net.",
    "The forehand from {ll} sails long. {wl} won't complain.",
    "{lf} sprays a forehand wide. Unforced error.",
    "A rush of blood from {ll} — forehand error.",
    "{ll} goes for too much on the forehand. Error.",
    "Wayward forehand from {ll}. Gift for {wl}.",
    "{ll} loses focus on the forehand — unforced error.",
    "Poor execution from {ll} on the forehand.",
    "Not the best timing from {ll}. Forehand goes astray.",
]

_UNFORCED_ERROR_BH = [
    "Unforced error from {ll} on the backhand side.",
    "{ll} dumps the backhand into the net.",
    "The backhand from {ll} goes long. Easy point for {wl}.",
    "Weak backhand from {ll} — error.",
    "{ll} can't handle the rally and puts a backhand wide.",
    "The backhand lets {ll} down. Unforced error.",
    "{ll} frames the backhand. Point to {wl}.",
    "Poor shot selection from {ll}. The backhand floats long.",
    "That backhand from {ll} lacked conviction. Error.",
    "Loose backhand from {ll}. {wl} stays solid.",
    "{ll} nets a routine backhand. Unforced error.",
    "Nervous backhand from {ll} goes wide.",
    "Sloppy from {ll} on the backhand. Free point.",
]

# Generic errors for dropshot/volley etc.
_UNFORCED_ERROR_GENERIC = [
    "Error from {ll}! The shot finds the net.",
    "{ll} makes an unforced error. Point {wl}.",
    "Loose shot from {ll}. {wl} picks up a free point.",
    "That shot from {ll} was never going in.",
    "A rare mistake from {ll}. {wl} benefits.",
    "The shot from {ll} drifts wide. Unforced error.",
    "{ll} overhits and it's an error.",
    "Tentative shot from {ll} falls short. Point to {wl}.",
]

# Long rally commentary (prepended)
_LONG_RALLY_PREFIX = [
    "After a gruelling {rally}-shot rally, ",
    "What a rally! {rally} shots traded and ",
    "An incredible {rally}-shot exchange ends as ",
    "Back and forth for {rally} shots! Finally, ",
    "{rally} shots of intense baseline tennis! ",
    "Neither player gives an inch across {rally} shots — ",
    "A marathon rally of {rally} shots concludes: ",
    "Exhausting. {rally} shots before ",
]

# Break-related commentary (appended)
_BREAK_COMMENTS = [
    "That's a break of serve!",
    "Huge break! {wl} breaks the serve!",
    "Break point converted! Momentum shifts to {wl}.",
    "{wl} breaks! The pressure was too much for {ll}.",
    "The serve is broken! {wl} seizes the initiative.",
    "Crucial break for {wl}!",
]

# Score-context commentary (appended for big moments)
_SET_WON = [
    "{wl} takes the set!",
    "Set to {wl}!",
    "{wl} wraps up the set!",
    "That seals the set for {wl}!",
    "And {wl} closes out the set!",
]

_MATCH_WON = [
    "{wl} wins the match!",
    "Game, set, match — {w}!",
    "{wl} clinches the victory!",
    "It's all over! {wl} wins!",
    "And that's the match! {wl} triumphs!",
    "{wl} completes the win!",
]

# Archetype / skill flavor (optional extra sentence)
_SKILL_FLAVOR = {
    "forehand": [
        "That forehand is a weapon.",
        "The forehand has been devastating today.",
        "{wl}'s forehand is on fire.",
        "Nobody wants to rally into that forehand.",
        "Built around that massive forehand.",
    ],
    "backhand": [
        "The backhand is world-class.",
        "{wl}'s backhand has been phenomenal.",
        "That backhand just keeps finding the target.",
        "A backhand to die for.",
    ],
    "serve": [
        "{wl}'s serve is a real weapon today.",
        "The serve has been firing all match.",
        "Hard to break when you serve like that.",
        "Huge serving from {wl}.",
    ],
    "speed": [
        "{wl}'s court coverage is remarkable.",
        "The footwork from {wl} is extraordinary.",
        "Nobody covers the court like {wl}.",
        "Lightning-fast movement from {wl}.",
    ],
    "stamina": [
        "{wl} shows no signs of fatigue.",
        "The fitness of {wl} is paying dividends.",
        "{wl} is built for these long rallies.",
        "Relentless physicality from {wl}.",
    ],
    "dropshot": [
        "What touch {wl} has!",
        "The hands on {wl} are magical.",
        "{wl}'s feel for the ball is outstanding.",
        "Soft hands from {wl}.",
    ],
    "volley": [
        "{wl} is so comfortable at the net.",
        "The net game from {wl} is superb.",
        "{wl}'s volleying has been clinical.",
        "Dominant at the net.",
    ],
}

# Tournament round flavor
_ROUND_FLAVOR = {
    "Final": [
        "This is what finals are all about!",
        "High stakes in this final!",
        "What a moment in this final!",
        "Nerves of steel in this final.",
    ],
    "Semi-Final": [
        "A huge point in this semi-final!",
        "One step from the final!",
        "Semi-final drama!",
    ],
    "Quarter-Final": [
        "Big moment in the quarter-finals!",
        "Quarter-final tennis at its finest.",
    ],
}

# Age-related flavor for young players
_YOUNG_PLAYER_FLAVOR = [
    "Incredible maturity from the {age}-year-old {wl}!",
    "Just {age} years old, and {wl} is already playing like a veteran.",
    "{wl} shows wisdom beyond his {age} years.",
    "The future looks bright for {age}-year-old {wl}!",
    "Remarkable composure for a {age}-year-old!",
]

# High-skill flavor (when winning shot skill >= 85)
_HIGH_SKILL_SHOT = [
    "{wl}'s {shot} rating of {skill_val} really shows here.",
    "When your {shot} is rated {skill_val}, shots like that are routine.",
    "A {skill_val}-rated {shot} — that's elite.",
]

# Comeback flavor (winning from behind)
_COMEBACK_FLAVOR = [
    "{wl} is fighting back!",
    "{wl} refuses to go away!",
    "Don't count {wl} out just yet!",
    "{wl} is clawing his way back into this!",
    "Resilience from {wl}!",
]

# Dominance flavor (when one player is cruising)
_DOMINANCE_FLAVOR = [
    "{wl} is in total control.",
    "Complete domination from {wl}.",
    "{wl} is making this look effortless.",
    "{ll} has no answers right now.",
    "{wl} is running away with this.",
]


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_commentary(
    point_summary: dict,
    score_info: dict,
    player1: dict,
    player2: dict,
    tournament: dict | None = None,
) -> str:
    """
    Build a commentary line for the just-completed point.

    Parameters
    ----------
    point_summary : dict from game_engine ('point_summary' event)
    score_info    : dict from game_engine ('score' event — post-point)
    player1, player2 : full player dicts (with skills, age, name, archetype …)
    tournament    : tournament dict (optional, for round / prestige context)
    """
    if not point_summary:
        return ""

    winner_id = point_summary["winner_id"]
    loser_id = point_summary["loser_id"]

    # Resolve winner / loser player dicts
    if player1["id"] == winner_id:
        winner, loser = player1, player2
    else:
        winner, loser = player2, player1

    shot = point_summary.get("winning_shot", "forehand")
    is_ace = point_summary.get("is_ace", False)
    rally = point_summary.get("rally_length", 1)
    ball_y = point_summary.get("ball_y", 300)
    is_break = point_summary.get("is_break", False)
    center = _is_center_y(ball_y)

    fmt = {
        "w": winner["name"],
        "wf": _first_name(winner["name"]),
        "wl": _last_name(winner["name"]),
        "l": loser["name"],
        "lf": _first_name(loser["name"]),
        "ll": _last_name(loser["name"]),
        "shot": shot,
        "rally": rally,
    }

    parts: list[str] = []

    # ---- 1. Long-rally prefix (rally >= 8) ----
    if rally >= 8:
        parts.append(random.choice(_LONG_RALLY_PREFIX).format(**fmt))

    # ---- 2. Core shot description ----
    if is_ace:
        parts.append(random.choice(_ACE_TEMPLATES).format(**fmt))
    elif center and not is_ace and shot in ("forehand", "backhand", "volley"):
        # Unforced error framing
        if shot == "forehand":
            parts.append(random.choice(_UNFORCED_ERROR_FH).format(**fmt))
        elif shot == "backhand":
            parts.append(random.choice(_UNFORCED_ERROR_BH).format(**fmt))
        else:
            parts.append(random.choice(_UNFORCED_ERROR_GENERIC).format(**fmt))
    elif center and shot == "dropshot":
        # Dropshot near center = bad dropshot from loser usually, but winner
        # description is fine since dropshots land near net
        parts.append(random.choice(_DROPSHOT_WINNER).format(**fmt))
    else:
        # Real winner
        if shot == "forehand":
            if center:
                parts.append(random.choice(_FOREHAND_WINNER_CENTER).format(**fmt))
            else:
                parts.append(random.choice(_FOREHAND_WINNER).format(**fmt))
        elif shot == "backhand":
            if center:
                parts.append(random.choice(_BACKHAND_WINNER_CENTER).format(**fmt))
            else:
                parts.append(random.choice(_BACKHAND_WINNER).format(**fmt))
        elif shot == "dropshot":
            parts.append(random.choice(_DROPSHOT_WINNER).format(**fmt))
        elif shot == "volley":
            parts.append(random.choice(_VOLLEY_WINNER).format(**fmt))
        elif shot == "serve":
            parts.append(random.choice(_ACE_TEMPLATES).format(**fmt))
        else:
            parts.append(f"{_last_name(winner['name'])} wins the point!")

    # ---- 3. Break comment (30 % chance or always on first break) ----
    if is_break and random.random() < 0.4:
        parts.append(random.choice(_BREAK_COMMENTS).format(**fmt))

    # ---- 4. Score-context: set / match won ----
    sets = score_info.get("sets", []) if score_info else []
    current_set = score_info.get("current_set", {}) if score_info else {}
    p1g = current_set.get("player1", 0)
    p2g = current_set.get("player2", 0)

    # Detect if this point just won a set
    winner_key = "player1" if winner_id == player1["id"] else "player2"
    wg = p1g if winner_key == "player1" else p2g
    lg = p2g if winner_key == "player1" else p1g
    set_won = (wg >= 6 and wg - lg >= 2) or (wg == 7 and lg == 6)
    if set_won:
        # Check if match is over (enough sets won)
        sets_won_by_winner = sum(
            1 for s in sets
            if (winner_key == "player1" and _set_won_by_p1(s))
            or (winner_key == "player2" and _set_won_by_p2(s))
        )
        sets_to_win = 3 if tournament and tournament.get("category") in ("Grand Slam", "Special") else 2
        if sets_won_by_winner + 1 >= sets_to_win:
            parts.append(random.choice(_MATCH_WON).format(**fmt))
        else:
            parts.append(random.choice(_SET_WON).format(**fmt))

    # ---- 5. Skill flavor (20 % chance, when winner skill is high) ----
    if random.random() < 0.20:
        top = _top_skill(winner)
        if top in _SKILL_FLAVOR:
            parts.append(random.choice(_SKILL_FLAVOR[top]).format(**fmt))

    # ---- 6. High-skill specific shot (15 % chance) ----
    if random.random() < 0.15 and shot in ("forehand", "backhand", "serve", "dropshot", "volley"):
        val = _skill_value(winner, shot)
        if val >= 80:
            tpl = random.choice(_HIGH_SKILL_SHOT)
            parts.append(tpl.format(**fmt, skill_val=val))

    # ---- 7. Young player flavor (10 % chance, age <= 20) ----
    w_age = winner.get("age", 30)
    if w_age <= 20 and random.random() < 0.12:
        parts.append(random.choice(_YOUNG_PLAYER_FLAVOR).format(**fmt, age=w_age))

    # ---- 8. Tournament round flavor (10 % chance) ----
    if tournament and random.random() < 0.10:
        round_name = _current_round_label(tournament)
        if round_name in _ROUND_FLAVOR:
            parts.append(random.choice(_ROUND_FLAVOR[round_name]).format(**fmt))

    # ---- 9. Comeback / dominance flavor (based on set score) ----
    if random.random() < 0.12:
        if wg < lg and lg - wg >= 2:
            parts.append(random.choice(_COMEBACK_FLAVOR).format(**fmt))
        elif wg > lg and wg - lg >= 3:
            parts.append(random.choice(_DOMINANCE_FLAVOR).format(**fmt))

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Small helpers for score analysis
# ---------------------------------------------------------------------------

def _set_won_by_p1(score_tuple):
    p1, p2 = score_tuple
    return (p1 >= 6 and p1 - p2 >= 2) or (p1 == 7 and p2 == 6)


def _set_won_by_p2(score_tuple):
    p1, p2 = score_tuple
    return (p2 >= 6 and p2 - p1 >= 2) or (p2 == 7 and p1 == 6)


def _current_round_label(tournament: dict) -> str:
    """Derive a human-readable round label from the tournament dict."""
    bracket = tournament.get("bracket", {})
    current_round = tournament.get("current_round", 0)
    total_rounds = len(bracket) if bracket else 0
    if total_rounds == 0:
        return ""
    remaining = total_rounds - current_round
    labels = {0: "Final", 1: "Semi-Final", 2: "Quarter-Final"}
    return labels.get(remaining, f"Round {current_round + 1}")
