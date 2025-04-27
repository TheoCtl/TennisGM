import json
import random
from math import log2, ceil
from datetime import datetime, timedelta

class TournamentScheduler:
    def __init__(self, data_path='data/default_data.json'):
        self.data_path = data_path
        self.current_week = 1
        self.current_date = datetime(2025, 1, 1)  # Starting date
        self.load_data()
        
    def load_data(self):
        with open(self.data_path) as f:
            data = json.load(f)
            self.players = data['players']
            self.tournaments = data['tournaments']
        print(f"Loaded {len(self.players)} players")  # Debug
        print(f"Loaded {len(self.tournaments)} tournaments")  # Debug
    
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
        current_tournaments = self.get_current_week_tournaments()
        available_players = [p for p in self.players if not p.get('injured', False) 
                            and not p.get('retired', False)]
    
        # Sort tournaments by prestige (reverse order)
        current_tournaments.sort(key=lambda x: (
            -int(x['category'].split()[-1]) if 'Challenger' in x['category'] else -1000
        ))
    
        # Sort players by ranking
        available_players.sort(key=lambda x: x.get('rank', 999))
    
        for tournament in current_tournaments:
            # Initialize participants if not exists
            if 'participants' not in tournament:
                tournament['participants'] = []
        
            # Clear existing participants if any
            tournament['participants'] = []
        
            # Fill with top available players
            needed = tournament['draw_size'] - len(tournament['participants'])
            tournament['participants'] = [p['id'] for p in available_players[:needed]]
            available_players = available_players[needed:]
                
    def generate_bracket(self, tournament_id):
        tournament = next(t for t in self.tournaments if t['id'] == tournament_id)
        participants = tournament['participants']
        draw_size = tournament['draw_size']
        
        # Fill byes if needed
        while len(participants) < draw_size:
            participants.append(None)  # Bye
            
        num_rounds = int(ceil(log2(draw_size)))
        tournament['bracket'] = []
        
        # Seed players (optional - could implement later)
        random.shuffle(participants)
        
        # Initialize rounds
        for _ in range(1, num_rounds):
            tournament['bracket'].append([])
        
        first_round = [(participants[i], participants[draw_size-1-i], None)
                       for i in range(draw_size//2)]
        tournament['bracket'].append(first_round)
        
        tournament['current_round'] = 0
        tournament['active_matches'] = first_round.copy()
    
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
        
    def simulate_match(self, tournament_id, match_idx):
        tournament = next(t for t in self.tournaments if t['id'] == tournament_id)
        
        # Get the match details
        player1_id, player2_id, _ = tournament['active_matches'][match_idx]
    
        # Handle byes
        if player1_id is None:
            return player2_id
        if player2_id is None:
            return player1_id
    
        # Simple simulation - replace with your logic later
        winner_id = random.choice([player1_id, player2_id])
        
        tournament['active_matches'][match_idx] = (player1_id, player2_id, winner_id)
    
        tournament['bracket'][tournament['current_round']][match_idx] = (player1_id, player2_id, winner_id)
        
        if all(match[2] is not None for match in tournament['active_matches']):
            self._prepare_next_round(tournament)
    
        return winner_id            
    
    def _advance_bracket(self, tournament, match_idx, winner_id):
        # Mark the current match as completed with winner
        tournament['active_matches'][match_idx] = (
            tournament['active_matches'][match_idx][0],
            tournament['active_matches'][match_idx][1],
            winner_id
        )
    
        # Check if all matches in current round are complete
        if all(len(m) == 3 for m in tournament['active_matches']):
            if len(tournament['bracket']) == tournament['current_round'] + 1:
                # Tournament final completed
                tournament['winner_id'] = winner_id
            else:
                # Prepare next round
                self._prepare_next_round(tournament)
            
    def _prepare_next_round(self, tournament):
        current_round = tournament['current_round']
        next_round = current_round + 1
        
        if next_round >= len(tournament['bracket']):
            # Tournament complete
            tournament['winner_id'] = tournament['active_matches'][0][2]
            return
        
        # Get winners from current round
        winners = [match[2] for match in tournament['active_matches']]
        
        next_round_matches = []
        for i in range(0, len(winners), 2):
            if i+1 < len(winners):
                next_round_matches.append((winners[i], winners[i+1], None))
        
        # Create next round matches
        tournament['bracket'][next_round] = next_round_matches
        tournament['active_matches'] = next_round_matches.copy()
        tournament['current_round'] = next_round