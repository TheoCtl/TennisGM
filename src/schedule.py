import json
import random
from math import log2, ceil
from datetime import datetime, timedelta
from sim.game_engine import GameEngine  # Import the Game Engine
from ranking import RankingSystem

PRESTIGE_ORDER = [
    "Grand Slam",
    "Masters 1000",
    "ATP 500",
    "ATP 250",
    "Challenger 175",
    "Challenger 125",
    "Challenger 100",
    "Challenger 75",
    "Challenger 50"
]

class TournamentScheduler:
    def __init__(self, data_path='data/default_data.json'):
        self.data_path = data_path
        self.current_week = 1
        self.current_year = 1
        self.current_date = datetime(2025, 1, 1)
        self.ranking_system = RankingSystem()  # Add this line
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
            self.current_year += 1
            for player in self.players: # A VERIFIER DES QUE POSSIBLE
                player['age'] += 1
        for tournament in self.tournaments:
            if tournament['week'] == self.current_week - 1 and tournament.get('winner_id'):
                self.ranking_system.update_ranking(tournament, self.current_date)        
        self.ranking_system.update_player_ranks(self.players, self.current_date)
        return self.current_week
    
    def assign_players_to_tournaments(self):
        """
        Assign players to tournaments for the current week.
        Players are distributed across tournaments based on prestige order, and each player can only play in one tournament per week.
        """
        current_tournaments = self.get_current_week_tournaments()
        available_players = [p for p in self.players if not p.get('injured', False) and not p.get('retired', False)]
        available_for_week = []

        # Initialize participants for all tournaments
        for tournament in current_tournaments:
            tournament['participants'] = []  # Ensure the 'participants' key exists

        # Calculate total spots available in tournaments
        total_spots = sum(t['draw_size'] for t in current_tournaments)

        # Randomly select players who will not play if there are more players than spots
        if len(current_tournaments) == 1:
            available_players.sort(key=lambda x: x.get('rank', 999))
            available_for_week.extend(available_players[:128])
        else:
            if len(available_players) > total_spots:
                num_to_skip = len(available_players) - total_spots
                skipped_players = random.sample(available_players, num_to_skip)
                available_for_week = [p for p in available_players if p not in skipped_players]
            else:
                available_for_week = available_players

        # Sort players by rank
        available_for_week.sort(key=lambda x: x.get('rank', 999))

        # Sort tournaments by prestige order
        current_tournaments.sort(key=lambda t: PRESTIGE_ORDER.index(t['category']))

        # Group tournaments by category
        tournaments_by_category = {}
        for tournament in current_tournaments:
            category = tournament['category']
            if category not in tournaments_by_category:
                tournaments_by_category[category] = []
            tournaments_by_category[category].append(tournament)

        # Assign players to tournaments
        for player in available_for_week:
            # Shuffle tournaments for each player to randomize their assignment
            for category in PRESTIGE_ORDER:
                if category in tournaments_by_category:
                    random.shuffle(tournaments_by_category[category])  # Shuffle tournaments in this category

                    # Find the first tournament in the shuffled list with enough spots
                    for tournament in tournaments_by_category[category]:
                        if len(tournament['participants']) < tournament['draw_size']:
                            tournament['participants'].append(player['id'])
                            break  # Once assigned, move to the next player
                    else:
                        continue  # If no tournament in this category has space, check the next category
                    break  # Break out of the category loop once the player is assigned

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
        """
        Fetch the matches for the current round of the tournament.
        """
        tournament = next(t for t in self.tournaments if t['id'] == tournament_id)
        current_round = tournament['current_round']

        # Ensure the current round exists in the bracket
        if current_round >= len(tournament['bracket']):
            return []

        # Fetch matches for the current round
        return [
            {
                'player1': next((p for p in self.players if p['id'] == m[0]), None),
                'player2': next((p for p in self.players if p['id'] == m[1]), None),
                'winner': next((p for p in self.players if p['id'] == m[2]), None) if len(m) > 2 else None
            }
            for m in tournament['bracket'][current_round]
        ]
        
    def simulate_through_match(self, tournament_id, target_match_idx):
        tournament = next(t for t in self.tournaments if t['id'] == tournament_id)

        # Validate match index
        if target_match_idx < 0 or target_match_idx >= len(tournament['active_matches']):
            raise IndexError(f"Match index {target_match_idx} is out of bounds.")

        # Simulate only the target match
        if len(tournament['active_matches'][target_match_idx]) == 4 and tournament['active_matches'][target_match_idx][2] is not None:
            return tournament['active_matches'][target_match_idx][2]

        player1_id, player2_id = tournament['active_matches'][target_match_idx][:2]

        # Handle byes
        if player1_id is None:
            winner_id = player2_id
            final_score = "BYE"
        elif player2_id is None:
            winner_id = player1_id
            final_score = "BYE"
        else:
            # Fetch player data
            player1 = next(p for p in self.players if p['id'] == player1_id)
            player2 = next(p for p in self.players if p['id'] == player2_id)

            # Simulate the match using the Game Engine
            game_engine = GameEngine(player1, player2)
            match_winner = game_engine.simulate_match()

            # Determine the winner ID
            winner_id = player1_id if match_winner == player1 else player2_id

            # Store the final score for this match
            final_score = game_engine.format_set_scores()

        # Update the match with the winner and score
        tournament['active_matches'][target_match_idx] = (player1_id, player2_id, winner_id, final_score)
        tournament['bracket'][tournament['current_round']][target_match_idx] = (player1_id, player2_id, winner_id, final_score)

        # Check if all matches in the current round are complete
        if all(len(m) == 4 and m[2] is not None for m in tournament['active_matches']):
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
                
    def update_match_result(self, tournament_id, match_index, winner_id):
        for tournament in self.tournaments:
            if tournament['id'] == tournament_id:
                match = list(tournament['active_matches'][match_index])
                # Update the winner
                match[2] = winner_id
                # Add the score if needed
                if len(match) == 3:
                    match.append("N/A")
                # Convert back to tuple if necessary (or keep as list)
                tournament['active_matches'][match_index] = tuple(match)
                break
            
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
        winners = []
        for idx, match in enumerate(tournament['active_matches']):
            if match[2] is not None:  # Ensure the match has a winner
                winners.append(match[2])
                # Store the final score in the bracket for the current round
                tournament['bracket'][current_round][idx] = (
                    match[0], match[1], match[2], match[3]
                )

        # Create next round matches
        next_round_matches = []
        for i in range(0, len(winners), 2):
            if i + 1 < len(winners):
                next_round_matches.append((winners[i], winners[i + 1], None))
            else:
                next_round_matches.append((winners[i], None, None))

        # Assign matches to the next round
        if next_round >= len(tournament['bracket']):
            tournament['bracket'].append(next_round_matches)
        else:
            tournament['bracket'][next_round] = next_round_matches

        tournament['active_matches'] = next_round_matches  # Update active matches
        tournament['current_round'] = next_round

        print(f"\nRound {current_round + 1} complete! Advancing to Round {next_round + 1}")
        