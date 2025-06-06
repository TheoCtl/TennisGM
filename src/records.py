import math
import json

class RecordsManager:
    def __init__(self, scheduler):
        self.scheduler = scheduler

    def update_all_records(self):
        self.update_mawn()
        self.update_most_gs_wins()
        self.update_most_m1000_wins()
        self.update_most_t_wins()
        self.update_weeks_at_top_records()
        def record_sort_key(rec):
            if rec["type"] == "most_matches_won":
                return (0, "")
            elif rec["type"].startswith("most_matches_won_"):
                return (1, rec["type"])
            elif rec["type"] == "most_t_wins":
                return (2, "")
            elif rec["type"] == "most_gs_wins":
                return (3, "")
            elif rec["type"] == "most_m1000_wins":
                return (4, "")
            elif rec["type"] == "most_weeks_at_1":
                return (5, "")
            elif rec["type"] == "most_weeks_in_16":
                return (6, "")
            return (99, rec["type"])
        self.scheduler.records.sort(key=record_sort_key)

    def update_most_t_wins(self):
        # Gather all players (active + HOF)
        all_players = self.scheduler.players + self.scheduler.hall_of_fame
        active_ids = {p['id'] for p in self.scheduler.players}
        t_counts = []
        for player in all_players:
            t_wins = sum(1 for win in player.get('tournament_wins', []))
            is_retired = player.get('id') not in active_ids
            display_name = player["name"] + (" (R)" if is_retired else "")
            t_counts.append({"name": display_name, "t_wins": t_wins})
        # Sort and keep top 10
        top10 = sorted(t_counts, key=lambda x: -x["t_wins"])[:10]
        # Update or create the record object
        record_obj = {
            "type": "most_t_wins",
            "title": "Most Tournament Wins",
            "top10": top10
        }
        # Replace or add in scheduler.records
        found = False
        for i, rec in enumerate(self.scheduler.records):
            if rec.get("type") == "most_t_wins":
                self.scheduler.records[i] = record_obj
                found = True
                break
        if not found:
            self.scheduler.records.append(record_obj)

    def update_most_m1000_wins(self):
        # Gather all players (active + HOF)
        all_players = self.scheduler.players + self.scheduler.hall_of_fame
        active_ids = {p['id'] for p in self.scheduler.players}
        m_counts = []
        for player in all_players:
            m_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "Masters 1000")
            is_retired = player.get('id') not in active_ids
            display_name = player["name"] + (" (R)" if is_retired else "")
            m_counts.append({"name": display_name, "m1000_wins": m_wins})
        # Sort and keep top 10
        top10 = sorted(m_counts, key=lambda x: -x["m1000_wins"])[:10]
        # Update or create the record object
        record_obj = {
            "type": "most_m1000_wins",
            "title": "Most Masters 1000 Wins",
            "top10": top10
        }
        # Replace or add in scheduler.records
        found = False
        for i, rec in enumerate(self.scheduler.records):
            if rec.get("type") == "most_m1000_wins":
                self.scheduler.records[i] = record_obj
                found = True
                break
        if not found:
            self.scheduler.records.append(record_obj)

    def update_weeks_at_top_records(self):
        all_players = self.scheduler.players + self.scheduler.hall_of_fame
        active_ids = {p['id'] for p in self.scheduler.players}

        # Most weeks at #1
        w1_list = []
        for player in all_players:
            w1 = player.get('w1', 0)
            is_retired = player.get('id') not in active_ids
            display_name = player["name"] + (" (R)" if is_retired else "")
            w1_list.append({"name": display_name, "weeks": w1})
        top10_w1 = sorted(w1_list, key=lambda x: -x["weeks"])[:10]
        record_w1 = {
            "type": "most_weeks_at_1",
            "title": "Most Weeks at #1",
            "top10": top10_w1
        }

        # Most weeks in top 16
        w16_list = []
        for player in all_players:
            w16 = player.get('w16', 0)
            is_retired = player.get('id') not in active_ids
            display_name = player["name"] + (" (R)" if is_retired else "")
            w16_list.append({"name": display_name, "weeks": w16})
        top10_w16 = sorted(w16_list, key=lambda x: -x["weeks"])[:10]
        record_w16 = {
            "type": "most_weeks_in_16",
            "title": "Most Weeks in Top 10",
            "top10": top10_w16
        }

        # Add or update records
        def upsert_record(record):
            found = False
            for i, rec in enumerate(self.scheduler.records):
                if rec.get("type") == record["type"]:
                    self.scheduler.records[i] = record
                    found = True
                    break
            if not found:
                self.scheduler.records.append(record)

        upsert_record(record_w1)
        upsert_record(record_w16)

    def update_most_gs_wins(self):
        # Gather all players (active + HOF)
        all_players = self.scheduler.players + self.scheduler.hall_of_fame
        active_ids = {p['id'] for p in self.scheduler.players}
        gs_counts = []
        for player in all_players:
            gs_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "Grand Slam")
            is_retired = player.get('id') not in active_ids
            display_name = player["name"] + (" (R)" if is_retired else "")
            gs_counts.append({"name": display_name, "gs_wins": gs_wins})
        # Sort and keep top 10
        top10 = sorted(gs_counts, key=lambda x: -x["gs_wins"])[:10]
        # Update or create the record object
        record_obj = {
            "type": "most_gs_wins",
            "title": "Most Grand Slam Wins",
            "top10": top10
        }
        # Replace or add in scheduler.records
        found = False
        for i, rec in enumerate(self.scheduler.records):
            if rec.get("type") == "most_gs_wins":
                self.scheduler.records[i] = record_obj
                found = True
                break
        if not found:
            self.scheduler.records.append(record_obj)
      
    def update_mawn_last_week(self):
        # Ensure every player (active and HOF) has a mawn list
        for player in self.scheduler.players + self.scheduler.hall_of_fame:
            if 'mawn' not in player or not isinstance(player['mawn'], list) or len(player['mawn']) != 5:
                player['mawn'] = [0, 0, 0, 0, 0]

        surface_map = {'clay': 0, 'grass': 1, 'hard': 2, 'indoor': 3, 'neutral': 4}
        last_week = self.scheduler.current_week - 1
        last_year = self.scheduler.current_year
        if last_week < 1:
            last_week = 52
            last_year -= 1

        for player in self.scheduler.players + self.scheduler.hall_of_fame:
            for entry in player.get('tournament_history', []):
                if entry.get('week') == last_week and entry.get('year') == last_year:
                    tname = entry.get('name')
                    #tournament = next(
                    #    (t for t in self.scheduler.tournaments
                    #    if t['name'] == tname and t.get('year') == last_year and t.get('week') == entry.get('week')),
                    #    None
                    #)
                    #with open("debug_tournament_log.txt", "a", encoding="utf-8") as debug_file:
                    #    debug_file.write(
                    #        f"Player: {player.get('name')} | Entry: {entry} | Tournament found: {json.dumps(tournament) if tournament else 'None'}\n"
                    #    )
                    #if tournament:
                    surface = entry.get('surface', 'neutral')
                    #else:
                    #    surface = 'neutral'
                    idx = surface_map.get(surface, 4)
                    matches_won = max(0, entry.get('round', 0))
                    player['mawn'][idx] += matches_won
            
    def update_mawn(self):
        # Ensure every player (active and HOF) has a mawn list
        for player in self.scheduler.players + self.scheduler.hall_of_fame:
            if 'mawn' not in player or not isinstance(player['mawn'], list) or len(player['mawn']) != 5:
                player['mawn'] = [0, 0, 0, 0, 0]

        all_players = self.scheduler.players + self.scheduler.hall_of_fame
        active_ids = {p['id'] for p in self.scheduler.players}

        # Most Matches Won (total)
        total_mawn = []
        for player in all_players:
            total = sum(player['mawn'])
            is_retired = player.get('id') not in active_ids
            display_name = player["name"] + (" (R)" if is_retired else "")
            total_mawn.append({"name": display_name, "matches_won": total})
        top10_total = sorted(total_mawn, key=lambda x: -x["matches_won"])[:10]
        record_total = {
            "type": "most_matches_won",
            "title": "Most Matches Won",
            "top10": top10_total
        }

        # Most Matches Won (surface)
        surfaces = ['clay', 'grass', 'hard', 'indoor']
        for idx, surf in enumerate(surfaces):
            surf_mawn = []
            for player in all_players:
                is_retired = player.get('id') not in active_ids
                display_name = player["name"] + (" (R)" if is_retired else "")
                surf_mawn.append({"name": display_name, "matches_won": player['mawn'][idx]})
            top10_surf = sorted(surf_mawn, key=lambda x: -x["matches_won"])[:10]
            record_surf = {
                "type": f"most_matches_won_{surf}",
                "title": f" MMW ({surf.capitalize()})",
                "top10": top10_surf
            }
            # Replace or add in scheduler.records
            found = False
            for i, rec in enumerate(self.scheduler.records):
                if rec.get("type") == record_surf["type"]:
                    self.scheduler.records[i] = record_surf
                    found = True
                    break
            if not found:
                self.scheduler.records.append(record_surf)

        # Add/update total matches won record
        found = False
        for i, rec in enumerate(self.scheduler.records):
            if rec.get("type") == "most_matches_won":
                self.scheduler.records[i] = record_total
                found = True
                break
        if not found:
            self.scheduler.records.append(record_total)