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
        self.load_data(data_path, save_path)
        self.records = []
        self.records_manager = RecordsManager(self)
        self.records_manager.update_all_records()
        
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
            'hall_of_fame': self.hall_of_fame,
            'records': self.records
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
            for player in self.players:
                if 'age' in player and not player.get('retired', False):
                    player['age'] += 1
            new_player_count = retired_count * 2
            while (len(self.players) + new_player_count) < 300 :
                new_player_count += 1
            new_players = self.newgen_generator.generate_new_players(self.current_year, count=new_player_count, existing_players=self.players)
            def calc_overall(p):
                skills = p.get("skills", {})
                if not skills:
                    return 0.0
                return round(sum(skills.values()) / max(1, len(skills)), 2)

            def calc_surface_sum(p):
                mods = p.get("surface_modifiers")
                if isinstance(mods, dict) and mods:
                    return (10 * (round(sum(mods.values()), 3)))
                # Fallback if missing: neutral 1.0 each
                return 40.0

            def calc_fut(p):
                return (0.5*(round(calc_overall(p) + (50 * p.get("potential_factor", 1.0)) + calc_surface_sum(p), 1)))
            
            new_players = sorted(((p, calc_fut(p)) for p in new_players), key=lambda x: x[1], reverse=True)
            best_new_players = new_players[:retired_count]
            self.players.extend(best_new_players)
            self._reset_tournaments_for_new_year()
            self._rebuild_ranking_history()
        else:
            current_week_tournaments = [t for t in self.tournaments if t['week'] == self.current_week]
            if current_week_tournaments:
                self.assign_players_to_tournaments()
                for tournament in current_week_tournaments:
                    self.generate_bracket(tournament['id'])
        self.ranking_system.update_player_ranks(self.players, self.current_date)
        for player in self.players:
            if not player.get('retired', False):
                if player.get('rank', 999) < player.get('highest_ranking', 999):
                    player['highest_ranking'] = player['rank']
        PlayerDevelopment.seasonal_development(self)
        self.previous_records = copy.deepcopy(self.records)
        self.update_weeks_at_top()
        self.records_manager.update_mawn_last_week()
        self.records_manager.update_all_records()
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
        Assign players to tournaments for the current week.
        Players are distributed across tournaments based on prestige order, and each player can only play in one tournament per week.
        """
        current_tournaments = self.get_current_week_tournaments()
        available_players = [p for p in self.players if not p.get('injured', False) and not p.get('retired', False)]
        available_for_week = []
        self.ranking_system.update_player_ranks(self.players, self.current_date)

        # Initialize participants for all tournaments
        for tournament in current_tournaments:
            tournament['participants'] = []  # Ensure the 'participants' key exists

        # Calculate total spots available in tournaments
        total_spots = sum(t['draw_size'] for t in current_tournaments)

        # NEW: Pre-fill ITF tournaments with random players ranked > 200
        itf_tournaments = [t for t in current_tournaments if t.get('category') == "ITF"]
        if itf_tournaments:
            eligible_itf = [p for p in available_players if p.get('rank', 999) > 200]
            random.shuffle(eligible_itf)
            total_itf_spots = sum(t['draw_size'] for t in itf_tournaments)
            itf_selected = eligible_itf[:total_itf_spots]

            # Assign selected players to ITF tournaments (fill in order)
            idx = 0
            for t in itf_tournaments:
                need = t['draw_size']
                chosen = itf_selected[idx: idx + need]
                t['participants'] = [p['id'] for p in chosen]
                idx += need

            # Remove selected ITF players from the pool so they won't be assigned elsewhere
            selected_ids = set(p['id'] for p in itf_selected)
            available_players = [p for p in available_players if p['id'] not in selected_ids]

        # Prevent >200 from entering non-ITF tournaments
        available_players = [p for p in available_players if p.get('rank', 999) <= 200]

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
                    
            available_for_week = [p for p in self.players if p['id'] in unique_winners]
        else:            
            # Nextgen Finals logic
            junior_finals = [t for t in current_tournaments if t['name'] == "Nextgen Finals"]
            if junior_finals:
                # Sort by best players under 20yo
                available_players.sort(key=lambda p: (p.get('rank', 999), p.get('age', 99)))
                under20 = []
                for player in available_players:
                    if player['age'] <= 20:
                        under20.append(player)
                available_for_week = under20[:8]
            else:
                # ATP Finals logic
                atp_finals = [t for t in current_tournaments if t['name'] == "Delta Finals"]
                if atp_finals:
                    available_players.sort(key=lambda x: x.get('rank', 0))
                    available_for_week.extend(available_players[:16])
                else:
                    # Grand Slam logic
                    grandslam_tournament = [t for t in current_tournaments if t['category'] == "Grand Slam"]
                    if grandslam_tournament:
                        available_players.sort(key=lambda x: x.get('rank', 0))
                        available_for_week.extend(available_players[:128])
                    else:
                        # Masters logic
                        masters_tournaments = [t for t in current_tournaments if t['category'] == "Masters 1000"]
                        if masters_tournaments:
                            available_players.sort(key=lambda x: x.get('rank', 999))
                            masters_draw = sum(t['draw_size'] for t in masters_tournaments)
                            initial_pool = available_players[:masters_draw]
                            kept = []
                            dropped = []
                            dropouts_count = 0
                            for p in initial_pool:
                                if random.random() < 0.10:
                                    dropouts_count += 1
                                    print(f"player {p} dropped")
                                    dropped.append(p)
                                else:
                                    kept.append(p)
                            
                            # Backfill with next-best players outside the initial pool
                            replacements = []
                            for p in available_players[masters_draw:]:
                                if p not in kept:
                                    if p not in dropped:
                                        replacements.append(p)
                                        if len(replacements) == dropouts_count:
                                            break
                                    
                            masters_pool = kept + replacements
                            # If still short (not enough replacements), keep pulling the next-best
                            if len(masters_pool) < masters_draw:
                                for p in available_players[masters_draw + len(replacements):]:
                                    if p not in masters_pool:
                                        masters_pool.append(p)
                                    if len(masters_pool) == masters_draw:
                                        break

                            # Remaining spots this week (for non-Masters events)
                            spots_left = max(0, total_spots - len(masters_pool))

                            # Fill the rest with next-best players not already in masters_pool
                            rest_candidates = [p for p in available_players if p not in masters_pool and p not in dropped]
                            if spots_left > 0:
                                rest = rest_candidates[:spots_left]
                            else:
                                rest = []

                            available_for_week = masters_pool + rest
                            # Final order not critical, but keep sorted for clarity
                            available_for_week.sort(key=lambda x: x.get('rank', 0), reverse=False)
                        else:
                            # Challenger logic
                            if all(t['category'].startswith("Challenger") for t in current_tournaments):
                                available_players.sort(key=lambda x: x.get('rank', 0), reverse=True)
                                available_for_week = available_players[:sum(t['draw_size'] for t in current_tournaments)]
                                available_for_week.sort(key=lambda x: x.get('rank', 0), reverse=False)
                            else:
                                # Basic logic
                                if len(available_players) > total_spots:
                                    num_to_skip = len(available_players) - total_spots
                                    skipped_players = random.sample(available_players, num_to_skip)
                                    available_for_week = [p for p in available_players if p not in skipped_players]
                                    available_for_week.sort(key=lambda x: x.get('rank', 0), reverse=False)
                                else:
                                    available_for_week = available_players
                                    available_for_week.sort(key=lambda x: x.get('rank', 0), reverse=False)


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
            placed = False
            # Shuffle tournaments for each player to randomize their assignment
            for category in self.PRESTIGE_ORDER:
                if category not in tournaments_by_category:
                    continue

                random.shuffle(tournaments_by_category[category])  # Shuffle tournaments in this category

                for tournament in tournaments_by_category[category]:
                    # Block top-200 from ITF
                    if tournament['category'] == "ITF" and player.get('rank', 999) <= 200:
                        continue
                    # Block >200 from any non-ITF
                    if tournament['category'] != "ITF" and player.get('rank', 999) > 200:
                        continue

                    if len(tournament['participants']) < tournament['draw_size']:
                        tournament['participants'].append(player['id'])
                        placed = True
                        break  # placed in a tournament within this category

                if placed:
                    break  # stop scanning categories for this player

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
                self._update_player_tournament_history(tournament, player1_id, tournament['current_round'])
            else:
                # Fetch player data
                player1 = next(p for p in self.players if p['id'] == player1_id)
                player2 = next(p for p in self.players if p['id'] == player2_id)
                original_players = {
                    player1_id: player1.copy(),
                    player2_id: player2.copy()
                }

                # Simulate the match using the Game Engine
                sets_to_win = 3 if tournament.get('category') == "Grand Slam" or tournament.get('category') =="Special" else 2
                game_engine = GameEngine(player1, player2, tournament['surface'], sets_to_win=sets_to_win)
                match_winner = game_engine.simulate_match()

                # Determine the winner ID
                winner_id = match_winner['id']

                # Store the final score for this match
                final_score = game_engine.format_set_scores()

                loser_id = player2_id if winner_id == player1['id'] else player1_id
                self._update_player_tournament_history(tournament, loser_id, tournament['current_round'])

            # Update the match with the winner and score
            tournament['active_matches'][target_match_idx] = (player1_id, player2_id, winner_id, final_score)
            tournament['bracket'][tournament['current_round']][target_match_idx] = (player1_id, player2_id, winner_id, final_score)

            # Check if all matches in the current round are complete
            if all(len(m) == 4 and m[2] is not None for m in tournament['active_matches']):
                self._prepare_next_round(tournament)

            return winner_id, game_engine.match_log
        finally:
            for player_id, original_stats in original_players.items():
                player = next(p for p in self.players if p['id'] == player_id)
                player.update(original_stats)
            
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
        self.news_feed.append("┌─── NEWS FEED ───┘")
        self.news_feed.append("│")
        
        # 1. Progressions/regressions weeks
        if self.current_week in [26, 52]:
            self.news_feed.append("├─ Player development week! ─┤")
            self.news_feed.append("│")

        # 2. Newgens and retirements (only when they happen)
        if self.current_week == 1:
            newgens = [p for p in self.players if p['age'] == 16]
            if newgens:
                self.news_feed.append(f"├─ New players joined the tour ─┤")
                self.news_feed.append(f"│ {', '.join(p['name'] for p in newgens)}")
                self.news_feed.append("│")
        if self.current_week == 1 and hasattr(self, 'current_year_retirees'):
            # Only announce if the player is in the top 100 HOF
            hof_members = sorted(
                self.hall_of_fame,
                key=lambda x: (-x['hof_points'], len(x.get('tournament_wins', [])))
            )[:100]
            hof_names = set(p['name'] for p in hof_members)
            hof_retirees = [p for p in self.current_year_retirees if p in hof_names]
            if hof_retirees:
                self.news_feed.append(f"├─ Hall of Fame entries ─┤")
                self.news_feed.append(f"│ {', '.join(hof_retirees)}")
                self.news_feed.append("│")
                
        # 3. Top 10 Achievements changes
        if hasattr(self, 'previous_records'):
            if self.records != self.previous_records:
                self.news_feed.append(f"├─ Achievements ─┤")
            for rec, prev in zip(self.records, self.previous_records):
                if rec.get("type") == prev.get("type") and rec.get("top10") != prev.get("top10"):
                    title = rec.get('title', rec.get('type'))
                    prev_names = [entry['name'] for entry in prev.get('top10', [])]
                    curr_names = [entry['name'] for entry in rec.get('top10', [])]

                    # New entries
                    a = 0
                    new_entries = [name for name in curr_names if name not in prev_names]
                    for name in new_entries:
                        a = 1
                        pos = curr_names.index(name) + 1
                        self.news_feed.append(f"│ {name} entered the Top 10 for {title} at n°{pos}")

                    # Position changes for players still in top 10
                    for name in set(curr_names) & set(prev_names):
                        old_pos = prev_names.index(name)
                        new_pos = curr_names.index(name)
                        if old_pos > new_pos:
                            direction = "up"
                            self.news_feed.append(
                                f"│ {name} moved {direction} in the Top 10 for {title}: {old_pos+1} → {new_pos+1}"
                            )
                    if a == 1:
                        self.news_feed.append("│")
                    else:
                        if old_pos > new_pos:
                            self.news_feed.append("│")
            self.news_feed.append("│")
        
        # 4. Last week's tournament winners with total career wins
        last_week = self.current_week - 1 if self.current_week > 1 else 52
        last_year = self.current_year if self.current_week > 1 else self.current_year - 1
    
        last_week_winners = []
        for tournament in self.tournaments:
            if tournament['week'] == last_week and tournament['category'].startswith("Challenger") == False and tournament['category'].startswith("ITF") == False and tournament.get('winner_id'):
                winner = next((p for p in self.players if p['id'] == tournament['winner_id']), None)
                if winner:
                    total_wins = len(winner.get('tournament_wins', []))
                    last_week_winners.append((winner, tournament, total_wins))

        if last_week_winners:
            self.news_feed.append(f"├─ Last Week ATP Winners ─┤")
            for winner, tournament, total_wins in last_week_winners:
                self.news_feed.append(
                    f"│ {winner['name']} won {tournament['name']} ({tournament['category']}, {tournament['surface']}) - Career win n°{total_wins}"
                )
        self.news_feed.append("│")
    
        # 5. Get ranking changes
        current_rankings = {p['id']: p['rank'] for p in self.players if not p.get('retired', False)}
        ranking_changes = {}
        if hasattr(self, 'old_rankings'):
            for player_id, current_rank in current_rankings.items():
                old_rank = self.old_rankings.get(player_id, 999)
                if old_rank != current_rank:
                    ranking_changes[player_id] = (old_rank, current_rank)

        top10_changes = [
            (p['name'], change[0], change[1]) 
            for p in self.players 
            if not p.get('retired', False) 
            and p['id'] in ranking_changes 
            and (change := ranking_changes[p['id']]) 
            and (change[1] <= 10 or change[0] <= 10)
        ]
        
        current_top10 = [(name, old, new) for name, old, new in top10_changes if new <= 10]
        dropped_out = [(name, old, new) for name, old, new in top10_changes if new > 10]
        
        current_top10.sort(key=lambda x: x[2])
        dropped_out.sort(key=lambda x: x[1])
        
        if top10_changes:
            self.news_feed.append(f"├─ Top 10 Changes ─┤")
            for name, old, new in current_top10:
                self.news_feed.append(f"│ {name} ({old} -> {new})")
            for name, old, new in dropped_out:
                self.news_feed.append(f"│ Dropped from top 10: {name} (was {old})")
        self.news_feed.append("└──────────────────────────────────────────────────────────────────────────────")

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