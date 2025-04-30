import json
from collections import defaultdict
from datetime import datetime, date, timedelta

class RankingSystem:
    # Points structure remains the same as before
    POINTS = {
        "Grand Slam": {
            "Winner": 800,
            "Final": 480,
            "Semi": 360,
            "Quarter": 180,
            "Round 16": 90,
            "Round 32": 45,
            "Round 64": 35,
            "Round 128": 10
        },
        "Masters 1000": {
            "Winner": 400,
            "Final": 240,
            "Semi": 180,
            "Quarter": 90,
            "Round 16": 45,
            "Round 32": 20,
            "Round 64": 25
        },
        "ATP 500": {
            "Winner": 200,
            "Final": 120,
            "Semi": 90,
            "Quarter": 45,
            "Round 16": 25,
            "Round 32": 20
        },
        "ATP 250": {
            "Winner": 100,
            "Final": 60,
            "Semi": 45,
            "Quarter": 25,
            "Round 16": 10,
            "Round 32": 10
        },
        "Challenger 175": {
            "Winner": 75,
            "Final": 40,
            "Semi": 30,
            "Quarter": 15,
            "Round 16": 15
        },
        "Challenger 125": {
            "Winner": 50,
            "Final": 30,
            "Semi": 20,
            "Quarter": 15,
            "Round 16": 10
        },
        "Challenger 100": {
            "Winner": 40,
            "Final": 25,
            "Semi": 17,
            "Quarter": 10,
            "Round 16": 8
        },
        "Challenger 75": {
            "Winner": 30,
            "Final": 20,
            "Semi": 12,
            "Quarter": 7,
            "Round 16": 6
        },
        "Challenger 50": {
            "Winner": 20,
            "Final": 15,
            "Semi": 6,
            "Quarter": 5,
            "Round 16": 4
        }
    } 

    def __init__(self, data_path='data/ranking.json'):
        self.data_path = data_path
        self.ranking_history = defaultdict(list)  # Stores points with dates
        self.load_ranking()

    def load_ranking(self):
        try:
            with open(self.data_path) as f:
                data = json.load(f)
                self.ranking_history = defaultdict(list, data.get('history', {}))
        except (FileNotFoundError, json.JSONDecodeError):
            self.ranking_history = defaultdict(list)

    def save_ranking(self):
        with open(self.data_path, 'w') as f:
            json.dump({'history': dict(self.ranking_history)}, f, indent=2)

    def calculate_points(self, tournament_category, round_reached, total_rounds):
        """Map round numbers to human-readable round names based on tournament type"""
        is_challenger = tournament_category.startswith("Challenger")
        is_250500 = tournament_category.startswith("ATP 250") or tournament_category.startswith("ATP 500")
        is_masters = tournament_category.startswith("Masters 1000")
        is_gs = tournament_category.startswith("Grand Slam")
        round_mapping = {
            # Grand Slams (8 rounds including final)
            8: {
                0: "Round 128", 1: "Round 64", 2: "Round 32", 3: "Round 16", 4: "Quarter", 5: "Semi", 6: "Final", 7: "Winner"
            },
            # Masters 1000 (7 rounds)
            7: {
                0: "Round 64", 1: "Round 32", 2: "Round 16", 3: "Quarter", 4: "Semi", 5: "Final", 6: "Winner"
            },
            # ATP 500/250 (6 rounds)
            6: {
                0: "Round 32", 1: "Round 16", 2: "Quarter", 3: "Semi", 4: "Final", 5: "Winner"
            },
            # Challengers (5 rounds)
            5: {
                0: "Round 16", 1: "Quarter", 2: "Semi", 3: "Final", 4: "Winner"
            }
        }
        
        if is_challenger:
            mapping = round_mapping[5]
        elif is_250500:
            mapping = round_mapping[6]
        elif is_masters:
            mapping = round_mapping[7]
        elif is_gs:
            mapping = round_mapping[8]
            
        round_name = mapping.get(round_reached, "")
        return self.POINTS.get(tournament_category, {}).get(round_name, 0)

    def update_ranking(self, tournament, current_date):
        if not tournament.get('bracket') or tournament['winner_id'] is None:
            return

        # Ensure we store dates as strings in ISO format
        if isinstance(current_date, (datetime, date)):
            date_str = current_date.isoformat()
        else:
            date_str = current_date  # Assume it's already a string

        category = tournament['category']
        num_rounds = len(tournament['bracket'])
        
        # Update points for all participants
        for round_num, matches in enumerate(tournament['bracket']):
            for match in matches:
                for player_id in match[:2]:  # Both players in the match
                    if player_id is not None:
                        points = self.calculate_points(category, round_num, num_rounds)
                        if points > 0:
                            self.ranking_history[str(player_id)].append({
                                'date': date_str,
                                'points': points,
                                'tournament': tournament['name'],
                                'round': round_num,
                                'category': category,
                            })

        # Add bonus for winner
        winner_points = self.calculate_points(category, num_rounds, num_rounds)
        if winner_points > 0:
            self.ranking_history[str(tournament['winner_id'])].append({
                'date': date_str,
                'points': winner_points,
                'tournament': tournament['name'],
                'round': num_rounds,
                'category': category,
                'is_winner': True
            })

        self.save_ranking()

    def get_current_points(self, player_id, current_date):
        """Calculate current points (only from last 52 weeks)"""
        if isinstance(current_date, datetime):
            current_date = current_date.date()  # Convert datetime to date if needed
    
        one_year_ago = current_date - timedelta(weeks=52)
        points = 0
        for entry in self.ranking_history.get(str(player_id), []):
            entry_date = datetime.fromisoformat(entry['date']).date()
            if entry_date >= one_year_ago:
                points += entry['points']
        return points

    def update_player_ranks(self, players, current_date):
        """Update all players' ranks based on current points"""
        if isinstance(current_date, datetime):
            current_date = current_date.date()
        
        # Calculate current points for all players
        ranked_players = []
        for player in players:
            points = self.get_current_points(player['id'], current_date)
            ranked_players.append({
                'id': player['id'],
                'name': player['name'],
                'points': points
            })
        
        # Sort by points descending
        ranked_players.sort(key=lambda x: (-x['points'], x['name']))
        
        # Update ranks in player objects
        for rank, player_data in enumerate(ranked_players, 1):
            for player in players:
                if player['id'] == player_data['id']:
                    player['rank'] = rank
                    player['points'] = player_data['points']
                    break

    def get_ranked_players(self, players, current_date):
        """Return players sorted by ranking points"""
        ranked = []
        for player in players:
            points = self.get_current_points(player['id'], current_date)
            ranked.append((player, points))
        
        # Sort by points descending, then by name ascending
        ranked.sort(key=lambda x: (-x[1], x[0]['name']))
        return ranked