import tkinter as tk
from schedule import TournamentScheduler
import collections
import sys
from io import StringIO
import functools

PRESTIGE_ORDER = ["Special", "Grand Slam", "Masters 1000", "ATP 500", "ATP 250", "Challenger 125", "Challenger 100", "Challenger 75"]

class TennisGMApp:
    def __init__(self, root):
        self.root = root
        self.scheduler = TournamentScheduler()
        self.menu_options = [
            "News Feed", "Tournaments", "ATP Rankings", "Hall of Fame", "Achievements", "Advance to next week", "Exit"
        ]
        self.build_main_menu()

    def build_main_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(
            self.root,
            text=f"Year {self.scheduler.current_year}, Week {self.scheduler.current_week}",
            font=("Arial", 16)
        ).pack(pady=10)
        # Build menu options dynamically
        menu_options = [
            "News Feed", "Tournaments", "ATP Rankings", "Hall of Fame", "Achievements", "History"
        ]
        # Check if all tournaments for the current week are completed
        current_tournaments = self.scheduler.get_current_week_tournaments()
        incomplete_tournaments = [t for t in current_tournaments if t['winner_id'] is None]
        if len(incomplete_tournaments) == 0:
            menu_options.append("Advance to next week")
        menu_options.append("Save & Quit")
        self.menu_options = menu_options  # Update for handle_menu
        for option in menu_options:
            btn = tk.Button(
                self.root,
                text=option,
                width=30,
                font=("Arial", 12),
                command=lambda opt=option: self.handle_menu(opt)
            )
            btn.pack(pady=4)

    def handle_menu(self, option):
        if option == "Advance to next week":
            self.scheduler.advance_week()
            self.build_main_menu()
        elif option == "News Feed":
            self.show_news_feed()
        elif option == "ATP Rankings":
            self.show_rankings()
        elif option == "Hall of Fame":
            self.show_hall_of_fame()
        elif option == "Achievements":
            self.show_achievements()
        elif option == "Tournaments":
            self.show_tournaments()
        elif option == "History":
            self.show_history()
        elif option == "Save & Quit":
            self.scheduler.save_game()  # Save before quitting
            self.root.quit()

    def show_news_feed(self):
        # Clear the main window
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="News Feed", font=("Arial", 16)).pack(pady=10)
        news = self.scheduler.news_feed if hasattr(self.scheduler, 'news_feed') else []
        if not news:
            tk.Label(self.root, text="No news yet.", font=("Arial", 12)).pack(pady=10)
        else:
            # Use a scrollable Text widget for long news feeds
            frame = tk.Frame(self.root)
            frame.pack(fill="both", expand=True)
            text = tk.Text(frame, wrap="word", font=("Arial", 11), height=20)
            text.pack(side="left", fill="both", expand=True)
            for line in news:
                text.insert("end", line + "\n")
            text.config(state="disabled")
            scrollbar = tk.Scrollbar(frame, command=text.yview)
            scrollbar.pack(side="right", fill="y")
            text.config(yscrollcommand=scrollbar.set)
        # Back button
        tk.Button(self.root, text="Back to Main Menu", command=self.build_main_menu, font=("Arial", 12)).pack(pady=10)

    def show_rankings(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="ATP Rankings", font=("Arial", 16)).pack(pady=10)

        search_var = tk.StringVar()
        def update_list(*args):
            query = search_var.get().lower()
            for widget in scroll_frame.winfo_children():
                widget.destroy()
            filtered_players = [
                (player, points) for player, points in ranked_players
                if query in player['name'].lower()
            ]
            for idx, (player, points) in enumerate(filtered_players, 1):
                btn = tk.Button(
                    scroll_frame,
                    text=f"{idx}. {player['name']} - {points} pts",
                    anchor="w",
                    width=40,
                    font=("Arial", 11),
                    command=lambda p=player: self.show_player_details(p)
                )
                btn.pack(fill="x", padx=2, pady=1)

        search_entry = tk.Entry(self.root, textvariable=search_var, font=("Arial", 12), width=40)
        search_entry.pack(pady=4)
        search_var.trace_add("write", update_list)

        ranked_players = self.scheduler.ranking_system.get_ranked_players(
            self.scheduler.players,
            self.scheduler.current_date
        )
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # Initial population
        for idx, (player, points) in enumerate(ranked_players, 1):
            btn = tk.Button(
                scroll_frame,
                text=f"{idx}. {player['name']} - {points} pts",
                anchor="w",
                width=40,
                font=("Arial", 11),
                command=lambda p=player: self.show_player_details(p)
            )
            btn.pack(fill="x", padx=2, pady=1)

        tk.Button(self.root, text="Back to Main Menu", command=self.build_main_menu, font=("Arial", 12)).pack(pady=10)

    def show_player_details(self, player):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text=f"{player['name']}", font=("Arial", 16)).pack(pady=10)
        details = [
            f"Rank: {player.get('rank', 'N/A')}",
            f"Highest Ranking: {player.get('highest_ranking', 'N/A')}",
            f"Age: {player.get('age', 'N/A')}, {player.get('hand', 'N/A')}-handed",
            f"Favorite surface: {player.get('favorite_surface', 'N/A')}",
            "",
            "Skills:",
            *(f"  {skill.capitalize()}: {player['skills'].get(skill, 'N/A')}" for skill in player['skills']),
            "",
            f"Total titles: {sum(1 for win in player.get('tournament_wins', []))}",
            f"Grand Slam titles: {sum(1 for win in player.get('tournament_wins', []) if win['category'] == 'Grand Slam')}",
            f"Total Matches Won: {sum(player.get('mawn', [0,0,0,0,0]))}",
            f"Weeks at #1: {player.get('w1', 0)}",
            f"Weeks in Top 10: {player.get('w16', 0)}",
        ]
        for line in details:
            tk.Label(self.root, text=line, anchor="w", font=("Arial", 11)).pack(fill="x")
        tk.Button(self.root, text="Show Tournament Wins", command=lambda: self.show_tournament_wins(player), font=("Arial", 12)).pack(pady=6)
        tk.Button(self.root, text="Back to Rankings", command=self.show_rankings, font=("Arial", 12)).pack(pady=2)
        tk.Button(self.root, text="Back to Main Menu", command=self.build_main_menu, font=("Arial", 12)).pack(pady=2)

    def show_tournament_wins(self, player, back_command=None):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text=f"{player['name']} - Tournament Wins", font=("Arial", 16)).pack(pady=10)
        wins = player.get('tournament_wins', [])
        wins_by_category = collections.defaultdict(lambda: collections.defaultdict(int))
        for win in wins:
            wins_by_category[win['category']][win['name']] += 1

        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        any_win = False
        for category in PRESTIGE_ORDER:
            if category in wins_by_category:
                total_in_category = sum(wins_by_category[category].values())
                tk.Label(scroll_frame, text=f"{category} ({total_in_category})", font=("Arial", 12, "underline")).pack(anchor="w", pady=(8,2))
                for tname, count in sorted(wins_by_category[category].items()):
                    tk.Label(scroll_frame, text=f"- {count}x {tname}", font=("Arial", 11)).pack(anchor="w")
                    any_win = True
        if not any_win:
            tk.Label(scroll_frame, text="No tournament wins yet", font=("Arial", 12)).pack(pady=10)
        # Always show the correct back button
        if back_command:
            tk.Button(self.root, text="Back to Player Details", command=back_command, font=("Arial", 12)).pack(pady=10)
        else:
            tk.Button(self.root, text="Back to Player Details", command=lambda: self.show_player_details(player), font=("Arial", 12)).pack(pady=10)

    def show_hall_of_fame(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="Hall of Fame", font=("Arial", 16)).pack(pady=10)

        search_var = tk.StringVar()
        def update_list(*args):
            query = search_var.get().lower()
            for widget in scroll_frame.winfo_children():
                widget.destroy()
            filtered_hof = [
                p for p in hof_members
                if query in p['name'].lower()
            ]
            for idx, player in enumerate(filtered_hof, 1):
                btn = tk.Button(
                    scroll_frame,
                    text=f"{idx}. {player['name']}: {player['hof_points']} HOF, {len(player.get('tournament_wins', []))} wins",
                    anchor="w",
                    width=50,
                    font=("Arial", 11),
                    command=lambda p=player: self.show_hof_player_details(p)
                )
                btn.pack(fill="x", padx=2, pady=1)

        search_entry = tk.Entry(self.root, textvariable=search_var, font=("Arial", 12), width=40)
        search_entry.pack(pady=4)
        search_var.trace_add("write", update_list)

        # Calculate hof_points for each player
        for player in self.scheduler.hall_of_fame:
            player['hof_points'] = 0
            for win in player.get('tournament_wins', []):
                if win['category'] == 'Special':
                    player['hof_points'] += 50
                elif win.get('name') == "ATP Finals":
                    player['hof_points'] += 30
                elif win.get('name') == "Nextgen Finals":
                    player['hof_points'] += 5
                elif win['category'] == "Grand Slam":
                    player['hof_points'] += 40
                elif win['category'] == "Masters 1000":
                    player['hof_points'] += 20
                elif win['category'] == "ATP 500":
                    player['hof_points'] += 10
                elif win['category'] == "ATP 250":
                    player['hof_points'] += 5
                elif win['category'].startswith("Challenger"):
                    player['hof_points'] += 1

        hof_members = sorted(
            self.scheduler.hall_of_fame,
            key=lambda x: (-x['hof_points'], len(x.get('tournament_wins', [])))
        )[:100]

        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # Initial population
        for idx, player in enumerate(hof_members, 1):
            btn = tk.Button(
                scroll_frame,
                text=f"{idx}. {player['name']}: {player['hof_points']} HOF, {len(player.get('tournament_wins', []))} wins",
                anchor="w",
                width=50,
                font=("Arial", 11),
                command=lambda p=player: self.show_hof_player_details(p)
            )
            btn.pack(fill="x", padx=2, pady=1)

        tk.Button(self.root, text="Back to Main Menu", command=self.build_main_menu, font=("Arial", 12)).pack(pady=10)

    def show_hof_player_details(self, player):
        for widget in self.root.winfo_children():
            widget.destroy()
        show_tournaments = getattr(self, "_show_tournaments", False)
        tk.Label(self.root, text=f"{player['name']}", font=("Arial", 16)).pack(pady=10)
        if not show_tournaments:
            w1 = player.get('w1')
            w16 = player.get('w16')
            t_wins = sum(1 for win in player.get('tournament_wins', []))
            m1000_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "Masters 1000")
            gs_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "Grand Slam")
            mawn = player.get('mawn', [0,0,0,0,0])
            details = [
                f"Highest Ranking: {player.get('highest_ranking', 'N/A')}",
                "",
                "Achievements:",
                f"  Total titles: {t_wins}",
                f"  Grand Slam titles: {gs_wins}",
                f"  Masters 1000 titles: {m1000_wins}",
                f"  Total Matches Won (clay, grass, hard, indoor): {sum(mawn)} ({mawn[0]}, {mawn[1]}, {mawn[2]}, {mawn[3]})",
                f"  Weeks at #1: {w1}w",
                f"  Weeks in Top 10: {w16}w",
            ]
            for line in details:
                tk.Label(self.root, text=line, anchor="w", font=("Arial", 11)).pack(fill="x")
            tk.Button(self.root, text="Show Tournament Wins", command=lambda: self._toggle_hof_tournaments(player, True), font=("Arial", 12)).pack(pady=6)
        else:
            numwin = len(player.get('tournament_wins'))
            hofpoints = player.get('hof_points')
            header = f"WINS ({numwin} W, {hofpoints} HOF)"
            tk.Label(self.root, text=header, font=("Arial", 12, "bold")).pack(pady=6)
            self.show_tournament_wins(player, back_command=lambda: self._toggle_hof_tournaments(player, False))
        tk.Button(self.root, text="Back to Hall of Fame", command=self.show_hall_of_fame, font=("Arial", 12)).pack(pady=2)
        tk.Button(self.root, text="Back to Main Menu", command=self.build_main_menu, font=("Arial", 12)).pack(pady=2)

    def _toggle_hof_tournaments(self, player, show):
        self._show_tournaments = show
        self.show_hof_player_details(player)
        
    def show_achievements(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="All-Time Achievements", font=("Arial", 16)).pack(pady=10)

        achievements = self.scheduler.records
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        for idx, record in enumerate(achievements):
            title = record.get("title", record.get("type", "Unknown"))
            btn = tk.Button(
                scroll_frame,
                text=title,
                anchor="w",
                width=40,
                font=("Arial", 12),
                command=lambda r=record: self.show_record_details(r)
            )
            btn.pack(fill="x", padx=2, pady=1)

        tk.Button(self.root, text="Back to Main Menu", command=self.build_main_menu, font=("Arial", 12)).pack(pady=10)

    def show_record_details(self, record):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text=record.get("title", "Record Details"), font=("Arial", 16)).pack(pady=10)
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # Display top 10 for the record
        if record["type"] == "most_t_wins":
            tk.Label(scroll_frame, text="Top 10 Tournament Winners:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(4,2))
            for idx, entry in enumerate(record["top10"]):
                tk.Label(scroll_frame, text=f"{idx+1}. {entry['name']} - {entry['t_wins']} Tournaments", font=("Arial", 11)).pack(anchor="w")
        elif record["type"] == "most_gs_wins":
            tk.Label(scroll_frame, text="Top 10 Grand Slam Winners:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(4,2))
            for idx, entry in enumerate(record["top10"]):
                tk.Label(scroll_frame, text=f"{idx+1}. {entry['name']} - {entry['gs_wins']} GS", font=("Arial", 11)).pack(anchor="w")
        elif record["type"] == "most_m1000_wins":
            tk.Label(scroll_frame, text="Top 10 Masters 1000 Winners:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(4,2))
            for idx, entry in enumerate(record["top10"]):
                tk.Label(scroll_frame, text=f"{idx+1}. {entry['name']} - {entry['m1000_wins']} Masters", font=("Arial", 11)).pack(anchor="w")
        elif record["type"] == "most_matches_won":
            tk.Label(scroll_frame, text="Top 10 Total Matches Won:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(4,2))
            for idx, entry in enumerate(record["top10"]):
                tk.Label(scroll_frame, text=f"{idx+1}. {entry['name']} - {entry['matches_won']} matches", font=("Arial", 11)).pack(anchor="w")
        elif record["type"].startswith("most_matches_won_"):
            surface = record["type"].replace("most_matches_won_", "").capitalize()
            tk.Label(scroll_frame, text=f"Top 10 Matches Won on {surface}:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(4,2))
            for idx, entry in enumerate(record["top10"]):
                tk.Label(scroll_frame, text=f"{idx+1}. {entry['name']} - {entry['matches_won']} matches", font=("Arial", 11)).pack(anchor="w")
        elif record["type"] == "most_weeks_at_1":
            tk.Label(scroll_frame, text="Top 10 Most Weeks at #1:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(4,2))
            for idx, entry in enumerate(record["top10"]):
                tk.Label(scroll_frame, text=f"{idx+1}. {entry['name']} - {entry['weeks']} weeks", font=("Arial", 11)).pack(anchor="w")
        elif record["type"] == "most_weeks_in_16":
            tk.Label(scroll_frame, text="Top 10 Most Weeks in Top 10:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(4,2))
            for idx, entry in enumerate(record["top10"]):
                tk.Label(scroll_frame, text=f"{idx+1}. {entry['name']} - {entry['weeks']} weeks", font=("Arial", 11)).pack(anchor="w")
        else:
            tk.Label(scroll_frame, text="Top 10:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(4,2))
            for idx, entry in enumerate(record.get("top10", [])):
                tk.Label(scroll_frame, text=f"{idx+1}. {entry.get('name', 'Unknown')}", font=("Arial", 11)).pack(anchor="w")

        tk.Button(self.root, text="Back to Achievements", command=self.show_achievements, font=("Arial", 12)).pack(pady=10)
        tk.Button(self.root, text="Back to Main Menu", command=self.build_main_menu, font=("Arial", 12)).pack(pady=2)

    def show_tournaments(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="Current Week Tournaments", font=("Arial", 16)).pack(pady=10)
        tournaments = self.scheduler.get_current_week_tournaments()
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        for idx, t in enumerate(tournaments):
            row_frame = tk.Frame(scroll_frame)
            row_frame.pack(fill="x", padx=2, pady=2)
            btn_manage = tk.Button(
                row_frame,
                text=f"{t['name']} ({t['category']}, {t['surface']})",
                anchor="w",
                width=40,
                font=("Arial", 12),
                command=lambda tournament=t: self.show_tournament_bracket(tournament)
            )
            btn_manage.pack(side="left", padx=2)
            btn_simulate = tk.Button(
                row_frame,
                text="Simulate Entire Tournament",
                font=("Arial", 11),
                command=functools.partial(self.simulate_entire_tournament_selected, [t])
            )
            btn_simulate.pack(side="left", padx=2)

        tk.Button(self.root, text="Back to Main Menu", command=self.build_main_menu, font=("Arial", 12)).pack(pady=10)

    def manage_tournament(self, tournament):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text=f"Managing Tournament: {tournament['name']} ({tournament['category']}, {tournament['surface']})", font=("Arial", 16)).pack(pady=10)

        # Ensure players are assigned
        if 'participants' not in tournament:
            self.scheduler.assign_players_to_tournaments()
        # Generate bracket if not already generated
        if 'bracket' not in tournament:
            self.scheduler.generate_bracket(tournament['id'])

        show_previous_rounds = getattr(self, "_show_previous_rounds", False)
        btn_toggle = tk.Button(self.root, text="Show Previous Rounds" if not show_previous_rounds else "Hide Previous Rounds",
                               command=lambda: self._toggle_previous_rounds(tournament, not show_previous_rounds), font=("Arial", 11))
        btn_toggle.pack(pady=4)

        # Previous rounds
        if show_previous_rounds and tournament['current_round'] > 0:
            for r in range(tournament['current_round']):
                tk.Label(self.root, text=f"Round {r + 1}:", font=("Arial", 12, "underline")).pack(anchor="w")
                for m in tournament['bracket'][r]:
                    def get_name_rank(pid):
                        player = next((p for p in self.scheduler.players if p['id'] == pid), None)
                        if player:
                            return f"{player['name']} ({player.get('rank', 'N/A')})"
                        return "BYE"

                    p1 = get_name_rank(m[0])
                    p2 = get_name_rank(m[1])
                    winner = get_name_rank(m[2]) if len(m) > 2 and m[2] is not None else None
                    final_score = m[3] if len(m) > 3 else "N/A"
                    if winner:
                        tk.Label(self.root, text=f"  {p1} vs {p2} -> {winner} | Score: {final_score}", font=("Arial", 10)).pack(anchor="w")
                    else:
                        tk.Label(self.root, text=f"  {p1} vs {p2}", font=("Arial", 10)).pack(anchor="w")

        tk.Label(self.root, text=f"Round {tournament['current_round'] + 1} Matches:", font=("Arial", 13, "bold")).pack(anchor="w", pady=(8,2))
        matches = self.scheduler.get_current_matches(tournament['id'])
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        for idx, match in enumerate(matches):
            p1 = f"{match['player1']['name']} ({match['player1']['rank']})" if match['player1'] else "BYE"
            p2 = f"{match['player2']['name']} ({match['player2']['rank']})" if match['player2'] else "BYE"
            status = ""
            if match['winner']:
                final_score = tournament['active_matches'][idx][3] if len(tournament['active_matches'][idx]) == 4 else "N/A"
                status = f" -> {match['winner']['name']} ({match['winner']['rank']}) | Score: {final_score}"
            row_frame = tk.Frame(scroll_frame)
            row_frame.pack(fill="x", padx=2, pady=2)
            tk.Label(row_frame, text=f"{idx + 1}. {p1} vs {p2}{status}", font=("Arial", 11), anchor="w", width=80, wraplength=800).pack(fill="x")
            btns_frame = tk.Frame(row_frame)
            btns_frame.pack(fill="x")
            btn_sim = tk.Button(btns_frame, text="Simulate", font=("Arial", 10),
                                command=lambda i=idx: self.simulate_match_in_tournament(tournament, i))
            btn_sim.pack(side="left", padx=2)
            btn_watch = tk.Button(btns_frame, text="Watch", font=("Arial", 10),
                                  command=lambda i=idx: self.watch_match_in_tournament(tournament, i))
            btn_watch.pack(side="left", padx=2)

        tk.Button(self.root, text="Back to Tournaments", command=self.show_tournaments, font=("Arial", 12)).pack(pady=10)
        tk.Button(self.root, text="Back to Main Menu", command=self.build_main_menu, font=("Arial", 12)).pack(pady=2)

    def _toggle_previous_rounds(self, tournament, show):
        self._show_previous_rounds = show
        self.manage_tournament(tournament)

    def simulate_match_in_tournament(self, tournament, match_idx):
        match = self.scheduler.get_current_matches(tournament['id'])[match_idx]
        if match['winner']:
            self.manage_tournament(tournament)
            return
        winner_id = self.scheduler.simulate_through_match(tournament['id'], match_idx)
        winner = next((p for p in self.scheduler.players if p['id'] == winner_id), None)
        self.manage_tournament(tournament)

    def watch_match_in_tournament(self, tournament, match_idx):
        match = self.scheduler.get_current_matches(tournament['id'])[match_idx]
        if match['winner']:
            self.manage_tournament(tournament)
            return
        # Redirect print statements to a buffer
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        winner_id, match_log = self.scheduler.simulate_through_match(tournament['id'], match_idx)
        sys.stdout = old_stdout
        output = mystdout.getvalue()
        screens = output.split("\n\n\na")
        self.display_simple_match_log(match_log, tournament)

    def display_simple_match_log(self, match_log, tournament):
        idx = 0
        def show_screen(i):
            for widget in self.root.winfo_children():
                widget.destroy()
            tk.Label(self.root, text="Match Log", font=("Arial", 16), fg="black", bg="white").pack(pady=10)
            frame = tk.Frame(self.root, bg="white")
            frame.pack(fill="both", expand=True)
            text = tk.Text(frame, wrap="word", font=("Arial", 11), height=10, fg="black", bg="white")
            text.pack(side="left", fill="both", expand=True)
            # Show current log line
            text.insert("end", match_log[i] + "\n")
            # If the next line is a set or match win, show it too
            if i + 1 < len(match_log) and (
                "won the set" in match_log[i+1] or "wins the match" in match_log[i+1]
            ):
                text.insert("end", match_log[i+1] + "\n")
                next_idx = i + 2
            else:
                next_idx = i + 1
            text.config(state="disabled")
            scrollbar = tk.Scrollbar(frame, command=text.yview)
            scrollbar.pack(side="right", fill="y")
            text.config(yscrollcommand=scrollbar.set)
            if next_idx < len(match_log):
                tk.Button(self.root, text="Next play", font=("Arial", 12), fg="black", bg="white",
                          command=lambda: show_screen(next_idx)).pack(pady=10)
            else:
                tk.Button(self.root, text="Back", font=("Arial", 12), fg="black", bg="white",
                          command=lambda: self.show_tournament_bracket(tournament)).pack(pady=10)
        show_screen(idx)

    def simulate_entire_tournament_selected(self, tournaments):
        # If only one tournament, simulate it; otherwise, ask user to select which one
        if len(tournaments) == 1:
            tournament = tournaments[0]
        else:
            # For simplicity, simulate the first incomplete tournament
            tournament = next((t for t in tournaments if t['winner_id'] is None), None)
            if not tournament:
                return
        winner_id = self.scheduler.simulate_entire_tournament(tournament['id'])
        winner = next((p for p in self.scheduler.players if p['id'] == winner_id), None)
        msg = f"Tournament complete! Winner: {winner['name']}" if winner else "Tournament complete! (Winner unknown)"
        # Show a popup
        popup = tk.Toplevel(self.root)
        popup.title("Simulation Result")
        tk.Label(popup, text=msg, font=("Arial", 12)).pack(pady=10)
        tk.Button(popup, text="OK", command=lambda: [popup.destroy(), self.show_tournaments()], font=("Arial", 12)).pack(pady=6)

    def show_tournament_bracket(self, tournament):
        for widget in self.root.winfo_children():
            widget.destroy()
        # Top bar frame
        top_bar = tk.Frame(self.root, bg="white")
        top_bar.pack(fill="x", pady=6)
        # Left buttons
        left_btns = tk.Frame(top_bar, bg="white")
        left_btns.pack(side="left")
        tk.Button(left_btns, text="Back to Tournaments", command=self.show_tournaments, font=("Arial", 12), fg="black", bg="white").pack(side="left", padx=2)
        tk.Button(left_btns, text="Back to Main Menu", command=self.build_main_menu, font=("Arial", 12), fg="black", bg="white").pack(side="left", padx=2)
        # Tournament name (centered)
        tk.Label(top_bar, text=f"{tournament['name']} Bracket", font=("Arial", 16), fg="black", bg="white").pack(side="left", expand=True, padx=40)
        # Right button
        tk.Button(top_bar, text="Simulate Current Round", font=("Arial", 12), fg="black", bg="white",
                  command=lambda: self.simulate_current_round_bracket(tournament)).pack(side="right", padx=2)

        frame = tk.Frame(self.root, bg="white")
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame, bg="white", width=1300, height=1600, highlightthickness=0)
        vscroll = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        hscroll = tk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")
        hscroll.pack(side="bottom", fill="x")

        scroll_y = getattr(self, "_bracket_scroll_y", 0)
        scroll_x = getattr(self, "_bracket_scroll_x", 0)

        canvas.yview_moveto(scroll_y)
        canvas.xview_moveto(scroll_x)

        bracket = tournament.get('bracket', [])
        num_rounds = len(bracket)
        match_height = 40
        match_gap = 100  # More vertical spacing
        round_gap = 400  # More horizontal spacing
        y_offset = 40

        player_lookup = {p['id']: p for p in self.scheduler.players}
        def get_name_rank(pid):
            player = player_lookup.get(pid)
            if player:
                return f"{player['name']} ({player.get('rank', 'N/A')})"
            return "BYE"

        # Store button references for command binding
        button_refs = []

        # Draw each round
        match_positions = []  # List of lists: match_positions[round][match_idx] = y

        for r, round_matches in enumerate(bracket):
            x = 40 + r * round_gap
            round_y_positions = []
            for m_idx, m in enumerate(round_matches):
                # For round 0 (first round), use regular spacing
                if r == 0:
                    y = y_offset + m_idx * (match_height + match_gap)
                else:
                    prev_y1 = match_positions[r-1][m_idx*2]
                    prev_y2 = match_positions[r-1][m_idx*2+1]
                    y = (prev_y1 + prev_y2) // 2
                round_y_positions.append(y)

                p1_id, p2_id = m[0], m[1]
                winner_id = m[2] if len(m) > 2 else None
                score = m[3] if len(m) > 3 else ""
                p1 = get_name_rank(p1_id)
                p2 = get_name_rank(p2_id)

                # Parse score string into list of sets
                p1_sets, p2_sets = [], []
                set_winners = []
                if score:
                    sets = score.split(",")
                    for s in sets:
                        s = s.strip()
                        if "-" in s:
                            a, b = s.split("-")
                            a, b = int(a.strip()), int(b.strip())
                            p1_sets.append(a)
                            p2_sets.append(b)
                            if a > b:
                                set_winners.append(1)
                            elif b > a:
                                set_winners.append(2)
                            else:
                                set_winners.append(0)  # Tie (rare)

                box_color = "#f0f0f0"
                outline_color = "#888"
                rect_width = 300
                font_bold = ("Arial", 11, "bold")
                font_normal = ("Arial", 11)

                # Draw rectangles for players
                canvas.create_rectangle(x, y, x+rect_width, y+match_height, fill=box_color, outline=outline_color)
                canvas.create_rectangle(x, y+match_height+8, x+rect_width, y+2*match_height+8, fill=box_color, outline=outline_color)

                # Player names (left aligned)
                canvas.create_text(x+10, y+match_height//2, anchor="w", text=p1, fill="black", font=font_bold if winner_id == p1_id else font_normal)
                canvas.create_text(x+10, y+match_height+8+match_height//2, anchor="w", text=p2, fill="black", font=font_bold if winner_id == p2_id else font_normal)

                # Scores (right aligned, each set separately, bold for set winner)
                score_x = x+rect_width-10
                # Draw p1's scores (right aligned, reverse order)
                sx = score_x
                for idx, val in enumerate(reversed(p1_sets)):
                    set_idx = len(p1_sets) - 1 - idx
                    set_font = font_bold if set_winners and set_winners[set_idx] == 1 else font_normal
                    canvas.create_text(sx, y+match_height//2, anchor="e", text=str(val), fill="black", font=set_font)
                    sx -= 14 
                # Draw p2's scores (right aligned, reverse order)
                sx = score_x
                for idx, val in enumerate(reversed(p2_sets)):
                    set_idx = len(p2_sets) - 1 - idx
                    set_font = font_bold if set_winners and set_winners[set_idx] == 2 else font_normal
                    canvas.create_text(sx, y+match_height+8+match_height//2, anchor="e", text=str(val), fill="black", font=set_font)
                    sx -= 14

                if r == tournament['current_round']:
                    btn_sim = tk.Button(canvas, text="Simulate", font=("Arial", 10),
                                    command=functools.partial(self.simulate_match_in_bracket, tournament, m_idx))
                    btn_watch = tk.Button(canvas, text="Watch", font=("Arial", 10),
                                      command=functools.partial(self.watch_match_in_bracket, tournament, m_idx))
                    btn_window_sim = canvas.create_window(x+10, y+2*match_height+18, anchor="nw", window=btn_sim)
                    btn_window_watch = canvas.create_window(x+80, y+2*match_height+18, anchor="nw", window=btn_watch)
                    button_refs.append((btn_sim, btn_watch))
                    
            match_positions.append(round_y_positions)
            # Draw lines to next round
            if r > 0:
                prev_x = 40 + (r-1) * round_gap
                for m_idx, y in enumerate(round_y_positions):
                    # Each match in this round comes from two matches in previous round
                    prev_y1 = match_positions[r-1][m_idx*2]
                    prev_y2 = match_positions[r-1][m_idx*2+1]
                    # Draw line from center of previous match 1 to center of this match
                    canvas.create_line(prev_x + rect_width, prev_y1 + match_height, x, y + match_height, fill=outline_color, width=2)
                    # Draw line from center of previous match 2 to center of this match
                    canvas.create_line(prev_x + rect_width, prev_y2 + match_height, x, y + match_height, fill=outline_color, width=2)
                    # Add Simulate/Watch buttons for current round matches
            
        max_x = 40 + num_rounds * round_gap + rect_width + 100
        max_y = y_offset + (2 ** (num_rounds-1)) * (match_height + match_gap)
        canvas.config(scrollregion=(0, 0, max_x, max_y))

        canvas.yview_moveto(scroll_y)
        canvas.xview_moveto(scroll_x)

        # Mouse wheel for vertical scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        # Shift+Wheel for horizontal scroll
        def _on_shift_mousewheel(event):
            canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<Shift-MouseWheel>", _on_shift_mousewheel)

        def on_scroll(*args):
            self._bracket_scroll_y = canvas.yview()[0]
            self._bracket_scroll_x = canvas.xview()[0]
        canvas.config(
            yscrollcommand=lambda *args: [vscroll.set(*args), on_scroll(*args)],
            xscrollcommand=lambda *args: [hscroll.set(*args), on_scroll(*args)]
        )

    def simulate_current_round_bracket(self, tournament):
        self.scheduler.simulate_current_round(tournament['id'])
        self.show_tournament_bracket(tournament)

    def simulate_match_in_bracket(self, tournament, match_idx):
        match = self.scheduler.get_current_matches(tournament['id'])[match_idx]
        if match['winner']:
            self.show_tournament_bracket(tournament)
            return
        winner_id = self.scheduler.simulate_through_match(tournament['id'], match_idx)
        self.show_tournament_bracket(tournament)

    def watch_match_in_bracket(self, tournament, match_idx):
        match = self.scheduler.get_current_matches(tournament['id'])[match_idx]
        if match['winner']:
            self.show_tournament_bracket(tournament)
            return
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        winner_id, match_log = self.scheduler.simulate_through_match(tournament['id'], match_idx)
        sys.stdout = old_stdout
        output = mystdout.getvalue()
        screens = output.split("\n\n\na")
        self.display_simple_match_log(match_log, tournament)

    def display_match_log_bracket(self, screens, tournament):
        idx = 0
        def show_screen(i):
            for widget in self.root.winfo_children():
                widget.destroy()
            tk.Label(self.root, text="Match Log", font=("Arial", 16), fg="black", bg="white").pack(pady=10)
            frame = tk.Frame(self.root, bg="white")
            frame.pack(fill="both", expand=True)
            text = tk.Text(frame, wrap="word", font=("Arial", 11), height=20, fg="black", bg="white")
            text.pack(side="left", fill="both", expand=True)
            for line in screens[i].strip().split('\n'):
                text.insert("end", line + "\n")
            text.config(state="disabled")
            scrollbar = tk.Scrollbar(frame, command=text.yview)
            scrollbar.pack(side="right", fill="y")
            text.config(yscrollcommand=scrollbar.set)
            btn_next = tk.Button(self.root, text="Next", font=("Arial", 12), fg="black", bg="white",
                                 command=lambda: show_screen(i+1) if i+1 < len(screens) else self.show_tournament_bracket(tournament))
            btn_next.pack(pady=10)
        show_screen(idx)
        
    def show_history(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="Tournament History", font=("Arial", 16)).pack(pady=10)
        # Order tournaments by category and prestige
        tournaments_by_category = collections.defaultdict(list)
        for t in self.scheduler.tournaments:
            tournaments_by_category[t['category']].append(t)
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        for category in PRESTIGE_ORDER:
            if category in tournaments_by_category:
                tk.Label(scroll_frame, text=category, font=("Arial", 13, "underline")).pack(anchor="w", pady=(8,2))
                for t in sorted(tournaments_by_category[category], key=lambda x: x['name']):
                    btn = tk.Button(
                        scroll_frame,
                        text=f"{t['name']} ({t['surface']})",
                        anchor="w",
                        width=40,
                        font=("Arial", 11),
                        command=lambda tournament=t: self.show_tournament_history_details(tournament)
                    )
                    btn.pack(fill="x", padx=2, pady=1)
        tk.Button(self.root, text="Back to Main Menu", command=self.build_main_menu, font=("Arial", 12)).pack(pady=10)
        
    def show_tournament_history_details(self, tournament):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text=f"{tournament['name']} ({tournament['category']}, {tournament['surface']})", font=("Arial", 16)).pack(pady=10)
        # Winners across the years
        history = tournament.get('history', [])
        if history:
            tk.Label(self.root, text="Winners by Year:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(6,2))
            for entry in sorted(history, key=lambda x: x['year'], reverse=True):
                winner_name = entry.get('winner', 'Unknown')
                tk.Label(self.root, text=f"{entry['year']}: {winner_name}", font=("Arial", 11)).pack(anchor="w")
        else:
            tk.Label(self.root, text="No history yet.", font=("Arial", 11)).pack(anchor="w", pady=6)
        # Player(s) who won it the most
        win_counts = collections.Counter(entry.get('winner', 'Unknown') for entry in history)
        if win_counts:
            max_wins = max(win_counts.values())
            top_winners = [name for name, count in win_counts.items() if count == max_wins]
            tk.Label(self.root, text=f"Most Titles ({max_wins}):", font=("Arial", 12, "bold")).pack(anchor="w", pady=(6,2))
            for name in top_winners:
                tk.Label(self.root, text=name, font=("Arial", 11)).pack(anchor="w")
        tk.Button(self.root, text="Back to History", command=self.show_history, font=("Arial", 12)).pack(pady=10)
        tk.Button(self.root, text="Back to Main Menu", command=self.build_main_menu, font=("Arial", 12)).pack(pady=2)
        
if __name__ == "__main__":
    root = tk.Tk()
    root.title("TennisGM")
    app = TennisGMApp(root)
    root.mainloop()