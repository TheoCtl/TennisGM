import json
import random
from datetime import datetime
import math
from archetypes import get_archetype_for_player

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
    
    NATIONALITIES = [
        "Arcton", "Halcyon", "Rin", "Hethrion", "Haran", "Loknig", "Jeonguk", "Bleak"
    ]

    def generate_player_with_ids(self, current_year, player_id, player_rank):
        """Generate a new young player with random attributes"""
        first_name = random.choice(self.name_data["first_names"])
        last_name_idx = random.randrange(len(self.name_data["last_names"]))
        last_name = self.name_data["last_names"][last_name_idx]

        # Increment the last name and update names.json
        new_last_name = self.increment_name(last_name)
        self.name_data["last_names"][last_name_idx] = new_last_name
        with open(self.names_path, 'w', encoding='utf-8') as f:
            json.dump(self.name_data, f, indent=2, ensure_ascii=False)

        r = random.random()
        if r > 0.9:
            if r >= 0.95:
                potential_factor = round(random.uniform(1.9, 2.0), 3)
            else:
                potential_factor = round(random.uniform(1.5, 2.0), 3)
        else:
            potential_factor = round(random.uniform(1.0, 1.5), 3)

        skills = self.generate_skills()
        surface_mods = self.generate_surface_modifiers()

        # Generate tendencies
        dropshot_tend = random.randint(0, 5)
        volley_tend = random.randint(0, 5)
        straight_tend = random.randint(35, 55)
        cross_tend = 100 - (dropshot_tend + volley_tend + straight_tend)
        # Ensure all are at least 0, and cross_tend at least 10 if possible
        if cross_tend < 10:
            # Reduce straight_tend if possible
            diff = 10 - cross_tend
            if straight_tend - diff >= 40:
                straight_tend -= diff
                cross_tend = 10
            else:
                # If not possible, set cross_tend to 10 and adjust others
                cross_tend = 10
                straight_tend = max(40, 100 - (dropshot_tend + volley_tend + cross_tend))

        player = {
            "id": player_id,
            "name": f"{first_name} {last_name}",
            "age": 16,
            "hand": random.choice(["Right", "Left"]),
            "nationality": random.choice(self.NATIONALITIES),
            "skills": skills,
            "potential_factor": potential_factor,
            "rank": player_rank,
            "highest_ranking": 999,
            "elo_rating": 1000,
            "highest_elo": 1000,  # Initialize to same as starting ELO rating (no championship points yet)
            "highest_overral": 0,
            "matches_played": 0,  # Initialize new players with 0 matches
            "mawn": [0, 0, 0, 0, 0],
            "w1": 0,
            "w16": 0,
            "points": 0,
            "highest_points": 0,
            "surface_modifiers": surface_mods,  # per-surface multipliers
            # Keep favorite_surface only for backward compatibility if needed:
            # "favorite_surface": random.choice(["clay", "grass", "hard", "indoor"]),
            "tournament_history": [],
            "tournament_wins": [],
            "bonus": random.choice(list(skills.keys())),
            # Shot tendencies
            "cross_tend": cross_tend,
            "straight_tend": straight_tend,
            "dropshot_tend": dropshot_tend,
            "volley_tend": volley_tend,
            "year_start_rankings": {},  # Track ranking at start of each year
        }

        # Assign a stable archetype at generation time so it remains constant through the career
        try:
            name, desc, key = get_archetype_for_player(player)
            player['archetype'] = name
            player['archetype_key'] = tuple(key)
        except Exception:
            # If archetype resolution fails for any reason, fall back to a generic value
            player.setdefault('archetype', 'Balanced Player')
            player.setdefault('archetype_key', tuple())

        return player
    
    def generate_player_id(self):
        """Generate a unique player ID based on current timestamp"""
        return int(datetime.now().timestamp() * 1000)
    
    def generate_skills(self):
        """Generate random skills for a new player (between 25 and 55)"""
        return {
            "serve": random.randint(35, 55),
            "forehand": random.randint(35, 55),
            "backhand": random.randint(35, 55),
            "speed": random.randint(35, 55),
            "stamina": random.randint(35, 55),
            "straight": random.randint(35, 55),
            "cross": random.randint(35, 55),
            "dropshot": random.randint(35, 55),
            "volley": random.randint(35, 55)
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
    
    def increment_name(self, name):
        """
        Increment alphabetic suffix with carry:
        - If last letter is Z, set it to A and carry to previous letter.
        - Example: AZZ -> BAA, ZZZ -> AAAA
        - Numbers are ignored; if no letters exist, return 'A'.
        """
        chars = list(name)
        i = len(chars) - 1
        saw_letter = False

        while i >= 0:
            c = chars[i]
            if c.isalpha():
                saw_letter = True
                u = c.upper()
                if u == 'Z':
                    chars[i] = 'A'
                    i -= 1  # carry to previous letter
                    continue
                else:
                    chars[i] = chr(ord(u) + 1)
                    return ''.join(chars)
            else:
                i -= 1  # skip non-letters entirely
        # If we’re here:
        # - either we carried past the first letter (all letters were Z -> now A),
        # - or there were no letters at all.
        return ('A' + ''.join(chars)) if saw_letter else 'A'
    
    def generate_surface_modifiers(self):
        """Create per-surface factors in [0.9, 1.1] and ensure their sum >= 3.8."""
        mods = {s: round(random.uniform(0.97, 1.03), 3) for s in ["clay", "grass", "hard", "indoor"]}
        total = sum(mods.values())
        if total < 3.9:
            # Raise the best value until sum reaches 3.9
            deficit = 3.9 - total
            increments = math.ceil(deficit / 0.01)
            best_key = max(mods, key=mods.get)
            mods[best_key] = round(mods[best_key] + 0.01 * increments, 3)
        return mods
