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
        """Apply 5% bonus to all skills if player's favorite surface matches"""
        if player.get("favorite_surface") == surface:
            boosted_player = player.copy()
            boosted_player["skills"] = {
                skill: min(100, math.floor(value * 1.05)) 
                for skill, value in player["skills"].items()
            }
            print(f"{player['name']} got boosted because of {surface} court.")
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
        self.match_log.append(
            f"{self._player_ref(winner_key)} won the set. Sets: {self.sets['player1']}-{self.sets['player2']}"
        )

        # Add the current set score to the set_scores list
        self.set_scores.append((self.games["player1"], self.games["player2"]))

        # Reset games for the next set
        self.games = {"player1": 0, "player2": 0}

    def format_set_scores(self):
        """
        Format the set scores as a string (e.g., "6-4, 7-5").
        """
        return ", ".join(f"{p1}-{p2}" for p1, p2 in self.set_scores)

    def simulate_match(self):
        """
        Simulate a full match until one player wins.
        """
        while not self.is_match_over():
            while not self.is_set_over():
                winner_key = self.simulate_point()
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

    def simulate_point(self):
        """
        Simulate a single point in the match.
        Returns the winner of the point (player1 or player2).
        """
        server = self.current_server
        receiver = self.current_receiver
        hitter = server
        defender = receiver

        # Step 1: Server makes the first shot
        shot_direction = self.choose_shot_direction(hitter)
        # Determine shot_leftright based on hitter's position and shot_direction
        shot_leftright = "left" if shot_direction == "cross" else "right"
        shot_power, shot_precision, shot_direction = self.calculate_shot(hitter, "serve", shot_direction, 1)
        side = "left" if self._get_player_key(defender) == "player1" else "right"
        ball_side, ball_row, ball_col = self.get_ball_coordinates(
            side, shot_power, shot_leftright, None  # No precision for serve
        )

        # Update positions based on the shot
        self.update_positions(defender, shot_leftright)

        # Step 2: Receiver tries to catch the shot
        caught, return_multiplier = self.can_catch(defender, shot_power, shot_precision, shot_type = "serve")
        if not caught:  # Missed shot
            self.reset_stamina_and_speed()
            return self._get_player_key(hitter)

        # Step 3: Alternate shots until one player fails
        while True:
            # Receiver returns the shot
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

            caught, return_multiplier = self.can_catch(defender, shot_power, shot_precision, shot_type)
            if not caught:
                side = "left" if self._get_player_key(defender) == "player1" else "right"
                ball_side, ball_row, ball_col = self.get_ball_coordinates(
                    side, shot_power, shot_leftright, shot_precision
                )
                self.reset_stamina_and_speed()
                return self._get_player_key(hitter)

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
        # A player wins the game if their games increased and it's not a set win yet
        if p1_games > 0 or p2_games > 0:
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
        Returns (x, y) coordinates for the ball on the ASCII court, given shot parameters and side.
        side: "right" or "left"
        """
        # Helper for y calculation
        def y_from_value(val, value_range):
            if val >= 85:
                return value_range[0]
            elif val >= 70:
                return value_range[1]
            elif val >= 50:
                return value_range[2]
            elif val >= 30:
                return value_range[3]
            elif val >= 20:
                return value_range[4]
            else:
                return value_range[5]

        if side == "right":
            x = 20 + round(min(100, shot_power) / 10)
            if shot_precision is None:
                x = max(7, x - 15)
                if shot_direction == "left":
                    y = y_from_value(shot_power, [0,1,1,2,2,3])
                else:
                    y = y_from_value(shot_power, [5,5,4,4,4,3])
            else:
                x = x - (30 - x)
                if shot_direction == "left":
                    y = y_from_value(shot_precision, [0,1,2,3,4,5])
                else:
                    y = y_from_value(shot_precision, [11,10,9,8,7,6])
            # Clamp to field
            x = max(0, min(29, x))
            y = max(0, min(11, y))
            return "right", y, x

        elif side == "left":
            x = 10 - round(min(100, shot_power) / 10)
            if shot_precision is None:
                x = min(23, x + 15)
                if shot_direction == "left":
                    y = y_from_value(shot_power, [11,10,10,9,9,8])
                else:
                    y = y_from_value(shot_power, [6,6,7,7,7,8])
            else:
                x = 2*x
                if shot_direction == "left":
                    y = y_from_value(shot_precision, [11,10,9,8,7,6])
                else:
                    y = y_from_value(shot_precision, [0,1,2,3,4,5])
            x = max(0, min(29, x))
            y = max(0, min(11, y))
            return "left", y, x

        # fallback
        return side, 7, 7