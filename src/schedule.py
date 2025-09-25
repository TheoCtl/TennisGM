import json
import random
import os
import copy
from math import log2, ceil
from datetime import datetime, timedelta
from collections import defaultdict
from sim.game_engine import GameEngine  # Import the Game Engine
from ranking import RankingSystem
from player_development import PlayerDevelopment
from newgen import NewGenGenerator
from records import RecordsManager

class TournamentScheduler:
    PRESTIGE_ORDER = [
        "Special",
        "Grand Slam",
        "Masters 1000",
        "ATP 500",
        "ATP 250",
        "Challenger 175",
        "Challenger 125",
        "Challenger 100",
        "Challenger 75",
        "Challenger 50",
        "ITF"
    ]
    
    @staticmethod
    def get_seeding_order(draw_size):
        """
        Standard tennis seeding positions for powers of 2.
        4  -> [1, 4, 2, 3]
        8  -> [1, 8, 4, 5, 2, 7, 3, 6]
        16 -> [1, 16, 8, 9, 4, 13, 5, 12, 2, 15, 7, 10, 3, 14, 6, 11]
        """
        if draw_size <= 1:
            return [1]
        order = [1, 2]
        while len(order) < draw_size:
            m = len(order) * 2
            reflected = [m + 1 - p for p in order]
            interleaved = []
            for a, b in zip(order, reflected):
                interleaved.extend([a, b])
            order = interleaved
        return order[:draw_size]
    
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
        self.world_crown = {
            'current_bracket': {},
            'current_year_teams': {},
            'match_results': {},
            'winners_history': [],
            'pending_matches': []
        }
        self.load_data(data_path, save_path)
        self.records = []
        self.records_manager = RecordsManager(self)
        self.records_manager.update_all_records()
        
        # Initialize World Crown if needed (for existing saves that haven't reached World Crown weeks yet)
        self.initialize_world_crown_if_needed()
        
        for player in self.players:
            if 'tournament_history' not in player:
                player['tournament_history'] = []
            if 'tournament_wins' not in player:
                player['tournament_wins'] = []
        for player in self.players + self.hall_of_fame:
            if 'w1' not in player:
                player['w1'] = 0
            if 'w16' not in player:
                player['w16'] = 0
        self._rebuild_ranking_history()  # FIX: call the method
        
        # Initialize ELO ratings for existing players if not already set
        for player in self.players:
            if 'elo_rating' not in player:
                self.ranking_system.initialize_elo_ratings(self.players)
                break
        
        self.ranking_system.update_combined_rankings(self.players, self.current_date)
        
    def save_game(self, save_path='data/save.json'):
        """Save all game data to a file"""
        game_data = {
            'current_year': self.current_year,
            'current_week': self.current_week,
            'current_date': self.current_date.isoformat(),
            'players': self.players,
            'tournaments': self.tournaments,
            'ranking_history': dict(self.ranking_system.ranking_history),
            'hall_of_fame': self.hall_of_fame,
            'records': self.records,
            'world_crown': self.world_crown
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
                self.records = data.get('records', [])
                
                for player in self.players:
                    if 'tournament_history' not in player:
                        player['tournament_history'] = []
                    if 'tournament_wins' not in player:
                        player['tournament_wins'] = []
                self.ranking_system.ranking_history = defaultdict(list)
                for player_id, entries in data.get('ranking_history', {}).items():
                    self.ranking_system.ranking_history[int(player_id)] = entries
                self.hall_of_fame = data.get('hall_of_fame', [])
                self.world_crown = data.get('world_crown', {
                    'current_bracket': {},
                    'current_year_teams': {},
                    'match_results': {},
                    'winners_history': [],
                    'pending_matches': []
                })
            print("Loaded saved game")
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            print (f"Error loading saved game: {str(e)}")
            try:
                with open(data_path) as f:
                    default_data = json.load(f)
                    self.players = default_data['players']
                    self.tournaments = default_data['tournaments']
                    self.current_year = 1
                    self.current_week = 1
                    self.current_date = datetime(2025, 1, 1)
                    self.ranking_system.ranking_history = defaultdict(list)
                    self.hall_of_fame = []
                    print("Loaded default data")
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error loading default data: {str(e)}. Creating minimal data.")
                self.players = []
                self.tournaments = []
                self.current_year = 1
                self.current_week = 1
                self.current_date = datetime(2025, 1, 1)
                self.hall_of_fame = []
        for player in self.players:
            if 'retired' not in player:
                player['retired'] = False
            if 'tournament_history' not in player:
                player['tournament_history'] = []
            if 'tournament_wins' not in player:
                player['tournament_wins'] = []
    
    def get_current_week_tournaments(self):
        return [t for t in self.tournaments if t['week'] == self.current_week]
    
    def advance_week(self):
        self.old_rankings = {p['id']: p['rank'] for p in self.players if not p.get('retired', False)}
        self.current_week += 1
        self.current_date += timedelta(days=7)
        for tournament in self.tournaments:
            if tournament['week'] == self.current_week - 1 and tournament.get('winner_id'):
                self._update_all_player_histories(tournament)
            if tournament['year'] < self.current_year and tournament['week'] == self.current_week:
                # Reset only if it's time for this tournament in the new year
                tournament['year'] = self.current_year
                tournament['winner_id'] = None
                tournament['participants'] = []
                tournament['bracket'] = []
                tournament['current_round'] = 0
                tournament['active_matches'] = []
        self._cleanup_old_tournament_history()
        if self.current_week > 52:
            self.current_week = 1
            self.current_year += 1
            self.current_year_retirees = self._process_retirements()
            retired_count = len(self.current_year_retirees)
            # Age up active players and update yearly ranking tracking
            for player in self.players:
                if 'age' in player and not player.get('retired', False):
                    player['age'] += 1
                    
                    # Update yearly ranking tracking
                    if 'year_start_rankings' not in player:
                        player['year_start_rankings'] = {}
                    
                    # Move current year to previous year and set new current year
                    if str(self.current_year - 1) in player['year_start_rankings']:
                        player['year_start_rankings'][str(self.current_year - 2)] = player['year_start_rankings'][str(self.current_year - 1)]
                    
                    player['year_start_rankings'][str(self.current_year - 1)] = player.get('rank', 999)

            # HARD CAP and 2x retirements rule
            target_max = 322
            slots = max(0, target_max - len(self.players))        # available slots to reach cap
            candidate_count = retired_count * 2                    # generate exactly 2x retirees

            if candidate_count > 0 and slots > 0:
                new_players = self.newgen_generator.generate_new_players(
                    self.current_year,
                    count=candidate_count,
                    existing_players=self.players
                )

                def calc_overall(p):
                    skills = p.get("skills", {})
                    if not skills:
                        return 0.0
                    return round(sum(skills.values()) / max(1, len(skills)), 2)

                def calc_surface_sum(p):
                    mods = p.get("surface_modifiers")
                    if isinstance(mods, dict) and mods:
                        return (10 * (round(sum(mods.values()), 3)))
                    return 40.0

                def calc_fut(p):
                    return (0.5*(round(calc_overall(p) + (50 * p.get("potential_factor", 1.0)) + calc_surface_sum(p), 1)))

                # Keep only the best up to the number of available slots
                scored = sorted(((p, calc_fut(p)) for p in new_players), key=lambda x: x[1], reverse=True)
                to_add = [p for p, _ in scored[:min(slots, candidate_count)]]
                for p in to_add:
                    p.setdefault('favorite', False)
                self.players.extend(to_add)
            # If no retirees or no slots, add nobody.

            self._reset_tournaments_for_new_year()
            self._rebuild_ranking_history()
        else:
            current_week_tournaments = [t for t in self.tournaments if t['week'] == self.current_week]
            if current_week_tournaments:
                self.assign_players_to_tournaments()
                for tournament in current_week_tournaments:
                    self.generate_bracket(tournament['id'])
        
        # Weekly decay removed - now balancing through halved ELO gains instead
        # self.ranking_system.apply_weekly_elo_decay(self.players)
        
        self.ranking_system.update_combined_rankings(self.players, self.current_date)
        for player in self.players:
            if not player.get('retired', False):
                if player.get('rank', 999) < player.get('highest_ranking', 999):
                    player['highest_ranking'] = player['rank']
                # Update highest ELO points (ELO rating + Championship points)
                current_elo_points = self.ranking_system.get_elo_points(player, self.current_date)
                if current_elo_points > player.get('highest_elo', 0):
                    player['highest_elo'] = current_elo_points
        PlayerDevelopment.seasonal_development(self)
        PlayerDevelopment.weekly_development(self)
        self.previous_records = copy.deepcopy(self.records)
        self.update_weeks_at_top()
        self.records_manager.update_mawn_last_week()
        self.records_manager.update_all_records()
        
        # Process World Crown matches for this week
        self.process_world_crown_week()
        
        self.generate_news_feed()
        return self.current_week
    
    def update_weeks_at_top(self):
        for player in self.players:
            if 'w1' not in player:
                player['w1'] = 0
            if 'w16' not in player:
                player['w16'] = 0
            if not player.get('retired', False):
                if player.get('rank', 999) == 1:
                    player['w1'] += 1
                if player.get('rank', 999) <= 10:
                    player['w16'] += 1
    
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
        Assign players to tournaments for the current week using probability-based selection.
        """
        current_tournaments = self.get_current_week_tournaments()
        available_players = [p for p in self.players if not p.get('injured', False) and not p.get('retired', False)]
        self.ranking_system.update_combined_rankings(self.players, self.current_date)

        # Initialize participants for all tournaments
        for tournament in current_tournaments:
            tournament['participants'] = []

        # Keep special tournament logic unchanged
        # Kings Cup logic
        kings_cup = [t for t in current_tournaments if t['name'] == "Kings Cup"]
        if kings_cup:
            gs_names = ["Winter Clash", "Fall Brawl", "Summer Battle", "Spring Break"]
            gs_winners = []
            for t in self.tournaments:
                if t['name'] in gs_names and t.get('winner_id'):
                    gs_winners.append(t['winner_id'])
                    break
            unique_winners = []
            for wid in gs_winners:
                if wid not in unique_winners:
                    unique_winners.append(wid)
                    
            if len(unique_winners) < 4:
                for t in self.tournaments:
                    if t['name'] == "Delta Finals" and t.get('winner_id'):
                        if t['winner_id'] not in unique_winners:
                            unique_winners.append(t['winner_id'])
                        break
            
            if len(unique_winners) < 4:
                available_players.sort(key=lambda x: x.get('rank', 999))
                for p in available_players:
                    if p['id'] not in unique_winners:
                        unique_winners.append(p['id'])
                    if len(unique_winners) == 4:
                        break
                        
            kings_cup[0]['participants'] = unique_winners
            return

        # Nextgen Finals logic
        junior_finals = [t for t in current_tournaments if t['name'] == "Nextgen Finals"]
        if junior_finals:
            def calc_overall(p):
                skills = p.get("skills", {})
                if not skills:
                    return 0.0
                return round(sum(skills.values()) / max(1, len(skills)), 2)

            def calc_surface_sum(p):
                mods = p.get("surface_modifiers")
                if isinstance(mods, dict) and mods:
                    return (10 * (round(sum(mods.values()), 3)))
                return 40.0

            def calc_fut(p):
                return (0.5 * (round(calc_overall(p) + (50 * p.get("potential_factor", 1.0)) + calc_surface_sum(p), 1)))

            u20 = [p for p in available_players if p.get('age', 99) < 20]
            ranked_by_fut = sorted(((p, calc_fut(p)) for p in u20), key=lambda x: x[1], reverse=True)
            junior_finals[0]['participants'] = [p['id'] for p, _ in ranked_by_fut[:8]]
            return

        # Delta Finals logic
        delta_finals = [t for t in current_tournaments if t['name'] == "Delta Finals"]
        if delta_finals:
            available_players.sort(key=lambda x: x.get('rank', 0))
            delta_finals[0]['participants'] = [p['id'] for p in available_players[:16]]
            return

        # New probability-based logic for regular tournaments
        def get_participation_chance(player_rank, category):
            """Get participation chance based on player rank and tournament category"""
            if category == "Grand Slam":
                return 0.99
            elif category == "Masters 1000":
                return 0.90 if player_rank <= 64 else 0.99
            elif category == "ATP 500":
                if player_rank <= 20:
                    return 0.66
                elif player_rank <= 50:
                    return 0.75
                elif player_rank <= 100:
                    return 0.85
                else:
                    return 0.99
            elif category == "ATP 250":
                if player_rank <= 20:
                    return 0.20
                elif player_rank <= 50:
                    return 0.50
                elif player_rank <= 100:
                    return 0.66
                elif player_rank <= 150:
                    return 0.80
                else:
                    return 0.99
            elif category == "Challenger 175":
                if player_rank <= 70:
                    return 0.0
                elif player_rank <= 100:
                    return 0.20
                elif player_rank <= 150:
                    return 0.75
                else:
                    return 0.99
            elif category == "Challenger 125":
                if player_rank <= 70:
                    return 0.0
                elif player_rank <= 100:
                    return 0.15
                elif player_rank <= 150:
                    return 0.70
                elif player_rank <= 200:
                    return 0.80
                else:
                    return 0.99
            elif category == "Challenger 100":
                if player_rank <= 70:
                    return 0.0
                elif player_rank <= 100:
                    return 0.10
                elif player_rank <= 150:
                    return 0.60
                elif player_rank <= 200:
                    return 0.70
                else:
                    return 0.99
            elif category == "Challenger 75":
                if player_rank <= 100:
                    return 0.0
                elif player_rank <= 150:
                    return 0.40
                elif player_rank <= 200:
                    return 0.66
                else:
                    return 0.99
            elif category == "Challenger 50":
                if player_rank <= 150:
                    return 0.0
                elif player_rank <= 200:
                    return 0.50
                else:
                    return 0.99
            elif category == "ITF":
                if player_rank <= 200:
                    return 0.0
                else:
                    return 0.33
            else:
                return 0.99  # Default for unknown categories

        # Sort tournaments by prestige order
        current_tournaments.sort(key=lambda t: self.PRESTIGE_ORDER.index(t['category']))
        
        # Create cumulative draw size list
        draw_sizes = [t['draw_size'] for t in current_tournaments]
        cumulative_draws = []
        total = 0
        for size in draw_sizes:
            total += size
            cumulative_draws.append(total)

        # Sort players by rank (best to worst)
        available_players.sort(key=lambda x: x.get('rank', 999))
        
        available_for_week = []
        
        # Go through each player and check tournament participation
        for i, player in enumerate(available_players):
            player_rank = player.get('rank', 999)
            current_tournament_idx = 0
            
            # Find which tournament we're currently filling
            for j, cumulative in enumerate(cumulative_draws):
                if len(available_for_week) < cumulative:
                    current_tournament_idx = j
                    break
            else:
                # All tournaments are full
                break
                
            current_tournament = current_tournaments[current_tournament_idx]
            category = current_tournament['category']
            
            # Safeguard: if remaining players equals remaining spots, automatically add player
            remaining_players = len(available_players) - i
            remaining_spots = cumulative_draws[-1] - len(available_for_week)
            
            if remaining_players <= remaining_spots:
                # Automatically add player to ensure tournaments are filled
                available_for_week.append(player)
            else:
                # Get participation chance and roll
                chance = get_participation_chance(player_rank, category)
                if random.random() < chance:
                    available_for_week.append(player)
                
            # Stop if all tournaments are full
            if len(available_for_week) >= cumulative_draws[-1]:
                break

        # Group tournaments by category for fair distribution
        tournaments_by_category = {}
        for i, tournament in enumerate(current_tournaments):
            category = tournament['category']
            if category not in tournaments_by_category:
                tournaments_by_category[category] = []
            tournaments_by_category[category].append((tournament, i))
        
        # Distribute players to tournaments, shuffling within same categories
        player_idx = 0
        for category in self.PRESTIGE_ORDER:
            if category not in tournaments_by_category:
                continue
                
            category_tournaments = tournaments_by_category[category]
            category_draw_size = sum(t[0]['draw_size'] for t in category_tournaments)
            
            # Get players for this category
            end_idx = min(player_idx + category_draw_size, len(available_for_week))
            category_players = available_for_week[player_idx:end_idx]
            
            # Shuffle players within this category to ensure fair distribution
            random.shuffle(category_players)
            
            # Distribute shuffled players to tournaments in this category
            shuffled_idx = 0
            for tournament, original_idx in category_tournaments:
                draw_size = tournament['draw_size']
                tournament_players = category_players[shuffled_idx:shuffled_idx + draw_size]
                tournament['participants'] = [p['id'] for p in tournament_players]
                shuffled_idx += len(tournament_players)
                
                # If we don't have enough players for this tournament, we're done
                if len(tournament_players) < draw_size:
                    return
                    
            player_idx = end_idx
            
            # If we've assigned all available players, we're done
            if player_idx >= len(available_for_week):
                break

    def generate_bracket(self, tournament_id):
        tournament = next(t for t in self.tournaments if t['id'] == tournament_id)

        # Ensure participants are assigned (handle empty lists too)
        if not tournament.get('participants'):
            self.assign_players_to_tournaments()
        participants = list(tournament.get('participants', []))
        draw_size = tournament['draw_size']

        # Trim or pad to draw size
        if len(participants) > draw_size:
            participants = sorted(
                participants,
                key=lambda pid: next((p['rank'] for p in self.players if p['id'] == pid), 999)
            )[:draw_size]
        while len(participants) < draw_size:
            participants.append(None)

        # Rank: best -> worst (None treated as worst)
        def rank_of(pid):
            if pid is None:
                return 10_000_000
            return next((p['rank'] for p in self.players if p['id'] == pid), 999)

        sorted_ids = sorted(participants, key=rank_of)  # best -> worst

        # Build pairs: best vs worst, 2nd best vs 2nd worst, ...
        pairs = []
        for i in range(draw_size // 2):
            p1 = sorted_ids[i]            # i-th best
            p2 = sorted_ids[-(i + 1)]     # i-th worst
            pairs.append((p1, p2))

        # Place pairs according to seeding order (pair i goes to match containing seed i+1)
        seeding_order = TournamentScheduler.get_seeding_order(draw_size)
        bracket_positions = [None] * draw_size
        for i, (p_top, p_bot) in enumerate(pairs):
            seed_pos_1based = seeding_order[i]            # where the i-th seed sits (1-based)
            pos = seed_pos_1based - 1                     # 0-based
            opp_pos = pos + 1 if (pos % 2 == 0) else pos - 1  # adjacent slot in same match
            bracket_positions[pos] = p_top
            bracket_positions[opp_pos] = p_bot

        # Build bracket rounds
        num_rounds = int(ceil(log2(draw_size)))
        tournament['bracket'] = [[] for _ in range(num_rounds)]

        # First round: adjacent positions form matches
        first_round = []
        for i in range(0, draw_size, 2):
            p1 = bracket_positions[i]
            p2 = bracket_positions[i + 1]
            first_round.append((p1, p2, None))

        tournament['bracket'][0] = first_round
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
        
        original_players = {}
        match_log = []  # FIX: always defined
        game_engine = None
        try:
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
                match_log = ["BYE - Player advances automatically"]
                self._update_player_tournament_history(tournament, player1_id, tournament['current_round'])
            else:
                # Fetch player data
                player1 = next(p for p in self.players if p['id'] == player1_id)
                player2 = next(p for p in self.players if p['id'] == player2_id)
                original_players = {
                    player1_id: player1.copy(),
                    player2_id: player2.copy()
                }

                sets_to_win = 3 if tournament.get('category') == "Grand Slam" or tournament.get('category') =="Special" else 2
                game_engine = GameEngine(player1, player2, tournament['surface'], sets_to_win=sets_to_win)
                # Store ball position events if in visualization mode
                point_events = []
                match_events = list(game_engine.simulate_match(visualize=True))
                match_log = game_engine.match_log
                
                # Extract point events with ball positions and find match winner
                match_winner = None
                if match_events:
                    for event in match_events:
                        if event['type'] == 'point':
                            point_events.append(event)
                        elif event['type'] == 'match_end':
                            match_winner = event['winner']
                    
                    # Set winner_id based on actual match winner
                    if match_winner:
                        winner_id = match_winner['id']
                    else:
                        # Fallback if no match_end event found
                        winner_id = player1['id'] if game_engine.sets['player1'] > game_engine.sets['player2'] else player2['id']
                else:
                    # Handle case with no events (quick match or error)
                    winner_id = player1['id'] if game_engine.sets['player1'] > game_engine.sets['player2'] else player2['id']
                final_score = game_engine.format_set_scores()

                loser_id = player2_id if winner_id == player1['id'] else player1_id
                self._update_player_tournament_history(tournament, loser_id, tournament['current_round'])
                
                # Update ELO ratings after the match
                result = 1 if winner_id == player1['id'] else 0
                self.ranking_system.update_elo_ratings(player1['id'], player2['id'], result, self.players)

            # Update the match with the winner and score
            tournament['active_matches'][target_match_idx] = (player1_id, player2_id, winner_id, final_score)
            tournament['bracket'][tournament['current_round']][target_match_idx] = (player1_id, player2_id, winner_id, final_score)

            # Check if all matches in the current round are complete
            if all(len(m) == 4 and m[2] is not None for m in tournament['active_matches']):
                self._prepare_next_round(tournament)

            return winner_id, match_log, point_events  # Return point events for visualization
        finally:
            # Restore original stats but preserve ELO rating changes
            for player_id, original_stats in original_players.items():
                player = next(p for p in self.players if p['id'] == player_id)
                # Save current ELO rating and highest ELO before restoring
                current_elo_rating = player.get('elo_rating')
                current_highest_elo = player.get('highest_elo')
                # Restore original stats
                player.update(original_stats)
                # Restore the updated ELO values
                if current_elo_rating is not None:
                    player['elo_rating'] = current_elo_rating
                if current_highest_elo is not None:
                    player['highest_elo'] = current_highest_elo
            
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
                'points': points,
                'surface': tournament.get('surface', 'neutral')
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
            winner_id = None
            for match in tournament['active_matches']:
                if len(match) > 2 and match[2] is not None:
                    winner_id = match[2]
                    break
            if winner_id:
                tournament['winner_id'] = winner_id
                if 'history' not in tournament:
                    tournament['history'] = []
                winner = next((p for p in self.players if p['id'] == winner_id), None)
                winner_name = winner['name'] if winner else "Unknown"
                tournament['history'].append({
                    'winner': winner_name,
                    'year': self.current_year
                    
                })
                if winner:
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
            if len(match) > 2 and match[2] is not None:  # Ensure the match has a winner
                winners.append(match[2])
                # Store the final score in the bracket for the current round
                tournament['bracket'][current_round][idx] = (
                    match[0], match[1], match[2], match[3] if len(match) > 3 else "N/A"
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
        
    def simulate_entire_tournament(self, tournament_id):
        """Simulate all remaining matches in a tournament automatically"""
        tournament = next(t for t in self.tournaments if t['id'] == tournament_id)

        # Ensure tournament is properly initialized
        if 'participants' not in tournament:
            self.assign_players_to_tournaments()
        if 'bracket' not in tournament or not tournament['bracket']:
            self.generate_bracket(tournament_id)

        while True:
            # Check if tournament is already complete
            if tournament.get('winner_id'):
                break
                
            current_round = tournament['current_round']

            # Safety check for round existence
            if current_round >= len(tournament['bracket']):
                break
                
            matches = tournament['active_matches']

            # Simulate all matches in current round
            for match_idx in range(len(matches)):
                # Skip already completed matches
                if len(matches[match_idx]) < 3 or matches[match_idx][2] is None:
                    self.simulate_through_match(tournament_id, match_idx)

            # Check if all matches in current round are complete
            if all(len(m) > 2 and m[2] is not None for m in matches):
                # If this was the final round, set the winner
                if current_round == len(tournament['bracket']) - 1:
                    if matches and matches[0][2]:
                        tournament['winner_id'] = matches[0][2]
                        winner = next((p for p in self.players if p['id'] == matches[0][2]), None)
                        if winner:
                            if 'tournament_wins' not in winner:
                                winner['tournament_wins'] = []
                            self._update_player_tournament_history(
                                tournament, 
                                matches[0][2], 
                                current_round
                            )
                    break
                else:
                    # Prepare next round
                    winners = [m[2] for m in matches if m[2] is not None]
                    next_round = current_round + 1

                    # Create matches for next round
                    next_round_matches = []
                    for i in range(0, len(winners), 2):
                        if i + 1 < len(winners):
                            next_round_matches.append((winners[i], winners[i+1], None))
                        else:
                            next_round_matches.append((winners[i], None, None))

                    # Update tournament state
                    if next_round >= len(tournament['bracket']):
                        tournament['bracket'].append(next_round_matches)
                    else:
                        tournament['bracket'][next_round] = next_round_matches

                    tournament['current_round'] = next_round
                    tournament['active_matches'] = next_round_matches
            else:
                # Shouldn't happen - all matches should be complete after simulation
                break
                
        return tournament.get('winner_id')
        
    def _process_retirements(self):
        """Handle player retirements at the end of the year"""
        retired_players = []
        retired_count = 0
    
        for player in self.players:
            if player.get('retired', False):
                continue
            
            age = player.get('age', 20)
            rank = player.get('rank', 20)
            # Calculate HOF points before adding to Hall of Fame
            hof_points = 0
            for win in player.get('tournament_wins', []):
                if win['category'] == 'Special':
                    hof_points += 50
                elif win['name'] == "ATP Finals":
                    hof_points += 30
                elif win['name'] == "Nextgen Finals":
                    hof_points += 5
                elif win['category'] == "Grand Slam":
                    hof_points += 40
                elif win['category'] == "Masters 1000":
                    hof_points += 20
                elif win['category'] == "ATP 500":
                    hof_points += 10
                elif win['category'] == "ATP 250":
                    hof_points += 5
                elif win['category'].startswith("Challenger"):
                    hof_points += 1
            player['hof_points'] = hof_points
        
            # Automatic retirement at 40+
            if age >= 40:
                player['retired'] = True
                retired_players.append(player['name'])
                retired_count += 1
                self._add_to_hall_of_fame(player)
                continue
            
            if age > 32 and rank > 200:
                player['retired'] = True
                retired_players.append(player['name'])
                retired_count += 1
                self._add_to_hall_of_fame(player)
                continue
            
            # Chance-based retirement for players 36-39
            if age >= 36:
                retirement_chance = (age - 35) * 0.2  # 20% at 36, 40% at 37, etc.
                if random.random() < retirement_chance:
                    player['retired'] = True
                    retired_players.append(player['name'])
                    retired_count += 1
                    self._add_to_hall_of_fame(player)
    
        # Remove retired players from self.players
        self.players = [p for p in self.players if not p.get('retired', False)]
    
        if retired_players:
            print(f"\nThe following players have retired: {', '.join(retired_players)}")
        return retired_players
    
    def _add_to_hall_of_fame(self, player):
        hof_entry = {
            'name' : player['name'],
            'tournament_wins' : player.get('tournament_wins', []).copy(),
            'highest_ranking': player.get('highest_ranking', 999),
            'hof_points': player.get('hof_points', 0),
            'mawn': player.get('mawn'),
            'w1': player.get('w1'),
            'w16': player.get('w16')
        }
        self.hall_of_fame.append(hof_entry)
        self.hall_of_fame = sorted(
            self.hall_of_fame,
            key=lambda x: (-x['hof_points'], len(x.get('tournament_wins', [])))
        )[:25]
    
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
        
        # Check if there's any news to report
        news_items = []
        
        # 1. Yearly recap (Week 1 only)
        if self.current_week == 1:
            yearly_news = self._generate_yearly_recap()
            news_items.extend(yearly_news)
        
        # 2. Player development weeks
        if self.current_week in [26, 52]:
            news_items.append({
                'type': 'development',
                'title': 'PLAYER DEVELOPMENT WEEK',
                'content': 'Players across the tour are working on their skills during this development period. Expect to see improvements in technique and fitness over the coming weeks.'
            })
        
        # 3. New players and retirements
        if self.current_week == 1:
            newgens = [p for p in self.players if p['age'] == 16]
            if newgens:
                # Templates for newgen announcements
                single_newgen_templates = [
                    "{name} has joined the professional tour at age 16, marking the beginning of what could be a promising career.",
                    "Young talent {name} makes their professional debut, entering the ATP tour with high expectations.",
                    "{name} steps into the professional arena at just 16 years old, ready to make their mark on tennis.",
                    "Rising star {name} officially turns professional, beginning their journey on the ATP circuit.",
                    "{name} launches their professional career, joining the tour as one of tennis's newest prospects."
                ]
                
                few_newgens_templates = [
                    "{names} have joined the professional tour, bringing fresh talent to the ATP circuit.",
                    "{names} make their professional debuts, adding exciting new prospects to the tour.",
                    "The ATP welcomes {names} as they begin their professional careers.",
                    "{names} enter the professional ranks, ready to challenge the established order.",
                    "Fresh faces {names} officially join the tour, marking the start of their professional journeys."
                ]
                
                many_newgens_templates = [
                    "{count} promising young players have joined the professional tour this year, including {names}.",
                    "The ATP tour gains {count} new talents this season, headlined by {names}.",
                    "{count} fresh prospects enter professional tennis, with {names} leading the new generation.",
                    "This year's rookie class features {count} players, notably {names}.",
                    "The professional tour welcomes {count} newcomers, including standouts {names}."
                ]
                
                if len(newgens) == 1:
                    template = random.choice(single_newgen_templates)
                    content = template.format(name=newgens[0]['name'])
                elif len(newgens) <= 3:
                    names = ', '.join(p['name'] for p in newgens[:-1]) + f" and {newgens[-1]['name']}"
                    template = random.choice(few_newgens_templates)
                    content = template.format(names=names)
                else:
                    names = f"{newgens[0]['name']}, {newgens[1]['name']}, and {newgens[2]['name']}"
                    template = random.choice(many_newgens_templates)
                    content = template.format(count=len(newgens), names=names)
                
                news_items.append({
                    'type': 'newgens',
                    'title': 'FRESH FACES ON TOUR',
                    'content': content
                })
        
        if self.current_week == 1 and hasattr(self, 'current_year_retirees'):
            # Only announce notable retirees (those in HOF or with significant achievements)
            hof_members = sorted(
                self.hall_of_fame,
                key=lambda x: (-x['hof_points'], len(x.get('tournament_wins', [])))
            )[:100]
            hof_names = set(p['name'] for p in hof_members)
            notable_retirees = [p for p in self.current_year_retirees if p in hof_names]
            
            if notable_retirees:
                # Templates for retirement announcements
                single_retirement_templates = [
                    "Tennis legend {name} has officially announced their retirement from professional tennis, ending a remarkable career that has earned them a place in the Hall of Fame.",
                    "The sport loses a true champion as {name} hangs up their racquet, concluding a distinguished career filled with memorable victories.",
                    "{name} calls time on their illustrious career, leaving behind a legacy that will inspire future generations.",
                    "After years of excellence, {name} steps away from professional tennis, cementing their status as one of the game's greats.",
                    "Hall of Famer {name} announces retirement, bringing the curtain down on a career that redefined tennis excellence."
                ]
                
                multiple_retirement_templates = [
                    "The tennis world bids farewell to {names}, who have all announced their retirement from professional tennis after distinguished careers.",
                    "An era comes to an end as {names} collectively retire, leaving behind legacies of championship excellence.",
                    "Tennis loses several icons as {names} step away from professional competition after remarkable careers.",
                    "The sport honors {names} as they transition into retirement, each having contributed immensely to tennis history.",
                    "Legendary careers conclude as {names} announce their retirement from the professional tour."
                ]
                
                if len(notable_retirees) == 1:
                    template = random.choice(single_retirement_templates)
                    content = template.format(name=notable_retirees[0])
                else:
                    names = ', '.join(notable_retirees[:-1]) + f" and {notable_retirees[-1]}"
                    template = random.choice(multiple_retirement_templates)
                    content = template.format(names=names)
                
                news_items.append({
                    'type': 'retirements',
                    'title': 'TENNIS LEGENDS RETIRE',
                    'content': content
                })
        
        # 4. Achievement milestones
        if hasattr(self, 'previous_records') and self.records != self.previous_records:
            achievement_news = self._generate_achievement_news()
            news_items.extend(achievement_news)
        
        # 5. Tournament results
        tournament_news = self._generate_tournament_news()
        news_items.extend(tournament_news)
        
        # 6. Ranking changes
        ranking_news = self._generate_ranking_news()
        news_items.extend(ranking_news)
        
        # 7. World Crown announcements
        world_crown_news = self._generate_world_crown_announcements()
        news_items.extend(world_crown_news)
        
        # Format the news feed
        if not news_items:
            self.news_feed = ["No significant tennis news this week."]
        else:
            self.news_feed.append("═══════════════════════════════════════════════════════════════════════════════")
            self.news_feed.append("                              ★ TENNIS WEEKLY ★                              ")
            self.news_feed.append(f"                          Year {self.current_year}, Week {self.current_week}")
            self.news_feed.append("═══════════════════════════════════════════════════════════════════════════════")
            self.news_feed.append("")
            
            for i, item in enumerate(news_items):
                # Add section header
                self.news_feed.append(f"▼ {item['title']}")
                self.news_feed.append("─" * (len(item['title']) + 2))
                
                # Add content with proper wrapping
                if isinstance(item['content'], list):
                    self.news_feed.extend(item['content'])
                else:
                    # Word wrap long content
                    words = item['content'].split()
                    lines = []
                    current_line = []
                    current_length = 0
                    
                    for word in words:
                        if current_length + len(word) + len(current_line) > 75:
                            if current_line:
                                lines.append(' '.join(current_line))
                                current_line = [word]
                                current_length = len(word)
                            else:
                                lines.append(word)
                        else:
                            current_line.append(word)
                            current_length += len(word)
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    self.news_feed.extend(lines)
                
                # Add spacing between sections (except for last item)
                if i < len(news_items) - 1:
                    self.news_feed.append("")
                    self.news_feed.append("")
            
            self.news_feed.append("")
            self.news_feed.append("═══════════════════════════════════════════════════════════════════════════════")

    def _generate_yearly_recap(self):
        """Generate yearly recap news for week 1"""
        recap_items = []
        
        # Best improved players
        improved_players = self._get_most_improved_players()
        if improved_players:
            content = []
            
            # Varied intro phrases for improvement stories
            improvement_intros = [
                "The biggest success stories of the past year:",
                "These players made remarkable strides in their rankings:",
                "Dramatic improvements highlighted last year's tour:",
                "The most inspiring ranking climbs of the year:",
                "These athletes transformed their careers with impressive gains:"
            ]
            content.append(random.choice(improvement_intros))
            
            # Varied templates for improvement descriptions
            improvement_templates = [
                "{name} (#{old_rank} → #{new_rank}, +{improvement} positions)",
                "{name} - Rose from #{old_rank} to #{new_rank} (+{improvement})",
                "{name}: #{old_rank} to #{new_rank} ({improvement} position climb)",
                "{name} jumped {improvement} spots from #{old_rank} to #{new_rank}",
                "{name} transformed from #{old_rank} to #{new_rank} (+{improvement})"
            ]
            
            for i, (player, old_rank, new_rank, improvement) in enumerate(improved_players[:5], 1):
                template = random.choice(improvement_templates)
                formatted = template.format(
                    name=player['name'], 
                    old_rank=old_rank, 
                    new_rank=new_rank, 
                    improvement=improvement
                )
                content.append(f"{i}. {formatted}")
            
            recap_items.append({
                'type': 'improved',
                'title': 'MOST IMPROVED PLAYERS',
                'content': content
            })
        
        # Most tournaments won last year
        tournament_winners = self._get_top_tournament_winners_last_year()
        if tournament_winners:
            content = []
            
            # Varied intro phrases for tournament winners
            winner_intros = [
                "Last year's most successful tournament champions:",
                "The tour's most prolific winners from the previous season:",
                "These players dominated the tournament circuit:",
                "The most consistent champions throughout the year:",
                "Last season's title-collecting superstars:"
            ]
            content.append(random.choice(winner_intros))
            
            # Varied templates for tournament wins
            winner_templates = [
                "{name} - {wins} {tournament_text}",
                "{name} captured {wins} {tournament_text}",
                "{name}: {wins} {tournament_text} claimed",
                "{name} secured {wins} championship {title_suffix}",
                "{name} dominated with {wins} {tournament_text}"
            ]
            
            for i, (player, wins) in enumerate(tournament_winners[:5], 1):
                tournament_text = "tournament" if wins == 1 else "tournaments"
                title_suffix = "title" if wins == 1 else "titles"
                
                template = random.choice(winner_templates)
                formatted = template.format(
                    name=player['name'], 
                    wins=wins, 
                    tournament_text=tournament_text,
                    title_suffix=title_suffix
                )
                content.append(f"{i}. {formatted}")
            
            recap_items.append({
                'type': 'winners',
                'title': 'TOP TOURNAMENT WINNERS',
                'content': content
            })
        
        return recap_items
    
    def _get_most_improved_players(self):
        """Get players with the biggest ranking improvements from last year"""
        improved = []
        last_year = str(self.current_year - 1)
        
        for player in self.players:
            if player.get('retired', False):
                continue
                
            year_rankings = player.get('year_start_rankings', {})
            if last_year in year_rankings:
                old_rank = year_rankings[last_year]
                new_rank = player.get('rank', 999)
                
                # Only count improvements (lower ranking number = better)
                if old_rank > new_rank and new_rank <= 200:  # Must be in top 200 now
                    improvement = old_rank - new_rank
                    improved.append((player, old_rank, new_rank, improvement))
        
        return sorted(improved, key=lambda x: x[3], reverse=True)
    
    def _get_top_tournament_winners_last_year(self):
        """Get players who won the most tournaments last year"""
        winner_counts = {}
        last_year = self.current_year - 1
        
        for player in self.players:
            if player.get('retired', False):
                continue
                
            wins_last_year = len([
                win for win in player.get('tournament_wins', [])
                if win.get('year') == last_year
            ])
            
            if wins_last_year > 0:
                winner_counts[player['id']] = (player, wins_last_year)
        
        return sorted(winner_counts.values(), key=lambda x: x[1], reverse=True)
    
    def _generate_achievement_news(self):
        """Generate news about achievement changes"""
        achievement_items = []
        
        # Templates for achievement announcements
        achievement_templates = [
            "{name} has entered the all-time top 10 for {title}, claiming the #{pos} position with their recent achievements.",
            "{name} breaks into the prestigious top 10 for {title}, securing #{pos} place in tennis history.",
            "{name} makes history by reaching #{pos} in the all-time {title} rankings.",
            "{name} achieves a remarkable milestone, entering the top 10 for {title} at #{pos}.",
            "{name} cements their legacy with a #{pos} ranking in the all-time {title} category.",
            "{name} joins tennis elite by claiming #{pos} in the historical {title} standings."
        ]
        
        for rec, prev in zip(self.records, self.previous_records):
            if rec.get("type") == prev.get("type") and rec.get("top10") != prev.get("top10"):
                title = rec.get('title', rec.get('type'))
                prev_names = [entry['name'] for entry in prev.get('top10', [])]
                curr_names = [entry['name'] for entry in rec.get('top10', [])]
                
                new_entries = [name for name in curr_names if name not in prev_names]
                
                if new_entries:
                    for name in new_entries:
                        pos = curr_names.index(name) + 1
                        template = random.choice(achievement_templates)
                        content = template.format(name=name, title=title.lower(), pos=pos)
                        
                        achievement_items.append({
                            'type': 'achievement',
                            'title': 'RECORD MILESTONE',
                            'content': content
                        })
        
        return achievement_items
    
    def _generate_tournament_news(self):
        """Generate news about recent tournament winners"""
        tournament_items = []
        
        last_week = self.current_week - 1 if self.current_week > 1 else 52
        
        # Get major tournament winners only (no Challengers or ITF)
        major_winners = []
        for tournament in self.tournaments:
            if (tournament['week'] == last_week and 
                not tournament['category'].startswith("Challenger") and 
                not tournament['category'].startswith("ITF") and 
                tournament.get('winner_id')):
                
                winner = next((p for p in self.players if p['id'] == tournament['winner_id']), None)
                if winner:
                    total_wins = len(winner.get('tournament_wins', []))
                    major_winners.append((winner, tournament, total_wins))
        
        if major_winners:
            content = []
            
            # Varied intro phrases
            intro_phrases = [
                "Last week's champions made their mark on the ATP circuit:",
                "The ATP tour witnessed impressive victories across multiple tournaments:",
                "Several players celebrated breakthrough moments and continued success:",
                "Championship glory was spread across the professional circuit:",
                "The tennis world saw commanding performances from these champions:"
            ]
            content.append(random.choice(intro_phrases))
            
            # Varied templates for tournament wins
            win_templates = [
                "captured", "claimed", "secured", "won", "triumphed at", "dominated", "conquered"
            ]
            
            surface_templates = [
                " on the {surface} courts",
                " across {surface} surfaces", 
                " on {surface}",
                " playing on {surface}"
            ]
            
            career_templates = [
                " This marks career title #{total} for the {nationality} star.",
                " The {nationality} player now has {total} professional titles to their name.",
                " Career victory #{total} goes to the talented {nationality} athlete.",
                " This brings the {nationality} champion's title count to {total}.",
                " The {nationality} sensation adds title #{total} to their impressive resume."
            ]
            
            for winner, tournament, total_wins in major_winners:
                win_verb = random.choice(win_templates)
                
                surface_text = ""
                if tournament['surface'] != 'hard':
                    surface_template = random.choice(surface_templates)
                    surface_text = surface_template.format(surface=tournament['surface'])
                
                career_template = random.choice(career_templates)
                career_text = career_template.format(
                    total=total_wins, 
                    nationality=winner.get('nationality', 'international')
                )
                
                content.append(f"• {winner['name']} {win_verb} the {tournament['name']} ({tournament['category']}){surface_text}.{career_text}")
            
            tournament_items.append({
                'type': 'tournaments',
                'title': 'TOURNAMENT CHAMPIONS',
                'content': content
            })
        
        return tournament_items
    
    def _generate_ranking_news(self):
        """Generate news about significant ranking changes"""
        ranking_items = []
        
        current_rankings = {p['id']: p['rank'] for p in self.players if not p.get('retired', False)}
        ranking_changes = {}
        
        if hasattr(self, 'old_rankings'):
            for player_id, current_rank in current_rankings.items():
                old_rank = self.old_rankings.get(player_id, 999)
                if old_rank != current_rank:
                    ranking_changes[player_id] = (old_rank, current_rank)
        
        # Focus on top 20 movements and new top 10 entries
        significant_changes = []
        for p in self.players:
            if (not p.get('retired', False) and 
                p['id'] in ranking_changes):
                
                old_rank, new_rank = ranking_changes[p['id']]
                
                # New top 10 entry
                if new_rank <= 10 and old_rank > 10:
                    significant_changes.append((p['name'], old_rank, new_rank, 'top10_entry'))
                # Dropped from top 10
                elif old_rank <= 10 and new_rank > 10:
                    significant_changes.append((p['name'], old_rank, new_rank, 'top10_exit'))
                # Significant movement in top 20
                elif new_rank <= 20 and abs(old_rank - new_rank) >= 5:
                    change_type = 'big_rise' if new_rank < old_rank else 'big_drop'
                    significant_changes.append((p['name'], old_rank, new_rank, change_type))
        
        if significant_changes:
            content = []
            
            # Varied intro phrases
            intro_phrases = [
                "Notable movements in the ATP Rankings:",
                "The latest rankings reveal significant changes:",
                "Several players experienced dramatic ranking shifts:",
                "This week's rankings brought major surprises:",
                "Significant changes have shaken up the ATP hierarchy:"
            ]
            content.append(random.choice(intro_phrases))
            
            # Sort by importance: top 10 entries, then big rises, then others
            priority = {'top10_entry': 0, 'big_rise': 1, 'big_drop': 2, 'top10_exit': 3}
            significant_changes.sort(key=lambda x: (priority.get(x[3], 4), x[2]))
            
            # Templates for different types of ranking changes
            top10_entry_templates = [
                "breaks into the top 10 for the first time, rising to #{new_rank}",
                "achieves a career-high ranking of #{new_rank}, entering the elite top 10",
                "makes their top 10 debut at #{new_rank}",
                "cracks the top 10 barrier, climbing to #{new_rank}",
                "reaches #{new_rank}, marking their first appearance in the top 10"
            ]
            
            top10_exit_templates = [
                "drops out of the top 10, falling to #{new_rank}",
                "slides from the elite group, now ranked #{new_rank}",
                "loses their top 10 status, dropping to #{new_rank}",
                "falls from grace to #{new_rank}",
                "exits the top 10 after dropping to #{new_rank}"
            ]
            
            big_rise_templates = [
                "surges {movement} positions to #{new_rank}",
                "climbs {movement} spots to reach #{new_rank}",
                "rockets up {movement} places to #{new_rank}",
                "soars {movement} positions to #{new_rank}",
                "jumps an impressive {movement} spots to #{new_rank}"
            ]
            
            big_drop_templates = [
                "falls {movement} positions to #{new_rank}",
                "drops {movement} spots to #{new_rank}",
                "slides {movement} places down to #{new_rank}",
                "tumbles {movement} positions to #{new_rank}",
                "plummets {movement} spots to #{new_rank}"
            ]
            
            for name, old_rank, new_rank, change_type in significant_changes:
                if change_type == 'top10_entry':
                    template = random.choice(top10_entry_templates)
                    content.append(f"• {name} {template.format(new_rank=new_rank)}")
                elif change_type == 'top10_exit':
                    template = random.choice(top10_exit_templates)
                    content.append(f"• {name} {template.format(new_rank=new_rank)}")
                elif change_type == 'big_rise':
                    movement = old_rank - new_rank
                    template = random.choice(big_rise_templates)
                    content.append(f"• {name} {template.format(movement=movement, new_rank=new_rank)}")
                elif change_type == 'big_drop':
                    movement = new_rank - old_rank
                    template = random.choice(big_drop_templates)
                    content.append(f"• {name} {template.format(movement=movement, new_rank=new_rank)}")
            
            ranking_items.append({
                'type': 'rankings',
                'title': 'RANKING MOVEMENTS',
                'content': content
            })
        
        return ranking_items

    def _generate_world_crown_announcements(self):
        """Generate World Crown tournament news for various weeks"""
        world_crown_items = []
        
        # Check for completed World Crown matches this week
        if hasattr(self, 'world_crown_week_news') and self.world_crown_week_news.get('week') == self.current_week:
            matches_info = self.world_crown_week_news['matches']
            content = []
            
            # Generate results announcement
            if self.current_week == 11:
                content.append("The World Crown tournament has begun! The first set of quarterfinal matches have concluded:")
            elif self.current_week == 13:
                content.append("The World Crown quarterfinals are complete! The semifinalists have been determined:")
            elif self.current_week == 18:
                content.append("The first World Crown semifinal has been decided:")
            elif self.current_week == 20:
                content.append("The World Crown finalists are set after the conclusion of the semifinals:")
            elif self.current_week == 47:
                content.append("The World Crown tournament has concluded with a thrilling final:")
            
            # Add results for each completed match
            for round_type, tie_id, tie_data in matches_info:
                if tie_data.get('winner') and tie_data.get('matches'):
                    team1 = tie_data['team1']
                    team2 = tie_data['team2']
                    winner = tie_data['winner']
                    score = f"{tie_data.get('team1_wins', 0)}-{tie_data.get('team2_wins', 0)}"
                    
                    content.append(f"• {winner} defeated {team2 if winner == team1 else team1} ({score})")
                    
                    # Add some match highlights
                    if len(tie_data['matches']) >= 3:
                        key_matches = tie_data['matches'][:2]  # First two matches as highlights
                        for match in key_matches:
                            content.append(f"  - {match['winner']} def. {match['player1'] if match['winner'] == match['player2'] else match['player2']} ({match['score']})")
            
            content.append("Check the World Crown section for full match details!")
            
            world_crown_items.append({
                'type': 'world_crown_results',
                'title': 'WORLD CROWN RESULTS',
                'content': content
            })
        
        # World Crown week announcements (11, 13, 18, 20, 47)
        elif self.current_week in [11, 13, 18, 20, 47]:
            # Check if there are matches this week
            matches = self.get_world_crown_matches_for_week(self.current_week)
            if matches:
                content = []
                
                # Week-specific announcements
                if self.current_week == 11:
                    round_name = "Quarterfinals (First Half)"
                    intro_templates = [
                        "The World Crown tournament begins this week with the first set of quarterfinal matches.",
                        "International tennis takes center stage as the World Crown quarterfinals commence.",
                        "Eight nations compete for glory as the World Crown tournament kicks off with quarterfinal action.",
                        "The prestigious World Crown tournament opens with exciting quarterfinal matchups."
                    ]
                elif self.current_week == 13:
                    round_name = "Quarterfinals (Second Half)"
                    intro_templates = [
                        "The World Crown quarterfinals conclude this week, determining the final four nations.",
                        "Semifinal spots are on the line as the remaining World Crown quarterfinals take place.",
                        "The World Crown tournament continues with the final quarterfinal matchups.",
                        "National pride is at stake in this week's concluding quarterfinal ties."
                    ]
                elif self.current_week == 18:
                    round_name = "Semifinals (First Match)"
                    intro_templates = [
                        "The World Crown semifinals begin, with four nations vying for a place in the final.",
                        "Semifinal action highlights the World Crown tournament as nations battle for the final.",
                        "The World Crown reaches the semifinal stage with elite international competition.",
                        "Four countries remain in contention as the World Crown semifinals commence."
                    ]
                elif self.current_week == 20:
                    round_name = "Semifinals (Second Match)"
                    intro_templates = [
                        "The World Crown finalists will be determined in this week's semifinal conclusion.",
                        "A place in the World Crown final is at stake in the remaining semifinal match.",
                        "The World Crown semifinals conclude, setting up the championship showdown.",
                        "Two nations will advance to the World Crown final after this week's semifinal action."
                    ]
                elif self.current_week == 47:
                    round_name = "Final"
                    intro_templates = [
                        "The World Crown final takes place this week, crowning this year's champion nation.",
                        "International tennis reaches its pinnacle with the World Crown championship match.",
                        "The World Crown tournament concludes with the highly anticipated final showdown.",
                        "Two nations compete for ultimate glory in the World Crown final."
                    ]
                
                content.append(random.choice(intro_templates))
                
                # Add match details
                match_details = []
                for round_type, tie_id, tie_data in matches:
                    team1 = tie_data['team1']
                    team2 = tie_data['team2']
                    if team1 and team2:
                        match_details.append(f"{team1} vs {team2}")
                    elif not team1 and not team2:
                        match_details.append("TBD vs TBD")
                    else:
                        # One team is determined, the other is TBD
                        determined_team = team1 or team2
                        match_details.append(f"{determined_team} vs TBD")
                
                if match_details:
                    if len(match_details) == 1:
                        content.append(f"This week's match: {match_details[0]}")
                    else:
                        content.append(f"This week's matches: {' and '.join(match_details)}")
                
                content.append("Check the World Crown section to follow the action and simulate matches!")
                
                world_crown_items.append({
                    'type': 'world_crown_week',
                    'title': f'WORLD CROWN - {round_name.upper()}',
                    'content': content
                })
        
        # World Crown results announcement (Week 48 - after final)
        if self.current_week == 48:
            # Check if there's a completed World Crown tournament from this year
            if (self.world_crown.get('winners_history') and 
                any(w['year'] == self.current_year for w in self.world_crown['winners_history'])):
                
                # Find this year's winner
                this_year_winner = next((w for w in self.world_crown['winners_history'] 
                                       if w['year'] == self.current_year), None)
                
                if this_year_winner:
                    content = []
                    
                    # Varied intro phrases for World Crown results
                    intro_templates = [
                        f"The {self.current_year} World Crown concluded with {this_year_winner['winner']} claiming the prestigious international trophy.",
                        f"{this_year_winner['winner']} emerged victorious in this year's World Crown competition, representing their nation with distinction.",
                        f"After intense competition across multiple rounds, {this_year_winner['winner']} captured the World Crown championship.",
                        f"The World Crown trophy returns to {this_year_winner['winner']} following their commanding performance in the final.",
                        f"{this_year_winner['winner']} celebrates World Crown glory, adding international prestige to their tennis achievements."
                    ]
                    
                    content.append(random.choice(intro_templates))
                    
                    # Add details about the tournament format
                    format_descriptions = [
                        "The tournament featured the world's top 5 players from each of the 8 participating nations, competing in a knockout format throughout the year.",
                        "Eight countries battled through quarterfinals, semifinals, and the final, with each tie decided by best-of-5 individual matches.",
                        "The competition showcased international tennis talent across multiple stages, with matches spread throughout the tennis season.",
                        "National pride was on display as the best players from each country represented their homeland in this unique team competition."
                    ]
                    
                    content.append(random.choice(format_descriptions))
                    content.append(f"Final result: {this_year_winner['final_score']}")
                    
                    world_crown_items.append({
                        'type': 'world_crown_champion',
                        'title': 'WORLD CROWN CHAMPIONS CROWNED',
                        'content': content
                    })
        
        return world_crown_items

    def simulate_current_round(self, tournament_id):
        """
        Simulate all matches in the current round of the tournament.
        """
        tournament = next(t for t in self.tournaments if t['id'] == tournament_id)
        matches = tournament.get('active_matches', [])
        for match_idx, match in enumerate(matches):
            # Only simulate matches that are not yet completed
            if len(match) < 3 or match[2] is None:
                self.simulate_through_match(tournament_id, match_idx)

    # World Crown Tournament Methods
    def initialize_world_crown_if_needed(self):
        """Initialize World Crown for current year if we haven't reached the first World Crown week yet"""
        # Check if World Crown is already initialized for current year
        if self.world_crown.get('current_year_teams') and self.world_crown.get('current_bracket'):
            return  # Already initialized
        
        # Only initialize if we haven't passed the first World Crown week (Week 11)
        if self.current_week < 11:
            self.initialize_world_crown_year()
    
    def initialize_world_crown_year(self):
        """Initialize World Crown tournament for the current year"""
        # Allow initialization any time before the first matches (week 11)
        # The original condition was too restrictive
            
        # Get the 8 nationalities
        nationalities = ["Arcton", "Halcyon", "Rin", "Hethrion", "Haran", "Loknig", "Jeonguk", "Bleak"]
        
        # Select top 5 players for each nationality based on ranking
        teams = {}
        for nationality in nationalities:
            national_players = [p for p in self.players if p.get('nationality') == nationality and not p.get('retired', False)]
            # Sort by current ranking (lower rank number = better)
            national_players.sort(key=lambda x: x.get('rank', 999999))
            teams[nationality] = national_players[:5]  # Top 5 players
        
        # Create bracket structure (quarterfinals)
        # Pair countries: Arcton vs Halcyon, Rin vs Hethrion, Haran vs Loknig, Jeonguk vs Bleak
        bracket = {
            'quarterfinals': {
                'qf1': {'team1': 'Arcton', 'team2': 'Halcyon', 'week': 11, 'winner': None, 'matches': []},
                'qf2': {'team1': 'Rin', 'team2': 'Hethrion', 'week': 11, 'winner': None, 'matches': []},
                'qf3': {'team1': 'Haran', 'team2': 'Loknig', 'week': 13, 'winner': None, 'matches': []},
                'qf4': {'team1': 'Jeonguk', 'team2': 'Bleak', 'week': 13, 'winner': None, 'matches': []}
            },
            'semifinals': {
                'sf1': {'team1': None, 'team2': None, 'week': 18, 'winner': None, 'matches': []},
                'sf2': {'team1': None, 'team2': None, 'week': 20, 'winner': None, 'matches': []}
            },
            'final': {
                'final': {'team1': None, 'team2': None, 'week': 47, 'winner': None, 'matches': []}
            }
        }
        
        self.world_crown = {
            'current_bracket': bracket,
            'current_year_teams': teams,
            'match_results': {},
            'winners_history': self.world_crown.get('winners_history', []),
            'pending_matches': []
        }

    def get_world_crown_matches_for_week(self, week):
        """Get World Crown matches scheduled for the given week"""
        matches = []
        bracket = self.world_crown.get('current_bracket', {})
        
        # Check quarterfinals
        for qf_id, qf_data in bracket.get('quarterfinals', {}).items():
            if qf_data['week'] == week and qf_data['winner'] is None:
                matches.append(('quarterfinals', qf_id, qf_data))
        
        # Check semifinals 
        for sf_id, sf_data in bracket.get('semifinals', {}).items():
            if sf_data['week'] == week:
                matches.append(('semifinals', sf_id, sf_data))
        
        # Check final
        final_data = bracket.get('final', {}).get('final')
        if final_data and final_data['week'] == week:
            matches.append(('final', 'final', final_data))
        
        return matches

    def simulate_world_crown_tie(self, round_type, tie_id):
        """Simulate a World Crown tie (5 matches between two countries)"""
        bracket = self.world_crown['current_bracket']
        tie_data = bracket[round_type][tie_id]
        
        team1_name = tie_data['team1']
        team2_name = tie_data['team2']
        team1_players = self.world_crown['current_year_teams'][team1_name]
        team2_players = self.world_crown['current_year_teams'][team2_name]
        
        team1_wins = 0
        team2_wins = 0
        matches_played = []
        
        # Play 5 matches (best players face each other)
        for i in range(5):
            if i < len(team1_players) and i < len(team2_players):
                p1 = team1_players[i]
                p2 = team2_players[i]
                
                # Simulate match using game engine - neutral conditions (no surface advantages)
                sets_to_win = 2  # World Crown uses best of 3 sets for more upsets
                # Create copies without surface modifiers for neutral play
                p1_neutral = p1.copy()
                p2_neutral = p2.copy()
                # Remove surface advantages for fair play
                if 'surface_modifiers' in p1_neutral:
                    del p1_neutral['surface_modifiers']
                if 'surface_modifiers' in p2_neutral:
                    del p2_neutral['surface_modifiers']
                if 'favorite_surface' in p1_neutral:
                    del p1_neutral['favorite_surface']
                if 'favorite_surface' in p2_neutral:
                    del p2_neutral['favorite_surface']
                    
                game_engine = GameEngine(p1_neutral, p2_neutral, 'hard', sets_to_win=sets_to_win)  
                match_winner = game_engine.simulate_match()
                final_score = game_engine.format_set_scores()
                
                result = {
                    'winner_id': match_winner['id'],
                    'score': final_score
                }
                
                matches_played.append({
                    'player1': p1['name'],
                    'player2': p2['name'],
                    'winner': p1['name'] if result['winner_id'] == p1['id'] else p2['name'],
                    'score': result['score']
                })
                
                if result['winner_id'] == p1['id']:
                    team1_wins += 1
                else:
                    team2_wins += 1
        
        # Determine tie winner (first to win 3 matches)
        tie_winner = team1_name if team1_wins >= 3 else team2_name
        
        # Update bracket
        tie_data['winner'] = tie_winner
        tie_data['matches'] = matches_played
        tie_data['team1_wins'] = team1_wins
        tie_data['team2_wins'] = team2_wins
        
        # Advance winner to next round
        if round_type == 'quarterfinals':
            if tie_id in ['qf1', 'qf2']:
                sf_slot = 'sf1'
                if bracket['semifinals']['sf1']['team1'] is None:
                    bracket['semifinals']['sf1']['team1'] = tie_winner
                else:
                    bracket['semifinals']['sf1']['team2'] = tie_winner
            else:  # qf3 or qf4
                sf_slot = 'sf2'
                if bracket['semifinals']['sf2']['team1'] is None:
                    bracket['semifinals']['sf2']['team1'] = tie_winner
                else:
                    bracket['semifinals']['sf2']['team2'] = tie_winner
        elif round_type == 'semifinals':
            if bracket['final']['final']['team1'] is None:
                bracket['final']['final']['team1'] = tie_winner
            else:
                bracket['final']['final']['team2'] = tie_winner
        elif round_type == 'final':
            # Tournament complete - add to winners history
            self.world_crown['winners_history'].append({
                'year': self.current_year,
                'winner': tie_winner,
                'final_score': f"{team1_wins}-{team2_wins}"
            })
    
    def process_world_crown_week(self):
        """Process World Crown events for current week"""
        if self.current_week == 1:
            self.initialize_world_crown_year()
        
        # Get matches for this week
        matches_for_week = self.get_world_crown_matches_for_week(self.current_week)
        
        if matches_for_week:
            # Store news about this week's matches before simulation
            self.world_crown_week_news = {
                'week': self.current_week,
                'matches': matches_for_week.copy()
            }
        
        # Simulate each tie
        for round_type, tie_id, tie_data in matches_for_week:
            self.simulate_world_crown_tie(round_type, tie_id)