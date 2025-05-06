import json
import random
from math import log2, ceil
from datetime import datetime, timedelta
from collections import defaultdict
from sim.game_engine import GameEngine  # Import the Game Engine
from ranking import RankingSystem
from player_development import PlayerDevelopment
from newgen import NewGenGenerator

class TournamentScheduler:
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
    
    def __init__(self, data_path='data/default_data.json', save_path='data/save.json'):
        self.data_path = data_path
        self.save_path = save_path
        self.current_week = 1
        self.current_year = 1
        self.current_date = datetime(2025, 1, 1)
        self.ranking_system = RankingSystem()
        self.newgen_generator = NewGenGenerator()
        self.hall_of_fame = []
        self.previous_rankings = {}
        self.news_feed = []
        self.load_data(data_path, save_path)
        
        for player in self.players:
            if 'tournament_history' not in player:
                player['tournament_history'] = []
            if 'tournament_wins' not in player:
                player['tournament_wins'] = []
        self._rebuild_ranking_history
        self.ranking_system.update_player_ranks(self.players, self.current_date)
        
    def save_game(self, save_path='data/save.json'):
        """Save all game data to a file"""
        game_data = {
            'current_year': self.current_year,
            'current_week': self.current_week,
            'current_date': self.current_date.isoformat(),
            'players': self.players,
            'tournaments': self.tournaments,
            'ranking_history': dict(self.ranking_system.ranking_history),
            'hall_of_fame': self.hall_of_fame
        }
    
        with open(save_path, 'w') as f:
            json.dump(game_data, f, indent=2)
        
    def load_data(self, data_path='data/default_data.json', save_path='data/save.json'):
        try:
            # Try loading saved game
            with open(save_path) as f:
                data = json.load(f)
                self.players = data['players']
                self.tournaments = data['tournaments']
                for player in self.players:
                    if 'retired' not in player: 
                        player['retired'] = False
                self.current_year = data['current_year']
                self.current_week = data['current_week']
                self.current_date = datetime.fromisoformat(data['current_date'])
                
                for player in self.players:
                    if 'tournament_history' not in player:
                        player['tournament_history'] = []
                    if 'tournament_wins' not in player:
                        player['tournament_wins'] = []
                self.ranking_system.ranking_history = defaultdict(list)
                for player_id, entries in data.get('ranking_history', {}).items():
                    self.ranking_system.ranking_history[int(player_id)] = entries
                self.hall_of_fame = data.get('hall_of_fame', [])
            print("Loaded saved game")
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            for player in self.players:
                if 'retired' not in player:
                    player['retired'] = False
            print (f"Error loading saved game: {str(e)}")
            # Fall back to default data
            with open(data_path) as f:
                data = json.load(f)
                self.players = data['players']
                self.tournaments = data['tournaments']
            print("Loaded default data")
            for player in self.players:
                player['tournament_history'] = []
                player['tournament_wins'] = []
            self.hall_of_fame = []
    
    def get_current_week_tournaments(self):
        return [t for t in self.tournaments if t['week'] == self.current_week]
    
    def advance_week(self):
        self.old_rankings = {p['id']: p['rank'] for p in self.players if not p.get('retired', False)}
        self.current_week += 1
        self.current_date += timedelta(days=7)
        for tournament in self.tournaments:
            if tournament['week'] == self.current_week - 1 and tournament.get('winner_id'):
                self._update_all_player_histories(tournament)
        self._cleanup_old_tournament_history()
        if self.current_week > 52:
            self.current_week = 1
            self.current_year += 1
            retired_count = self._process_retirements()
            new_player_count = retired_count + 5
            for player in self.players:
                if 'age' in player and not player.get('retired', False):
                    player['age'] += 1
            new_players = self.newgen_generator.generate_new_players(self.current_year, count=new_player_count, existing_players=self.players)
            self.players.extend(new_players)
            self._reset_tournaments_for_new_year()
            self._rebuild_ranking_history()
        else:
            current_week_tournaments = [t for t in self.tournaments if t['week'] == self.current_week]
            if current_week_tournaments:
                self.assign_players_to_tournaments()
                for tournament in current_week_tournaments:
                    self.generate_bracket(tournament['id'])
        self.generate_news_feed()
        self.ranking_system.update_player_ranks(self.players, self.current_date)
        PlayerDevelopment.seasonal_development(self)
        return self.current_week
    
    def _cleanup_old_tournament_history(self):
        cutoff_year = self.current_year - 1
        cutoff_week = self.current_week
    
        for player in self.players:
            if 'tournament_history' not in player:
                continue
            player['tournament_history'] = [
                entry for entry in player['tournament_history']
                if not self._is_tournament_too_old(entry, cutoff_year, cutoff_week)
            ]
            
    def _is_tournament_too_old(self, tournament_entry, cutoff_year, cutoff_week):
        if tournament_entry['year'] < cutoff_year:
            return True
        elif tournament_entry['year'] == cutoff_year:
            return tournament_entry.get('week', 0) < cutoff_week
        return False
    
    def _update_all_player_histories(self, tournament):
        """Update history for all participants in a tournament"""
        player_rounds = {}
    
        # Find furthest round reached for each player
        for round_num, matches in enumerate(tournament['bracket']):
            for match in matches:
                for player_id in match[:2]:  # Both players
                    if player_id is not None:
                        if player_id not in player_rounds or round_num > player_rounds[player_id]:
                            player_rounds[player_id] = round_num
    
        # Update history for each player
        for player_id, round_reached in player_rounds.items():
            self._update_player_tournament_history(tournament, player_id, round_reached)
            
    def _rebuild_ranking_history(self):
        """Rebuild ranking history from player tournament histories"""
        self.ranking_system.ranking_history = defaultdict(list)
    
        for player in self.players:
            if 'tournament_history' not in player:
                continue
            
            for entry in player['tournament_history']:
                # Create date from year/week
                entry_date = datetime(entry['year'], 1, 1) + timedelta(weeks=entry.get('week', 0))
            
                self.ranking_system.ranking_history[player['id']].append({
                    'date': entry_date.isoformat(),
                    'points': entry['points'],
                    'tournament': entry['name'],
                    'category': entry['category'],
                    'round': entry['round']
                })
    
        self.ranking_system.save_ranking()
    
    def _update_final_tournament_standings(self, tournament):
        player_rounds = {}
        for round_num, matches in enumerate(tournament['bracket']):
            for match in matches:
                for player_id in match[:2]:
                    if player_id is not None:
                        if player_id not in player_rounds or round_num > player_rounds[player_id]:
                            player_rounds[player_id] = round_num
                            
        for player_id, round_reached in player_rounds.items():
            self._update_player_tournament_history(tournament, player_id, round_reached)
    
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
        current_tournaments.sort(key=lambda t: self.PRESTIGE_ORDER.index(t['category']))

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
            for category in self.PRESTIGE_ORDER:
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
        
        match = tournament['active_matches'][target_match_idx]
        player1_id, player2_id = match[:2]

        # Handle byes
        if player1_id is None:
            winner_id = player2_id
            final_score = "BYE"
            self._update_player_tournament_history(tournament, player2_id, tournament['current_round'])
        elif player2_id is None:
            winner_id = player1_id
            final_score = "BYE"
            self._update_player_tournament_history(tournament, player1_id, tournament['current_round'])
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
            
            loser_id = player2_id if winner_id == player1 else player1_id
            self._update_player_tournament_history(tournament, loser_id, tournament['current_round'])

        # Update the match with the winner and score
        tournament['active_matches'][target_match_idx] = (player1_id, player2_id, winner_id, final_score)
        tournament['bracket'][tournament['current_round']][target_match_idx] = (player1_id, player2_id, winner_id, final_score)

        # Check if all matches in the current round are complete
        if all(len(m) == 4 and m[2] is not None for m in tournament['active_matches']):
            self._prepare_next_round(tournament)

        return winner_id
    
    def _update_player_tournament_history(self, tournament, player_id, round_reached):
        """Update a player's tournament history when they lose a match"""
        player = next((p for p in self.players if p['id'] == player_id), None)
        if not player:
            return

        if 'tournament_history' not in player:
            player['tournament_history'] = []
            
        points = self.ranking_system.calculate_points(
            tournament['category'], round_reached, len(tournament['bracket']))

        # Check if player already has an entry for this tournament
        existing_entry = next(
            (entry for entry in player['tournament_history'] 
            if entry['name'] == tournament['name'] and entry['year'] == self.current_year),
            None
        )

        if existing_entry:
            # Update existing entry if this is a later round
            if round_reached > existing_entry.get('round', -1):
                existing_entry['round'] = round_reached
                existing_entry['points'] = points
        else:
            # Add new entry
            player['tournament_history'].append({
                'name': tournament['name'],
                'category': tournament['category'],
                'year': self.current_year,
                'week': self.current_week,
                'round': round_reached,
                'points': points
            })
        
    def _advance_bracket(self, tournament, match_idx, winner_id):
        # Mark the current match as completed with winner
        tournament['active_matches'][match_idx] = (
            tournament['active_matches'][match_idx][0],
            tournament['active_matches'][match_idx][1],
            winner_id
        )
    
        # Check if all matches in current round are complete
        if all(len(m) == 3 for m in tournament['active_matches']):
            if len(tournament['bracket']) == tournament['current_round']:
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
                    # Add to wins
                    if 'tournament_wins' not in winner:
                        winner['tournament_wins'] = []
                    winner['tournament_wins'].append({
                        'name': tournament['name'],
                        'category': tournament['category'],
                        'year': self.current_year
                    })
                
                # Ensure winner's history is updated (they might not have lost any matches)
                    self._update_player_tournament_history(
                        tournament, 
                        tournament['winner_id'], 
                        len(tournament['bracket'])  # Final round
                    )
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
        
    def _process_retirements(self):
        """Handle player retirements at the end of the year"""
        retired_players = []
        retired_count = 0
    
        for player in self.players:
            if player.get('retired', False):
                continue
            
            age = player.get('age', 20)
        
            # Automatic retirement at 40+
            if age >= 40:
                player['retired'] = True
                retired_players.append(player['name'])
                retired_count += 1
                self._add_to_hall_of_fame(player)
                continue
            
            # Chance-based retirement for players 35-39
            if age >= 35:
                retirement_chance = (age - 34) * 0.05  # 5% at 35, 10% at 36, etc.
                if random.random() < retirement_chance:
                    player['retired'] = True
                    retired_players.append(player['name'])
                    retired_count += 1
                    self._add_to_hall_of_fame(player)
    
        if retired_players:
            print(f"\nThe following players have retired: {', '.join(retired_players)}")
        return retired_count
    
    def _add_to_hall_of_fame(self, player):
        hof_entry = {
            'name' : player['name'],
            'tournament_wins' : player.get('tournament_wins', []).copy()
        }
        self.hall_of_fame.append(hof_entry)
    
    def _reset_tournaments_for_new_year(self):
        self.old_rankings = {p['id']: p['rank'] for p in self.players if not p.get('retired', False)}
        for tournament in self.tournaments:
            tournament['participants'] = []
            tournament['bracket'] = []
            tournament['active_matches'] = []
            tournament['current_round'] = 0
            tournament['winner_id'] = None
            
            if 'matches' in tournament:
                del tournament['matches']
                
        current_week_tournaments = [t for t in self.tournaments if t['week'] == self.current_week]
        if current_week_tournaments:
            self.assign_players_to_tournaments()
            for tournament in current_week_tournaments:
                self.generate_bracket(tournament['id'])
                
    def generate_news_feed(self):
        self.news_feed = []
        
        # 5. Progressions/regressions weeks
        if self.current_week in [26, 52]:
            self.news_feed.append("Player development week: Skills have progressed/regressed!")

        # 6. Newgens and retirements (only when they happen)
        if self.current_week == 1:
            # Check for newgens added last week (week 52)
            newgens = [p for p in self.players if p['age'] == 16]
            if newgens:
                self.news_feed.append(f"New players joined the tour: {', '.join(p['name'] for p in newgens)}")

            # Check for retirements
            retired = [p for p in self.players if p.get('retired', False) and p['age'] >= 35]
            if retired:
                self.news_feed.append(f"Retirements: {', '.join(p['name'] for p in retired[:3])}" + 
                                    ("..." if len(retired) > 3 else ""))
    
        # 1. Get ranking changes
        current_rankings = {p['id']: p['rank'] for p in self.players if not p.get('retired', False)}
        ranking_changes = {}
        if hasattr(self, 'old_rankings'):
            for player_id, current_rank in current_rankings.items():
                old_rank = self.old_rankings.get(player_id, 999)
                if old_rank != current_rank:
                    ranking_changes[player_id] = (old_rank, current_rank)
    
        # 2. Biggest progression/regression
        if ranking_changes:
            biggest_jump = max(ranking_changes.items(), key=lambda x: x[1][0] - x[1][1])
            biggest_drop = max(ranking_changes.items(), key=lambda x: x[1][1] - x[1][0])

            jumper = next(p for p in self.players if p['id'] == biggest_jump[0])
            dropper = next(p for p in self.players if p['id'] == biggest_drop[0])

            self.news_feed.append(
                f"Biggest progression: {jumper['name']} ({biggest_jump[1][0]}→{biggest_jump[1][1]})"
            )
            self.news_feed.append(
                f"Biggest regression: {dropper['name']} ({biggest_drop[1][0]}→{biggest_drop[1][1]})"
            )

        # 3. Top 20 changes
        top20_changes = [
            (p['name'], change[0], change[1]) 
            for p in self.players 
            if not p.get('retired', False) 
            and p['id'] in ranking_changes 
            and (change := ranking_changes[p['id']]) 
            and (change[1] <= 20 or change[0] <= 20)
        ]

        for name, old, new in top20_changes:
            if old > 20:  # New entry to top 20
                self.news_feed.append(f"New in top 20: {name} (entered at {new})")
            elif new > 20:  # Dropped out of top 20
                self.news_feed.append(f"Dropped from top 20: {name} (was {old})")
            else:  # Movement within top 20
                self.news_feed.append(f"Top 20 change: {name} ({old}→{new})")

        # 4. Last week's tournament winners
        last_week = self.current_week - 1 if self.current_week > 1 else 52
        last_year = self.current_year if self.current_week > 1 else self.current_year - 1

        for tournament in self.tournaments:
            if tournament['week'] == last_week and tournament.get('winner_id'):
                winner = next((p for p in self.players if p['id'] == tournament['winner_id']), None)
                if winner:
                    self.news_feed.append(
                        f"Tournament winner: {winner['name']} won {tournament['name']} ({tournament['category']})"
                    )