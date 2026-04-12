import random
import math

# Surface gameplay effects: modifiers applied during match simulation.
# Each surface makes certain shots/mechanics naturally stronger or weaker.
# Format: {surface: {effect_key: multiplier}}
#   serve_power    – multiplied onto serve shot_power
#   forehand_power – multiplied onto forehand shot_power
#   lift_power     – multiplied onto lift base_power
#   volley_power   – multiplied onto volley base_power
#   straight_prec  – multiplied onto straight precision_skill
#   slice_stamina  – multiplied onto stamina drain when receiving a slice
#   stamina_drain  – multiplied onto all per-rally stamina drain
#   speed          – multiplied onto effective speed in can_catch
SURFACE_EFFECTS = {
    "clay":    {"stamina_drain": 0.8, "lift_power": 1.05, "dropshot_power": 1.05},
    "grass":   {"serve_power": 1.05, "slice_stamina": 1.7, "backhand_power": 1.05},
    "hard":    {"forehand_power": 1.05, "speed": 1.05, "cross_prec": 1.05},
    "indoor":  {"volley_power": 1.05, "straight_prec": 1.05, "serve_power": 1.05},
}

class GameEngine:
    SURFACES = ["clay", "grass", "hard", "indoor"]
    
    def __init__(self, player1, player2, surface, sets_to_win=2):
        """
        Initialize the game engine with two players.
        Each player is a dictionary containing stats like serve, forehand, backhand, speed, etc.
        """
        self.surface = surface
        self.surface_fx = SURFACE_EFFECTS.get(surface, {})
        self.original_player1 = player1
        self.original_player2 = player2
        self.p1 = self._apply_random_form(player1.copy())
        self.p2 = self._apply_random_form(player2.copy())
        self.games = {"player1": 0, "player2": 0}  # Games won in the current set
        self.sets = {"player1": 0, "player2": 0}  # Sets won in the match
        self.set_scores = []  # Track the scores of each set as tuples (player1_games, player2_games)
        self.current_server = self.p1  # Player 1 serves first by default
        self.current_receiver = self.p2
        self.sets_to_win = sets_to_win
        self.match_log = []

        # Track player positions: "right" or "left"
        self.positions = {player1["id"]: "right", player2["id"]: "left"}

        # Track stamina and speed for each player
        # match_stamina: persistent 0-100 pool that drains over the match
        self.match_stamina = {player1["id"]: 100.0, player2["id"]: 100.0}
        self.speed = {player1["id"]: player1["skills"]["speed"], player2["id"]: player2["skills"]["speed"]}
        self.last_shot_power = 0  # Initialize last shot power
        self.last_shot_precision = 50
        
        # Track volley mode for each player (once a player hits a volley, they can only hit volleys)
        self.volley_mode = {player1["id"]: False, player2["id"]: False}
        
        # Track match statistics for each player
        self.match_stats = {
            player1["id"]: {
                "aces": 0,
                "breaks": 0,
                "forehand_winners": 0,
                "backhand_winners": 0,
                "dropshot_winners": 0,
                "volley_winners": 0,
                "lift_winners": 0,
                "slice_winners": 0
            },
            player2["id"]: {
                "aces": 0,
                "breaks": 0,
                "forehand_winners": 0,
                "backhand_winners": 0,
                "dropshot_winners": 0,
                "volley_winners": 0,
                "lift_winners": 0,
                "slice_winners": 0
            }
        }
        # Track the last shot type for winner classification
        self.last_shot_type = None

    def _stamina_snapshot(self):
        """Return a dict with both players' match stamina as fraction 0.0-1.0."""
        return {
            self.p1['id']: max(0.0, self.match_stamina[self.p1['id']] / 100.0),
            self.p2['id']: max(0.0, self.match_stamina[self.p2['id']] / 100.0),
        }
        
    def _apply_random_form(self, player):
        """Apply random form multiplier to all skills"""
        form_multiplier = random.uniform(0.975, 1.025)
        player_copy = player.copy()
        player_copy["skills"] = {
            skill: min(100, math.floor(value * form_multiplier))
            for skill, value in player["skills"].items()
        }
        return player_copy

    def update_sets(self, winner_key):
        """
        Update the sets won in the match based on the winner of the set.
        """
        self.sets[winner_key] += 1
        
        # Add the current set score to the set_scores list
        self.set_scores.append((self.games["player1"], self.games["player2"]))

        # Reset games for the next set
        self.games = {"player1": 0, "player2": 0}

    def format_set_scores(self):
        """
        Format the set scores as a string (e.g., "6-4, 7-5").
        """
        return ", ".join(f"{p1}-{p2}" for p1, p2 in self.set_scores)

    def simulate_match(self, visualize=False):
        """
        Simulate a full match until one player wins.
        If visualize=True, yields point events for visualization.
        """
        if visualize:
            return self._simulate_match_visualize()
        else:
            return self._simulate_match_normal()

    def _simulate_match_visualize(self):
        """Simulate match with visualization (yields events)"""
        while not self.is_match_over():
            while not self.is_set_over():
                winner_key, point_events = self.simulate_point(visualize=True)
                # Update games and stats BEFORE yielding so the point_events reflect the updated state
                self.update_games(winner_key)
                
                # Update the score event in point_events with the current score and stats AFTER the point was won
                if point_events and point_events[0]['type'] == 'score':
                    point_events[0]['current_set'] = {'player1': self.games['player1'], 'player2': self.games['player2']}
                    point_events[0]['match_stats'] = {
                        'player1': self.match_stats[self.p1['id']].copy(),
                        'player2': self.match_stats[self.p2['id']].copy()
                    }
                
                point_data = {
                    'type': 'point',
                    'events': point_events,
                    'winner': winner_key
                }
                yield point_data
                self.current_server, self.current_receiver = self.current_receiver, self.current_server
            set_winner_key = self.is_set_over()
            self.update_sets(set_winner_key)
            self.recover_set_stamina()

        if self.sets["player1"] == self.sets_to_win:
            match_winner = self.p1
        elif self.sets["player2"] == self.sets_to_win:
            match_winner = self.p2
        else:
            # This should never happen if match simulation is correct
            raise ValueError(f"Match ended without a winner! Sets: P1={self.sets['player1']}, P2={self.sets['player2']}")

        self.match_log.append(
            f"{match_winner['name']} wins the match! Final Score: {self.format_set_scores()}"
        )
        yield {'type': 'match_end', 'winner': match_winner}

    def _simulate_match_normal(self):
        """Simulate match without visualization (returns winner)"""        
        while not self.is_match_over():
            while not self.is_set_over():
                winner_key = self.simulate_point(visualize=False)
                self.update_games(winner_key)
                self.current_server, self.current_receiver = self.current_receiver, self.current_server

            set_winner_key = self.is_set_over()
            self.update_sets(set_winner_key)
            self.recover_set_stamina()
        
        if self.sets["player1"] == self.sets_to_win:
            match_winner = self.p1
        elif self.sets["player2"] == self.sets_to_win:
            match_winner = self.p2
        else:
            # This should never happen if match simulation is correct
            raise ValueError(f"Match ended without a winner! Sets: P1={self.sets['player1']}, P2={self.sets['player2']}")

        self.match_log.append(
            f"{match_winner['name']} wins the match! Final Score: {self.format_set_scores()}"
        )
        return match_winner
    
    def _is_important_point(self):
        """
        Determine if the current point is an 'important point' where mental stat matters.
        Important points: set points, match points, and break points.
        Returns a dict mapping player_key -> True if that player is facing pressure
        (i.e. their opponent has a set/match/break point).
        Both players are considered under pressure during important points.
        """
        p1_games = self.games["player1"]
        p2_games = self.games["player2"]
        p1_sets = self.sets["player1"]
        p2_sets = self.sets["player2"]

        important = False

        # Set point: one player is one game away from winning the set
        # (at 5-x with x<5, or 6-5, or 6-6 tiebreak scenarios)
        if (p1_games >= 5 and p1_games > p2_games) or (p2_games >= 5 and p2_games > p1_games):
            important = True

        # Match point: one player is one game from winning the set AND 
        # that set win would give them the match
        if (p1_games >= 5 and p1_games > p2_games and p1_sets == self.sets_to_win - 1):
            important = True
        if (p2_games >= 5 and p2_games > p1_games and p2_sets == self.sets_to_win - 1):
            important = True

        # Tiebreak (6-6) is always important
        if p1_games == 6 and p2_games == 6:
            important = True

        return important

    def _get_mental_modifier(self, player):
        """
        Calculate the mental stat modifier for important points.
        Mental stat of 50 = neutral (no change).
        Formula: skills * (1 + (mental - 50) / 500)
        At mental 80: +6% boost. At mental 20: -6% penalty.
        Range is roughly -10% to +10%.
        """
        mental = player["skills"].get("mental", 50)
        return 1.0 + (mental - 50) / 500.0

    def _apply_mental_boost(self):
        """Apply mental modifier to both players' skills during important points."""
        self._mental_backup = {}
        for player in [self.p1, self.p2]:
            modifier = self._get_mental_modifier(player)
            self._mental_backup[player["id"]] = player["skills"].copy()
            player["skills"] = {
                skill: min(100, math.floor(value * modifier)) if skill != "mental" else value
                for skill, value in player["skills"].items()
            }
            # Update speed tracking with both mental boost and stamina modifier
            self.speed[player["id"]] = int(player["skills"]["speed"] * self._get_stamina_speed_modifier(player))

    def _revert_mental_boost(self):
        """Revert mental modifier after the point is over."""
        if hasattr(self, '_mental_backup'):
            for player in [self.p1, self.p2]:
                if player["id"] in self._mental_backup:
                    player["skills"] = self._mental_backup[player["id"]]
            del self._mental_backup

    def simulate_point(self, visualize=False):
        """
        Simulate a single point in the match.
        Returns the winner of the point (player1 or player2), or (winner, events) if visualize=True.
        """
        # Apply mental boost if this is an important point
        is_important = self._is_important_point()
        if is_important:
            self._apply_mental_boost()

        server = self.current_server
        receiver = self.current_receiver
        hitter = server
        defender = receiver
        
        # Initialize visualization events if needed
        point_events = None
        if visualize:
            point_events = [{
                'type': 'score',
                'sets': self.set_scores.copy(),  # Previous set scores
                'current_set': {'player1': self.games['player1'], 'player2': self.games['player2']},
                'player1_name': self.p1['name'],
                'player2_name': self.p2['name'],
                'match_stats': {
                    'player1': self.match_stats[self.p1['id']].copy(),
                    'player2': self.match_stats[self.p2['id']].copy()
                }
            }]

        # Step 1: Server makes the first shot
        shot_direction = self.choose_shot_direction(hitter, opponent=defender)
        # Determine shot_leftright based on hitter's position and shot_direction
        shot_leftright = "left" if shot_direction == "cross" else "right"
        shot_power, shot_precision, shot_direction = self.calculate_shot(hitter, "serve", shot_direction, 1)
        side = "left" if self._get_player_key(defender) == "player1" else "right"
        ball_side, target_x, target_y = self.get_ball_coordinates(
            side, shot_power, shot_leftright, None  # No precision for serve
        )
        
        # Add serve visualization
        if visualize:
            point_events.append({
                'type': 'shot',
                'shot_type': 'serve',
                'ball_positions': [{
                    'type': 'ball_position',
                    'x': target_x,
                    'y': target_y,
                    'power': shot_power,
                }],
                'hitter_id': hitter['id'],
                'stamina': self._stamina_snapshot(),
            })
        rally_length = 1

        # Update positions based on the shot
        self.update_positions(defender, shot_leftright)

        # Step 2: Receiver tries to catch the shot
        caught, return_multiplier = self.can_catch(defender, shot_power, shot_precision, shot_type="serve", hitter=hitter)
        if not caught:  # Missed shot
            # Add the final ball position for the serve with a message indicator
            if visualize:
                point_events.append({
                    'type': 'shot',
                    'shot_type': 'serve',
                    'ball_positions': [{
                        'type': 'ball_position',
                        'x': target_x,
                        'y': target_y,
                        'power': shot_power,
                    }],
                    'hitter_id': hitter['id'],
                    'is_final': True,
                    'stamina': self._stamina_snapshot(),
                })            
            self.reset_stamina_and_speed()
            winner_key = self._get_player_key(hitter)
            # Track ace
            self.match_stats[hitter['id']]["aces"] += 1
            if visualize:
                point_events.append({
                    'type': 'point_summary',
                    'winner_id': hitter['id'],
                    'loser_id': defender['id'],
                    'winning_shot': 'serve',
                    'is_ace': True,
                    'rally_length': rally_length,
                    'ball_y': target_y,
                    'server_id': server['id'],
                    'is_break': False,
                })
            return (winner_key, point_events) if visualize else winner_key

        # Step 3: Alternate shots until someone misses
        # Continue rally until someone misses
        while True:
            # Receiver becomes the hitter
            hitter, defender = defender, hitter
            shot_direction = self.choose_shot_direction(hitter, opponent=defender)
            # Determine shot type: dropshot/volley/lift/slice/forehand/backhand
            if shot_direction in ("cross", "straight"):
                shot_type = self.determine_shot_type(hitter, shot_leftright)
            elif shot_direction in ("lift", "slice"):
                shot_type = shot_direction
                # Determine actual ball direction based on cross/straight tendencies
                c_w = max(1, hitter.get("cross_tend", 50))
                s_w = max(1, hitter.get("straight_tend", 50))
                shot_direction = random.choices(["cross", "straight"], weights=[c_w, s_w], k=1)[0]
            else:
                shot_type = shot_direction
            
            # If hitter chooses to hit a volley, activate volley mode
            if shot_type == "volley":
                self.volley_mode[hitter["id"]] = True

            # Determine shot_leftright for visualization/positioning
            hitter_position = self.positions[hitter["id"]]
            if hitter_position == "right":
                shot_leftright = "left" if shot_direction == "cross" else "right"
            else:
                shot_leftright = "right" if shot_direction == "cross" else "left"

            shot_power, shot_precision, shot_direction = self.calculate_shot(hitter, shot_type, shot_direction, return_multiplier)
            side = "left" if self._get_player_key(defender) == "player1" else "right"
            
            # For dropshot, calculate success before getting coordinates
            shot_success = None
            if shot_type == "dropshot":
                dropshot_skill = hitter["skills"].get("dropshot", 30)
                success_chance = max(0.05, min(0.95, (dropshot_skill - self.last_shot_power + 100) / 200))
                shot_success = random.random() < success_chance
            
            # Get ball coordinates with dropshot/volley success info
            # For dropshot, always use success coordinates (ball near net)
            ball_coords_success = True if shot_type == "dropshot" else shot_success
            ball_side, ball_row, ball_col = self.get_ball_coordinates(
                side, shot_power, shot_leftright, shot_precision, shot_type, ball_coords_success
            )
            self.update_positions(defender, shot_leftright)

            rally_length += 1
            if visualize:
                point_events.append({
                    'type': 'shot',
                    'shot_type': shot_type,
                    'ball_positions': [{
                        'type': 'ball_position',
                        'x': ball_row,
                        'y': ball_col,
                        'power': shot_power,
                    }],
                    'hitter_id': hitter['id'],
                    'stamina': self._stamina_snapshot(),
                })

            # Dropshot/volley mechanics
            if shot_type == "dropshot":
                if shot_success:
                    defender_speed = self.speed[defender["id"]]
                    diff = defender_speed - dropshot_skill
                    if diff < 0:
                        self.reset_stamina_and_speed()
                        winner_key = self._get_player_key(hitter)
                        self.match_stats[hitter['id']]["dropshot_winners"] += 1
                        # Track break
                        if self._get_player_key(hitter) != self._get_player_key(server):
                            self.match_stats[hitter['id']]["breaks"] += 1
                        return (winner_key, point_events) if visualize else winner_key
                    elif diff < 2:
                        return_multiplier = 0.3
                    elif diff < 4:
                        return_multiplier = 0.4
                    elif diff < 6:
                        return_multiplier = 0.5
                    elif diff <= 7:
                        return_multiplier = 0.6
                    else:  # diff > 7
                        return_multiplier = 0.75
                else:
                    return_multiplier = 2.0  # For missed dropshot

            # Handle catching
            if shot_type == "dropshot":
                # Dropshot: opponent always catches (if not already a winner which returned above)
                caught = True
                if self.volley_mode[defender["id"]]:
                    return_multiplier = 3
                self.volley_mode[defender["id"]] = True
            else:
                # For all other shots, use the normal can_catch logic
                caught, catch_return_multiplier = self.can_catch(defender, shot_power, shot_precision, shot_type, hitter=hitter)
                return_multiplier = catch_return_multiplier

            # Lift: weak lifts give opponent a better return multiplier
            if shot_type == "lift" and caught and shot_power < 35:
                return_multiplier = max(return_multiplier, 1.3 + (35 - shot_power) / 50)

            if not caught:
                side = "left" if self._get_player_key(defender) == "player1" else "right"
                ball_side, target_x, target_y = self.get_ball_coordinates(
                    side, shot_power, shot_leftright, shot_precision, shot_type, shot_success
                )
                if visualize:
                    point_events.append({
                        'type': 'shot',
                        'shot_type': shot_type,
                        'ball_positions': [{
                            'type': 'ball_position',
                            'x': target_x,
                            'y': target_y,
                            'power': shot_power,
                        }],
                        'hitter_id': hitter['id'],
                        'stamina': self._stamina_snapshot(),
                    })
                self.reset_stamina_and_speed()
                winner_key = self._get_player_key(hitter)
                
                # Track winner by shot type
                if shot_type == "forehand":
                    self.match_stats[hitter['id']]["forehand_winners"] += 1
                elif shot_type == "backhand":
                    self.match_stats[hitter['id']]["backhand_winners"] += 1
                elif shot_type == "dropshot":
                    self.match_stats[hitter['id']]["dropshot_winners"] += 1
                elif shot_type == "volley":
                    self.match_stats[hitter['id']]["volley_winners"] += 1
                elif shot_type == "lift":
                    self.match_stats[hitter['id']]["lift_winners"] += 1
                elif shot_type == "slice":
                    self.match_stats[hitter['id']]["slice_winners"] += 1
                
                # Track break (point won by non-server while not on serve)
                is_break = self._get_player_key(hitter) != self._get_player_key(server)
                if is_break:
                    self.match_stats[hitter['id']]["breaks"] += 1
                
                if visualize:
                    point_events.append({
                        'type': 'point_summary',
                        'winner_id': hitter['id'],
                        'loser_id': defender['id'],
                        'winning_shot': shot_type,
                        'is_ace': False,
                        'rally_length': rally_length,
                        'ball_y': target_y,
                        'server_id': server['id'],
                        'is_break': is_break,
                    })
                
                return (winner_key, point_events) if visualize else winner_key

            self.reduce_stamina(defender, shot_precision, shot_type=shot_type)

    def calculate_shot(self, player, shot_type, direction, previous_multiplier=1):
        """
        Calculate the power and placement of a shot based on the player's stats.
        Adjust shot power based on how comfortably the player catches the ball.
        For dropshot, use their own skill for both power and precision.
        Volleys get a power boost based on volley skill (upside of volley mode).
        Lift: power boost over neutral, low precision scaling with lift skill.
        Slice: very high precision, power malus scaling with slice skill.
        """
        fx = self.surface_fx

        if shot_type == "dropshot":
            base_power = player["skills"].get(shot_type, 30) * previous_multiplier
            # Surface: clay boosts dropshot power
            base_power *= fx.get("dropshot_power", 1.0)
            precision_skill = player["skills"].get(shot_type, 30)
        elif shot_type == "lift":
            lift_skill = player["skills"].get("lift", 30)
            # Power boost compared to neutral shots
            base_power = lift_skill * previous_multiplier * 1.3
            # Surface: clay boosts lift power
            base_power *= fx.get("lift_power", 1.0)
            # Low precision that scales with lift skill
            precision_skill = max(5, int(lift_skill * 0.4 + 5))
        elif shot_type == "slice":
            slice_skill = player["skills"].get("slice", 30)
            # Power malus: low slice = very low power, high slice = moderate power
            power_factor = 0.2 + (slice_skill / 100) * 0.5  # 0.2 to 0.7
            base_power = slice_skill * previous_multiplier * power_factor
            # Very high precision compared to neutral shots
            precision_skill = min(95, int(slice_skill * 1.2 + 20))
        else:
            base_power = player["skills"][shot_type] * previous_multiplier
            precision_skill = player["skills"][direction]

            # Surface: grass boosts backhand power
            if shot_type == "backhand":
                base_power *= fx.get("backhand_power", 1.0)

            # Volley power boost: 1.[volley_stat-10], simulating time compression for opponent
            if shot_type == "volley":
                volley_skill = player["skills"].get("volley", 30)
                volley_power_boost = 1.0 + max(0, (volley_skill - 30) / 100)  # 1.0 to 1.5x
                base_power = base_power * volley_power_boost
                # Surface: indoor boosts volley power
                base_power *= fx.get("volley_power", 1.0)

            # Surface: hard boosts forehand power
            if shot_type == "forehand":
                base_power *= fx.get("forehand_power", 1.0)

            # Surface: indoor boosts straight precision, hard boosts cross precision
            if direction == "straight":
                precision_skill = int(precision_skill * fx.get("straight_prec", 1.0))
            if direction == "cross":
                precision_skill = int(precision_skill * fx.get("cross_prec", 1.0))
        
        precision = self._weighted_random_precision(precision_skill)

        # Special handling for serves
        if shot_type == "serve":
            power_multiplier = random.uniform(0.5, 1.3)  # Serve gets a special bonus range
            # Surface: grass boosts serve power
            power_multiplier *= fx.get("serve_power", 1.0)
        else:
            last_shot_power = self.last_shot_power
            if last_shot_power <= 10:
                power_multiplier = random.uniform(1, 1.5)
            elif 10 < last_shot_power <= 20:
                power_multiplier = random.uniform(0.9, 1.5)
            elif 20 < last_shot_power <= 30:
                power_multiplier = random.uniform(0.8, 1.4)
            elif 30 < last_shot_power <= 40:
                power_multiplier = random.uniform(0.7, 1.4)
            elif 40 < last_shot_power <= 50:
                power_multiplier = random.uniform(0.6, 1.3)
            elif 50 < last_shot_power <= 60:
                power_multiplier = random.uniform(0.5, 1.3)
            elif 60 < last_shot_power <= 70:
                power_multiplier = random.uniform(0.4, 1.2)
            elif 70 < last_shot_power <= 80:
                power_multiplier = random.uniform(0.3, 1.2)
            elif 80 < last_shot_power <= 90:
                power_multiplier = random.uniform(0.2, 1.1)
            elif 90 < last_shot_power <= 100:
                power_multiplier = random.uniform(0.1, 1)
            else:
                power_multiplier = random.uniform(0, 0.8)

        shot_power = round(base_power * power_multiplier * self._get_stamina_power_modifier(player))
        self.last_shot_power = shot_power
        return shot_power, precision, direction
    
    def _weighted_random_precision(self, skill):
        # Use triangular distribution with mode at skill value
        precision = random.triangular(1, 100, skill)
        return min(100, max(1, round(precision)))

    def _get_stamina_speed_modifier(self, player):
        """Speed penalty when match_stamina drops below 40%.
        At 40: no penalty. At 0: -25% speed."""
        ms = self.match_stamina[player["id"]]
        if ms >= 40:
            return 1.0
        return 1.0 - (40 - ms) / 40 * 0.25

    def _get_stamina_power_modifier(self, player):
        """Power penalty when match_stamina drops below 20%.
        At 20: no penalty. At 0: -30% power."""
        ms = self.match_stamina[player["id"]]
        if ms >= 20:
            return 1.0
        return 1.0 - (20 - ms) / 20 * 0.30

    def reduce_stamina(self, player, opponent_shot_precision, shot_type=None):
        """
        Small per-catch drain for rally-length sensitivity and visual feedback.
        The main stamina drain happens per-point in reset_stamina_and_speed.
        Receiving a slice costs 1.5x stamina (1.7x on grass).
        Surface stamina_drain modifier (e.g. clay 0.8x) applies to all drain.
        """
        fx = self.surface_fx
        stamina_skill = max(1, player["skills"]["stamina"])
        drain = opponent_shot_precision / (stamina_skill * 10.0)
        # Slices wear down the receiver (grass amplifies this further)
        if shot_type == "slice":
            drain *= fx.get("slice_stamina", 1.5)
        # Surface stamina drain modifier (e.g. clay = 0.8x → less drain)
        drain *= fx.get("stamina_drain", 1.0)
        self.match_stamina[player["id"]] = max(0, self.match_stamina[player["id"]] - drain)
        # Update speed with current stamina penalty
        self.speed[player["id"]] = int(player["skills"]["speed"] * self._get_stamina_speed_modifier(player))

    def reset_stamina_and_speed(self):
        """
        Called after each point. Applies the main per-point stamina drain (every point
        costs energy regardless of rally length), then a tiny recovery between points.
        Also resets volley mode and reverts mental boost.
        """
        self._revert_mental_boost()
        for player in [self.p1, self.p2]:
            stamina_skill = max(1, player["skills"]["stamina"])
            # Per-game drain: each game costs significant energy
            drain = 3.5 * (100.0 / (stamina_skill + 50))
            self.match_stamina[player["id"]] = max(0, self.match_stamina[player["id"]] - drain)
            # Small recovery between games
            recovery = stamina_skill / 100.0
            self.match_stamina[player["id"]] = min(100.0, self.match_stamina[player["id"]] + recovery)
            # Update speed with current stamina penalty
            self.speed[player["id"]] = int(player["skills"]["speed"] * self._get_stamina_speed_modifier(player))
            self.volley_mode[player["id"]] = False

    def recover_set_stamina(self):
        """Bigger stamina recovery between sets (changeover rest)."""
        for player in [self.p1, self.p2]:
            recovery = player["skills"]["stamina"] / 8.0
            self.match_stamina[player["id"]] = min(100.0, self.match_stamina[player["id"]] + recovery)

    def can_catch(self, player, shot_power, shot_precision, shot_type, hitter=None):
        """
        Determine if the player can catch the shot based on their speed and shot power.
        If hitter is in volley mode, precision_factor is increased by 1.1x (downside of volley mode).
        """
        # Effective speed (surface modifier, e.g. hard ×1.2)
        eff_speed = self.speed[player["id"]] * self.surface_fx.get("speed", 1.0)

        # Special case for serve returns
        if shot_type == "serve":  # Default serve precision
            # Simple serve return check: if serve power > speed, can't return
            if shot_power > eff_speed:
                return False, 0
            elif (eff_speed - shot_power) <= 10:
                return True, 0.8
            else:
                # Good return gets full power
                return True, 1.0
        
        # Base catch chance (speed vs power)
        speed_power_ratio = max(1, shot_power) / eff_speed
        # Precision factor (0.5-1.5) - higher precision makes catching harder
        precision_factor = 0.3 + (shot_precision / 70)
        # If catcher (player) is in volley mode, precision factor is harder (downside of volley mode)
        if self.volley_mode[player["id"]]:
            precision_factor *= 1.85
        # Combined catch score
        catch_score = speed_power_ratio * precision_factor
        # Determine if caught based on catch score
        if catch_score > 1.3:  # Missed
            return False, 0 
        elif catch_score > 1:  # Difficult catch
            return True, 0.7  # weak return
        else:  # easy catch
            return True, 1

    def _get_direction_targeting_weak_side(self, hitter, opponent):
        """Determine which direction (cross/straight) targets opponent's weaker groundstroke."""
        opp_fh = opponent["skills"]["forehand"]
        opp_bh = opponent["skills"]["backhand"]

        # Determine which shot_leftright forces the opponent onto their weaker wing
        if opponent["hand"] == "Right":
            # Right-hander: backhand when ball lands on "right" side
            target_side = "right" if opp_bh < opp_fh else "left"
        else:
            # Left-hander: backhand when ball lands on "left" side
            target_side = "left" if opp_bh < opp_fh else "right"

        hitter_pos = self.positions[hitter["id"]]
        if hitter_pos == "right":
            # cross → left, straight → right
            return "straight" if target_side == "right" else "cross"
        else:
            # cross → right, straight → left
            return "cross" if target_side == "right" else "straight"

    def _apply_archetype_tendencies(self, player, tendencies):
        """Adjust tendencies based on player archetype so playstyle matches archetype identity.
        
        Skills in the archetype key that map to shot types get boosted tendencies.
        E.g. a 'Serve & Volley' archetype (key contains 'volley') will hit volleys much more often.
        """
        archetype_key = player.get('archetype_key', ())
        if not archetype_key:
            return tendencies

        # Tendency indices: 0=cross, 1=straight, 2=dropshot, 3=volley, 4=lift, 5=slice
        SKILL_TENDENCY_MAP = {
            'dropshot': {2: 3.0},          # Dropshot archetype → 3x dropshot tendency
            'volley': {3: 3.0},            # Volley archetype → 3x volley tendency
            'cross': {0: 1.4},             # Cross specialist → 1.4x cross tendency
            'straight': {1: 1.4},          # Straight specialist → 1.4x straight tendency
            'lift': {4: 2.0},              # Lift player → 2x lift tendency
            'slice': {5: 2.0},             # Slice player → 2x slice tendency
            'serve': {1: 1.15},            # Servers tend to play more linear
            'speed': {2: 1.3, 3: 1.3},    # Fast players exploit net/short balls more
        }

        for skill in archetype_key:
            if skill in SKILL_TENDENCY_MAP:
                for idx, mult in SKILL_TENDENCY_MAP[skill].items():
                    tendencies[idx] *= mult

        return tendencies

    def _get_mentality_adjusted_tendencies(self, player, opponent):
        """Adjust shot tendencies based on player archetype and mentality.
        
        First: archetype shapes the player's natural playstyle.
        Then: mentality further adjusts based on opportunism or strategy.
        Finally: IQ refines decision-making.
        """
        mentality = player.get("mentality", "neutral")

        base = [
            player.get("cross_tend", 40),
            player.get("straight_tend", 40),
            player.get("dropshot_tend", 10),
            player.get("volley_tend", 10),
            player.get("lift_tend", 10),
            player.get("slice_tend", 10),
        ]

        # Apply archetype influence before mentality
        base = self._apply_archetype_tendencies(player, base)

        if mentality == "opportunist":
            skills = player["skills"]
            avg_skill = sum(skills.values()) / len(skills)

            # Boost cross/straight based on player's own directional skill strength
            cross_bonus = 1 + max(0, skills["cross"] - avg_skill) / 100
            straight_bonus = 1 + max(0, skills["straight"] - avg_skill) / 100
            # Boost special shots more aggressively if they are above average
            dropshot_bonus = 1 + max(0, skills["dropshot"] - avg_skill) / 50
            volley_bonus = 1 + max(0, skills["volley"] - avg_skill) / 50
            lift_bonus = 1 + max(0, skills.get("lift", 0) - avg_skill) / 50
            slice_bonus = 1 + max(0, skills.get("slice", 0) - avg_skill) / 50

            result = [
                base[0] * cross_bonus,
                base[1] * straight_bonus,
                base[2] * dropshot_bonus,
                base[3] * volley_bonus,
                base[4] * lift_bonus,
                base[5] * slice_bonus,
            ]
            return self._apply_iq_to_tendencies(player, opponent, result)

        elif mentality == "strategist":
            opp_skills = opponent["skills"]
            opp_avg = sum(opp_skills.values()) / len(opp_skills)

            # More dropshots/lifts when the opponent is slow
            speed_weakness = max(0, opp_avg - opp_skills["speed"]) / max(1, opp_avg)
            dropshot_boost = 1 + speed_weakness * 3
            lift_boost = 1 + speed_weakness * 2

            # Target the opponent's weaker groundstroke side
            weak_direction = self._get_direction_targeting_weak_side(player, opponent)
            fh_bh_diff = abs(opp_skills["forehand"] - opp_skills["backhand"])
            side_boost = 1 + (fh_bh_diff / 100) * 1.5

            cross_mult = side_boost if weak_direction == "cross" else 1.0
            straight_mult = side_boost if weak_direction == "straight" else 1.0

            # Boost slice when opponent has low stamina relative to average
            stam_weakness = max(0, opp_avg - opp_skills.get("stamina", 50)) / max(1, opp_avg)
            slice_boost = 1 + stam_weakness * 2

            result = [
                base[0] * cross_mult,
                base[1] * straight_mult,
                base[2] * dropshot_boost,
                base[3],  # volley unchanged
                base[4] * lift_boost,
                base[5] * slice_boost,
            ]
            return self._apply_iq_to_tendencies(player, opponent, result)

        # neutral or unknown → raw tendencies
        return self._apply_iq_to_tendencies(player, opponent, base)

    def _apply_iq_to_tendencies(self, player, opponent, tendencies):
        """Apply IQ-based adjustments to shot tendencies.
        
        IQ modifies decisions to be more intelligent:
        - Favor player's stronger directional skill
        - Favor player's best special shot
        - Target opponent's weaknesses (slow opponents → more dropshots/lifts)
        - Target opponent's weaker groundstroke side
        IQ 50 = neutral. Range: ~-0.2 to +0.2 scaling factor.
        """
        iq = player["skills"].get("iq", 50)
        iq_factor = (iq - 50) / 250.0  # Range: -0.2 to +0.2

        if abs(iq_factor) < 0.01:
            return tendencies

        skills = player["skills"]

        # 1. Favor player's stronger direction
        cross_val = skills.get("cross", 50)
        straight_val = skills.get("straight", 50)
        if cross_val != straight_val:
            stronger_idx = 0 if cross_val > straight_val else 1
            diff = abs(cross_val - straight_val)
            tendencies[stronger_idx] *= (1 + iq_factor * diff / 80.0)

        # 2. Favor player's best special shot among dropshot/volley/lift/slice
        special_map = {
            2: skills.get("dropshot", 30),
            3: skills.get("volley", 30),
            4: skills.get("lift", 30),
            5: skills.get("slice", 30),
        }
        avg_special = sum(special_map.values()) / max(1, len(special_map))
        for idx, val in special_map.items():
            if val > avg_special:
                tendencies[idx] *= (1 + iq_factor * (val - avg_special) / 80.0)
            elif val < avg_special:
                tendencies[idx] *= max(0.5, 1 - abs(iq_factor) * (avg_special - val) / 160.0)

        # 3. Target opponent weaknesses
        opp_skills = opponent["skills"]
        opp_avg = sum(opp_skills.values()) / max(1, len(opp_skills))

        # Slow opponent → boost dropshot and lift
        opp_speed = opp_skills.get("speed", 50)
        if opp_speed < opp_avg:
            slowness = (opp_avg - opp_speed) / max(1, opp_avg)
            tendencies[2] *= (1 + iq_factor * slowness * 2)   # dropshot
            tendencies[4] *= (1 + iq_factor * slowness * 1.5)  # lift

        # Weak groundstroke side → target it
        opp_fh = opp_skills.get("forehand", 50)
        opp_bh = opp_skills.get("backhand", 50)
        if abs(opp_fh - opp_bh) > 3:
            weak_dir = self._get_direction_targeting_weak_side(player, opponent)
            weakness = abs(opp_fh - opp_bh) / 100.0
            if weak_dir == "cross":
                tendencies[0] *= (1 + iq_factor * weakness * 2)
            else:
                tendencies[1] *= (1 + iq_factor * weakness * 2)

        return tendencies

    def choose_shot_direction(self, player, opponent=None):
        """
        Choose the shot direction (cross, straight, dropshot, volley, lift, slice)
        using player tendencies, adjusted by mentality and IQ.
        If player is in volley mode, they can only hit volleys.
        If opponent is in volley mode, this player cannot choose volleys (to prevent double volleys).
        """
        # If player is in volley mode, they can only hit volleys
        if self.volley_mode[player["id"]]:
            return "volley"
        
        # Get mentality-adjusted tendencies
        tendencies = self._get_mentality_adjusted_tendencies(player, opponent or player)
        shot_types = ["cross", "straight", "dropshot", "volley", "lift", "slice"]
        
        # If opponent is in volley mode, remove volley from available options
        if opponent and self.volley_mode[opponent["id"]]:
            volley_idx = shot_types.index("volley")
            shot_types.pop(volley_idx)
            tendencies.pop(volley_idx)
        
        return random.choices(shot_types, weights=tendencies, k=1)[0]

    def determine_shot_type(self, player, incoming_direction):
        """
        Determine whether the player will use a forehand or backhand based on the incoming shot direction.
        The incoming direction is reversed for the opponent because the court is mirrored.
        """
        reversed_direction = "Left" if incoming_direction == "right" else "Right"
        if player["hand"] == reversed_direction:
            return "forehand"
        else:  # Left-handed player
            return "backhand"

    def update_positions(self, player, shot_leftright):
        """
        Update the positions of the players based on the shot direction.
        """
        if shot_leftright == "left":
            self.positions[player["id"]] = "right" 
        else: 
            self.positions[player["id"]] = "left"

    def update_games(self, winner_key):
        """
        Update the games won in the current set based on the winner of the point.
        """
        self.games[winner_key] += 1
        p1_games = self.games["player1"]
        p2_games = self.games["player2"]
        
        # Check if this game win results in a set win
        set_winner = self.is_set_over()
        if set_winner:
            # Combine game and set winning messages
            self.match_log.append(
                f"{self._player_ref(winner_key)} won the game. Score: {p1_games}-{p2_games} / "
                f"{self._player_ref(set_winner)} won the set. Sets: {self.sets['player1']}-{self.sets['player2']}"
            )
        elif p1_games > 0 or p2_games > 0:
            # Regular game win message
            self.match_log.append(
                f"{self._player_ref(winner_key)} won the game. Score: {p1_games}-{p2_games}"
            )

    def is_set_over(self):
        """
        Check if the current set is over based on tennis rules.
        """
        p1_games = self.games["player1"]
        p2_games = self.games["player2"]

        # A player wins the set if they have at least 6 games and a 2-game lead
        if p1_games >= 6 and p1_games - p2_games >= 2:
            return "player1"
        elif p2_games >= 6 and p2_games - p1_games >= 2:
            return "player2"

        # Tiebreaker: First to 7 games wins if the score is 6-6
        if p1_games == 7 and p2_games == 6:
            return "player1"
        elif p2_games == 7 and p1_games == 6:
            return "player2"

        return None

    def is_match_over(self):
        """
        Check if the match is over (first to 2 sets wins).
        """
        return self.sets["player1"] == self.sets_to_win or self.sets["player2"] == self.sets_to_win
    
    def _player_ref(self, player_key):
        """Return player name for logging purposes"""
        return self.p1['name'] if player_key == "player1" else self.p2['name']
    
    def _get_player_key(self, player):
        """Return 'player1' or 'player2' based on player ID"""
        return "player1" if player['id'] == self.p1['id'] else "player2"
    
    def get_original_players(self):
        """Return the original player stats without surface/form bonuses"""
        return {
            'player1': self._remove_bonuses(self.p1),
            'player2': self._remove_bonuses(self.p2)
        }
        
    def _remove_bonuses(self, player):
        """Remove any temporary bonuses from a player's stats"""
        original = player.copy()
        if 'original_skills' in player:
            original['skills'] = player['original_skills']
        return original
            
    def get_ball_coordinates(self, side, shot_power, shot_direction, shot_precision=None, shot_type=None, shot_success=None):
        """
        Returns (x, y) coordinates for the ball in screen space (1200x600 court).
        side: "right" or "left"
        shot_type: "serve", "forehand", "backhand", "dropshot", "volley", etc.
        shot_success: True/False for dropshot/volley outcomes
        """
        # Court dimensions
        COURT_WIDTH = 1200
        COURT_HEIGHT = 600
        MARGIN_X = 100
        MARGIN_Y = 75
        BASELINE_Y = COURT_HEIGHT // 2  # Center line

        if side == "right":
            # Available court space
            court_space = COURT_WIDTH - (2 * MARGIN_X)
            half_court = COURT_WIDTH / 2
            
            if shot_type == "dropshot" and shot_success is not None:
                # Dropshot special coordinates only
                if shot_success:
                    # Successful: randomly either [650, 100] or [650, 500]
                    x = 650
                    y = random.choice([125, 475])
                else:
                    # Unsuccessful: [900, 300]
                    x = 900
                    y = 300
                return side, x, y
            
            elif shot_precision is None:  # Serve
                # Calculate base X position
                power_factor = shot_power / 100.0
                x = half_court + (300 * power_factor)  # Scale between half_court and half_court + 300
                
                # Enforce serve X boundaries (300-900)
                x = max(300, min(900, x))
                
                # Special serve positioning rules
                if 450 < x < 600:
                    x = 450
                elif 600 < x < 750:
                    x = 750
                
                # Calculate Y position for serve
                # High power → ball lands on the exteriors (far from centre)
                # Low power  → ball stays near the centre
                spread = power_factor  # 0..1
                min_offset = spread * 120          # power 100 → at least 120px from centre
                max_offset = 80 + spread * 120     # power 100 → up to 200px from centre
                offset = random.uniform(min_offset, max_offset)
                direction = random.choice([-1, 1])
                y = BASELINE_Y + direction * offset
                
            else:  # Regular shots
                # For right side, shots land between 900-1175
                # Higher power = deeper shots (closer to 1175)
                power_factor = shot_power / 100.0  # 0.0 to 1.0
                x = 900 + (275 * power_factor)  # Scale between 900 and 1175
                # Ensure we stay within bounds
                x = min(1175, max(900, x))
                
                # Regular shot Y position
                precision_factor = (shot_precision - 50) / 50.0  # -1 to 1
                y = BASELINE_Y + (precision_factor * 250)  # Base Y calculation
            
            # Enforce global Y boundaries for all shots
            if y < 100:
                y = 100
            elif y > 500:
                y = 500
            
            if shot_direction == "left":
                # Invert Y position for left direction
                y = BASELINE_Y - (y - BASELINE_Y)
                # Re-apply Y boundaries after inversion
                if y < 100:
                    y = 100
                elif y > 500:
                    y = 500
            
            return side, x, y

        elif side == "left":
            # Mirror calculations for left side
            court_space = COURT_WIDTH - (2 * MARGIN_X)
            half_court = COURT_WIDTH / 2
            
            if shot_type == "dropshot" and shot_success is not None:
                # Dropshot special coordinates only
                if shot_success:
                    # Successful: randomly either [550, 100] or [550, 500]
                    x = 550
                    y = random.choice([125, 475])
                else:
                    # Unsuccessful: [300, 300]
                    x = 300
                    y = 300
                return side, x, y
            
            elif shot_precision is None:  # Serve
                # Calculate base X position (mirrored)
                power_factor = shot_power / 100.0
                x = half_court - (300 * power_factor)
                
                # Enforce serve X boundaries (300-900)
                x = max(300, min(900, x))
                
                # Special serve positioning rules
                if 450 < x < 600:
                    x = 450
                elif 600 < x < 750:
                    x = 750
                
                # Calculate Y position for serve (mirrors right side logic)
                spread = power_factor
                min_offset = spread * 120
                max_offset = 80 + spread * 120
                offset = random.uniform(min_offset, max_offset)
                direction = random.choice([-1, 1])
                y = BASELINE_Y + direction * offset
                
            else:  # Regular shots
                # For left side, shots land between 25-300
                # Higher power = deeper shots (closer to 25)
                power_factor = shot_power / 100.0  # 0.0 to 1.0
                x = 300 - (275 * power_factor)  # Scale between 300 and 25
                # Ensure we stay within bounds
                x = max(25, min(300, x))
                
                # Regular shot Y position
                precision_factor = (shot_precision - 50) / 50.0
                y = BASELINE_Y + (precision_factor * 250)
            
            # Enforce global Y boundaries for all shots
            if y < 100:
                y = 100
            elif y > 500:
                y = 500
            
            if shot_direction == "right":
                # Invert Y position for right direction
                y = BASELINE_Y - (y - BASELINE_Y)
                # Re-apply Y boundaries after inversion
                if y < 100:
                    y = 100
                elif y > 500:
                    y = 500
            
            return side, x, y

        # fallback
        return side, COURT_WIDTH/2, BASELINE_Y