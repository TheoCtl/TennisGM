import json
from collections import defaultdict
from datetime import datetime, date, timedelta

class RankingSystem:
    # Points structure remains the same as before
    POINTS = {
        "Grand Slam": {
            "Winner": 2000,
            "Final": 1200,
            "Semi": 720,
            "Quarter": 360,
            "Round 16": 180,
            "Round 32": 90,
            "Round 64": 45,
            "Round 128": 0
        },
        "Masters 1000": {
            "Winner": 1000,
            "Final": 600,
            "Semi": 360,
            "Quarter": 180,
            "Round 16": 90,
            "Round 32": 45,
            "Round 64": 0
        },
        "ATP 500": {
            "Winner": 500,
            "Final": 300,
            "Semi": 180,
            "Quarter": 90,
            "Round 16": 45,
            "Round 32": 0
        },
        "ATP 250": {
            "Winner": 250,
            "Final": 150,
            "Semi": 90,
            "Quarter": 45,
            "Round 16": 20,
            "Round 32": 0
        },
        "Challenger 175": {
            "Winner": 175,
            "Final": 100,
            "Semi": 60,
            "Quarter": 30,
            "Round 16": 0
        },
        "Challenger 125": {
            "Winner": 125,
            "Final": 75,
            "Semi": 45,
            "Quarter": 25,
            "Round 16": 0
        },
        "Challenger 100": {
            "Winner": 100,
            "Final": 60,
            "Semi": 35,
            "Quarter": 18,
            "Round 16": 0
        },
        "Challenger 75": {
            "Winner": 75,
            "Final": 45,
            "Semi": 25,
            "Quarter": 13,
            "Round 16": 0
        },
        "Challenger 50": {
            "Winner": 50,
            "Final": 30,
            "Semi": 15,
            "Quarter": 9,
            "Round 16": 0
        }
    } 

    def __init__(self, data_path='data/ranking.json'):
        self.data_path = data_path
        self.ranking_history = defaultdict(list)  # Stores points with dates
        self.players = []
        self.load_ranking()

    def load_ranking(self):
        try:
            with open(self.data_path) as f:
                data = json.load(f)
                self.ranking_history = defaultdict(list, 
                    {str(k): v for k, v in data.get('history', {}).items()}
                )
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
        points = self.POINTS.get(tournament_category, {}).get(round_name, 0)
        
        return points

    def get_current_points(self, player_id, current_date):
        """Calculate points from both ranking history and current tournament history"""

        if isinstance(current_date, datetime):
            current_date = current_date.date()
            
        player = next((p for p in self.players if p['id'] == player_id), None)
        if player and player.get('retired', False):
            return 0
    
        one_year_ago = current_date - timedelta(weeks=52)
        points = 0
    
        # Check ranking history first
        for entry in self.ranking_history.get(str(player_id), []):
            entry_date = datetime.fromisoformat(entry['date']).date() if isinstance(entry['date'], str) else entry['date']
            if entry_date <= one_year_ago:
                points += entry.get('points', 0)
    
        # Double-check with player tournament history (as backup)
        if player and 'tournament_history' in player:
            for entry in player['tournament_history']:
                entry_date = datetime(entry['year'], 1, 1) + timedelta(weeks=entry.get('week', 0))
                if entry_date.date() <= one_year_ago:
                    points += entry.get('points', 0)
    
        return points

    def update_ranking(self, tournament, current_date):
        """Maintain this for backward compatibility"""
        if not tournament.get('bracket'):
            return
    
        # Store basic ranking info
        date_str = current_date.isoformat() if isinstance(current_date, (datetime, date)) else current_date
        category = tournament['category']
    
        for round_num, matches in enumerate(tournament['bracket']):
            for match in matches:
                for player_id in match[:2]:
                    if player_id:
                        points = self.calculate_points(category, round_num, len(tournament['bracket']))
                        self.ranking_history[str(player_id)].append({
                            'date': date_str,
                            'points': points,
                            'tournament': tournament['name'],
                            'category': category,
                            'round': round_num
                        })
    
        if tournament.get('winner_id') is not None:
            winner_points = self.calculate_points(category, len(tournament['bracket'])-1, len(tournament['bracket']))
            self.ranking_history[str(tournament['winner_id'])].append({
                'date': date_str,
                'points': winner_points,
                'tournament': tournament['name'],
                'category': category,
                'round': len(tournament['bracket'])-1,
                'is_winner': True
            })
    
        self.save_ranking()

    def update_player_ranks(self, players, current_date):
        """Update all players' ranks based on current points"""
        if isinstance(current_date, datetime):
            current_date = current_date.date()
            
        self.players = players
        current_rankings = {p['id']: p.get('rank', 999) for p in players if not p.get('retired', False)}
        
        # Calculate current points for all players
        ranked_players = []
        for player in players:
            if player.get('retired', False):
                continue
            points = self.get_current_points(player['id'], current_date)
            ranked_players.append({
                'id': player['id'],
                'name': player['name'],
                'points': points
            })
        
        # Sort by points descending
        ranked_players.sort(key=lambda x: (-x['points'], x['name']))
        
        # Update ranks in player objects
        ranking_changes = {}
        for rank, player_data in enumerate(ranked_players, 1):
            for player in players:
                if player['id'] == player_data['id']:
                    old_rank = player.get('rank', 999)
                    player['rank'] = rank
                    player['points'] = player_data['points']
                    if old_rank != rank:
                        ranking_changes[player['id']] = (old_rank, rank)
                    break
        self.previous_rankings = current_rankings
        return ranking_changes

    def get_ranked_players(self, players, current_date):
        """Return players sorted by ranking points"""
        self.players = players
        ranked = []
        for player in players:
            if player.get('retired', False):
                continue
            points = self.get_current_points(player['id'], current_date)
            ranked.append((player, points))
        
        # Sort by points descending, then by name ascending
        ranked.sort(key=lambda x: (-x[1], x[0]['name']))
        return ranked