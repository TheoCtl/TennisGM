import random
import math

class GameEngine:
    SURFACES = ["clay", "grass", "hard", "indoor"]
    
    def __init__(self, player1, player2, surface):
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
        """Apply random form multiplier (0.9-1.1) to all skills"""
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

        print(f"Sets: {self._player_ref('player1')}: {self.sets['player1']} - {self._player_ref('player2')}: {self.sets['player2']} | Set Scores: {self.format_set_scores()}")
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
            
        if self.sets["player1"] == 2:
            match_winner = self.player1
        else:
            match_winner = self.player2

        print(f"{match_winner['name']} wins the match! Final Score: {self.format_set_scores()}")
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
        shot_power, shot_precision, shot_direction = self.calculate_shot(hitter, "serve", shot_direction, 1)
        print(f"{hitter['name']} (Speed: {self.speed[hitter['id']]}, Stamina: {self.stamina[hitter['id']]}) "
              f"serves with power {shot_power} to {shot_direction}")

        # Update positions based on the shot
        self.update_positions(hitter, shot_direction)

        # Step 2: Receiver tries to catch the shot
        caught, return_multiplier = self.can_catch(defender, shot_power, shot_precision)
        if not caught:  # Missed shot
            print(f"Point winner (serve unreturned): {hitter['name']}")
            self.reset_stamina_and_speed()
            return self._get_player_key(hitter)

        # Reduce stamina for catching the ball
        self.reduce_stamina(receiver, shot_power)

        # Step 3: Alternate shots until one player fails
        while True:
            # Receiver returns the shot
            hitter, defender = defender, hitter
            shot_type = self.determine_shot_type(hitter, shot_direction)
            shot_direction = self.choose_shot_direction(hitter)
            shot_power, shot_precision, shot_direction = self.calculate_shot(hitter, shot_type, shot_direction, return_multiplier)
            print(f"{hitter['name']} (Speed: {self.speed[hitter['id']]}, Stamina: {self.stamina[hitter['id']]}) "
                  f"hits a {shot_type} with power {shot_power} to {shot_direction} with {shot_precision} precision")

            # Update positions based on the shot
            self.update_positions(hitter, shot_direction)

            caught, return_multiplier = self.can_catch(defender, shot_power, shot_precision)
            if not caught:
                print(f"Point winner (rally): {hitter['name']}")
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
            power_multiplier = random.uniform(0.5, 1.5)  # Serve gets a special bonus range
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

    def can_catch(self, player, shot_power, shot_precision):
        """
        Determine if the player can catch the shot based on their speed and shot power.
        """
        # Special case for serve returns
        if shot_precision is None or shot_precision == 50:  # Default serve precision
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
        reversed_direction = "left" if incoming_direction == "right" else "right"
        position = self.positions[player["id"]]
        if player["hand"] == "right":
            return "forehand" if reversed_direction == position else "backhand"
        else:  # Left-handed player
            return "forehand" if reversed_direction != position else "backhand"

    def update_positions(self, player, shot_direction):
        """
        Update the positions of the players based on the shot direction.
        """
        if shot_direction == "cross":
            self.positions[player["id"]] = "left" if self.positions[player["id"]] == "right" else "right"

    def update_games(self, winner_key):
        """
        Update the games won in the current set based on the winner of the point.
        """
        self.games[winner_key] += 1
        print(f"Games: {self._player_ref('player1')}: {self.games['player1']} - {self._player_ref('player2')}: {self.games['player2']}")

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
        return self.sets["player1"] == 2 or self.sets["player2"] == 2
    
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