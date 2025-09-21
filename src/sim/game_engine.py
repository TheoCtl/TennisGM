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
        self.player1 = self._apply_surface_bonus(player1, surface)
        self.player2 = self._apply_surface_bonus(player2, surface)
        self.player1 = self._apply_random_form(self.player1)
        self.player2 = self._apply_random_form(self.player2)
        self.games = {"player1": 0, "player2": 0}  # Games won in the current set
        self.sets = {"player1": 0, "player2": 0}  # Sets won in the match
        self.set_scores = []  # Track the scores of each set as tuples (player1_games, player2_games)
        self.current_server = player1  # Player 1 serves first by default
        self.current_receiver = player2
        self.sets_to_win = sets_to_win
        self.match_log = []

        # Track player positions: "right" or "left"
        self.positions = {player1["id"]: "right", player2["id"]: "left"}

        # Track stamina and speed for each player
        self.stamina = {player1["id"]: player1["skills"]["stamina"], player2["id"]: player2["skills"]["stamina"]}
        self.speed = {player1["id"]: player1["skills"]["speed"], player2["id"]: player2["skills"]["speed"]}
        self.last_shot_power = 0  # Initialize last shot power
        self.last_shot_precision = 50
        
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
            print(f"{player['name']} surface factor on {surface}: x{factor:.2f}")
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
        form_multiplier = random.uniform(0.9, 1.1)
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
        while not self.is_match_over():
            while not self.is_set_over():
                result = self.simulate_point(visualize=visualize)
                
                if visualize:
                    # When visualizing, simulate_point returns a tuple (winner_key, events)
                    winner_key, point_events = result
                    point_data = {
                        'type': 'point',
                        'events': point_events,
                        'winner': winner_key
                    }
                    yield point_data
                else:
                    # When not visualizing, simulate_point just returns winner_key
                    winner_key = result
                    
                self.update_games(winner_key)

                # Alternate server and receiver after each point
                self.current_server, self.current_receiver = self.current_receiver, self.current_server

            set_winner_key = self.is_set_over()
            self.update_sets(set_winner_key)
            
        if self.sets["player1"] == self.sets_to_win:
            match_winner = self.player1
        else:
            match_winner = self.player2

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
                'player1_name': self.player1['name'],
                'player2_name': self.player2['name']
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
        caught, return_multiplier = self.can_catch(defender, shot_power, shot_precision, shot_type = "serve")
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
            return (winner_key, point_events) if visualize else winner_key

        # Step 3: Alternate shots until someone misses
        # Continue rally until someone misses
        while True:
            # Receiver becomes the hitter
            hitter, defender = defender, hitter
            shot_type = self.determine_shot_type(hitter, shot_leftright)
            shot_direction = self.choose_shot_direction(hitter)
            
            # Determine shot_leftright based on hitter's position and shot_direction
            hitter_position = self.positions[hitter["id"]]  # "left" or "right"
            if hitter_position == "right":
                shot_leftright = "left" if shot_direction == "cross" else "right"
            else:  # hitter_position == "left"
                shot_leftright = "right" if shot_direction == "cross" else "left"
                
            shot_power, shot_precision, shot_direction = self.calculate_shot(hitter, shot_type, shot_direction, return_multiplier)
            side = "left" if self._get_player_key(defender) == "player1" else "right"
            ball_side, ball_row, ball_col = self.get_ball_coordinates(
                side, shot_power, shot_leftright, shot_precision
            )
            # Update positions based on the shot
            self.update_positions(defender, shot_leftright)

            # Add current ball position to events if visualizing
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

            caught, return_multiplier = self.can_catch(defender, shot_power, shot_precision, shot_type)
            if not caught:
                side = "left" if self._get_player_key(defender) == "player1" else "right"
                ball_side, target_x, target_y = self.get_ball_coordinates(
                    side, shot_power, shot_leftright, shot_precision
                )
                
                # Add final missed shot position if visualizing
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
                return (winner_key, point_events) if visualize else winner_key

            # Reduce stamina for catching the ball
            self.reduce_stamina(hitter, shot_power)

    def calculate_shot(self, player, shot_type, direction, previous_multiplier=1):
        """
        Calculate the power and placement of a shot based on the player's stats.
        Adjust shot power based on how comfortably the player catches the ball.
        """
        base_power = player["skills"][shot_type] * previous_multiplier
        precision_skill = player["skills"][direction]
        precision = self._weighted_random_precision(precision_skill)

        # Special handling for serves
        if shot_type == "serve":
            power_multiplier = random.uniform(0.5, 1.3)  # Serve gets a special bonus range
        else:
            # Determine the comfort level of the shot
            last_shot_power = self.last_shot_power  # Track the opponent's last shot power

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
        self.last_shot_power = shot_power  # Update the last shot power for the next calculation
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
        """
        for player in [self.player1, self.player2]:
            self.stamina[player["id"]] = player["skills"]["stamina"]
            self.speed[player["id"]] = player["skills"]["speed"]

    def can_catch(self, player, shot_power, shot_precision, shot_type):
        """
        Determine if the player can catch the shot based on their speed and shot power.
        """
        # Special case for serve returns
        if shot_type == "serve":  # Default serve precision
            # Simple serve return check: if serve power > speed, can't return
            if shot_power > self.speed[player["id"]]:
                return False, 0
            else:
                # Good return gets full power
                return True, 1.0
        
        # Base catch chance (speed vs power)
        speed_power_ratio = max(1, shot_power) / self.speed[player["id"]]
        # Precision factor (0.5-1.5) - higher precision makes catching harder
        precision_factor = 0.5 + (shot_precision / 100)
        # Combined catch score
        catch_score = speed_power_ratio * precision_factor
        # Determine if caught based on catch score
        if catch_score > 1.2:  # Missed
            return False, 0 
        elif catch_score > 1:  # Difficult catch
            return True, 0.9  # weak return
        else:  # easy catch
            return True, 1

    def choose_shot_direction(self, player):
        """
        Choose the shot direction (cross or straight).
        For now, this is randomized. Later, you can integrate user input for human players.
        """
        return random.choice(["cross", "straight"])

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
                f"{self._player_ref(winner_key)} won the set. Sets: {self.sets['player1']}-{self.sets['player2']}"
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
        return self.player1['name'] if player_key == "player1" else self.player2['name']
    
    def _get_player_key(self, player):
        """Return 'player1' or 'player2' based on player ID"""
        return "player1" if player['id'] == self.player1['id'] else "player2"
    
    def get_original_players(self):
        """Return the original player stats without surface/form bonuses"""
        return {
            'player1': self._remove_bonuses(self.player1),
            'player2': self._remove_bonuses(self.player2)
        }
        
    def _remove_bonuses(self, player):
        """Remove any temporary bonuses from a player's stats"""
        original = player.copy()
        if 'original_skills' in player:
            original['skills'] = player['original_skills']
        return original
            
    def get_ball_coordinates(self, side, shot_power, shot_direction, shot_precision=None):
        """
        Returns (x, y) coordinates for the ball in screen space (1200x600 court).
        side: "right" or "left"
        """
        # Court dimensions
        COURT_WIDTH = 1200
        COURT_HEIGHT = 600
        MARGIN_X = 100
        MARGIN_Y = 75
        BASELINE_Y = COURT_HEIGHT // 2  # Center line
                
        # Helper for y calculation (now in screen coordinates)
        def y_from_value(val, value_range):
            if val >= 85:
                return BASELINE_Y + (value_range[0] * 20)  # Convert ASCII rows to pixels
            elif val >= 70:
                return BASELINE_Y + (value_range[1] * 20)
            elif val >= 50:
                return BASELINE_Y + (value_range[2] * 20)
            elif val >= 30:
                return BASELINE_Y + (value_range[3] * 20)
            elif val >= 20:
                return BASELINE_Y + (value_range[4] * 20)
            else:
                return BASELINE_Y + (value_range[5] * 20)

        if side == "right":
            # Available court space
            court_space = COURT_WIDTH - (2 * MARGIN_X)
            half_court = COURT_WIDTH / 2
            
            if shot_precision is None:  # Serve
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
            
            if shot_precision is None:  # Serve
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