import random

class GameEngine:
    def __init__(self, player1, player2):
        """
        Initialize the game engine with two players.
        Each player is a dictionary containing stats like serve, forehand, backhand, speed, etc.
        """
        self.player1 = player1
        self.player2 = player2
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

    def update_sets(self, winner):
        """
        Update the sets won in the match based on the winner of the set.
        """
        if winner == self.player1:
            self.sets["player1"] += 1
        else:
            self.sets["player2"] += 1

        # Add the current set score to the set_scores list
        self.set_scores.append((self.games["player1"], self.games["player2"]))

        print(f"Sets: {self.sets} | Set Scores: {self.format_set_scores()}")

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
                winner = self.simulate_point()
                self.update_games(winner)

                # Alternate server and receiver after each point
                self.current_server, self.current_receiver = self.current_receiver, self.current_server

            set_winner = self.is_set_over()
            self.update_sets(set_winner)

        # Determine the match winner
        match_winner = self.player1 if self.sets["player1"] == 2 else self.player2
        print(f"{match_winner['name']} wins the match! Final Score: {self.format_set_scores()}")
        return match_winner

    def simulate_point(self):
        """
        Simulate a single point in the match.
        Returns the winner of the point (player1 or player2).
        """
        server = self.current_server
        receiver = self.current_receiver

        # Step 1: Server makes the first shot
        shot_direction = self.choose_shot_direction(server)
        shot_power, shot_direction = self.calculate_shot(server, "serve", shot_direction)
        print(f"{server['name']} (Speed: {self.speed[server['id']]}, Stamina: {self.stamina[server['id']]}) "
              f"serves with power {shot_power} to {shot_direction}")

        # Update positions based on the shot
        self.update_positions(server, shot_direction)

        # Step 2: Receiver tries to catch the shot
        if not self.can_catch(receiver, shot_power, shot_direction):
            print(f"{receiver['name']} fails to catch the ball!")
            return server  # Server wins the point

        # Reduce stamina for catching the ball
        self.reduce_stamina(receiver, shot_power)

        # Step 3: Alternate shots until one player fails
        while True:
            # Receiver returns the shot
            shot_type = self.determine_shot_type(receiver, shot_direction)
            shot_direction = self.choose_shot_direction(receiver)
            shot_power, shot_direction = self.calculate_shot(receiver, shot_type, shot_direction)
            print(f"{receiver['name']} (Speed: {self.speed[receiver['id']]}, Stamina: {self.stamina[receiver['id']]}) "
                  f"hits a {shot_type} with power {shot_power} to {shot_direction}")

            # Update positions based on the shot
            self.update_positions(receiver, shot_direction)

            # Server tries to catch the return
            if not self.can_catch(server, shot_power, shot_direction):
                print(f"{server['name']} fails to catch the ball!")
                self.reset_stamina_and_speed()  # Reset stamina and speed at the end of the point
                return receiver  # Receiver wins the point

            # Reduce stamina for catching the ball
            self.reduce_stamina(server, shot_power)

            # Server returns the shot
            shot_type = self.determine_shot_type(server, shot_direction)
            shot_direction = self.choose_shot_direction(server)
            shot_power, shot_direction = self.calculate_shot(server, shot_type, shot_direction)
            print(f"{server['name']} (Speed: {self.speed[server['id']]}, Stamina: {round(self.stamina[server['id']])}) "
                  f"hits a {shot_type} with power {shot_power} to {shot_direction}")

            # Update positions based on the shot
            self.update_positions(server, shot_direction)

            # Receiver tries to catch the return
            if not self.can_catch(receiver, shot_power, shot_direction):
                print(f"{receiver['name']} fails to catch the ball!")
                self.reset_stamina_and_speed()  # Reset stamina and speed at the end of the point
                return server  # Server wins the point

            # Reduce stamina for catching the ball
            self.reduce_stamina(receiver, shot_power)

    def calculate_shot(self, player, shot_type, direction):
        """
        Calculate the power and placement of a shot based on the player's stats.
        Adjust shot power based on how comfortably the player catches the ball.
        """
        base_power = (player["skills"][shot_type] + player["skills"][direction]) / 2

        # Special handling for serves
        if shot_type == "serve":
            multiplier = random.uniform(0.7, 1.3)  # Serve gets a special bonus range
        else:
            # Determine the comfort level of the shot
            opponent_last_shot_power = self.last_shot_power  # Track the opponent's last shot power
            speed_diff = self.speed[player["id"]] - opponent_last_shot_power

            if speed_diff > 30:
                multiplier = random.uniform(1, 2)
            elif 10 < speed_diff <= 30:
                multiplier = random.uniform(0.5, 1.5)
            else:
                multiplier = random.uniform(0, 1)

        shot_power = round(base_power * multiplier)
        self.last_shot_power = shot_power  # Update the last shot power for the next calculation
        return shot_power, direction

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

    def can_catch(self, player, shot_power, shot_direction):
        """
        Determine if the player can catch the shot based on their speed and shot power.
        """
        return self.speed[player["id"]] >= shot_power

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

    def update_games(self, winner):
        """
        Update the games won in the current set based on the winner of the point.
        """
        if winner == self.player1:
            self.games["player1"] += 1
        else:
            self.games["player2"] += 1

        print(f"Games: {self.games}")

    def is_set_over(self):
        """
        Check if the current set is over based on tennis rules.
        """
        p1_games = self.games["player1"]
        p2_games = self.games["player2"]

        # A player wins the set if they have at least 6 games and a 2-game lead
        if p1_games >= 6 and p1_games - p2_games >= 2:
            return self.player1
        elif p2_games >= 6 and p2_games - p1_games >= 2:
            return self.player2

        # Tiebreaker: First to 7 games wins if the score is 6-6
        if p1_games == 7 and p2_games == 6:
            return self.player1
        elif p2_games == 7 and p1_games == 6:
            return self.player2

        return None

    def is_match_over(self):
        """
        Check if the match is over (first to 2 sets wins).
        """
        return self.sets["player1"] == 2 or self.sets["player2"] == 2