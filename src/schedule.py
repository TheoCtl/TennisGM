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
        tournament['bracket'] = [[] for _ in range(num_rounds)]  # Initialize all rounds as empty lists
        
        # Seed players (optional - could implement later)
        random.shuffle(participants)
        
        # Initialize first round
        first_round = [(participants[i], participants[draw_size-1-i], None)
                       for i in range(draw_size // 2)]
        tournament['bracket'][0] = first_round  # Assign first round to the bracket
        
        tournament['current_round'] = 0
        tournament['active_matches'] = first_round.copy()
    
    def get_current_matches(self, tournament_id):
        tournament = next(t for t in self.tournaments if t['id'] == tournament_id)
        return [
            {
                'match_id': i,
                'player1': next((p for p in self.players if p['id'] == m[0]), None) if m[0] else None,
                'player2': next((p for p in self.players if p['id'] == m[1]), None) if m[1] else None,
                'winner': next((p for p in self.players if p['id'] == m[2]), None) if m[2] else None
            }
            for i, m in enumerate(tournament['active_matches'])
        ]
        
    def simulate_through_match(self, tournament_id, target_match_idx):
        tournament = next(t for t in self.tournaments if t['id'] == tournament_id)

        # Debug: Log tournament and match details
        print(f"Simulating match {target_match_idx} in tournament {tournament['id']}")
        print(f"Active matches: {tournament['active_matches']}")

        # Validate match index
        if target_match_idx < 0 or target_match_idx >= len(tournament['active_matches']):
            raise IndexError(f"Match index {target_match_idx} is out of bounds.")

        # Simulate only the target match
        if tournament['active_matches'][target_match_idx][2] is not None:
            # Match already completed
            print(f"Match {target_match_idx} already completed.")
            return tournament['active_matches'][target_match_idx][2]

        player1_id, player2_id = tournament['active_matches'][target_match_idx][:2]

        # Handle byes
        if player1_id is None:
            winner_id = player2_id
        elif player2_id is None:
            winner_id = player1_id
        else:
            winner_id = random.choice([player1_id, player2_id])

        # Update the match with the winner
        tournament['active_matches'][target_match_idx] = (player1_id, player2_id, winner_id)
        tournament['bracket'][tournament['current_round']][target_match_idx] = (player1_id, player2_id, winner_id)

        # Debug: Log match result
        print(f"Match {target_match_idx} result: {player1_id} vs {player2_id} -> Winner: {winner_id}")

        # Check if all matches in the current round are complete
        if all(m[2] is not None for m in tournament['active_matches']):
            print("All matches in the current round are complete. Preparing next round...")
            self._prepare_next_round(tournament)  # Advance to the next round if complete

        # Return the winner of the target match
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

        # Check if the current round is the final round
        if next_round >= len(tournament['bracket']):
            # Tournament is complete
            if tournament['active_matches'] and tournament['active_matches'][0][2]:
                tournament['winner_id'] = tournament['active_matches'][0][2]  # Winner of the final match
                winner = next((p for p in self.players if p['id'] == tournament['winner_id']), None)
                if winner:
                    print(f"\nTOURNAMENT CHAMPION: {winner['name']}!")
                else:
                    print("\nTOURNAMENT CHAMPION: Unknown (Player not found)!")
            else:
                print("\nError: Final match has no winner!")
            return  # Exit as the tournament is complete

        # Get winners from the current round
        winners = [match[2] for match in tournament['active_matches'] if match[2] is not None]

        next_round_matches = []
        for i in range(0, len(winners), 2):
            if i + 1 < len(winners):
                next_round_matches.append((winners[i], winners[i + 1], None))
            else:
                next_round_matches.append((winners[i], None, None))

        # Create next round matches
        tournament['bracket'][next_round] = next_round_matches  # Assign matches to the next round
        tournament['active_matches'] = next_round_matches
        tournament['current_round'] = next_round

        print(f"\nRound {current_round + 1} complete! Advancing to Round {next_round + 1}")