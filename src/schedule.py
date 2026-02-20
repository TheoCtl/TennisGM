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
        "ITF",
        "Juniors"
    ]
    
    @staticmethod
    def get_seeding_order(draw_size):
        """
        Standard professional tennis seeding positions for powers of 2.
        Returns a list where result[i] is the 1-based bracket position for seed i+1.

        Ensures proper separation:
        - Seeds 1 and 2 in opposite halves (meet only in Final)
        - Seeds 3 and 4 split across halves (3 with 2, 4 with 1 — meet 1/2 in SF)
        - Seeds 5-8 one per quarter, etc.

        4   -> [1, 4, 3, 2]         → SF: 1v4, 2v3
        8   -> [1, 8, 5, 4, 3, 6, 7, 2]  → QF: 1v8, 4v5, 3v6, 2v7
        16  -> [1, 16, 9, 8, 5, 12, 13, 4, 3, 14, 11, 6, 7, 10, 15, 2]
        """
        if draw_size <= 1:
            return [1]

        # positions[i] = 0-based bracket position for seed (i+1)
        positions = [None] * draw_size
        positions[0] = 0                  # Seed 1 at top
        positions[1] = draw_size - 1      # Seed 2 at bottom

        placed = [1, 2]
        group_size = draw_size

        while len(placed) < draw_size:
            group_size //= 2
            new_sum = len(placed) * 2 + 1  # paired seeds sum to this
            new_seeds = list(range(len(placed) + 1, len(placed) * 2 + 1))

            for s in placed:
                opponent = new_sum - s
                s_pos = positions[s - 1]
                s_group = s_pos // group_size
                s_pos_in_group = s_pos % group_size
                # Mirror within the same group
                opp_pos = s_group * group_size + (group_size - 1 - s_pos_in_group)
                positions[opponent - 1] = opp_pos

            placed.extend(new_seeds)

        return [p + 1 for p in positions]  # convert to 1-based
    
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
        self.ranking_system.update_all_junior_rankings(self.players)

        # Generate initial news feed so there's content on game start
        self.generate_news_feed()
        
    def save_game(self, save_path='data/save.json'):
        """Save all game data to a file"""
        game_data = {
            'current_year': self.current_year,
            'current_week': self.current_week,
            'current_date': self.current_date.isoformat(),
            'players': self.players,
            'tournaments': self.tournaments,
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
                    # Initialize required player stats if missing
                    if 'tournament_history' not in player:
                        player['tournament_history'] = []
                    if 'tournament_wins' not in player:
                        player['tournament_wins'] = []
                    if 'matches_played' not in player:
                        # Calculate matches_played from tournament_history
                        player['matches_played'] = len(player['tournament_history'])
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

            # MIGRATION: Ensure dropshot/volley skills and tendencies exist
            skills = player.setdefault('skills', {})
            if 'dropshot' not in skills:
                skills['dropshot'] = random.randint(25, 55)
            if 'volley' not in skills:
                skills['volley'] = random.randint(25, 55)
            # Tendencies: cross, straight, dropshot, volley
            if not all(k in player for k in ('cross_tend', 'straight_tend', 'dropshot_tend', 'volley_tend')):
                dropshot_tend = random.randint(0, 10)
                volley_tend = random.randint(0, 10)
                straight_tend = random.randint(40, 60)
                cross_tend = 100 - (dropshot_tend + volley_tend + straight_tend)
                if cross_tend < 10:
                    diff = 10 - cross_tend
                    if straight_tend - diff >= 40:
                        straight_tend -= diff
                        cross_tend = 10
                    else:
                        cross_tend = 10
                        straight_tend = max(40, 100 - (dropshot_tend + volley_tend + cross_tend))
                player['cross_tend'] = cross_tend
                player['straight_tend'] = straight_tend
                player['dropshot_tend'] = dropshot_tend
                player['volley_tend'] = volley_tend
    
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

            # GOAL 300
            target_max = 300
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
                        return (5 * (round(sum(mods.values()), 3)))
                    return 40.0

                def calc_fut(p):
                    return (0.5*(round(calc_overall(p) + (22.5 * p.get("potential_factor", 1.0)) + calc_surface_sum(p), 1)))

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
        self.ranking_system.update_all_junior_rankings(self.players)
        for player in self.players:
            if not player.get('retired', False):
                if player.get('rank', 999) < player.get('highest_ranking', 999):
                    player['highest_ranking'] = player['rank']
                # Update highest ELO points (ELO rating + Championship points)
                current_elo_points = self.ranking_system.get_elo_points(player, self.current_date)
                if current_elo_points > player.get('highest_elo', 0):
                    player['highest_elo'] = current_elo_points
        # Snapshot skills before development so news can report improvements
        self._pre_dev_skills = {
            p['id']: {k: v for k, v in p.get('skills', {}).items()}
            for p in self.players if not p.get('retired', False)
        }
        PlayerDevelopment.seasonal_development(self)
        PlayerDevelopment.weekly_development(self)
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
            gs_names = ["WINTER SPLIT", "AUTUMN SPLIT", "SUMMER SPLIT", "SPRING SPLIT"]
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
                    if t['name'] == "Final Masters" and t.get('winner_id'):
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
                    return (5 * (round(sum(mods.values()), 3)))
                return 40.0

            def calc_fut(p):
                return (0.5*(round(calc_overall(p) + (22.5 * p.get("potential_factor", 1.0)) + calc_surface_sum(p), 1)))

            u20 = [p for p in available_players if p.get('age', 99) < 20]
            
            # Get full FUT ranking and top 4 by junior_ranking
            ranked_by_fut = sorted(((p, calc_fut(p)) for p in u20), key=lambda x: x[1], reverse=True)
            top_fut_players = [p['id'] for p, _ in ranked_by_fut[:4]]
            
            ranked_by_jr = sorted(((p, p.get('junior_ranking', 0)) for p in u20), key=lambda x: x[1], reverse=True)
            top_jr_players = [p['id'] for p, _ in ranked_by_jr[:4] if p.get('junior_ranking', 0) > 0]
            
            # Start with top 4 FUT, then add top 4 junior_ranking (skip duplicates)
            participants = list(top_fut_players)
            for pid in top_jr_players:
                if pid not in participants:
                    participants.append(pid)
            
            # Fill remaining spots from next best FUT players until we have 8
            fut_idx = 4
            while len(participants) < 8 and fut_idx < len(ranked_by_fut):
                candidate_id = ranked_by_fut[fut_idx][0]['id']
                if candidate_id not in participants:
                    participants.append(candidate_id)
                fut_idx += 1
            
            junior_finals[0]['participants'] = participants[:8]
            return

        # Final Masters logic
        delta_finals = [t for t in current_tournaments if t['name'] == "Final Masters"]
        if delta_finals:
            available_players.sort(key=lambda x: x.get('rank', 0))
            delta_finals[0]['participants'] = [p['id'] for p in available_players[:16]]
            return

        # Junior tournaments logic - players aged 16-19 ranked outside top 250
        juniors = [t for t in current_tournaments if t['category'] == "Juniors"]
        junior_player_ids = set()
        if juniors:
            # Filter eligible junior players: aged 16-19 and ranked outside top 250
            eligible_juniors = [
                p for p in available_players 
                if 16 <= p.get('age', 99) <= 19 and p.get('rank', 999) > 250
            ]
            
            # Randomly select up to 16 eligible players for each junior tournament
            for tournament in juniors:
                if len(eligible_juniors) >= 16:
                    # Randomly select 16 from eligible pool
                    selected = random.sample(eligible_juniors, 16)
                    tournament['participants'] = [p['id'] for p in selected]
                    junior_player_ids.update(p['id'] for p in selected)
                    # Remove selected players from eligible pool for other junior tournaments
                    eligible_juniors = [p for p in eligible_juniors if p not in selected]
                else:
                    # If not enough players, assign all eligible players
                    tournament['participants'] = [p['id'] for p in eligible_juniors]
                    junior_player_ids.update(p['id'] for p in eligible_juniors)
                    eligible_juniors = []

        # Exclude junior participants and junior tournaments from the regular assignment flow
        if junior_player_ids:
            available_players = [p for p in available_players if p['id'] not in junior_player_ids]
        current_tournaments = [t for t in current_tournaments if t['category'] != "Juniors"]

        if not current_tournaments:
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
                    return 0.4
                elif player_rank <= 50:
                    return 0.6
                elif player_rank <= 100:
                    return 0.85
                else:
                    return 0.99
            elif category == "ATP 250":
                if player_rank <= 20:
                    return 0.2
                elif player_rank <= 50:
                    return 0.4
                elif player_rank <= 100:
                    return 0.6
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
        
        # Define premium tournament categories that get ranking-based seeding
        PREMIUM_CATEGORIES = ["Special", "Grand Slam", "Masters 1000", "ATP 500", "ATP 250"]
        
        # Distribute players to tournaments, using ranking seeding for premium tournaments
        player_idx = 0
        for category in self.PRESTIGE_ORDER:
            if category not in tournaments_by_category:
                continue
                
            category_tournaments = tournaments_by_category[category]
            category_draw_size = sum(t[0]['draw_size'] for t in category_tournaments)
            
            # Get players for this category
            end_idx = min(player_idx + category_draw_size, len(available_for_week))
            category_players = available_for_week[player_idx:end_idx]
            
            # If there are multiple tournaments in this category, shuffle to randomly distribute players across them
            # Otherwise, keep ranking order for single premium tournaments (for better seeding)
            if len(category_tournaments) > 1 or category not in PREMIUM_CATEGORIES:
                random.shuffle(category_players)
            
            # Distribute players to tournaments in this category
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
        
        # If there's only one player, automatically declare them the winner
        if len(participants) == 1:
            winner_id = participants[0]
            tournament['winner_id'] = winner_id
            tournament['bracket'] = [[(winner_id, None, winner_id, "BYE")]]
            tournament['current_round'] = 0
            tournament['active_matches'] = [(winner_id, None, winner_id, "BYE")]
            self._update_player_tournament_history(tournament, winner_id, 0)
            # Add tournament win record
            winner = next((p for p in self.players if p['id'] == winner_id), None)
            if winner:
                if 'tournament_wins' not in winner:
                    winner['tournament_wins'] = []
                winner['tournament_wins'].append({
                    'name': tournament['name'],
                    'category': tournament['category'],
                    'year': self.current_year
                })
            return

        # Trim or pad to draw size
        if len(participants) > draw_size:
            participants = sorted(
                participants,
                key=lambda pid: next((p['rank'] for p in self.players if p['id'] == pid), 999)
            )[:draw_size]
        while len(participants) < draw_size:
            participants.append(None)

        # Define premium tournament categories that get ranking-based seeding
        PREMIUM_CATEGORIES = ["Special", "Grand Slam", "Masters 1000", "ATP 500", "ATP 250"]
        use_ranking_seeding = tournament['category'] in PREMIUM_CATEGORIES
        
        # Rank: best -> worst (None treated as worst)
        def rank_of(pid):
            if pid is None:
                return 10_000_000
            return next((p['rank'] for p in self.players if p['id'] == pid), 999)

        if use_ranking_seeding:
            # Premium tournaments: use ranking-based seeding (top half vs randomized bottom half)
            sorted_ids = sorted(participants, key=rank_of)  # best -> worst

            half_draw = draw_size // 2
            top_half = sorted_ids[:half_draw]  # Top seeds (ranked 1 to half_draw)
            bottom_half = sorted_ids[half_draw:]  # Bottom half players
            
            # Randomize the bottom half for more interesting matchups
            random.shuffle(bottom_half)
            
            # Build pairs: top seed vs random bottom half player
            pairs = []
            for i in range(half_draw):
                p_top = top_half[i]           # i-th best seeded player
                p_bottom = bottom_half[i]     # randomly assigned bottom half player
                pairs.append((p_top, p_bottom))

            # Place pairs according to seeding order (pair i goes to match containing seed i+1)
            seeding_order = TournamentScheduler.get_seeding_order(draw_size)
            bracket_positions = [None] * draw_size
            for i, (p_top, p_bot) in enumerate(pairs):
                seed_pos_1based = seeding_order[i]            # where the i-th seed sits (1-based)
                pos = seed_pos_1based - 1                     # 0-based
                opp_pos = pos + 1 if (pos % 2 == 0) else pos - 1  # adjacent slot in same match
                bracket_positions[pos] = p_top
                bracket_positions[opp_pos] = p_bot
        else:
            # Challenger/ITF tournaments: use random seeding (shuffle all participants)
            random.shuffle(participants)
            bracket_positions = participants

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
            point_events = []  # Initialize point_events list
            match_log = []  # Initialize match_log list

            # Handle byes
            if player1_id is None and player2_id is None:
                # BYE vs BYE case - the next round should also get a BYE
                winner_id = None
                final_score = "BYE"
                match_log = ["BYE vs BYE - No players advance, next round gets BYE"]
            elif player1_id is None:
                # BYE vs Player case
                winner_id = player2_id
                final_score = "BYE"
                match_log = ["BYE - Player advances automatically with a default win"]
                self._update_player_tournament_history(tournament, player2_id, tournament['current_round'])
            elif player2_id is None:
                # Player vs BYE case
                winner_id = player1_id
                final_score = "BYE"
                match_log = ["BYE - Player advances automatically with a default win"]
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

            # Update matches_played for both players right when we record the match result
            if player1_id is not None:
                player1 = next(p for p in self.players if p['id'] == player1_id)
                player1['matches_played'] = player1.get('matches_played', 0) + 1
            if player2_id is not None:
                player2 = next(p for p in self.players if p['id'] == player2_id)
                player2['matches_played'] = player2.get('matches_played', 0) + 1

            # Check if all matches in the current round are complete
            if all(len(m) == 4 and m[2] is not None for m in tournament['active_matches']):
                self._prepare_next_round(tournament)

            return winner_id, match_log, point_events  # Return point events for visualization
        finally:
            # Restore original stats but preserve ELO rating changes
            for player_id, original_stats in original_players.items():
                player = next(p for p in self.players if p['id'] == player_id)
                # Save current values that should persist across the temporary simulation
                current_elo_rating = player.get('elo_rating')
                current_highest_elo = player.get('highest_elo')
                current_matches_played = player.get('matches_played', 0)

                # Restore original stats (these were the pre-simulation snapshot)
                player.update(original_stats)

                # Restore the updated values we want to keep (ELOs and matches_played)
                if current_elo_rating is not None:
                    player['elo_rating'] = current_elo_rating
                if current_highest_elo is not None:
                    player['highest_elo'] = current_highest_elo
                # Persist matches_played so the increment we applied when writing the match isn't lost
                player['matches_played'] = current_matches_played
            
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

                # Persist matches_played for both players when a result is written
                p1_id, p2_id = match[0], match[1]
                if p1_id is not None:
                    p1 = next((p for p in self.players if p['id'] == p1_id), None)
                    if p1 is not None:
                        p1['matches_played'] = p1.get('matches_played', 0) + 1
                if p2_id is not None:
                    p2 = next((p for p in self.players if p['id'] == p2_id), None)
                    if p2 is not None:
                        p2['matches_played'] = p2.get('matches_played', 0) + 1

                # Update both active_matches and the bracket so the saved structure contains the score
                tournament['active_matches'][match_index] = tuple(match)
                # Ensure bracket exists and update it as well
                if 'bracket' in tournament and 0 <= tournament.get('current_round', 0) < len(tournament['bracket']):
                    try:
                        tournament['bracket'][tournament['current_round']][match_index] = tuple(match)
                    except Exception:
                        # If bracket structure isn't aligned, ignore and rely on active_matches
                        pass
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
            if len(match) > 2:  # Match has been processed
                if match[0] is None and match[1] is None:
                    # This was a BYE vs BYE match, next round gets a BYE
                    # For display purposes, mark match[0] as winner to show in bold
                    if len(match) <= 2:
                        tournament['bracket'][current_round][idx] = (None, None, None, "BYE")
                    winners.append(None)
                elif match[2] is not None:  # Regular match with a winner
                    winners.append(match[2])
                # Store the final score in the bracket
                tournament['bracket'][current_round][idx] = (
                    match[0], match[1], match[2], match[3] if len(match) > 3 else "N/A"
                )

        # Create next round matches
        next_round_matches = []
        for i in range(0, len(winners), 2):
            if i + 1 < len(winners):
                # If either winner is None (from BYE vs BYE), the next match gets a BYE
                if winners[i] is None or winners[i + 1] is None:
                    next_round_matches.append((None, None, None))
                else:
                    next_round_matches.append((winners[i], winners[i + 1], None))
            else:
                # Last match in an odd-numbered round
                if winners[i] is None:
                    next_round_matches.append((None, None, None))
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
                if win['name'] == "Kings Cup":
                    hof_points += 50
                elif win['name'] == "Final Masters":
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
            
            if age >= 28 and rank > 150:
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
            'highest_elo': player.get('highest_elo', 999),
            'hof_points': player.get('hof_points', 0),
            'mawn': player.get('mawn'),
            'w1': player.get('w1'),
            'w16': player.get('w16')
        }
        self.hall_of_fame.append(hof_entry)
        self.hall_of_fame = sorted(
            self.hall_of_fame,
            key=lambda x: (-x['hof_points'], len(x.get('tournament_wins', [])))
        )[:50]
    
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

        # 6. Tournament Showcase (upcoming week preview)
        showcase_news = self._generate_tournament_showcase()
        news_items.extend(showcase_news)

        # 7. Tweet-style color news
        tweet_news = self._generate_tweet_news()
        news_items.extend(tweet_news)

        # Store structured news items (formatting is handled by the UI)
        self.news_feed = news_items

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
                "{name} (#{old_rank} → #{new_rank}, +{improvement})"
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
        last_year = str(self.current_year - 2)
        
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
        """Generate news about recent tournament winners with contextual info"""
        tournament_items = []

        last_week = self.current_week - 1 if self.current_week > 1 else 52

        for tournament in self.tournaments:
            if (tournament['week'] == last_week and
                not tournament['category'].startswith("Challenger") and
                not tournament['category'].startswith("ITF") and
                not tournament['category'] == "Juniors" and
                tournament.get('winner_id')):

                winner = next((p for p in self.players if p['id'] == tournament['winner_id']), None)
                if not winner:
                    continue

                wins = winner.get('tournament_wins', [])
                total_wins = len(wins)
                category = tournament['category']

                # Build contextual flavor instead of mentioning nationality
                context_line = self._get_win_context(winner, tournament, wins, total_wins)

                win_verbs = ["captured", "claimed", "secured", "won", "triumphed at", "conquered"]
                verb = random.choice(win_verbs)

                headline = f"{winner['name']} {verb} the {tournament['name']} ({category})."
                content = f"{headline} {context_line}"

                tournament_items.append({
                    'type': 'tournaments',
                    'title': f"\U0001F3C6 {tournament['name'].upper()}",
                    'content': content
                })

        return tournament_items

    def _get_win_context(self, winner, tournament, wins, total_wins):
        """Generate contextual information about a tournament win instead of nationality."""
        category = tournament['category']

        is_first_title = total_wins == 1

        # Count wins by category
        gs_wins = [w for w in wins if w['category'] == 'Grand Slam']
        m1000_wins = [w for w in wins if w['category'] == 'Masters 1000']

        is_first_gs = category == 'Grand Slam' and len(gs_wins) == 1
        is_first_m1000 = category == 'Masters 1000' and len(m1000_wins) == 1

        # Is this the biggest win of their career?
        prestige_index = self.PRESTIGE_ORDER.index(category) if category in self.PRESTIGE_ORDER else 99
        previous_wins = wins[:-1] if total_wins > 1 else []
        prev_best = min(
            (self.PRESTIGE_ORDER.index(w['category'])
             for w in previous_wins if w['category'] in self.PRESTIGE_ORDER),
            default=99
        )
        is_biggest_win = prestige_index < prev_best and total_wins > 1

        # Is defending champion?
        is_defending = any(
            w['name'] == tournament['name'] and w['year'] == self.current_year - 1
            for w in previous_wins
        )

        is_young = winner.get('age', 30) < 20

        # Priority-ordered context selection
        if is_first_title:
            return random.choice([
                "It's the first professional title of his career!",
                "A breakthrough moment \u2014 his first ever title on the professional tour!",
                "He lifts his maiden trophy in what could be the start of something special.",
            ])

        if is_first_gs:
            return random.choice([
                "It's his first Grand Slam title \u2014 a career-defining moment!",
                "He finally breaks through at Grand Slam level!",
                "A landmark achievement \u2014 Grand Slam champion for the first time!",
            ])

        if category == 'Grand Slam' and len(gs_wins) > 1:
            count = len(gs_wins)
            ordinal = f"{count}{'nd' if count == 2 else 'rd' if count == 3 else 'th'}"
            return random.choice([
                f"That's Grand Slam title #{count} for the champion.",
                f"He adds a {ordinal} Grand Slam to his collection.",
                f"Grand Slam #{count} \u2014 cementing his place among the greats.",
            ])

        if is_defending:
            return random.choice([
                "He successfully defends his title from last year.",
                "Back-to-back champion! He retains his crown.",
                "The defending champion proves his dominance once more.",
            ])

        if is_biggest_win:
            return random.choice([
                "It's the biggest tournament win of his career so far.",
                "A new career milestone \u2014 his most prestigious title to date.",
                "He reaches new heights with the biggest title of his career.",
            ])

        if is_first_m1000:
            return random.choice([
                "It's his first Masters 1000 title \u2014 a major step forward.",
                "He breaks through at Masters level for the first time.",
                "A first Masters 1000 crown \u2014 a sign of things to come.",
            ])

        if is_young:
            return random.choice([
                f"At just {winner['age']}, he's already collecting titles at this level.",
                f"Only {winner['age']} years old and already a champion here.",
                f"Remarkable maturity from the {winner['age']}-year-old.",
            ])

        # Default: career title count
        return random.choice([
            f"That's career title #{total_wins} for him.",
            f"Title #{total_wins} goes on the resume.",
            f"He now has {total_wins} professional titles to his name.",
        ])

    def _generate_tournament_showcase(self):
        """Generate a preview/showcase for the most prestigious upcoming tournament this week."""
        items = []

        # Find the most prestigious tournament happening THIS week (current_week)
        current_tournaments = [
            t for t in self.tournaments
            if t['week'] == self.current_week
            and not t['category'].startswith("ITF")
            and t['category'] != "Juniors"
        ]

        if not current_tournaments:
            return items

        # Pick the most prestigious one
        def prestige_score(t):
            try:
                return len(self.PRESTIGE_ORDER) - self.PRESTIGE_ORDER.index(t['category'])
            except ValueError:
                return 0

        best_tournament = max(current_tournaments, key=prestige_score)
        cat = best_tournament['category']

        # Skip challengers — not exciting enough for a showcase
        if cat.startswith("Challenger"):
            return items

        name = best_tournament['name']
        surface = best_tournament.get('surface', 'hard')
        draw_size = best_tournament.get('draw_size', 32)
        history = best_tournament.get('history', [])

        # ── City lore generation (deterministic from tournament name) ──
        city_name = self._extract_city_name(name)
        city_lore = self._generate_city_lore(city_name, surface, cat, name)

        # ── Last winner ──
        last_winner_str = None
        if history:
            last_entry = history[-1]
            last_winner_name = last_entry.get('winner', 'Unknown')
            last_year = last_entry.get('year', '?')
            last_winner_str = f"Defending champion: {last_winner_name} ({last_year})."

        # ── All-time most successful player at this tournament ──
        dynasty_str = None
        if history:
            from collections import Counter
            winner_counts = Counter(h['winner'] for h in history)
            most_wins_name, most_wins_count = winner_counts.most_common(1)[0]
            if most_wins_count >= 2:
                dynasty_str = f"All-time leader: {most_wins_name} ({most_wins_count} titles)."

        # ── Favorite to win (based on ranking + surface modifier) ──
        favorite_str = None
        participants = best_tournament.get('participants', [])
        if participants:
            candidate_players = []
            for pid in participants:
                p = next((pl for pl in self.players if pl['id'] == pid), None)
                if p and not p.get('retired', False):
                    surf_mod = p.get('surface_modifiers', {}).get(surface, 1.0)
                    rank = p.get('rank', 999)
                    # Lower rank = better; higher surf_mod = better
                    # Score: inverse rank weighted by surface mod
                    score = surf_mod * (1000 - min(rank, 999))
                    candidate_players.append((p, score, surf_mod, rank))

            if candidate_players:
                candidate_players.sort(key=lambda x: x[1], reverse=True)
                fav, fav_score, fav_surf, fav_rank = candidate_players[0]
                surf_desc = ""
                if fav_surf >= 1.02:
                    surf_desc = f", a {surface} specialist"
                elif fav_surf >= 1.01:
                    surf_desc = f", comfortable on {surface}"

                favorite_str = random.choice([
                    f"Pre-tournament favorite: #{fav_rank} {fav['name']}{surf_desc}.",
                    f"Bookmakers' pick: {fav['name']} (#{fav_rank}){surf_desc}.",
                    f"The one to beat: {fav['name']}, currently ranked #{fav_rank}{surf_desc}.",
                ])

                # Add a dark horse if there is one
                if len(candidate_players) >= 5:
                    # Dark horse: someone ranked lower but with great surface mod
                    dark_horses = [
                        (p, sc, sm, r) for p, sc, sm, r in candidate_players[3:10]
                        if sm >= 1.015 and r > candidate_players[0][3] + 20
                    ]
                    if dark_horses:
                        dh = dark_horses[0]
                        favorite_str += random.choice([
                            f" Dark horse: #{dh[3]} {dh[0]['name']} — deadly on {surface}.",
                            f" Watch out for {dh[0]['name']} (#{dh[3]}), a {surface} specialist who could upset the draw.",
                            f" Sleeper pick: {dh[0]['name']} (#{dh[3]}) thrives on {surface} courts.",
                        ])

        # ── Surface context ──
        surface_flavor = {
            'clay': random.choice([
                f"Played on clay — expect long rallies, heavy topspin, and grueling baseline battles.",
                f"The red clay courts will reward patience and endurance this week.",
                f"Clay-court tennis at its finest. Footwork and stamina will be key.",
            ]),
            'grass': random.choice([
                f"The fast grass courts will favor big servers and aggressive net play.",
                f"Grass season is here — low bounces, quick points, and serve-and-volley magic.",
                f"On grass, the ball skids and stays low. Adaptability is everything.",
            ]),
            'hard': random.choice([
                f"Hard courts provide a balanced test — rewarding all-around excellence.",
                f"On hard courts, there's nowhere to hide. The most complete player usually wins.",
                f"The hard-court surface levels the playing field — pure tennis fundamentals decide.",
            ]),
            'indoor': random.choice([
                f"Indoor conditions mean controlled environments, fast surfaces, and big serving.",
                f"No wind, no sun — just pure skill under the roof. Indoor tennis rewards precision.",
                f"The indoor courts offer speed and consistency. Serve and return will be crucial.",
            ]),
            'neutral': random.choice([
                f"A unique surface that tests every aspect of a player's game equally.",
                f"On neutral courts, there are no surface advantages — only talent matters.",
            ]),
        }

        # ── Build the showcase content ──
        lines = []

        # Opening with city lore
        if city_lore:
            lines.append(city_lore)
        lines.append("")

        # Tournament details
        draw_text = f"{draw_size}-player draw"
        lines.append(f"📋 {cat} | {surface.capitalize()} | {draw_text}")
        lines.append(surface_flavor.get(surface, ""))

        if last_winner_str:
            lines.append(f"🏆 {last_winner_str}")
        if dynasty_str:
            lines.append(f"👑 {dynasty_str}")
        if favorite_str:
            lines.append(f"⭐ {favorite_str}")

        # Fun stat about the tournament's history
        if len(history) >= 3:
            unique_winners = len(set(h['winner'] for h in history))
            total_editions = len(history)
            if unique_winners == total_editions:
                lines.append(f"📊 {total_editions} editions, {unique_winners} different champions — no repeat winners yet!")
            elif unique_winners <= total_editions // 2:
                lines.append(f"📊 Only {unique_winners} different champions in {total_editions} editions. An exclusive club.")
            else:
                lines.append(f"📊 {unique_winners} different champions across {total_editions} editions of this tournament.")

        items.append({
            'type': 'showcase',
            'title': f'🏟️ TOURNAMENT SHOWCASE: {name.upper()}',
            'content': lines
        })

        return items

    # Mapping of tournament names to their host city
    TOURNAMENT_CITY_MAP = {
        'WINTER SPLIT': 'Eden',
        'SPRING SPLIT': 'Eden',
        'SUMMER SPLIT': 'Eden',
        'AUTUMN SPLIT': 'Eden',
        'Eden Masters': 'Eden',
        'Final Masters': 'Halcyon',
        'Nextgen Finals': 'Halcyon',
        'Kings Cup': 'Halcyon',
        'Halcyon Masters': 'Halcyon',
    }

    def _extract_city_name(self, tournament_name):
        """Extract the city/location name from a tournament name."""
        # Check explicit mapping first
        if tournament_name in self.TOURNAMENT_CITY_MAP:
            return self.TOURNAMENT_CITY_MAP[tournament_name]
        # Remove common suffixes to get the city name
        for suffix in [' Open', ' Championships', ' Championship', ' Masters',
                       ' Challenger', ' Grand Prix', ' Champs', ' Tournament',
                       ' International', ' Invitational', ' Finals']:
            if tournament_name.endswith(suffix):
                return tournament_name[:-len(suffix)]
        return tournament_name

    def _generate_city_lore(self, city_name, surface, category, tournament_name=''):
        """Generate deterministic fictional city lore based on city name."""

        # ── Special handcrafted lore for major cities ──
        if city_name == 'Eden':
            return self._eden_lore(surface, category)
        if city_name == 'Halcyon':
            return self._halcyon_lore(surface, category, tournament_name)

        # Use hash of city name as seed for consistent generation
        seed = sum(ord(c) for c in city_name)
        rng = random.Random(seed)

        # Population ranges based on tournament category
        pop_ranges = {
            'Grand Slam': (800000, 5000000),
            'Special': (500000, 3000000),
            'Masters 1000': (400000, 2500000),
            'ATP 500': (150000, 800000),
            'ATP 250': (50000, 400000),
            'Challenger 175': (30000, 150000),
            'Challenger 125': (20000, 100000),
            'Challenger 100': (15000, 80000),
            'Challenger 75': (8000, 50000),
            'Challenger 50': (5000, 30000),
        }
        pop_min, pop_max = pop_ranges.get(category, (10000, 100000))
        population = rng.randint(pop_min, pop_max)

        # Format population nicely
        if population >= 1000000:
            pop_str = f"{population / 1000000:.1f} million"
        else:
            pop_str = f"{population:,}"

        # City descriptors based on surface (gives a sense of climate/geography)
        surface_vibes = {
            'clay': [
                'sun-drenched', 'Mediterranean-style', 'warm', 'terracotta-roofed',
                'hillside', 'vineyard-surrounded', 'coastal',
            ],
            'grass': [
                'lush', 'garden-lined', 'temperate', 'green',
                'historic', 'sprawling', 'river-side',
            ],
            'hard': [
                'modern', 'bustling', 'cosmopolitan', 'vibrant',
                'fast-growing', 'dynamic', 'urban',
            ],
            'indoor': [
                'northern', 'industrial', 'sleek', 'architecturally striking',
                'culturally rich', 'sophisticated', 'winter-weathered',
            ],
            'neutral': [
                'prestigious', 'iconic', 'legendary', 'celebrated',
            ],
        }
        descriptors = surface_vibes.get(surface, ['notable'])
        city_adj = rng.choice(descriptors)

        # Landmarks / features
        landmarks = [
            f"famous for its annual food festival",
            f"known for its centuries-old university",
            f"home to the iconic {city_name} Cathedral",
            f"built around a historic harbor",
            f"renowned for its botanical gardens",
            f"famous for its bustling open-air markets",
            f"home to the prestigious {city_name} Academy of Arts",
            f"known for its ancient city walls",
            f"celebrated for its musical heritage",
            f"built along the banks of the River {city_name[:3].capitalize()}or",
            f"famous for its annual carnival",
            f"renowned for its architecture and public squares",
            f"home to one of the oldest tennis clubs in the region",
            f"known for its thriving café culture",
            f"surrounded by scenic mountain trails",
            f"famous for its thermal springs",
            f"home to the {city_name} National Museum",
            f"known for its vibrant nightlife and music scene",
            f"celebrated for its tradition of sporting excellence",
            f"built on the ruins of an ancient trading post",
        ]
        landmark = rng.choice(landmarks)

        # Founded year (deterministic)
        founded = rng.randint(200, 1800)

        # Tournament-specific establishment year
        tournament_est = rng.randint(2025 - rng.randint(15, 80), 2024)

        # Build the lore sentence
        templates = [
            f"Welcome to {city_name}, a {city_adj} city of {pop_str} inhabitants, {landmark}. The tournament has been a fixture of the tennis calendar since {tournament_est}.",
            f"{city_name} (pop. {pop_str}) — a {city_adj} destination {landmark}. Tennis has been played here since {tournament_est}, making it one of the tour's cherished stops.",
            f"The tour arrives in {city_name}, a {city_adj} city of {pop_str}. Founded in {founded}, the city is {landmark}. This tournament was first held in {tournament_est}.",
            f"Nestled in the heart of its region, {city_name} is a {city_adj} city of {pop_str}, {landmark}. This event has been a staple since {tournament_est}.",
        ]

        return rng.choice(templates)

    def _eden_lore(self, surface, category):
        """Handcrafted lore for Eden — the second-largest city in the world, host of all Grand Slams and the Eden Masters."""
        rng = random.Random(42 + hash(surface))  # Vary slightly per surface

        intro_options = [
            "Eden — the crown jewel of world tennis. With a population of 4.2 million, it is the second-largest city on the planet and the undisputed capital of the sport.",
            "Welcome to Eden (pop. 4.2 million), the legendary city where every Grand Slam is played. No other venue carries more history, more prestige, or more pressure.",
            "The tour returns to Eden, the sprawling metropolis of 4.2 million souls that serves as the spiritual home of professional tennis.",
            "Eden. Population: 4.2 million. The second-biggest city in the world and the only place on Earth to host all four Grand Slams.",
        ]
        intro = rng.choice(intro_options)

        surface_fragments = {
            'hard': "The iconic Eden Arena — with its retractable roof and 22,000-seat centre court — transforms into a hard-court cathedral every season.",
            'clay': "When clay season arrives, Eden's courts are resurfaced with the famous red terre battue, and the city's tree-lined boulevards fill with the sound of sliding footwork.",
            'grass': "The pristine grass courts of Eden are the pride of the groundskeeping world — trimmed to exactly 8mm, they reward touch, precision, and courage at the net.",
            'indoor': "As autumn descends, Eden's arenas seal their roofs and the atmosphere becomes electric under the lights — serve speed climbs, rallies shorten, and the crowd's roar reverberates off every surface.",
        }

        color_options = [
            "Home to the Eden Grand Library, the Meridian Tower, and the famous riverside promenade, the city buzzes with energy year-round.",
            "Beyond tennis, Eden is renowned for its world-class universities, its skyline of glass and stone, and a café culture that rivals any on the continent.",
            "The city's six districts each have their own character — from the historic Old Quarter to the gleaming financial hub of Meridian South.",
            "Eden's cultural heritage is unmatched: opera houses, galleries, and the legendary Founders' Park where the first-ever professional tennis match was played.",
        ]

        parts = [intro]
        if surface in surface_fragments:
            parts.append(surface_fragments[surface])
        parts.append(rng.choice(color_options))
        return " ".join(parts)

    def _halcyon_lore(self, surface, category, tournament_name=''):
        """Handcrafted lore for Halcyon — the largest city in the world, host of the Final Masters, Nextgen Finals, Kings Cup, and Halcyon Masters."""
        rng = random.Random(77 + hash(tournament_name))  # Vary per event

        intro_options = [
            "Halcyon — the largest city in the world (pop. 6.8 million) and the stage where legends are crowned. The season's most decisive events are all played here.",
            "Welcome to Halcyon, the planet's greatest metropolis with 6.8 million inhabitants. When tennis needs its grandest stage, it comes here.",
            "The tour descends on Halcyon (pop. 6.8 million), the colossal capital of commerce, culture, and elite tennis.",
            "Halcyon. Population: 6.8 million. The biggest city in the world, and the place where season-defining titles are won and lost.",
        ]
        intro = rng.choice(intro_options)

        event_flavors = {
            'Final Masters': "The Final Masters — reserved for the top 8 players in the world — transforms Halcyon's Sovereign Arena into the most exclusive venue in sport. Only the elite are invited.",
            'Nextgen Finals': "The Nextgen Finals spotlight the brightest young talents on the tour. In the cavernous Halcyon Youth Arena, future champions announce themselves to the world.",
            'Kings Cup': "The Kings Cup is tennis royalty made literal: only Grand Slam champions are invited. Halcyon's Throne Court — with its golden accents and royal box — is the fitting backdrop.",
            'Halcyon Masters': "The Halcyon Masters brings Masters 1000 tennis to the world's biggest city. The Halcyon Central Courts, set against the iconic skyline, draw crowds of over 80,000 across the week.",
        }
        event_bit = event_flavors.get(tournament_name, '')

        color_options = [
            "Halcyon's neon-lit skyline, its titanic Sovereign Bridge, and the legendary Night Market district make it a city unlike any other.",
            "Beyond the courts, Halcyon offers the Grand Observatory, miles of waterfront parkland, and a dining scene that draws visitors from every nation.",
            "The city never sleeps: Halcyon's eight interconnected districts pulse with commerce, art, and sport from dawn until well past midnight.",
            "From the ancient Starfall Citadel in the old town to the gleaming spires of the New Central, Halcyon is a city of contrasts and ambition.",
        ]

        parts = [intro]
        if event_bit:
            parts.append(event_bit)
        parts.append(rng.choice(color_options))
        return " ".join(parts)

    def _generate_tweet_news(self):
        """Generate short tweet-style news items about interesting events."""
        tweets = []
        last_week = self.current_week - 1 if self.current_week > 1 else 52

        # ── 1. Young players (<20) with deep runs — KEEP ONLY THE BEST ONE ──
        best_prospect = None  # (player, round_idx, total_rounds, tournament)
        for tournament in self.tournaments:
            if (tournament['week'] == last_week and
                not tournament['category'].startswith("ITF") and
                not tournament['category'] == "Juniors"):

                bracket = tournament.get('bracket', [])
                if not bracket:
                    continue

                total_rounds = len(bracket)
                # Score prestige of tournament category
                cat_prestige = len(self.PRESTIGE_ORDER) - (
                    self.PRESTIGE_ORDER.index(tournament['category'])
                    if tournament['category'] in self.PRESTIGE_ORDER else 0)

                for round_idx, round_matches in enumerate(bracket):
                    if round_idx < total_rounds - 2:
                        continue
                    for match in round_matches:
                        for pid in match[:2]:
                            if pid is None or pid == tournament.get('winner_id'):
                                continue
                            player = next((p for p in self.players if p['id'] == pid), None)
                            if not player or player.get('age', 30) >= 20:
                                continue
                            # Score: higher round + higher prestige = better story
                            score = round_idx * 10 + cat_prestige
                            if best_prospect is None or score > best_prospect[4]:
                                best_prospect = (player, round_idx, total_rounds, tournament, score)

        if best_prospect:
            player, round_idx, total_rounds, tournament, _ = best_prospect
            archetype = player.get('archetype', 'Balanced Player')
            round_name = "final" if round_idx == total_rounds - 1 else "semifinals"
            tweet_templates = [
                f"Keep an eye on {player['name']}! The {player['age']}-year-old {archetype.lower()} reached the {round_name} of the {tournament['name']}.",
                f"{player['name']} ({player['age']}) is showing serious promise. The young {archetype.lower()} made it to the {round_name} at the {tournament['name']}.",
                f"Prospect alert: {player['name']}, a {player['age']}-year-old {archetype.lower()}, just reached the {round_name} of a {tournament['category']} event.",
                f"The future looks bright for {player['name']}. At {player['age']}, the {archetype.lower()} is already competing deep in {tournament['category']} draws.",
            ]
            tweets.append({
                'type': 'tweet',
                'title': '💬 PROSPECT WATCH',
                'content': random.choice(tweet_templates)
            })

        # ── 2. Seasonal ranking rise ──
        for player in self.players:
            if player.get('retired', False):
                continue
            year_rankings = player.get('year_start_rankings', {})
            current_rank = player.get('rank', 999)
            last_year_key = str(self.current_year - 1)
            if last_year_key in year_rankings:
                old_rank = year_rankings[last_year_key]
                if old_rank > 100 and current_rank <= 50:
                    if random.random() < 0.08:
                        archetype = player.get('archetype', 'player')
                        tweets.append({
                            'type': 'tweet',
                            'title': '💬 RISING STAR',
                            'content': random.choice([
                                f"{player['name']} has been on a tear this season — from #{old_rank} to #{current_rank}. The {archetype.lower()} is making a statement.",
                                f"Remember the name: {player['name']}. Ranked #{old_rank} at the start of the year, now all the way up to #{current_rank}.",
                                f"{player['name']}'s rise continues. The {archetype.lower()} started the year at #{old_rank} and now sits at #{current_rank}.",
                            ])
                        })

        # ── 3. New world #1 (first time ever) ──
        current_no1 = next(
            (p for p in self.players if p.get('rank') == 1 and not p.get('retired', False)),
            None
        )
        if current_no1 and current_no1.get('w1', 0) == 1:
            tweets.append({
                'type': 'tweet',
                'title': '👑 NEW WORLD #1',
                'content': random.choice([
                    f"{current_no1['name']} reaches the summit! A new world #1 is crowned.",
                    f"History is made — {current_no1['name']} rises to the #1 ranking for the first time!",
                    f"A new era begins. {current_no1['name']} is the new world #1.",
                ])
            })

        # ── 4. Veteran still winning (age >= 32) ──
        for tournament in self.tournaments:
            if (tournament['week'] == last_week and tournament.get('winner_id') and
                not tournament['category'].startswith("Challenger") and
                not tournament['category'].startswith("ITF") and
                not tournament['category'] == "Juniors"):
                winner = next((p for p in self.players if p['id'] == tournament['winner_id']), None)
                if winner and winner.get('age', 20) >= 32:
                    tweets.append({
                        'type': 'tweet',
                        'title': '💬 AGELESS',
                        'content': random.choice([
                            f"Age is just a number. {winner['name']}, {winner['age']}, proves he still has what it takes with a title at the {tournament['name']}.",
                            f"Don't count out the veterans. {winner['name']} ({winner['age']}) is still winning at the highest level.",
                            f"{winner['name']} rolls back the years. At {winner['age']}, the {winner.get('archetype', 'veteran').lower()} shows no signs of slowing down.",
                        ])
                    })

        # ── 5. Weekly stat improvements (who gained skill points this week) ──
        pre_dev = getattr(self, '_pre_dev_skills', {})
        if pre_dev:
            improvers = []
            for player in self.players:
                if player.get('retired', False) or player['id'] not in pre_dev:
                    continue
                old_skills = pre_dev[player['id']]
                new_skills = player.get('skills', {})
                gained = {}
                for sk, new_val in new_skills.items():
                    old_val = old_skills.get(sk, new_val)
                    if new_val > old_val:
                        gained[sk] = new_val - old_val
                if gained:
                    total_gain = sum(gained.values())
                    improvers.append((player, gained, total_gain))

            # Sort by total gain descending, take top few
            improvers.sort(key=lambda x: x[2], reverse=True)
            for player, gained, total_gain in improvers[:2]:
                skill_names = list(gained.keys())
                if len(skill_names) == 1:
                    skill_str = f"{skill_names[0]} (+{gained[skill_names[0]]})"
                elif len(skill_names) == 2:
                    skill_str = f"{skill_names[0]} (+{gained[skill_names[0]]}) and {skill_names[1]} (+{gained[skill_names[1]]})"
                else:
                    skill_str = ", ".join(f"{s} (+{gained[s]})" for s in skill_names[:3])

                age = player.get('age', 20)
                archetype = player.get('archetype', 'player')
                templates = [
                    f"📈 {player['name']} has been putting in the work. Noticeable improvement in {skill_str} this week.",
                    f"Training paying off for {player['name']}! The {archetype.lower()} improved his {skill_str}.",
                    f"{player['name']} ({age}) leveling up — gains in {skill_str}. Watch this space.",
                    f"The grind never stops. {player['name']} showing improvement in {skill_str}.",
                ]
                if age < 20:
                    templates.append(f"Only {age} and already improving fast. {player['name']} boosted his {skill_str} this week.")
                tweets.append({
                    'type': 'tweet',
                    'title': '📊 DEVELOPMENT UPDATE',
                    'content': random.choice(templates)
                })

        # ── 6. Ranking milestones (first time top 10, top 50, career high) ──
        old_ranks = getattr(self, 'old_rankings', {})
        for player in self.players:
            if player.get('retired', False):
                continue
            current_rank = player.get('rank', 999)
            old_rank = old_ranks.get(player['id'], 999)

            # First time top 10
            if current_rank <= 10 and old_rank > 10:
                tweets.append({
                    'type': 'tweet',
                    'title': '🔟 TOP 10 BREAKTHROUGH',
                    'content': random.choice([
                        f"Welcome to the elite! {player['name']} breaks into the top 10 for the first time, climbing to #{current_rank}.",
                        f"{player['name']} cracks the top 10! A milestone moment in his career — now ranked #{current_rank}.",
                        f"Top 10 alert: {player['name']} has arrived. From #{old_rank} to #{current_rank} this week.",
                    ])
                })
            # First time top 50
            elif current_rank <= 50 and old_rank > 50:
                if random.random() < 0.5:  # Don't always report top 50 entries
                    tweets.append({
                        'type': 'tweet',
                        'title': '💬 CLIMBING THE RANKS',
                        'content': random.choice([
                            f"{player['name']} enters the top 50 for the first time! Now ranked #{current_rank}.",
                            f"Milestone: {player['name']} moves to #{current_rank}, breaking into the top 50.",
                            f"Steady climb for {player['name']} — he's now a top-50 player at #{current_rank}.",
                        ])
                    })

            # New career-high ranking (only for players already ranked decently)
            if (current_rank < old_rank and current_rank <= 30 and
                current_rank == player.get('highest_ranking', 999)):
                # Only report if it's a meaningful jump
                if old_rank - current_rank >= 3:
                    tweets.append({
                        'type': 'tweet',
                        'title': '⬆️ CAREER HIGH',
                        'content': random.choice([
                            f"New career-high ranking for {player['name']}! He jumps from #{old_rank} to #{current_rank}.",
                            f"{player['name']} hits a new peak — #{current_rank} is the highest he's ever been ranked.",
                            f"Career best! {player['name']} surges to #{current_rank}, up {old_rank - current_rank} spots this week.",
                        ])
                    })

        # ── 7. Biggest ranking drop of the week ──
        biggest_drop = None
        for player in self.players:
            if player.get('retired', False):
                continue
            current_rank = player.get('rank', 999)
            old_rank = old_ranks.get(player['id'], 999)
            drop = current_rank - old_rank
            if drop >= 10 and old_rank <= 50:  # Only notable drops for top players
                if biggest_drop is None or drop > biggest_drop[1]:
                    biggest_drop = (player, drop, old_rank, current_rank)

        if biggest_drop:
            player, drop, old_rank, current_rank = biggest_drop
            tweets.append({
                'type': 'tweet',
                'title': '📉 ROUGH WEEK',
                'content': random.choice([
                    f"Tough times for {player['name']}. Drops {drop} spots from #{old_rank} to #{current_rank}.",
                    f"{player['name']} slides from #{old_rank} to #{current_rank}. What's going on?",
                    f"Not the week {player['name']} wanted — down {drop} places to #{current_rank}.",
                    f"Concerned fans watching {player['name']} fall from #{old_rank} to #{current_rank}. Time to regroup.",
                ])
            })

        # ── 8. Title collection hot streak (multiple wins in recent weeks) ──
        for player in self.players:
            if player.get('retired', False):
                continue
            recent_wins = [w for w in player.get('tournament_wins', [])
                          if w.get('year') == self.current_year]
            if len(recent_wins) >= 3:
                if random.random() < 0.12:
                    tweets.append({
                        'type': 'tweet',
                        'title': '🔥 HOT STREAK',
                        'content': random.choice([
                            f"{player['name']} is on fire this season! Already {len(recent_wins)} titles in {self.current_year}.",
                            f"Can anyone stop {player['name']}? That's {len(recent_wins)} tournament wins this year and counting.",
                            f"{player['name']} is collecting trophies like it's nothing — {len(recent_wins)} titles in {self.current_year} so far.",
                            f"Dominant season from {player['name']}. {len(recent_wins)} titles this year. The rest of the tour is on notice.",
                        ])
                    })

        # ── 9. Upset alert — low-ranked player won a big tournament ──
        for tournament in self.tournaments:
            if (tournament['week'] == last_week and tournament.get('winner_id') and
                tournament['category'] in ('Grand Slam', 'Masters 1000', 'ATP 500')):
                winner = next((p for p in self.players if p['id'] == tournament['winner_id']), None)
                if winner and winner.get('rank', 999) > 50:
                    tweets.append({
                        'type': 'tweet',
                        'title': '😱 UPSET SPECIAL',
                        'content': random.choice([
                            f"Nobody saw this coming! World #{winner.get('rank', '?')} {winner['name']} wins the {tournament['name']}. The bracket is in shambles.",
                            f"UPSET OF THE YEAR candidate: #{winner.get('rank', '?')} {winner['name']} takes down the field at the {tournament['name']}!",
                            f"{winner['name']}, ranked #{winner.get('rank', '?')}, just won a {tournament['category']} event. Tennis is chaos and we love it.",
                        ])
                    })

        # ── 10. Surface specialist commentary ──
        for tournament in self.tournaments:
            if (tournament['week'] == last_week and tournament.get('winner_id') and
                not tournament['category'].startswith("Challenger") and
                not tournament['category'].startswith("ITF") and
                not tournament['category'] == "Juniors"):
                surface = tournament.get('surface', '')
                winner = next((p for p in self.players if p['id'] == tournament['winner_id']), None)
                if winner and surface:
                    surface_mod = winner.get('surface_modifiers', {}).get(surface, 1.0)
                    surface_wins = [w for w in winner.get('tournament_wins', [])
                                   if any(t.get('surface') == surface and t['name'] == w['name']
                                         for t in self.tournaments)]
                    if surface_mod >= 1.02 and len(surface_wins) >= 3:
                        tweets.append({
                            'type': 'tweet',
                            'title': f'🎾 {surface.upper()} KING',
                            'content': random.choice([
                                f"{winner['name']} is absolutely lethal on {surface}. Another title on his favorite surface.",
                                f"Is {winner['name']} the best {surface}-court player on tour? The results speak for themselves.",
                                f"{winner['name']} + {surface} = automatic titles. The {winner.get('archetype', 'player').lower()} is a {surface} specialist.",
                            ])
                        })

        # ── 11. HOT TAKES & color commentary (randomized filler tweets) ──
        # Top player hasn't won a slam this year
        top_5 = [p for p in self.players if p.get('rank', 999) <= 5 and not p.get('retired', False)]
        for p in top_5:
            gs_wins_this_year = [w for w in p.get('tournament_wins', [])
                                if w.get('year') == self.current_year and w.get('category') == 'Grand Slam']
            total_gs = len([w for w in p.get('tournament_wins', []) if w.get('category') == 'Grand Slam'])
            if total_gs > 0 and len(gs_wins_this_year) == 0 and self.current_week > 30:
                if random.random() < 0.04:
                    tweets.append({
                        'type': 'tweet',
                        'title': '🗣️ HOT TAKE',
                        'content': random.choice([
                            f"Is {p['name']} past his Grand Slam-winning days? Still ranked #{p['rank']} but no Slam title in {self.current_year}.",
                            f"Hot take: {p['name']} won't add another Grand Slam to his collection. Prove me wrong.",
                            f"For a player of {p['name']}'s caliber, a year without a Grand Slam title has to sting.",
                        ])
                    })

        # Random stat leader spotlight
        if random.random() < 0.15:
            stat_choices = [
                ('serve', '🎯 SERVE MACHINE'),
                ('forehand', '💥 FOREHAND WEAPON'),
                ('backhand', '🔄 BACKHAND MAESTRO'),
                ('speed', '⚡ SPEED DEMON'),
                ('volley', '🏐 NET WIZARD'),
                ('dropshot', '🪶 TOUCH ARTIST'),
            ]
            stat_key, title = random.choice(stat_choices)
            active = [p for p in self.players if not p.get('retired', False) and p.get('rank', 999) <= 100]
            if active:
                best = max(active, key=lambda p: p.get('skills', {}).get(stat_key, 0))
                stat_val = best.get('skills', {}).get(stat_key, 0)
                if stat_val >= 70:
                    tweets.append({
                        'type': 'tweet',
                        'title': title,
                        'content': random.choice([
                            f"{best['name']} has the best {stat_key} on tour right now ({stat_val} rating). Absolute weapon.",
                            f"Stat check: {best['name']}'s {stat_key} is rated {stat_val}. Best among top-100 players.",
                            f"Want to see elite {stat_key} technique? Watch {best['name']}. {stat_val} rating, best on tour.",
                        ])
                    })

        # ── 12. Biggest weekly ranking climber ──
        biggest_climb = None
        for player in self.players:
            if player.get('retired', False):
                continue
            current_rank = player.get('rank', 999)
            old_rank = old_ranks.get(player['id'], 999)
            climb = old_rank - current_rank
            if climb >= 10 and current_rank <= 100:
                if biggest_climb is None or climb > biggest_climb[1]:
                    biggest_climb = (player, climb, old_rank, current_rank)

        if biggest_climb:
            player, climb, old_rank, current_rank = biggest_climb
            tweets.append({
                'type': 'tweet',
                'title': '🚀 BIGGEST MOVER',
                'content': random.choice([
                    f"Biggest mover of the week: {player['name']} rockets up {climb} spots to #{current_rank}!",
                    f"{player['name']} is this week's biggest climber — #{old_rank} → #{current_rank}. (+{climb})",
                    f"Up {climb} ranks! {player['name']} jumps from #{old_rank} to #{current_rank} in a single week.",
                ])
            })

        # ── 13. First career title (only for challengers/smaller events) ──
        for tournament in self.tournaments:
            if (tournament['week'] == last_week and tournament.get('winner_id') and
                tournament['category'].startswith("Challenger")):
                winner = next((p for p in self.players if p['id'] == tournament['winner_id']), None)
                if winner:
                    total_wins = len(winner.get('tournament_wins', []))
                    if total_wins == 1:
                        tweets.append({
                            'type': 'tweet',
                            'title': '💬 FIRST STEPS',
                            'content': random.choice([
                                f"Everyone starts somewhere. {winner['name']} picks up his first professional title at the {tournament['name']}. A career begins.",
                                f"First title secured! {winner['name']} wins the {tournament['name']}. From unknown to champion.",
                                f"{winner['name']} will never forget this week — his first ever professional title, at the {tournament['name']}.",
                            ])
                        })

        # ── 14. Veterans declining (big drop for old player) ──
        for player in self.players:
            if player.get('retired', False) or player.get('age', 20) < 30:
                continue
            current_rank = player.get('rank', 999)
            old_rank = old_ranks.get(player['id'], 999)
            if current_rank - old_rank >= 8 and old_rank <= 60:
                if random.random() < 0.3:
                    tweets.append({
                        'type': 'tweet',
                        'title': '💬 FATHER TIME',
                        'content': random.choice([
                            f"Is the end near for {player['name']}? The {player['age']}-year-old drops from #{old_rank} to #{current_rank}.",
                            f"{player['name']} ({player['age']}) sliding down the rankings — #{old_rank} to #{current_rank}. Retirement talk incoming?",
                            f"Father Time remains undefeated. {player['name']}, {player['age']}, falls to #{current_rank}.",
                        ])
                    })

        # ── 15. Close to milestone title count ──
        for player in self.players:
            if player.get('retired', False):
                continue
            total_wins = len(player.get('tournament_wins', []))
            if total_wins in [9, 19, 24, 29, 49]:
                if random.random() < 0.05:
                    milestone = total_wins + 1
                    tweets.append({
                        'type': 'tweet',
                        'title': '🏆 MILESTONE WATCH',
                        'content': random.choice([
                            f"{player['name']} sits at {total_wins} career titles. Can he reach {milestone} this season?",
                            f"Just one more win from a milestone — {player['name']} has {total_wins} titles. #{milestone} is calling.",
                            f"Milestone alert: {player['name']} is one title away from {milestone} career wins.",
                        ])
                    })

        # ── 16. Young prodigy enters top 30 (under 24 — peak development age) ──
        for player in self.players:
            if player.get('retired', False):
                continue
            current_rank = player.get('rank', 999)
            old_rank = old_ranks.get(player['id'], 999)
            age = player.get('age', 30)
            if age < 24 and current_rank <= 30 and old_rank > 30:
                archetype = player.get('archetype', 'player')
                tweets.append({
                    'type': 'tweet',
                    'title': '🌟 FUTURE STAR',
                    'content': random.choice([
                        f"{player['name']} enters the top 30 at just {age} years old! Still in his prime development years — the ceiling is scary.",
                        f"Only {age} and already #{current_rank} in the world. {player['name']} hasn't even hit his peak yet. Remember this tweet.",
                        f"{player['name']} ({age}) breaks into the top 30. With years of development still ahead, this {archetype.lower()} could be special.",
                        f"Top 30 before turning 24. {player['name']} is doing things ahead of schedule — and he's only going to get better.",
                    ])
                })

        # ── 17. Scouting report — under 20 enters top 150 ──
        for player in self.players:
            if player.get('retired', False):
                continue
            current_rank = player.get('rank', 999)
            old_rank = old_ranks.get(player['id'], 999)
            age = player.get('age', 30)
            if age < 20 and current_rank <= 150 and old_rank > 150:
                archetype = player.get('archetype', 'player')
                potential = player.get('potential_factor', 1.0)
                tweets.append({
                    'type': 'tweet',
                    'title': '🔎 SCOUTING REPORT',
                    'content': random.choice([
                        f"Scouts are buzzing about {player['name']}. The {age}-year-old {archetype.lower()} just broke into the top 150. Future superstar material?",
                        f"Add {player['name']} to your watchlist. At {age}, reaching #{current_rank} is extremely rare. This kid is the real deal.",
                        f"📋 Scouting alert: {player['name']} ({age}) enters the top 150 at #{current_rank}. The {archetype.lower()} is years ahead of the curve.",
                        f"They don't reach the top 150 at {age} unless they're something special. {player['name']} is one to watch very closely.",
                    ])
                })

        # ── 18. Young vs Old matchup narrative ──
        for tournament in self.tournaments:
            if tournament['week'] == last_week and tournament.get('bracket'):
                bracket = tournament['bracket']
                total_rounds = len(bracket)
                # Check the final specifically
                if total_rounds >= 1:
                    final_round = bracket[-1]
                    for match in final_round:
                        if len(match) >= 3 and match[2] is not None:
                            p1 = next((p for p in self.players if p['id'] == match[0]), None)
                            p2 = next((p for p in self.players if p['id'] == match[1]), None)
                            if p1 and p2:
                                age_diff = abs(p1.get('age', 25) - p2.get('age', 25))
                                young = p1 if p1.get('age', 25) < p2.get('age', 25) else p2
                                old = p2 if young == p1 else p1
                                if age_diff >= 10 and young.get('age', 25) <= 22:
                                    winner = next((p for p in self.players if p['id'] == match[2]), None)
                                    if winner:
                                        if winner['id'] == young['id']:
                                            tweets.append({
                                                'type': 'tweet',
                                                'title': '⚔️ CLASH OF GENERATIONS',
                                                'content': f"Youth prevails! {young['name']} ({young['age']}) defeats {old['name']} ({old['age']}) in the {tournament['name']} final. The changing of the guard continues."
                                            })
                                        else:
                                            tweets.append({
                                                'type': 'tweet',
                                                'title': '⚔️ CLASH OF GENERATIONS',
                                                'content': f"Experience wins out! {old['name']} ({old['age']}) holds off {young['name']} ({young['age']}) in the {tournament['name']} final. Not yet, kid."
                                            })

        # ── 18. Overall rating spotlight ──
        if random.random() < 0.10:
            active = [p for p in self.players if not p.get('retired', False)]
            if active:
                def calc_ovr(p):
                    skills = p.get('skills', {})
                    return round(sum(skills.values()) / max(1, len(skills)), 1) if skills else 0

                best_ovr = max(active, key=calc_ovr)
                ovr = calc_ovr(best_ovr)
                if ovr >= 65:
                    tweets.append({
                        'type': 'tweet',
                        'title': '👤 PLAYER SPOTLIGHT',
                        'content': random.choice([
                            f"{best_ovr['name']} currently has the highest overall rating on tour ({ovr}). The complete package.",
                            f"By the numbers, {best_ovr['name']} is the most complete player in tennis right now. OVR: {ovr}.",
                            f"No weaknesses. {best_ovr['name']} tops the tour with a {ovr} overall rating.",
                        ])
                    })

        # ── 19. Nationality dominance ──
        if random.random() < 0.08:
            from collections import Counter
            nationalities = Counter(
                p.get('nationality', 'Unknown')
                for p in self.players
                if not p.get('retired', False) and p.get('rank', 999) <= 20
            )
            if nationalities:
                top_nat, count = nationalities.most_common(1)[0]
                if count >= 3:
                    players_from = [p['name'] for p in self.players
                                   if p.get('nationality') == top_nat and p.get('rank', 999) <= 20
                                   and not p.get('retired', False)][:3]
                    tweets.append({
                        'type': 'tweet',
                        'title': '🌍 NATIONAL PRIDE',
                        'content': random.choice([
                            f"{top_nat} is dominating tennis right now! {count} players in the top 20, including {', '.join(players_from)}.",
                            f"What are they putting in the water in {top_nat}? {count} top-20 players and counting.",
                            f"{top_nat} tennis is having a golden era — {', '.join(players_from)} all in the top 20.",
                        ])
                    })

        # ── 20. Weekly matches played milestone ──
        for player in self.players:
            if player.get('retired', False):
                continue
            mp = player.get('matches_played', 0)
            if mp in [100, 250, 500, 750, 1000]:
                tweets.append({
                    'type': 'tweet',
                    'title': '📊 MATCH MILESTONE',
                    'content': random.choice([
                        f"{player['name']} has now played {mp} professional matches. A testament to longevity and dedication.",
                        f"Milestone: {player['name']} reaches {mp} career matches played. What a journey.",
                        f"{mp} matches and counting for {player['name']}. The body of work speaks for itself.",
                    ])
                })

        # ── 21. Title defense upcoming ──
        next_week = self.current_week + 1 if self.current_week < 52 else 1
        for tournament in self.tournaments:
            if tournament['week'] == next_week:
                for player in self.players:
                    if player.get('retired', False):
                        continue
                    defending = any(
                        w['name'] == tournament['name'] and w.get('year') == self.current_year - 1
                        for w in player.get('tournament_wins', [])
                    )
                    if defending:
                        career_wins_here = len([
                            w for w in player.get('tournament_wins', [])
                            if w['name'] == tournament['name']
                        ])
                        tweets.append({
                            'type': 'tweet',
                            'title': '🏟️ TITLE DEFENSE',
                            'content': random.choice([
                                f"All eyes on {player['name']} next week as he defends his {tournament['name']} title. Can he do it again?",
                                f"{player['name']} returns to the {tournament['name']} as defending champion. The pressure is on.",
                                f"Reminder: {player['name']} won the {tournament['name']} last year. He'll look to defend his crown next week.",
                                f"Must-watch next week: {player['name']} puts his {tournament['name']} title on the line.",
                            ]) if career_wins_here <= 1 else random.choice([
                                f"{player['name']} heads to the {tournament['name']} as defending champion — and he's won it {career_wins_here} times. Good luck to the field.",
                                f"The {tournament['name']} is {player['name']}'s kingdom. He returns to defend title #{career_wins_here}.",
                            ])
                        })

        # ── 22. Early regression (age 28-30 only — rare and newsworthy) ──
        if pre_dev:
            for player in self.players:
                if player.get('retired', False) or player['id'] not in pre_dev:
                    continue
                age = player.get('age', 20)
                if age < 28 or age > 30:
                    continue
                old_skills = pre_dev[player['id']]
                new_skills = player.get('skills', {})
                lost = {}
                for sk, new_val in new_skills.items():
                    old_val = old_skills.get(sk, new_val)
                    if new_val < old_val:
                        lost[sk] = old_val - new_val
                if lost:
                    skill_str = " and ".join(f"{s} (-{lost[s]})" for s in list(lost.keys())[:2])
                    tweets.append({
                        'type': 'tweet',
                        'title': '⚠️ EARLY REGRESSION',
                        'content': random.choice([
                            f"Concerning signs for {player['name']} ({age}). His {skill_str} took a dip this week. Too early to panic?",
                            f"{player['name']} is only {age}, but his {skill_str} already showing signs of decline. Unusual at this age.",
                            f"Early regression alert: {player['name']}'s {skill_str} dropped this week. At {age}, this is worth monitoring closely.",
                            f"The clock might be ticking earlier than expected for {player['name']}. {skill_str} declining at just {age}.",
                        ])
                    })

        # ── 23. Archetype showdown in a final ──
        for tournament in self.tournaments:
            if tournament['week'] == last_week and tournament.get('bracket'):
                bracket = tournament['bracket']
                if not bracket:
                    continue
                final_round = bracket[-1]
                for match in final_round:
                    if len(match) >= 3 and match[0] is not None and match[1] is not None:
                        p1 = next((p for p in self.players if p['id'] == match[0]), None)
                        p2 = next((p for p in self.players if p['id'] == match[1]), None)
                        if p1 and p2:
                            a1 = p1.get('archetype', '')
                            a2 = p2.get('archetype', '')
                            k1 = set(p1.get('archetype_key', []))
                            k2 = set(p2.get('archetype_key', []))
                            # Only report if archetypes are different and skill overlap is low
                            if a1 and a2 and a1 != a2 and len(k1 & k2) <= 1:
                                if not tournament['category'].startswith("Challenger") and not tournament['category'].startswith("ITF") and tournament['category'] != "Juniors":
                                    tweets.append({
                                        'type': 'tweet',
                                        'title': '🎯 ARCHETYPE SHOWDOWN',
                                        'content': random.choice([
                                            f"What a final at the {tournament['name']}! {p1['name']} ({a1}) vs {p2['name']} ({a2}). Two completely different styles going head to head.",
                                            f"Style clash at the {tournament['name']} final: the {a1.lower()} {p1['name']} against the {a2.lower()} {p2['name']}. Tactics will decide this one.",
                                            f"{a1} meets {a2} in the {tournament['name']} final. {p1['name']} vs {p2['name']} — contrasting philosophies, one trophy.",
                                        ])
                                    })

        # ── 24. Stat comparison — two top players head to head ──
        if random.random() < 0.10:
            top_players = [p for p in self.players
                          if not p.get('retired', False) and p.get('rank', 999) <= 15]
            if len(top_players) >= 2:
                p1, p2 = random.sample(top_players, 2)
                s1 = p1.get('skills', {})
                s2 = p2.get('skills', {})
                # Find skills where each player leads
                p1_leads = [(sk, s1.get(sk, 0), s2.get(sk, 0)) for sk in s1
                           if s1.get(sk, 0) > s2.get(sk, 0) + 5]
                p2_leads = [(sk, s2.get(sk, 0), s1.get(sk, 0)) for sk in s2
                           if s2.get(sk, 0) > s1.get(sk, 0) + 5]
                if p1_leads and p2_leads:
                    p1_best = max(p1_leads, key=lambda x: x[1] - x[2])
                    p2_best = max(p2_leads, key=lambda x: x[1] - x[2])
                    tweets.append({
                        'type': 'tweet',
                        'title': '📊 STAT COMPARISON',
                        'content': random.choice([
                            f"{p1['name']} vs {p2['name']} — who's better? {p1['name']}'s {p1_best[0]} ({p1_best[1]}) edges out ({p1_best[2]}), but {p2['name']}'s {p2_best[0]} ({p2_best[1]}) is superior ({p2_best[2]}). Depends what you value.",
                            f"Tale of the tape: {p1['name']} has the {p1_best[0]} advantage ({p1_best[1]} vs {p1_best[2]}), {p2['name']} wins on {p2_best[0]} ({p2_best[1]} vs {p2_best[2]}). Who would you rather have?",
                            f"Quick comparison — {p1['name']}: {p1_best[0]} {p1_best[1]}. {p2['name']}: {p2_best[0]} {p2_best[1]}. Both elite, completely different strengths.",
                        ])
                    })

        # ── 25. Dynasty watch — same tournament won 3+ times ──
        for tournament in self.tournaments:
            if (tournament['week'] == last_week and tournament.get('winner_id') and
                not tournament['category'].startswith("ITF") and
                not tournament['category'] == "Juniors"):
                winner = next((p for p in self.players if p['id'] == tournament['winner_id']), None)
                if winner:
                    times_won = len([
                        w for w in winner.get('tournament_wins', [])
                        if w['name'] == tournament['name']
                    ])
                    if times_won >= 3:
                        ordinal = f"{times_won}{'rd' if times_won == 3 else 'th'}"
                        tweets.append({
                            'type': 'tweet',
                            'title': '🏆 DYNASTY WATCH',
                            'content': random.choice([
                                f"{winner['name']} wins the {tournament['name']} for the {ordinal} time. He owns this tournament.",
                                f"Dynasty alert: {winner['name']} captures his {ordinal} {tournament['name']} title. Does anyone else even bother entering?",
                                f"The {tournament['name']} belongs to {winner['name']}. Title #{times_won} at his favorite hunting ground.",
                                f"{times_won} titles at the same tournament. {winner['name']} and the {tournament['name']} — a love story for the ages.",
                            ])
                        })

        # ── 26. Cold streak — top-30 player, no title all year (late season) ──
        if self.current_week > 30:
            for player in self.players:
                if player.get('retired', False):
                    continue
                current_rank = player.get('rank', 999)
                if current_rank > 30:
                    continue
                titles_this_year = [w for w in player.get('tournament_wins', [])
                                   if w.get('year') == self.current_year]
                if len(titles_this_year) == 0:
                    if random.random() < 0.04:
                        tweets.append({
                            'type': 'tweet',
                            'title': '🧊 COLD STREAK',
                            'content': random.choice([
                                f"Week {self.current_week} and still no title for #{current_rank} {player['name']} in {self.current_year}. The drought continues.",
                                f"{player['name']} is ranked #{current_rank} but has zero titles this year. Is something off, or just unlucky?",
                                f"Titleless in {self.current_year}: {player['name']} (#{current_rank}) still searching for silverware. Time is running out.",
                                f"For someone ranked #{current_rank}, going titleless this deep into the season is unusual. {player['name']} needs a breakthrough.",
                            ])
                        })

        # ── 27. Youngest in top X ──
        if random.random() < 0.10:
            active_ranked = [p for p in self.players
                            if not p.get('retired', False) and p.get('rank', 999) <= 150]
            if active_ranked:
                youngest = min(active_ranked, key=lambda p: (p.get('age', 99), p.get('rank', 999)))
                age = youngest.get('age', 99)
                rank = youngest.get('rank', 999)
                if age <= 20:
                    if rank <= 10:
                        tier = "top 10"
                    elif rank <= 20:
                        tier = "top 20"
                    elif rank <= 50:
                        tier = "top 50"
                    elif rank <= 100:
                        tier = "top 100"
                    else:
                        tier = "top 150"
                    tweets.append({
                        'type': 'tweet',
                        'title': '👶 YOUNGEST ON TOUR',
                        'content': random.choice([
                            f"At just {age}, {youngest['name']} is the youngest player in the {tier}. The future of tennis, right here.",
                            f"Fun fact: {youngest['name']} ({age}) is the youngest {tier} player on tour right now. Ranked #{rank}.",
                            f"Nobody in the {tier} is younger than {youngest['name']}. At {age}, he's got the whole tennis world ahead of him.",
                            f"{youngest['name']}, {age} years old, #{rank} in the world. Youngest player in the {tier}. Let that sink in.",
                        ])
                    })

        # ── 28. Fanboy tweet ──
        if random.random() < 0.20:
            candidates = [p for p in self.players
                         if not p.get('retired', False) and p.get('rank', 999) <= 80
                         and p.get('archetype')]
            if candidates:
                player = random.choice(candidates)
                archetype = player.get('archetype', 'player')
                arch_key = player.get('archetype_key', [])
                skills = player.get('skills', {})
                # Pick the best skill from their archetype key skills
                best_skill = None
                best_val = 0
                for sk in arch_key:
                    val = skills.get(sk, 0)
                    if val > best_val:
                        best_skill = sk
                        best_val = val
                if not best_skill:
                    # Fallback to their overall best skill
                    if skills:
                        best_skill = max(skills, key=skills.get)
                        best_val = skills[best_skill]

                if best_skill and best_val > 0:
                    rank = player.get('rank', '?')
                    age = player.get('age', '?')

                    # Skill flavor descriptions
                    skill_flavors = {
                        'serve': ['serving', 'serve', 'delivery'],
                        'forehand': ['forehand', 'forehand technique', 'forehand power'],
                        'backhand': ['backhand', 'backhand precision', 'two-hander' if random.random() < 0.5 else 'backhand'],
                        'speed': ['movement', 'court coverage', 'footwork'],
                        'stamina': ['endurance', 'fitness', 'stamina'],
                        'straight': ['down-the-line game', 'straight shots', 'line-painting'],
                        'cross': ['cross-court game', 'angles', 'cross-court winners'],
                        'dropshot': ['touch', 'dropshots', 'feel at the net'],
                        'volley': ['net game', 'volleys', 'hands at the net'],
                    }
                    skill_word = random.choice(skill_flavors.get(best_skill, [best_skill]))

                    fan_tweets = [
                        f"{player['name']} is playing so well recently. His style of {archetype.lower()} is so fun to watch and his {skill_word} is absolutely elite right now! 🎾🔥",
                        f"I don't care what anyone says, {player['name']} is the most entertaining player on tour. That {skill_word}?? Unreal. Pure {archetype.lower()} magic ✨",
                        f"Just watched {player['name']} highlights and WOW. The {skill_word} is on another level. {archetype} at its finest 🙌",
                        f"Hot take: {player['name']} is underrated. #{rank} doesn't do him justice. The way he plays as a {archetype.lower()} with that {skill_word}... chef's kiss 👨‍🍳",
                        f"My guy {player['name']} making the {archetype.lower()} style look so smooth. That {skill_word} is a thing of beauty 😍",
                        f"Been watching {player['name']} since day one. {age} years old, ranked #{rank}, and that {skill_word} keeps getting better. {archetype} GOAT don't @ me 🐐",
                        f"If you're not watching {player['name']} play, you're missing out. The {archetype.lower()} playstyle combined with his {skill_word}... poetry in motion 📝",
                        f"Unpopular opinion: {player['name']}'s {skill_word} is the best on tour and it's not even close. {archetype} built different 💪",
                    ]
                    tweets.append({
                        'type': 'tweet',
                        'title': '🗨️ FAN ZONE',
                        'content': random.choice(fan_tweets)
                    })

        # Shuffle and limit to keep the feed interesting but not overwhelming
        random.shuffle(tweets)
        if len(tweets) > 12:
            # Always keep priority tweets (new #1, top 10 breakthrough, upset)
            priority_titles = {'👑 NEW WORLD #1', '🔟 TOP 10 BREAKTHROUGH', '😱 UPSET SPECIAL',
                              '⚔️ CLASH OF GENERATIONS', '🚀 BIGGEST MOVER', '🌟 FUTURE STAR',
                              '🔎 SCOUTING REPORT', '🏆 DYNASTY WATCH', '⚠️ EARLY REGRESSION'}
            priority = [t for t in tweets if t['title'] in priority_titles]
            others = [t for t in tweets if t['title'] not in priority_titles]
            random.shuffle(others)
            tweets = priority + others
            tweets = tweets[:12]

        return tweets
    
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
