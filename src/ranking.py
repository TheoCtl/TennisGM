import json
import math
from collections import defaultdict
from datetime import datetime, date, timedelta

class RankingSystem:
    # Points structure remains the same as before
    POINTS = {
        "Special": {
            "Winner": 0,
            "Final": 0,
            "Semi": 0
        },
        "Grand Slam": {
            "Winner": 100,
            "Final": 0,
            "Semi": 0,
            "Quarter": 0,
            "Round 16": 0,
            "Round 32": 0,
            "Round 64": 0,
            "Round 128": 0
        },
        "Masters 1000": {
            "Winner": 50,
            "Final": 0,
            "Semi": 0,
            "Quarter": 0,
            "Round 16": 0,
            "Round 32": 0,
            "Round 64": 0
        },
        "ATP 500": {
            "Winner": 35,
            "Final": 0,
            "Semi": 0,
            "Quarter": 0,
            "Round 16": 0,
            "Round 32": 0
        },
        "ATP 250": {
            "Winner": 25,
            "Final": 0,
            "Semi": 0,
            "Quarter": 0,
            "Round 16": 0,
            "Round 32": 0
        },
        "Challenger 175": {
            "Winner": 15,
            "Final": 0,
            "Semi": 0,
            "Quarter": 0,
            "Round 16": 0
        },
        "Challenger 125": {
            "Winner": 13,
            "Final": 0,
            "Semi": 0,
            "Quarter": 0,
            "Round 16": 0
        },
        "Challenger 100": {
            "Winner": 11,
            "Final": 0,
            "Semi": 0,
            "Quarter": 0,
            "Round 16": 0
        },
        "Challenger 75": {
            "Winner": 9,
            "Final": 0,
            "Semi": 0,
            "Quarter": 0,
            "Round 16": 0
        },
        "Challenger 50": {
            "Winner": 7,
            "Final": 0,
            "Semi": 0,
            "Quarter": 0,
            "Round 16": 0
        },
        "ITF": {
            "Winner": 5,
            "Final": 0,
            "Semi": 0,
            "Quarter": 0,
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
        is_kings = tournament_category.startswith("Special")
        is_itf = tournament_category.startswith("ITF")
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
            },
            # Kings
            3: {
                0: "Semi", 1: "Final", 2: "Winner"
            }
        }
        
        if is_challenger:
            mapping = round_mapping[5]
        elif is_itf:
            mapping = round_mapping[5]
        elif is_250500:
            mapping = round_mapping[6]
        elif is_masters:
            mapping = round_mapping[7]
        elif is_gs:
            mapping = round_mapping[8]
        elif is_kings:
            mapping = round_mapping[3]
            
        round_name = mapping.get(round_reached, "")
        points = self.POINTS.get(tournament_category, {}).get(round_name, 0)
        
        return points

    def get_current_points(self, player_id, current_date):
        """Calculate championship points from tournament results in last 52 weeks using tournament_history"""
        if isinstance(current_date, datetime):
            current_date = current_date.date()
            
        player = next((p for p in self.players if p['id'] == player_id), None)
        if not player or player.get('retired', False):
            return 0
    
        championship_points = 0
        
        # Calculate points from player's tournament_history using calculate_points
        if 'tournament_history' in player:
            for tournament_entry in player['tournament_history']:                
                try:
                    points = self.calculate_points(
                        tournament_entry.get('category', ''),
                        tournament_entry.get('round', 0),
                        tournament_entry.get('total_rounds', 0)
                    )
                    championship_points += points
                except (ValueError, TypeError):
                    # Skip invalid date entries
                    continue
        
        return championship_points

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
        """Return players sorted by combined rating (ELO + Championship points)"""
        self.players = players
        ranked = []
        for player in players:
            if player.get('retired', False):
                continue
            elo_rating = self.get_elo_rating(player)
            championship_points = self.get_current_points(player['id'], current_date)
            combined_rating = elo_rating + championship_points
            ranked.append((player, combined_rating))
        
        # Sort by combined rating descending, then by name ascending
        ranked.sort(key=lambda x: (-x[1], x[0]['name']))
        return ranked
    
    def calculate_expected_score(self, rating_a, rating_b):
        """Calculate expected score for player A against player B using ELO formula"""
        return 1 / (1 + 10**((rating_b - rating_a) / 400))

    def update_elo_ratings(self, player1_id, player2_id, result, players):
        """
        Update ELO ratings after a match
        result: 1 if player1 wins, 0 if player2 wins, 0.5 for draw
        """
        # Find players
        player1 = next((p for p in players if p['id'] == player1_id), None)
        player2 = next((p for p in players if p['id'] == player2_id), None)
        
        if not player1 or not player2:
            return
        
        # Get current ELO ratings (initialize to 1500 for new players)
        rating1 = player1.get('elo_rating', 1000)
        rating2 = player2.get('elo_rating', 1000)
        
        # Get matches played count (already updated during match simulation)
        matches_played1 = player1.get('matches_played', 0)
        matches_played2 = player2.get('matches_played', 0)
        
        # Calculate expected scores
        expected1 = self.calculate_expected_score(rating1, rating2)
        expected2 = self.calculate_expected_score(rating2, rating1)
        
        # Calculate dynamic K-factors using Tennis Abstract formula: 250/(matches_played + 5)^0.4
        k1 = 250 / ((matches_played1 + 5) ** 0.4)
        k2 = 250 / ((matches_played2 + 5) ** 0.4)
        
        # Apply tournament level modifier (1.1 for Grand Slams)
        tournament_level = player1.get('current_tournament', {}).get('category', '')
        level_modifier = 1.1 if tournament_level == "Grand Slam" else 1.0
        
        # Update ratings with Tennis Abstract formula and apply stability factor
        rating_change1 = (level_modifier * k1) * (result - expected1)
        rating_change2 = (level_modifier * k2) * ((1 - result) - expected2)
            
        new_rating1 = rating1 + rating_change1
        new_rating2 = rating2 + rating_change2
        
        # Store updated ratings (minimum of 1000 to prevent extreme low ratings)
        player1['elo_rating'] = max(1000, round(new_rating1))
        player2['elo_rating'] = max(1000, round(new_rating2))
        
        # Calculate current ELO points (rating + championship points) for comparison
        player1_elo_points = player1['elo_rating'] + self.get_current_points(player1['id'], datetime.now().date())
        player2_elo_points = player2['elo_rating'] + self.get_current_points(player2['id'], datetime.now().date())
        
        # Update highest ELO points if current ELO points are higher
        if player1_elo_points > player1.get('highest_elo', player1_elo_points):
            player1['highest_elo'] = player1_elo_points
        if player2_elo_points > player2.get('highest_elo', player2_elo_points):
            player2['highest_elo'] = player2_elo_points
        
        return {
            'player1_old': rating1,
            'player1_new': player1['elo_rating'],
            'player2_old': rating2, 
            'player2_new': player2['elo_rating']
        }

    def initialize_elo_ratings(self, players):
        """Initialize ELO ratings for existing players based on their current rank"""
        active_players = [p for p in players if not p.get('retired', False)]
        total_players = len(active_players)
        
        for player in active_players:
            # Better ELO initialization: Start from 1500 and adjust based on rank
            current_rank = player.get('rank', total_players)
            
            # Clamp rank to valid range to avoid negative ELO
            effective_rank = min(current_rank, total_players)
            
            # Calculate ELO based on rank percentile
            # Rank 1 gets ~2000, middle ranks get ~1500, bottom ranks get ~1000
            if total_players > 1:
                percentile = 1 - (effective_rank - 1) / (total_players - 1)
            else:
                percentile = 1.0  # Single player gets max ELO
                
            base_elo = 1000 + (percentile * 1000)  # Range from 1000 to 2000
            player['elo_rating'] = round(base_elo)
            
            # Initialize highest_elo to current ELO points (rating + championship) if not already set
            if 'highest_elo' not in player:
                championship_points = self.get_current_points(player['id'], datetime.now().date())
                player['highest_elo'] = player['elo_rating'] + championship_points
            
        return players

    def get_combined_rating(self, player, current_date):
        """Get combined rating: ELO + Championship points"""
        elo_rating = player.get('elo_rating', 0)
        championship_points = self.get_current_points(player['id'], current_date)
        return elo_rating + championship_points
    
    def get_elo_rating(self, player):
        """Get just the ELO rating for a player"""
        return player.get('elo_rating', 0)
    
    def get_elo_points(self, player, current_date):
        """Get ELO points (ELO rating + Championship points) - this is what's displayed to users"""
        elo_rating = player.get('elo_rating', 0)
        championship_points = self.get_current_points(player['id'], current_date)
        return elo_rating + championship_points

    def update_combined_rankings(self, players, current_date):
        """Update rankings based on combined ELO + Championship points"""
        if isinstance(current_date, datetime):
            current_date = current_date.date()
            
        self.players = players
        
        # Calculate combined ratings for all players
        ranked_players = []
        for player in players:
            if player.get('retired', False):
                continue
            elo_rating = self.get_elo_rating(player)
            championship_points = self.get_current_points(player['id'], current_date)
            combined_rating = elo_rating + championship_points
            
            ranked_players.append({
                'id': player['id'],
                'name': player['name'],
                'combined_rating': combined_rating,
                'elo_rating': elo_rating,
                'championship_points': championship_points
            })
        
        # Sort by combined rating descending
        ranked_players.sort(key=lambda x: (-x['combined_rating'], x['name']))
        
        # Update ranks in player objects
        ranking_changes = {}
        for rank, player_data in enumerate(ranked_players, 1):
            for player in players:
                if player['id'] == player_data['id']:
                    old_rank = player.get('rank', 999)
                    player['rank'] = rank
                    # Store separate values for display
                    player['points'] = player_data['combined_rating']  # Total for main display
                    player['elo_points'] = player_data['elo_rating']  # ELO component
                    player['championship_points'] = player_data['championship_points']  # Championship component
                    if old_rank != rank:
                        ranking_changes[player['id']] = (old_rank, rank)
                    break
                    
        return ranking_changes