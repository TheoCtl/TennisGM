import json
import random
from math import log2, ceil
from datetime import datetime, timedelta

class TournamentScheduler:
    def __init__(self, data_path='data/'):
        self.data_path = data_path
        self.current_week = 1
        self.current_date = datetime(2025, 1, 1)  # Starting date
        self.load_data()
        
    def load_data(self):
        with open(f'{self.data_path}tournaments.json') as f:
            self.tournaments = json.load(f)['tournaments']
        with open(f'{self.data_path}players.json') as f:
            self.players = json.load(f)['players']
    
    def get_current_week_tournaments(self):
        return [t for t in self.tournaments if t['week'] == self.current_week]
    
    def advance_week(self):
        self.current_week += 1
        self.current_date += timedelta(days=7)
        if self.current_week > 52:
            self.current_week = 1
            # Handle year change if needed
        return self.current_week
    
    def assign_players_to_tournaments(self):
        # Simple assignment logic - players choose tournaments based on ranking
        current_tournaments = self.get_current_week_tournaments()
        available_players = [p for p in self.players if not p['injured'] and not p['retired']]
        
        # Sort tournaments by prestige (Challenger 50 < 75 < 100 < ATP 250 etc.)
        current_tournaments.sort(key=lambda x: (
            -int(x['category'].split()[-1]) if 'Challenger' in x['category'] else -1000
        ))
        
        # Assign top players to top tournaments
        available_players.sort(key=lambda x: x['rank'])
        
        for tournament in current_tournaments:
            tournament['participants'] = []
            draw_size = tournament['draw_size']
            
            # Take next available players
            while len(tournament['participants']) < draw_size and available_players:
                player = available_players.pop(0)
                tournament['participants'].append(player['id'])
                
    def generate_bracket(self, tournament_id):
        tournament = next(t for t in self.tournaments if t['id'] == tournament_id)
        participants = tournament['participants']
        draw_size = tournament['draw_size']
        
        # Fill byes if needed
        while len(participants) < draw_size:
            participants.append(None)  # Bye
        
        # Seed players (optional - could implement later)
        random.shuffle(participants)
        
        # Create bracket structure
        bracket = []
        num_rounds = int(ceil(log2(draw_size)))
        
        # Initialize rounds
        for _ in range(num_rounds):
            bracket.append([])
        
        # First round matches
        bracket[0] = [(participants[i], participants[draw_size-1-i]) 
                     for i in range(draw_size//2)]
        
        tournament['bracket'] = bracket
        tournament['current_round'] = 0
        tournament['active_matches'] = bracket[0].copy()
        return bracket
    
    def get_current_matches(self, tournament_id):
        tournament = next(t for t in self.tournaments if t['id'] == tournament_id)
        return [
            {
                'match_id': i,
                'player1': next((p for p in self.players if p['id'] == m[0]), None) if m[0] else None,
                'player2': next((p for p in self.players if p['id'] == m[1]), None) if m[1] else None,
                'winner': None
            }
            for i, m in enumerate(tournament['active_matches'])
        ]
        
    def simulate_match(self, tournament_id, match_id):
        tournament = next(t for t in self.tournaments if t['id'] == tournament_id)
        match = tournament['active_matches'][match_id]
        
        # Handle byes
        if match[0] is None:
            return match[1]
        if match[1] is None:
            return match[0]
        
        # Simple simulation - replace with your preferred logic later
        p1 = next(p for p in self.players if p['id'] == match[0])
        p2 = next(p for p in self.players if p['id'] == match[1])
        winner_id = match[0] if random.random() < 0.5 else match[1]
        
        # Advance bracket
        self._advance_bracket(tournament, match_id, winner_id)
        return winner_id            
    
    def _advance_bracket(self, tournament, match_id, winner_id):
        # Remove from active matches
        tournament['active_matches'][match_id] = (tournament['active_matches'][match_id][0], 
                                               tournament['active_matches'][match_id][1], 
                                               winner_id)
        
        # Check if round is complete
        if all(len(m) == 3 for m in tournament['active_matches']):
            self._prepare_next_round(tournament)
            
    def _prepare_next_round(self, tournament):
        current_round = tournament['current_round']
        next_round = current_round + 1
        
        if next_round >= len(tournament['bracket']):
            # Tournament complete
            tournament['winner_id'] = tournament['active_matches'][0][2]
            return
        
        # Get winners from current round
        winners = [m[2] for m in tournament['active_matches']]
        
        # Create next round matches
        tournament['bracket'][next_round] = list(zip(winners[::2], winners[1::2]))
        tournament['active_matches'] = tournament['bracket'][next_round].copy()
        tournament['current_round'] = next_round