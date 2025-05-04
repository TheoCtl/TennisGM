import json
import random
from datetime import datetime

class NewGenGenerator:
    def __init__(self, names_path='data/names.json'):
        self.names_path = names_path
        self.name_data = self.load_names()
        
    def load_names(self):
        try:
            with open(self.names_path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback names if the file is missing or corrupted
            return {
                "first_names": ["Player"],
                "last_names": [str(i) for i in range(1, 11)]
            }
    
    def generate_player(self, current_year):
        """Generate a new young player with random attributes"""
        first_name = random.choice(self.name_data["first_names"])
        last_name = random.choice(self.name_data["last_names"])
        
        player = {
            "id": self.generate_player_id(),
            "name": f"{first_name} {last_name}",
            "age": 16,
            "hand": random.choice(["Right", "Left"]),
            "rank": 999,  # Initial unranked status
            "points": 0,
            "tournament_history": [],
            "tournament_wins": [],
            "skills": self.generate_skills(),
        }
        return player
    
    def generate_player_id(self):
        """Generate a unique player ID based on current timestamp"""
        return int(datetime.now().timestamp() * 1000)
    
    def generate_skills(self):
        """Generate random skills for a new player (between 20 and 40)"""
        return {
            "serve": random.randint(30, 50),
            "forehand": random.randint(30, 50),
            "backhand": random.randint(30, 50),
            "speed": random.randint(30, 50),
            "stamina": random.randint(30, 50),
            "cross": random.randint(30, 50),
            "straight": random.randint(30, 50)
        }
    
    def generate_new_players(self, current_year, count):
        """Generate multiple new young players"""
        return [self.generate_player(current_year) for _ in range(count)]