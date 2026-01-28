import random
import math

class GameEngine:
    SURFACES = ["clay", "grass", "hard", "indoor"]
    
    def __init__(self, player1, player2, surface, sets_to_win=2):
        """
        Initialize the game engine with two players.
        Each player is a dictionary containing stats like serve, forehand, backhand, speed, etc.
        """
        self.surface = surface
        self.original_player1 = player1
        self.original_player2 = player2
        player1_with_surface = self._apply_surface_bonus(player1, surface)
        player2_with_surface = self._apply_surface_bonus(player2, surface)
        self.p1 = self._apply_random_form(player1_with_surface)
        self.p2 = self._apply_random_form(player2_with_surface)
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
        self.stamina = {player1["id"]: player1["skills"]["stamina"], player2["id"]: player2["skills"]["stamina"]}
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
                "volley_winners": 0
            },
            player2["id"]: {
                "aces": 0,
                "breaks": 0,
                "forehand_winners": 0,
                "backhand_winners": 0,
                "dropshot_winners": 0,
                "volley_winners": 0
            }
        }
        # Track the last shot type for winner classification
        self.last_shot_type = None
        
    def _apply_surface_bonus(self, player, surface):
        """Apply per-surface multiplier to all skills if available; fallback to legacy favorite_surface bonus."""
        boosted_player = player.copy()

        # Prefer new per-surface modifiers if present
        mods = player.get("surface_modifiers")
        if isinstance(mods, dict) and surface in mods:
            factor = float(mods.get(surface, 1.0))
            boosted_player["skills"] = {
                skill: min(100, math.floor(value * factor))
                for skill, value in player["skills"].items()
            }
            return boosted_player

        # Fallback to legacy favorite_surface logic for older saves
        if player.get("favorite_surface") == surface:
            boosted_player["skills"] = {
                skill: min(100, math.floor(value * 1.05)) 
                for skill, value in player["skills"].items()
            }
            return boosted_player

        return player
    
    def _apply_random_form(self, player):
        """Apply random form multiplier to all skills"""
        form_multiplier = random.uniform(0.95, 1.05)
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
    
    def simulate_point(self, visualize=False):
        """
        Simulate a single point in the match.
        Returns the winner of the point (player1 or player2), or (winner, events) if visualize=True.
        """
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
        shot_direction = self.choose_shot_direction(hitter)
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
                'hitter_id': hitter['id']
            })

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
                    'is_final': True  # Mark this as the final shot of the point
                })            
            self.reset_stamina_and_speed()
            winner_key = self._get_player_key(hitter)
            # Track ace
            self.match_stats[hitter['id']]["aces"] += 1
            return (winner_key, point_events) if visualize else winner_key

        # Step 3: Alternate shots until someone misses
        # Continue rally until someone misses
        while True:
            # Receiver becomes the hitter
            hitter, defender = defender, hitter
            shot_direction = self.choose_shot_direction(hitter)
            # Determine shot type: dropshot/volley/forehand/backhand
            if shot_direction in ("cross", "straight"):
                shot_type = self.determine_shot_type(hitter, shot_leftright)
            else:
                shot_type = shot_direction

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
            ball_side, ball_row, ball_col = self.get_ball_coordinates(
                side, shot_power, shot_leftright, shot_precision, shot_type, shot_success
            )
            self.update_positions(defender, shot_leftright)

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
                    'hitter_id': hitter['id']
                })

            # Dropshot/volley mechanics
            if shot_type == "dropshot":
                if shot_success:
                    defender_speed = self.speed[defender["id"]]
                    if defender_speed < dropshot_skill:
                        self.reset_stamina_and_speed()
                        winner_key = self._get_player_key(hitter)
                        self.match_stats[hitter['id']]["dropshot_winners"] += 1
                        # Track break
                        if self._get_player_key(hitter) != self._get_player_key(server):
                            self.match_stats[hitter['id']]["breaks"] += 1
                        return (winner_key, point_events) if visualize else winner_key
                    else:
                        # Set return multiplier based on defender's speed
                        if defender_speed < 50: 
                            self.reset_stamina_and_speed()
                            winner_key = self._get_player_key(hitter)
                            self.match_stats[hitter['id']]["dropshot_winners"] += 1
                            # Track break
                            if self._get_player_key(hitter) != self._get_player_key(server):
                                self.match_stats[hitter['id']]["breaks"] += 1
                            return (winner_key, point_events) if visualize else winner_key
                        elif 50 <= defender_speed < 55:
                            return_multiplier = 0.2
                        elif 55 <= defender_speed < 60:
                            return_multiplier = 0.3
                        elif 60 <= defender_speed < 65:
                            return_multiplier = 0.4
                        elif 65 <= defender_speed < 70:
                            return_multiplier = 0.5
                        elif 70 <= defender_speed < 75:
                            return_multiplier = 0.6
                        else:  # defender_speed >= 75
                            return_multiplier = 0.7
                        # The defender will try to catch with this return multiplier
                else:
                    return_multiplier = 2.0  # For missed dropshot

            # For successful dropshot with fast defender, skip can_catch check
            if (shot_type == "dropshot" and shot_success and 
                self.speed[defender["id"]] >= 50):
                # We've already set the return_multiplier based on defender speed
                # The defender automatically catches successful dropshot when fast enough
                caught = True
                # If defender catches a dropshot, check if they're already in volley mode for *3 bonus
                if self.volley_mode[defender["id"]]:
                    # Already in volley mode - apply *3 multiplier
                    return_multiplier = 3
                # Enter volley mode after catching the dropshot
                self.volley_mode[defender["id"]] = True
                # return_multiplier is already set in the blocks above
            else:
                # For all other shots, use the normal can_catch logic
                caught, catch_return_multiplier = self.can_catch(defender, shot_power, shot_precision, shot_type, hitter=hitter)
    
                # For missed dropshot, keep the 2.0 multiplier
                if shot_type == "dropshot" and not shot_success and caught:
                    # Keep return_multiplier = 2.0 that was set in the blocks above
                    # Apply *3 multiplier if defender is in volley mode and catching a dropshot
                    if self.volley_mode[defender["id"]]:
                        return_multiplier = 3
                else:
                    # Use the normal return multiplier from can_catch
                    # Apply *3 multiplier if defender is in volley mode and catching a dropshot
                    if shot_type == "dropshot" and self.volley_mode[defender["id"]]:
                        catch_return_multiplier = 3
                    return_multiplier = catch_return_multiplier
                
                # Activate volley mode if defender catches a volley
                if shot_type == "volley" and caught:
                    self.volley_mode[defender["id"]] = True

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
                        'hitter_id': hitter['id']
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
                
                # Track break (point won by non-server while not on serve)
                if self._get_player_key(hitter) != self._get_player_key(server):
                    self.match_stats[hitter['id']]["breaks"] += 1
                
                return (winner_key, point_events) if visualize else winner_key

            self.reduce_stamina(hitter, shot_power)

    def calculate_shot(self, player, shot_type, direction, previous_multiplier=1):
        """
        Calculate the power and placement of a shot based on the player's stats.
        Adjust shot power based on how comfortably the player catches the ball.
        For dropshot, use their own skill for both power and precision.
        Volleys get a power boost based on volley skill (upside of volley mode).
        """
        if shot_type == "dropshot":
            base_power = player["skills"].get(shot_type, 30) * previous_multiplier
            precision_skill = player["skills"].get(shot_type, 30)
        else:
            base_power = player["skills"][shot_type] * previous_multiplier
            precision_skill = player["skills"][direction]
            
            # Volley power boost: 1.[volley_stat-10], simulating time compression for opponent
            if shot_type == "volley":
                volley_skill = player["skills"].get("volley", 30)
                volley_power_boost = 1.0 + max(0, (volley_skill - 30) / 100)  # 1.0 to 1.5x
                base_power = base_power * volley_power_boost
        
        precision = self._weighted_random_precision(precision_skill)

        # Special handling for serves
        if shot_type == "serve":
            power_multiplier = random.uniform(0.5, 1.3)  # Serve gets a special bonus range
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

        shot_power = round(base_power * power_multiplier)
        self.last_shot_power = shot_power
        return shot_power, precision, direction
    
    def _weighted_random_precision(self, skill):
        # Use triangular distribution with mode at skill value
        precision = random.triangular(1, 100, skill)
        return min(100, max(1, round(precision)))

    def reduce_stamina(self, player, opponent_shot_power):
        """
        Reduce the player's stamina based on the opponent's shot power.
        Halve the player's speed if stamina reaches 0 or lower.
        """
        self.stamina[player["id"]] -= round(opponent_shot_power / 3)
        if self.stamina[player["id"]] <= 0:
            self.speed[player["id"]] = player["skills"]["speed"] // 2

    def reset_stamina_and_speed(self):
        """
        Reset stamina and speed for both players to their original values at the end of a point.
        Also reset volley mode for both players.
        """
        for player in [self.p1, self.p2]:
            self.stamina[player["id"]] = player["skills"]["stamina"]
            self.speed[player["id"]] = player["skills"]["speed"]
            self.volley_mode[player["id"]] = False

    def can_catch(self, player, shot_power, shot_precision, shot_type, hitter=None):
        """
        Determine if the player can catch the shot based on their speed and shot power.
        If hitter is in volley mode, precision_factor is increased by 1.1x (downside of volley mode).
        """
        # Special case for serve returns
        if shot_type == "serve":  # Default serve precision
            # Simple serve return check: if serve power > speed, can't return
            if shot_power > self.speed[player["id"]]:
                return False, 0
            elif (self.speed[player["id"]] - shot_power) <= 10:
                return True, 0.8
            else:
                # Good return gets full power
                return True, 1.0
        
        # Base catch chance (speed vs power)
        speed_power_ratio = max(1, shot_power) / self.speed[player["id"]]
        # Precision factor (0.5-1.5) - higher precision makes catching harder
        precision_factor = 0.3 + (shot_precision / 70)
        # If hitter is in volley mode, precision factor is harder (downside of volley mode)
        if hitter and self.volley_mode[hitter["id"]]:
            precision_factor *= 1.2
        # Combined catch score
        catch_score = speed_power_ratio * precision_factor
        # Determine if caught based on catch score
        if catch_score > 1.3:  # Missed
            return False, 0 
        elif catch_score > 1:  # Difficult catch
            return True, 0.7  # weak return
        else:  # easy catch
            return True, 1

    def choose_shot_direction(self, player):
        """
        Choose the shot direction (cross, straight, dropshot, volley) using player tendencies.
        If player is in volley mode, they can only hit volleys.
        """
        # If player is in volley mode, they can only hit volleys
        if self.volley_mode[player["id"]]:
            return "volley"
        
        tendencies = [
            player.get("cross_tend", 40),
            player.get("straight_tend", 40),
            player.get("dropshot_tend", 10),
            player.get("volley_tend", 10)
        ]
        shot_types = ["cross", "straight", "dropshot", "volley"]
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
                precision_factor = random.uniform(-0.8, 0.8)
                y = BASELINE_Y + (precision_factor * 200)  # Base Y calculation for serves
                
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
                
                # Calculate Y position for serve
                precision_factor = random.uniform(-0.8, 0.8)
                y = BASELINE_Y + (precision_factor * 200)
                
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