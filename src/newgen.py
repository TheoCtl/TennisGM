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
    
    def generate_player_with_ids(self, current_year, player_id, player_rank):
        """Generate a new young player with random attributes"""
        first_name = random.choice(self.name_data["first_names"])
        last_name = random.choice(self.name_data["last_names"])
        if random.random() < 0.5:
            potential_factor = round(random.uniform(1, 1.5), 3)
        else:
            potential_factor = 1.0
        return {
            "id": player_id,
            "name": f"{first_name} {last_name}",
            "age": 16,
            "hand": random.choice(["Right", "Left"]),
            "skills": self.generate_skills(),
            "potential_factor": potential_factor,
            "rank": player_rank,  # Initial unranked status
            "points": 0,
            "favorite_surface": random.choice(["clay", "grass", "hard", "indoor"]),
            "tournament_history": [],
            "tournament_wins": [],
        }
    
    def generate_player_id(self):
        """Generate a unique player ID based on current timestamp"""
        return int(datetime.now().timestamp() * 1000)
    
    def generate_skills(self):
        """Generate random skills for a new player (between 30 and 50)"""
        return {
            "serve": random.randint(25, 50),
            "forehand": random.randint(25, 50),
            "backhand": random.randint(25, 50),
            "speed": random.randint(25, 50),
            "stamina": random.randint(25, 50),
            "straight": random.randint(25, 50),
            "cross": random.randint(25, 50)
        }
    
    def generate_new_players(self, current_year, count, existing_players=None):
        """Generate multiple new young players with unique IDs and ranks within the batch"""
        new_players = []
    
        # Get existing IDs and ranks
        existing_ids = {p['id'] for p in existing_players} if existing_players else set()
        existing_ranks = {p.get('rank', 999) for p in existing_players} if existing_players else set()
    
        # Track IDs and ranks assigned in this batch
        batch_ids = set()
        batch_ranks = set()
    
        # Find next available ID (max existing + 1 or 1 if empty)
        next_id = max(existing_ids) + 1 if existing_ids else 1
    
        # Find next available rank (first gap or max + 1)
        next_rank = 1
        if existing_ranks:
            while next_rank in existing_ranks:
                next_rank += 1
    
        for _ in range(count):
            # Generate unique ID for this batch
            while next_id in batch_ids or (existing_ids and next_id in existing_ids):
                next_id += 1

            # Generate unique rank for this batch
            while next_rank in batch_ranks or (existing_ranks and next_rank in existing_ranks):
                next_rank += 1

            # Create player with these unique values
            player = self.generate_player_with_ids(
                current_year,
                next_id,
                next_rank
            )

            # Track used values
            batch_ids.add(next_id)
            batch_ranks.add(next_rank)

            # Increment for next player
            next_id += 1
            next_rank += 1

            new_players.append(player)

        return new_players