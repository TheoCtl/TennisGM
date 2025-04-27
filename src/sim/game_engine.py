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
        self.current_server = player1  # Player 1 serves first by default
        self.current_receiver = player2

    def simulate_point(self):
        """
        Simulate a single point in the match.
        Returns the winner of the point (player1 or player2).
        """
        server = self.current_server
        receiver = self.current_receiver

        # Step 1: Server makes the first shot
        shot_power, shot_zone = self.calculate_shot(server, "serve", self.choose_shot_direction(server))
        print(f"{server['name']} serves with power {shot_power} to zone {shot_zone}")

        # Step 2: Receiver tries to catch the shot
        if not self.can_catch(receiver, shot_power, shot_zone):
            print(f"{receiver['name']} fails to catch the ball!")
            return server  # Server wins the point

        # Step 3: Alternate shots until one player fails
        while True:
            # Receiver returns the shot
            shot_type = self.determine_shot_type(receiver, shot_zone)
            shot_direction = self.choose_shot_direction(receiver)
            shot_power, shot_zone = self.calculate_shot(receiver, shot_type, shot_direction)
            print(f"{receiver['name']} returns with power {shot_power} to zone {shot_zone}")

            # Server tries to catch the return
            if not self.can_catch(server, shot_power, shot_zone):
                print(f"{server['name']} fails to catch the ball!")
                return receiver  # Receiver wins the point

            # Server returns the shot
            shot_type = self.determine_shot_type(server, shot_zone)
            shot_direction = self.choose_shot_direction(server)
            shot_power, shot_zone = self.calculate_shot(server, shot_type, shot_direction)
            print(f"{server['name']} returns with power {shot_power} to zone {shot_zone}")

            # Receiver tries to catch the return
            if not self.can_catch(receiver, shot_power, shot_zone):
                print(f"{receiver['name']} fails to catch the ball!")
                return server  # Server wins the point

    def calculate_shot(self, player, shot_type, direction):
        """
        Calculate the power and placement of a shot based on the player's stats.
        """
        shot_power = player["skills"][shot_type] + player["skills"][direction] + random.randint(-5, 5)  # Add randomness
        shot_zone = direction  # Simplified for now
        return shot_power, shot_zone

    def can_catch(self, player, shot_power, shot_zone):
        """
        Determine if the player can catch the shot based on their speed and shot power.
        """
        return player["skills"]["speed"] >= shot_power

    def choose_shot_direction(self, player):
        """
        Choose the shot direction (cross or straight).
        For now, this is randomized. Later, you can integrate user input for human players.
        """
        return random.choice(["cross", "straight"])

    def determine_shot_type(self, player, incoming_zone):
        """
        Determine whether the player will use a forehand or backhand based on the incoming shot zone.
        """
        if player["hand"] == "right":
            return "forehand" if incoming_zone == "left" else "backhand"
        else:  # Left-handed player
            return "forehand" if incoming_zone == "right" else "backhand"

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

    def update_sets(self, winner):
        """
        Update the sets won in the match based on the winner of the set.
        """
        if winner == self.player1:
            self.sets["player1"] += 1
        else:
            self.sets["player2"] += 1

        print(f"Sets: {self.sets}")

        # Reset games for the next set
        self.games = {"player1": 0, "player2": 0}

    def is_match_over(self):
        """
        Check if the match is over (first to 2 sets wins).
        """
        return self.sets["player1"] == 2 or self.sets["player2"] == 2

    def simulate_match(self):
        """
        Simulate a full match until one player wins.
        """
        while not self.is_match_over():
            while not self.is_set_over():
                winner = self.simulate_point()
                self.update_games(winner)
                self.current_server, self.current_receiver = self.current_receiver, self.current_server

            set_winner = self.is_set_over()
            self.update_sets(set_winner)

        match_winner = self.player1 if self.sets["player1"] == 2 else self.player2
        print(f"{match_winner['name']} wins the match!")