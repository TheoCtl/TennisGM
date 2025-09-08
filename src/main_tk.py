import tkinter as tk
from schedule import TournamentScheduler
import collections
import sys
from io import StringIO
import functools

PRESTIGE_ORDER = ["Special", "Grand Slam", "Masters 1000", "ATP 500", "ATP 250", "Challenger 175", "Challenger 125", "Challenger 100", "Challenger 75", "Challenger 50", "ITF"]

class TennisGMApp:
    def __init__(self, root):
        self.root = root
        self.scheduler = TournamentScheduler()
        self._migrate_favorites()
        self.menu_options = [
            "News Feed", "Tournaments", "ATP Rankings", "Hall of Fame", "Achievements", "Advance to next week", "Exit"
        ]
        self.build_main_menu()

    def _migrate_favorites(self):
        changed = False
        for p in self.scheduler.players:
            if 'ovrcap' in p:
                p.pop('ovrcap', None)
                changed = True
            if 'favorite' not in p:
                p['favorite'] = False
                changed = True
        if changed:
            # Persist migration
            if hasattr(self.scheduler, 'save_game'):
                self.scheduler.save_game()

    def _player_by_id(self, pid):
        return next((p for p in self.scheduler.players if p['id'] == pid), None)

    def _is_favorite(self, pid_or_player):
        if isinstance(pid_or_player, dict):
            return bool(pid_or_player.get('favorite'))
        pl = self._player_by_id(pid_or_player)
        return bool(pl and pl.get('favorite'))

    def _tournament_has_favorite(self, tournament):
        # Prefer participants; fallback to scanning bracket round 0
        part_ids = list(tournament.get('participants', []))
        if not part_ids and tournament.get('bracket'):
            for m in tournament['bracket'][0]:
                p1, p2 = m[0], m[1]
                if p1: part_ids.append(p1)
                if p2: part_ids.append(p2)
        return any(self._is_favorite(pid) for pid in part_ids)

    def build_main_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Modern header with gradient-like effect
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=100)
        header_frame.pack(fill="x", pady=0)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🎾 TennisGM", font=("Arial", 24, "bold"), 
                fg="white", bg="#2c3e50").pack(pady=(15, 5))
        tk.Label(header_frame, text=f"Year {self.scheduler.current_year}, Week {self.scheduler.current_week}",
                font=("Arial", 14), fg="#bdc3c7", bg="#2c3e50").pack()
        
        # Main content area
        content_frame = tk.Frame(self.root, bg="#ecf0f1")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Build menu options in the requested layout
        # News Feed centered at top
        news_btn = tk.Button(
            content_frame,
            text="📰 News Feed",
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=15,
            activebackground="#2980b9",
            activeforeground="white",
            command=lambda: self.handle_menu("News Feed")
        )
        news_btn.grid(row=0, column=0, columnspan=2, padx=10, pady=8, sticky="ew")
        
        # Row 1: Tournaments and World Crown
        tournaments_btn = tk.Button(
            content_frame,
            text="🏆 Tournaments",
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=15,
            activebackground="#2980b9",
            activeforeground="white",
            command=lambda: self.handle_menu("Tournaments")
        )
        tournaments_btn.grid(row=1, column=0, padx=10, pady=8, sticky="ew")
        
        world_crown_btn = tk.Button(
            content_frame,
            text="🌍 World Crown",
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=15,
            activebackground="#2980b9",
            activeforeground="white",
            command=lambda: self.handle_menu("World Crown")
        )
        world_crown_btn.grid(row=1, column=1, padx=10, pady=8, sticky="ew")
        
        # Row 2: ATP Rankings and Prospects
        rankings_btn = tk.Button(
            content_frame,
            text="🏅 ATP Rankings",
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=15,
            activebackground="#2980b9",
            activeforeground="white",
            command=lambda: self.handle_menu("ATP Rankings")
        )
        rankings_btn.grid(row=2, column=0, padx=10, pady=8, sticky="ew")
        
        prospects_btn = tk.Button(
            content_frame,
            text="🌟 Prospects",
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=15,
            activebackground="#2980b9",
            activeforeground="white",
            command=lambda: self.handle_menu("Prospects")
        )
        prospects_btn.grid(row=2, column=1, padx=10, pady=8, sticky="ew")
        
        # Row 3: Hall of Fame and Achievements
        hall_btn = tk.Button(
            content_frame,
            text="👑 Hall of Fame",
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=15,
            activebackground="#2980b9",
            activeforeground="white",
            command=lambda: self.handle_menu("Hall of Fame")
        )
        hall_btn.grid(row=3, column=0, padx=10, pady=8, sticky="ew")
        
        achievements_btn = tk.Button(
            content_frame,
            text="🏆 Achievements",
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=15,
            activebackground="#2980b9",
            activeforeground="white",
            command=lambda: self.handle_menu("Achievements")
        )
        achievements_btn.grid(row=3, column=1, padx=10, pady=8, sticky="ew")
        
        # Row 4: History (and Advance if available)
        current_row = 4
        current_tournaments = self.scheduler.get_current_week_tournaments()
        incomplete_tournaments = [t for t in current_tournaments if t['winner_id'] is None]
        
        if len(incomplete_tournaments) == 0:
            # Both History and Advance to next week
            history_btn = tk.Button(
                content_frame,
                text="📚 History",
                font=("Arial", 12, "bold"),
                bg="#3498db",
                fg="white",
                relief="flat",
                bd=0,
                padx=20,
                pady=15,
                activebackground="#2980b9",
                activeforeground="white",
                command=lambda: self.handle_menu("History")
            )
            history_btn.grid(row=current_row, column=0, padx=10, pady=8, sticky="ew")
            
            advance_btn = tk.Button(
                content_frame,
                text="⏭️ Advance to next week",
                font=("Arial", 12, "bold"),
                bg="#27ae60",
                fg="white",
                relief="flat",
                bd=0,
                padx=20,
                pady=15,
                activebackground="#229954",
                activeforeground="white",
                command=lambda: self.handle_menu("Advance to next week")
            )
            advance_btn.grid(row=current_row, column=1, padx=10, pady=8, sticky="ew")
            current_row += 1
        else:
            # Just History centered
            history_btn = tk.Button(
                content_frame,
                text="📚 History",
                font=("Arial", 12, "bold"),
                bg="#3498db",
                fg="white",
                relief="flat",
                bd=0,
                padx=20,
                pady=15,
                activebackground="#2980b9",
                activeforeground="white",
                command=lambda: self.handle_menu("History")
            )
            history_btn.grid(row=current_row, column=0, columnspan=2, padx=10, pady=8, sticky="ew")
            current_row += 1
        
        # Save & Quit centered at bottom
        save_btn = tk.Button(
            content_frame,
            text="💾 Save & Quit",
            font=("Arial", 12, "bold"),
            bg="#e74c3c",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=15,
            activebackground="#c0392b",
            activeforeground="white",
            command=lambda: self.handle_menu("Save & Quit")
        )
        save_btn.grid(row=current_row, column=0, columnspan=2, padx=10, pady=8, sticky="ew")
        
        # Update menu options for handle_menu
        self.menu_options = ["News Feed", "Tournaments", "World Crown", "ATP Rankings", 
                           "Prospects", "Hall of Fame", "Achievements", "History"]
        if len(incomplete_tournaments) == 0:
            self.menu_options.append("Advance to next week")
        self.menu_options.append("Save & Quit")
        
        # Configure grid weights for responsive design
        for i in range(2):
            content_frame.grid_columnconfigure(i, weight=1)

    def handle_menu(self, option):
        if option == "Advance to next week":
            self.scheduler.advance_week()
            self.build_main_menu()
        elif option == "News Feed":
            self.show_news_feed()
        elif option == "ATP Rankings":
            self.show_rankings()
        elif option == "Prospects":
            self.show_prospects()
        elif option == "Hall of Fame":
            self.show_hall_of_fame()
        elif option == "World Crown":
            self.show_world_crown()
        elif option == "Achievements":
            self.show_achievements()
        elif option == "Tournaments":
            self.show_tournaments()
        elif option == "History":
            self.show_history()
        elif option == "Save & Quit":
            self.scheduler.save_game()  # Save before quitting
            self.root.quit()

    def show_prospects(self):
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Modern header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=70)
        header_frame.pack(fill="x", pady=0)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🌟 Prospects (Under 20)", 
                font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(expand=True)

        # Tab system for prospects by age with modern styling
        tab_container = tk.Frame(self.root, bg="#34495e", height=50)
        tab_container.pack(fill="x", pady=0)
        tab_container.pack_propagate(False)
        
        tab_frame = tk.Frame(tab_container, bg="#34495e")
        tab_frame.pack(expand=True)
        
        self.current_prospects_tab = getattr(self, 'current_prospects_tab', "All")
        
        tabs = ["All", "19", "18", "17", "16"]
        for tab in tabs:
            is_active = tab == self.current_prospects_tab
            bg_color = "#e67e22" if is_active else "#5d6d7e"  # Orange for prospects
            
            btn = tk.Button(tab_frame, text=f"{tab} years" if tab != "All" else tab, 
                          bg=bg_color, fg="white",
                          command=lambda t=tab: self.switch_prospects_tab(t),
                          font=("Arial", 11, "bold" if is_active else "normal"), 
                          relief="flat", bd=0, padx=12, pady=8,
                          activebackground="#d35400", activeforeground="white")
            btn.pack(side="left", padx=2)

        # Compute FUT = overall + potential_factor + sum(surface_modifiers)
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

        # Search bar
        search_var = tk.StringVar()
        search_entry = tk.Entry(self.root, textvariable=search_var, font=("Arial", 12), width=40)
        search_entry.pack(pady=4)

        # Scrollable list
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        def update_list(*args):
            query = search_var.get().lower()
            for widget in scroll_frame.winfo_children():
                widget.destroy()
            
            # Get prospects based on tab selection
            if self.current_prospects_tab == "All":
                u20 = [p for p in self.scheduler.players if p.get("age", 99) < 20]
            else:
                target_age = int(self.current_prospects_tab)
                u20 = [p for p in self.scheduler.players if p.get("age", 99) == target_age]
            
            ranked = sorted(((p, calc_fut(p)) for p in u20), key=lambda x: x[1], reverse=True)
            filtered = [(p, fut) for (p, fut) in ranked if query in p.get('name', '').lower()]
            
            for idx, (player, fut) in enumerate(filtered, 1):
                # Create card-style entry for prospects
                is_favorite = player.get('favorite', False)
                
                # Top 3 prospects get special styling
                if idx == 1:
                    bg_color = "#f39c12"  # Gold
                    fg_color = "white"
                    rank_icon = "🥇"
                elif idx == 2:
                    bg_color = "#e67e22"  # Orange
                    fg_color = "white"
                    rank_icon = "🥈"
                elif idx == 3:
                    bg_color = "#d35400"  # Dark orange
                    fg_color = "white"
                    rank_icon = "🥉"
                else:
                    bg_color = "#e67e22" if is_favorite else "white"  # Orange theme for favorites
                    fg_color = "white" if is_favorite else "#2c3e50"
                    rank_icon = "⭐" if is_favorite else "🌟"

                entry_frame = tk.Frame(scroll_frame, bg=bg_color, relief="raised", bd=1)
                entry_frame.pack(fill="x", padx=5, pady=2)
                
                text = f"{rank_icon} {idx}. {player['name']} - FUT {fut} | {player.get('age', 1.0)}yo"
                btn = tk.Button(
                    entry_frame,
                    text=text,
                    anchor="w",
                    bg=bg_color,
                    fg=fg_color,
                    font=("Arial", 12, "bold" if idx <= 3 or is_favorite else "normal"),
                    relief="flat",
                    bd=0,
                    padx=15,
                    pady=8,
                    activebackground="#d35400" if bg_color != "white" else "#f39c12",
                    activeforeground="white" if bg_color != "white" else "#2c3e50",
                    command=lambda pl=player: self.show_u20_player_details(pl)
                )
                btn.pack(fill="x")

        # Store update function for tab switching
        self.update_prospects_list = update_list
        
        # Initial population and search binding
        update_list()
        search_var.trace_add("write", update_list)

        # Styled back button
        button_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        button_frame.pack(fill="x", pady=0)
        button_frame.pack_propagate(False)
        
        tk.Button(button_frame, text="← Back to Main Menu", command=self.build_main_menu, 
                 font=("Arial", 12, "bold"), bg="#e67e22", fg="white", relief="flat",
                 activebackground="#d35400", activeforeground="white", bd=0, padx=20, pady=8).pack(expand=True)

    def switch_prospects_tab(self, tab):
        self.current_prospects_tab = tab
        self.show_prospects()

    def _render_player_details(self, player, back_label, back_func):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Modern header with player name
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Determine player status icon
        rank = player.get('rank', 'N/A')
        age = player.get('age', 0)
        if isinstance(rank, int):
            if rank <= 10:
                status_icon = "👑"  # Top 10
            elif rank <= 50:
                status_icon = "⭐"  # Top 50
            else:
                status_icon = "🎾"  # Other ranked
        elif age < 21:
            status_icon = "🌱"  # Prospect
        else:
            status_icon = "🏛️"  # Hall of Fame or retired
        
        title_label = tk.Label(
            header_frame,
            text=f"{status_icon} {player['name']}",
            font=("Arial", 20, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(expand=True)

        # Favorite toggle section
        def _toggle_fav(pl):
            pl['favorite'] = not pl.get('favorite', False)
            # Persist immediately
            try:
                self.scheduler.save_game()
            except Exception:
                pass
            # Re-render same details screen
            self._render_player_details(pl, back_label, back_func)

        fav_frame = tk.Frame(self.root, bg="#ecf0f1")
        fav_frame.pack(fill="x", padx=20, pady=10)
        
        fav_state = bool(player.get('favorite'))
        fav_btn_text = "⭐ Remove from Favorites" if fav_state else "⭐ Add to Favorites"
        fav_color = "#e74c3c" if fav_state else "#f39c12"
        
        tk.Button(
            fav_frame, 
            text=fav_btn_text, 
            font=("Arial", 12, "bold"),
            bg=fav_color,
            fg="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            activebackground="#c0392b" if fav_state else "#e67e22",
            activeforeground="white",
            command=lambda: _toggle_fav(player)
        ).pack()

        # Format surface modifiers
        def format_surface_mods(p):
            mods = p.get('surface_modifiers')
            if isinstance(mods, dict):
                parts = []
                for s in ["clay", "grass", "hard", "indoor"]:
                    v = mods.get(s)
                    parts.append(f"{s.capitalize()}: {v:.3f}" if isinstance(v, (int, float)) else f"{s.capitalize()}: -")
                return ", ".join(parts)
            return "N/A"

        # Build skill lines with progcap/regcap display
        age = player.get('age', 0)
        use_prog = age <= 30
        caps = player.get('skill_caps', {})
        skills = player.get('skills', {})
        skill_lines = []
        for skill_name, val in skills.items():
            cap_dict = caps.get(skill_name, {}) if isinstance(caps, dict) else {}
            if use_prog:
                cap = int(cap_dict.get('progcap', 0) or 0)
                suffix = f" (+{cap})" if cap > 0 else ""
            else:
                cap = int(cap_dict.get('regcap', 0) or 0)
                suffix = f" (-{cap})" if cap > 0 else ""
            skill_lines.append(f"  {skill_name.capitalize()}: {val}{suffix}")

        # Scrollable main content
        scroll_container = tk.Frame(self.root, bg="#ecf0f1")
        scroll_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(scroll_container, bg="#ecf0f1")
        scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        main_frame = tk.Frame(canvas, bg="#ecf0f1")
        
        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        # Basic info card
        info_card = tk.Frame(main_frame, bg="white", relief="raised", bd=2)
        info_card.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            info_card,
            text="👤 Player Information",
            font=("Arial", 14, "bold"),
            bg="#3498db",
            fg="white",
            padx=15,
            pady=8
        ).pack(fill="x")
        
        info_content = tk.Frame(info_card, bg="white")
        info_content.pack(fill="x", padx=15, pady=10)
        
        basic_info = [
            ("🏆 Current Rank", player.get('rank', 'N/A')),
            ("🎯 Highest Ranking", player.get('highest_ranking', 'N/A')),
            ("🎂 Age", f"{player.get('age', 'N/A')} years old"),
            ("✋ Playing Hand", f"{player.get('hand', 'N/A')}-handed"),
            ("🌍 Nationality", player.get('nationality', 'N/A')),
            ("⚡ Potential Factor", player.get('potential_factor', 'N/A')),
        ]
        
        for label, value in basic_info:
            row = tk.Frame(info_content, bg="white")
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{label}:", font=("Arial", 11, "bold"), bg="white", fg="#2c3e50", anchor="w").pack(side="left")
            tk.Label(row, text=str(value), font=("Arial", 11), bg="white", fg="#7f8c8d", anchor="w").pack(side="right")
        
        # Surface modifiers card
        surface_card = tk.Frame(main_frame, bg="white", relief="raised", bd=2)
        surface_card.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            surface_card,
            text="🏟️ Surface Performance",
            font=("Arial", 14, "bold"),
            bg="#e67e22",
            fg="white",
            padx=15,
            pady=8
        ).pack(fill="x")
        
        surface_content = tk.Frame(surface_card, bg="white")
        surface_content.pack(fill="x", padx=15, pady=10)
        
        mods = player.get('surface_modifiers', {})
        if isinstance(mods, dict):
            surface_icons = {"clay": "🟫", "grass": "🟢", "hard": "🔵", "indoor": "🏢"}
            for surface in ["clay", "grass", "hard", "indoor"]:
                value = mods.get(surface, 0)
                icon = surface_icons.get(surface, "🎾")
                row = tk.Frame(surface_content, bg="white")
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f"{icon} {surface.capitalize()}:", font=("Arial", 11, "bold"), bg="white", fg="#2c3e50", anchor="w").pack(side="left")
                tk.Label(row, text=f"{value:.3f}" if isinstance(value, (int, float)) else "-", font=("Arial", 11), bg="white", fg="#7f8c8d", anchor="w").pack(side="right")
        
        # Skills card
        skills_card = tk.Frame(main_frame, bg="white", relief="raised", bd=2)
        skills_card.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            skills_card,
            text="⚡ Skills & Abilities",
            font=("Arial", 14, "bold"),
            bg="#9b59b6",
            fg="white",
            padx=15,
            pady=8
        ).pack(fill="x")
        
        skills_content = tk.Frame(skills_card, bg="white")
        skills_content.pack(fill="x", padx=15, pady=10)
        
        # Build skill display with caps
        age = player.get('age', 0)
        use_prog = age <= 30
        caps = player.get('skill_caps', {})
        skills = player.get('skills', {})
        
        for skill_name, val in skills.items():
            cap_dict = caps.get(skill_name, {}) if isinstance(caps, dict) else {}
            if use_prog:
                cap = int(cap_dict.get('progcap', 0) or 0)
                suffix = f" (+{cap})" if cap > 0 else ""
            else:
                cap = int(cap_dict.get('regcap', 0) or 0)
                suffix = f" (-{cap})" if cap > 0 else ""
            
            row = tk.Frame(skills_content, bg="white")
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"🎯 {skill_name.capitalize()}:", font=("Arial", 11, "bold"), bg="white", fg="#2c3e50", anchor="w").pack(side="left")
            tk.Label(row, text=f"{val}{suffix}", font=("Arial", 11), bg="white", fg="#7f8c8d", anchor="w").pack(side="right")
        
        # Career stats card
        stats_card = tk.Frame(main_frame, bg="white", relief="raised", bd=2)
        stats_card.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            stats_card,
            text="📊 Career Statistics",
            font=("Arial", 14, "bold"),
            bg="#27ae60",
            fg="white",
            padx=15,
            pady=8
        ).pack(fill="x")
        
        stats_content = tk.Frame(stats_card, bg="white")
        stats_content.pack(fill="x", padx=15, pady=10)
        
        total_titles = sum(1 for win in player.get('tournament_wins', []))
        gs_titles = sum(1 for win in player.get('tournament_wins', []) if win.get('category') == 'Grand Slam')
        
        career_stats = [
            ("🏆 Total Titles", total_titles),
            ("👑 Grand Slam Titles", gs_titles),
            ("🎾 Total Matches Won", sum(player.get('mawn', [0,0,0,0,0]))),
            ("1️⃣ Weeks at #1", player.get('w1', 0)),
            ("🔟 Weeks in Top 10", player.get('w16', 0)),
        ]
        
        for label, value in career_stats:
            row = tk.Frame(stats_content, bg="white")
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{label}:", font=("Arial", 11, "bold"), bg="white", fg="#2c3e50", anchor="w").pack(side="left")
            tk.Label(row, text=str(value), font=("Arial", 11), bg="white", fg="#7f8c8d", anchor="w").pack(side="right")

        # Action buttons
        button_frame = tk.Frame(main_frame, bg="#ecf0f1")
        button_frame.pack(fill="x", pady=15)
        
        tk.Button(
            button_frame,
            text="🏆 View Tournament Wins",
            command=lambda: self.show_tournament_wins(player, back_command=lambda: self._render_player_details(player, back_label, back_func)),
            font=("Arial", 12, "bold"),
            bg="#f39c12",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            activebackground="#e67e22",
            activeforeground="white"
        ).pack(pady=(0, 10))

        # Navigation buttons
        nav_frame = tk.Frame(button_frame, bg="#ecf0f1")
        nav_frame.pack()
        
        tk.Button(
            nav_frame, 
            text=f"↩️ {back_label}", 
            command=back_func, 
            font=("Arial", 12, "bold"),
            bg="#95a5a6",
            fg="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            activebackground="#7f8c8d",
            activeforeground="white"
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            nav_frame, 
            text="🏠 Back to Main Menu", 
            command=self.build_main_menu, 
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            activebackground="#2980b9",
            activeforeground="white"
        ).pack(side="left")

    def show_player_details(self, player):
        self._render_player_details(player, "Back to Rankings", self.show_rankings)

    def show_u20_player_details(self, player):
        self._render_player_details(player, "Back to Prospects", self.show_prospects)

    def show_news_feed(self):
        # Clear the main window
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Modern header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=70)
        header_frame.pack(fill="x", pady=0)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📰 News Feed", 
                font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(expand=True)
                
        news = self.scheduler.news_feed if hasattr(self.scheduler, 'news_feed') else []
        
        # Content area
        content_frame = tk.Frame(self.root, bg="#ecf0f1")
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        if not news:
            # No news message with styling
            no_news_frame = tk.Frame(content_frame, bg="white", relief="solid", bd=1)
            no_news_frame.pack(fill="x", padx=20, pady=50)
            tk.Label(no_news_frame, text="📰 No news yet.", font=("Arial", 14), 
                    bg="white", fg="#7f8c8d", pady=30).pack()
        else:
            # Use a scrollable Text widget for long news feeds with styling
            frame = tk.Frame(content_frame, bg="#ecf0f1")
            frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            text = tk.Text(frame, wrap="word", font=("Arial", 12), height=20, 
                          bg="white", fg="#2c3e50", relief="solid", bd=1, padx=15, pady=15)
            text.pack(side="left", fill="both", expand=True)
            
            for line in news:
                # Add some formatting to news entries
                if any(keyword in line.lower() for keyword in ["wins", "champion", "victory"]):
                    text.insert("end", f"🏆 {line}\n", "winner")
                elif "world crown" in line.lower():
                    text.insert("end", f"🌍 {line}\n", "worldcrown")
                else:
                    text.insert("end", f"• {line}\n", "normal")
            
            # Configure text tags for styling
            text.tag_configure("winner", foreground="#27ae60", font=("Arial", 12, "bold"))
            text.tag_configure("worldcrown", foreground="#9b59b6", font=("Arial", 12, "bold"))
            text.tag_configure("normal", foreground="#2c3e50")
            
            text.config(state="disabled")
            scrollbar = tk.Scrollbar(frame, command=text.yview)
            scrollbar.pack(side="right", fill="y")
            text.config(yscrollcommand=scrollbar.set)
            
        # Styled back button
        button_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        button_frame.pack(fill="x", pady=0)
        button_frame.pack_propagate(False)
        
        tk.Button(button_frame, text="← Back to Main Menu", command=self.build_main_menu, 
                 font=("Arial", 12, "bold"), bg="#3498db", fg="white", relief="flat",
                 activebackground="#2980b9", activeforeground="white", bd=0, padx=20, pady=8).pack(expand=True)

    def show_rankings(self):
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Modern header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=70)
        header_frame.pack(fill="x", pady=0)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🏅 ATP Rankings", 
                font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(expand=True)

        # Tab system for rankings with modern styling
        tab_container = tk.Frame(self.root, bg="#34495e", height=50)
        tab_container.pack(fill="x", pady=0)
        tab_container.pack_propagate(False)
        
        tab_frame = tk.Frame(tab_container, bg="#34495e")
        tab_frame.pack(expand=True)
        
        self.current_rankings_tab = getattr(self, 'current_rankings_tab', "All Players")
        
        tabs = ["All Players", "Favorites"]
        for tab in tabs:
            is_active = tab == self.current_rankings_tab
            bg_color = "#3498db" if is_active else "#5d6d7e"
            
            btn = tk.Button(tab_frame, text=tab, bg=bg_color, fg="white",
                          command=lambda t=tab: self.switch_rankings_tab(t),
                          font=("Arial", 12, "bold" if is_active else "normal"), 
                          relief="flat", bd=0, padx=15, pady=8,
                          activebackground="#2980b9", activeforeground="white")
            btn.pack(side="left", padx=2)

        # Content area with background
        content_frame = tk.Frame(self.root, bg="#ecf0f1")
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Search box with styling
        search_var = tk.StringVar()
        search_frame = tk.Frame(content_frame, bg="#ecf0f1")
        search_frame.pack(pady=10)
        tk.Label(search_frame, text="🔍 Search Players:", font=("Arial", 11, "bold"), 
                bg="#ecf0f1", fg="#2c3e50").pack(side="left", padx=(0, 5))
        search_entry = tk.Entry(search_frame, textvariable=search_var, font=("Arial", 12), 
                               width=30, relief="solid", bd=1)
        search_entry.pack(side="left")

        # Scrollable frame for rankings
        frame = tk.Frame(content_frame, bg="#ecf0f1")
        frame.pack(fill="both", expand=True, padx=10)
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

        def update_list(*args):
            query = search_var.get().lower()
            for widget in scroll_frame.winfo_children():
                widget.destroy()
                
            ranked_players = self.scheduler.ranking_system.get_ranked_players(
                self.scheduler.players,
                self.scheduler.current_date
            )
            
            filtered_players = []
            for ranking_pos, (player, points) in enumerate(ranked_players, 1):
                # Tab-based filtering
                if self.current_rankings_tab == "Favorites" and not player.get('favorite', False):
                    continue
                if query and query not in player['name'].lower():
                    continue
                filtered_players.append((ranking_pos, player, points))
                
            for ranking_pos, player, points in filtered_players:
                # Create card-style entry
                is_favorite = player.get('favorite', False)
                
                # Top 3 get special colors
                if ranking_pos == 1:
                    bg_color = "#f39c12"  # Gold
                    fg_color = "white"
                    rank_icon = "🥇"
                elif ranking_pos == 2:
                    bg_color = "#95a5a6"  # Silver
                    fg_color = "white"
                    rank_icon = "🥈"
                elif ranking_pos == 3:
                    bg_color = "#d35400"  # Bronze
                    fg_color = "white"
                    rank_icon = "🥉"
                else:
                    bg_color = "#3498db" if is_favorite else "white"
                    fg_color = "white" if is_favorite else "#2c3e50"
                    rank_icon = "⭐" if is_favorite else ""

                entry_frame = tk.Frame(scroll_frame, bg=bg_color, relief="raised", bd=1)
                entry_frame.pack(fill="x", padx=5, pady=2)
                
                btn = tk.Button(
                    entry_frame,
                    text=f"{rank_icon} {ranking_pos}. {player['name']} - {points} pts",
                    anchor="w",
                    bg=bg_color,
                    fg=fg_color,
                    font=("Arial", 12, "bold" if ranking_pos <= 3 or is_favorite else "normal"),
                    relief="flat",
                    bd=0,
                    padx=15,
                    pady=8,
                    activebackground="#2980b9" if bg_color != "white" else "#ecf0f1",
                    activeforeground="white" if bg_color != "white" else "#2c3e50",
                    command=lambda p=player: self.show_player_details(p)
                )
                btn.pack(fill="x")

        # Store update function for tab switching
        self.update_rankings_list = update_list
        
        # Initial population
        update_list()
        search_var.trace_add("write", update_list)

        # Styled back button
        button_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        button_frame.pack(fill="x", pady=0)
        button_frame.pack_propagate(False)
        
        tk.Button(button_frame, text="← Back to Main Menu", command=self.build_main_menu, 
                 font=("Arial", 12, "bold"), bg="#3498db", fg="white", relief="flat",
                 activebackground="#2980b9", activeforeground="white", bd=0, padx=20, pady=8).pack(expand=True)

    def switch_rankings_tab(self, tab):
        self.current_rankings_tab = tab
        self.show_rankings()

    def show_tournament_wins(self, player, back_command=None):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Modern header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text=f"🏆 {player['name']} - Tournament Wins",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(expand=True)

        # Bold tournaments that were won (points == Winner points for their category).
        # All entries in tournament_history are from the last 52 weeks; skip "Special".
        recent_wins_keys = set()
        try:
            points_map = self.scheduler.ranking_system.POINTS
            for entry in player.get('tournament_history', []):
                cat = entry.get('category')
                if not cat or cat == "Special":
                    continue
                winner_pts = points_map.get(cat, {}).get("Winner")
                if winner_pts is None:
                    continue
                if entry.get('points', -1) == winner_pts:
                    recent_wins_keys.add((entry.get('name', ''), cat))
        except Exception:
            recent_wins_keys = set()

        # Group wins by category and tournament name (historical list)
        wins = player.get('tournament_wins', [])
        wins_by_category = collections.defaultdict(lambda: collections.defaultdict(int))
        for win in wins:
            name = win.get('name', 'Unknown')
            cat = win.get('category', 'Unknown')
            wins_by_category[cat][name] += 1

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
                
                # Category header with color coding
                if category == 'Grand Slam':
                    cat_color = "#8e44ad"  # Purple
                    cat_icon = "👑"
                elif 'Masters' in category:
                    cat_color = "#e67e22"  # Orange
                    cat_icon = "🏆"
                elif 'ATP 500' == category:
                    cat_color = "#f39c12"  # Gold
                    cat_icon = "🥇"
                elif 'ATP 250' == category:
                    cat_color = "#3498db"  # Blue
                    cat_icon = "🎾"
                else:
                    cat_color = "#95a5a6"  # Gray
                    cat_icon = "🏟️"
                
                # Category card
                category_frame = tk.Frame(scroll_frame, bg=cat_color, relief="raised", bd=2)
                category_frame.pack(fill="x", padx=10, pady=5)
                
                # Category header
                header_frame = tk.Frame(category_frame, bg=cat_color)
                header_frame.pack(fill="x", padx=15, pady=8)
                
                tk.Label(
                    header_frame,
                    text=f"{cat_icon} {category} ({total_in_category} titles)",
                    font=("Arial", 14, "bold"),
                    bg=cat_color,
                    fg="white"
                ).pack(anchor="w")
                
                # Tournament wins in this category
                wins_content = tk.Frame(category_frame, bg="white")
                wins_content.pack(fill="x", padx=2, pady=(0, 2))
                
                for tname, count in sorted(wins_by_category[category].items()):
                    is_recent_win = (tname, category) in recent_wins_keys
                    
                    win_frame = tk.Frame(wins_content, bg="#f8f9fa" if not is_recent_win else "#fff3cd")
                    win_frame.pack(fill="x", padx=8, pady=2)
                    
                    # Tournament name and count
                    info_frame = tk.Frame(win_frame, bg=win_frame['bg'])
                    info_frame.pack(fill="x", padx=10, pady=8)
                    
                    # Recent win badge
                    if is_recent_win:
                        tk.Label(
                            info_frame,
                            text="🔥 RECENT",
                            font=("Arial", 8, "bold"),
                            bg="#ffc107",
                            fg="white",
                            padx=6,
                            pady=2
                        ).pack(side="right")
                    
                    tk.Label(
                        info_frame,
                        text=f"🏆 {count}x {tname}",
                        font=("Arial", 11, "bold" if is_recent_win else "normal"),
                        bg=win_frame['bg'],
                        fg="#2c3e50",
                        anchor="w"
                    ).pack(side="left", fill="x", expand=True)
                
                any_win = True
        
        if not any_win:
            # No wins message
            no_wins_frame = tk.Frame(scroll_frame, bg="white", relief="solid", bd=1)
            no_wins_frame.pack(fill="x", padx=20, pady=50)
            tk.Label(
                no_wins_frame, 
                text="🎾 No tournament wins yet", 
                font=("Arial", 14), 
                bg="white", 
                fg="#7f8c8d", 
                pady=30
            ).pack()

        # Modern back button
        back_frame = tk.Frame(self.root, bg="#ecf0f1")
        back_frame.pack(fill="x", padx=20, pady=15)
        
        if back_command:
            tk.Button(
                back_frame, 
                text="↩️ Back to Player Details", 
                command=back_command, 
                font=("Arial", 12, "bold"),
                bg="#3498db",
                fg="white",
                relief="flat",
                bd=0,
                padx=20,
                pady=8,
                activebackground="#2980b9",
                activeforeground="white"
            ).pack()
        else:
            tk.Button(
                back_frame, 
                text="↩️ Back to Player Details", 
                command=lambda: self.show_player_details(player), 
                font=("Arial", 12, "bold"),
                bg="#3498db",
                fg="white",
                relief="flat",
                bd=0,
                padx=20,
                pady=8,
                activebackground="#2980b9",
                activeforeground="white"
            ).pack()

    def show_hall_of_fame(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Modern header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🏛️ Hall of Fame",
            font=("Arial", 20, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(expand=True)

        # Search section
        search_frame = tk.Frame(self.root, bg="#ecf0f1")
        search_frame.pack(fill="x", padx=20, pady=15)
        
        tk.Label(
            search_frame,
            text="🔍 Search Legends:",
            font=("Arial", 12, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        ).pack(side="left", padx=(0, 10))
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, font=("Arial", 12), width=30)
        search_entry.pack(side="left")
        
        def create_hof_cards(players_to_show):
            for widget in scroll_frame.winfo_children():
                widget.destroy()
            
            for idx, player in enumerate(players_to_show, 1):
                # Determine HOF tier for styling
                hof_points = player['hof_points']
                wins = len(player.get('tournament_wins', []))
                
                if hof_points >= 200:
                    tier_color = "#f1c40f"  # Gold for legends
                    tier_icon = "👑"
                    tier_name = "LEGEND"
                elif hof_points >= 100:
                    tier_color = "#c0392b"  # Deep red for hall of fame
                    tier_icon = "🏆"
                    tier_name = "IMMORTAL"
                elif hof_points >= 50:
                    tier_color = "#8e44ad"  # Purple for great
                    tier_icon = "⭐"
                    tier_name = "GREAT"
                else:
                    tier_color = "#34495e"  # Gray for inducted
                    tier_icon = "🎾"
                    tier_name = "INDUCTED"
                
                # Main player card
                player_frame = tk.Frame(scroll_frame, bg=tier_color, relief="raised", bd=2)
                player_frame.pack(fill="x", padx=10, pady=5)
                
                # Player info section
                info_frame = tk.Frame(player_frame, bg=tier_color)
                info_frame.pack(fill="x", padx=15, pady=10)
                
                # Rank and name
                rank_name_frame = tk.Frame(info_frame, bg=tier_color)
                rank_name_frame.pack(fill="x")
                
                rank_label = tk.Label(
                    rank_name_frame,
                    text=f"#{idx}",
                    font=("Arial", 14, "bold"),
                    bg=tier_color,
                    fg="white",
                    width=4
                )
                rank_label.pack(side="left")
                
                name_label = tk.Label(
                    rank_name_frame,
                    text=f"{tier_icon} {player['name']}",
                    font=("Arial", 14, "bold"),
                    bg=tier_color,
                    fg="white",
                    anchor="w"
                )
                name_label.pack(side="left", padx=(10, 0), fill="x", expand=True)
                
                # Tier badge
                tier_label = tk.Label(
                    rank_name_frame,
                    text=tier_name,
                    font=("Arial", 10, "bold"),
                    bg="white",
                    fg=tier_color,
                    padx=8,
                    pady=2
                )
                tier_label.pack(side="right")
                
                # Stats
                stats_label = tk.Label(
                    info_frame,
                    text=f"HOF Points: {hof_points} • Tournament Wins: {wins}",
                    font=("Arial", 10),
                    bg=tier_color,
                    fg="#ecf0f1",
                    anchor="w"
                )
                stats_label.pack(fill="x", pady=(5, 0))
                
                # View details button
                button_frame = tk.Frame(player_frame, bg=tier_color)
                button_frame.pack(fill="x", padx=15, pady=(0, 10))
                
                btn_details = tk.Button(
                    button_frame,
                    text="📖 View Career Details",
                    font=("Arial", 11, "bold"),
                    bg="white",
                    fg=tier_color,
                    relief="flat",
                    bd=0,
                    padx=15,
                    pady=5,
                    activebackground="#ecf0f1",
                    activeforeground=tier_color,
                    command=lambda p=player: self.show_hof_player_details(p)
                )
                btn_details.pack(side="left")
        
        def update_list(*args):
            query = search_var.get().lower()
            filtered_hof = [
                p for p in hof_members
                if query in p['name'].lower()
            ]
            create_hof_cards(filtered_hof)
        
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

        # Initial population with cards
        create_hof_cards(hof_members)

        # Modern back button
        back_frame = tk.Frame(self.root, bg="#ecf0f1")
        back_frame.pack(fill="x", padx=20, pady=15)
        
        tk.Button(
            back_frame, 
            text="🏠 Back to Main Menu", 
            command=self.build_main_menu, 
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            activebackground="#2980b9",
            activeforeground="white"
        ).pack()

    def show_hof_player_details(self, player):
        for widget in self.root.winfo_children():
            widget.destroy()
        show_tournaments = getattr(self, "_show_tournaments", False)
        
        # Modern header with HOF styling
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Determine HOF tier for icon
        hof_points = player.get('hof_points', 0)
        if hof_points >= 200:
            status_icon = "👑"  # Legend
        elif hof_points >= 100:
            status_icon = "🏆"  # Immortal
        elif hof_points >= 50:
            status_icon = "⭐"  # Great
        else:
            status_icon = "🏛️"  # Inducted
        
        title_label = tk.Label(
            header_frame,
            text=f"{status_icon} {player['name']} (Hall of Fame)",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(expand=True)
        if not show_tournaments:
            # Main content area
            main_frame = tk.Frame(self.root, bg="#ecf0f1")
            main_frame.pack(fill="both", expand=True, padx=20, pady=15)
            
            w1 = player.get('w1', 0)
            w16 = player.get('w16', 0)
            t_wins = sum(1 for win in player.get('tournament_wins', []))
            m1000_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "Masters 1000")
            gs_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "Grand Slam")
            mawn = player.get('mawn', [0,0,0,0,0])
            
            # HOF Status Card
            status_card = tk.Frame(main_frame, bg="white", relief="raised", bd=2)
            status_card.pack(fill="x", pady=(0, 10))
            
            # Determine tier color
            if hof_points >= 200:
                tier_color = "#f1c40f"  # Gold
                tier_name = "LEGEND"
            elif hof_points >= 100:
                tier_color = "#c0392b"  # Deep red
                tier_name = "IMMORTAL"
            elif hof_points >= 50:
                tier_color = "#8e44ad"  # Purple
                tier_name = "GREAT"
            else:
                tier_color = "#34495e"  # Gray
                tier_name = "INDUCTED"
            
            tk.Label(
                status_card,
                text=f"🏛️ Hall of Fame Status: {tier_name}",
                font=("Arial", 14, "bold"),
                bg=tier_color,
                fg="white",
                padx=15,
                pady=8
            ).pack(fill="x")
            
            status_content = tk.Frame(status_card, bg="white")
            status_content.pack(fill="x", padx=15, pady=10)
            
            status_info = [
                ("🏆 HOF Points", hof_points),
                ("🎯 Highest Ranking", player.get('highest_ranking', 'N/A')),
            ]
            
            for label, value in status_info:
                row = tk.Frame(status_content, bg="white")
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f"{label}:", font=("Arial", 11, "bold"), bg="white", fg="#2c3e50", anchor="w").pack(side="left")
                tk.Label(row, text=str(value), font=("Arial", 11), bg="white", fg="#7f8c8d", anchor="w").pack(side="right")
            
            # Career Achievements Card
            achievements_card = tk.Frame(main_frame, bg="white", relief="raised", bd=2)
            achievements_card.pack(fill="x", pady=(0, 10))
            
            tk.Label(
                achievements_card,
                text="🏆 Career Achievements",
                font=("Arial", 14, "bold"),
                bg="#27ae60",
                fg="white",
                padx=15,
                pady=8
            ).pack(fill="x")
            
            achievements_content = tk.Frame(achievements_card, bg="white")
            achievements_content.pack(fill="x", padx=15, pady=10)
            
            achievements_data = [
                ("🏆 Total Titles", t_wins),
                ("👑 Grand Slam Titles", gs_wins),
                ("🥇 Masters 1000 Titles", m1000_wins),
                ("🎾 Total Matches Won", sum(mawn)),
                ("1️⃣ Weeks at #1", f"{w1}w"),
                ("🔟 Weeks in Top 10", f"{w16}w"),
            ]
            
            for label, value in achievements_data:
                row = tk.Frame(achievements_content, bg="white")
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f"{label}:", font=("Arial", 11, "bold"), bg="white", fg="#2c3e50", anchor="w").pack(side="left")
                tk.Label(row, text=str(value), font=("Arial", 11), bg="white", fg="#7f8c8d", anchor="w").pack(side="right")
            
            # Surface Breakdown Card
            surface_card = tk.Frame(main_frame, bg="white", relief="raised", bd=2)
            surface_card.pack(fill="x", pady=(0, 10))
            
            tk.Label(
                surface_card,
                text="🏟️ Surface Performance",
                font=("Arial", 14, "bold"),
                bg="#e67e22",
                fg="white",
                padx=15,
                pady=8
            ).pack(fill="x")
            
            surface_content = tk.Frame(surface_card, bg="white")
            surface_content.pack(fill="x", padx=15, pady=10)
            
            surfaces = [("🟫 Clay", mawn[0]), ("🟢 Grass", mawn[1]), ("🔵 Hard", mawn[2]), ("🏢 Indoor", mawn[3])]
            
            for label, value in surfaces:
                row = tk.Frame(surface_content, bg="white")
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f"{label}:", font=("Arial", 11, "bold"), bg="white", fg="#2c3e50", anchor="w").pack(side="left")
                tk.Label(row, text=f"{value} wins", font=("Arial", 11), bg="white", fg="#7f8c8d", anchor="w").pack(side="right")
            
            # Action button
            button_frame = tk.Frame(main_frame, bg="#ecf0f1")
            button_frame.pack(fill="x", pady=15)
            
            tk.Button(
                button_frame, 
                text="🏆 View Tournament Wins", 
                command=lambda: self._toggle_hof_tournaments(player, True), 
                font=("Arial", 12, "bold"),
                bg="#f39c12",
                fg="white",
                relief="flat",
                bd=0,
                padx=20,
                pady=8,
                activebackground="#e67e22",
                activeforeground="white"
            ).pack()
        else:
            # Show tournament wins mode
            numwin = len(player.get('tournament_wins', []))
            hofpoints = player.get('hof_points', 0)
            
            # Stats header
            stats_frame = tk.Frame(self.root, bg="#ecf0f1")
            stats_frame.pack(fill="x", padx=20, pady=10)
            
            tk.Label(
                stats_frame,
                text=f"📊 Tournament Wins: {numwin} titles • HOF Points: {hofpoints}",
                font=("Arial", 12, "bold"),
                bg="#ecf0f1",
                fg="#2c3e50"
            ).pack()
            
            self.show_tournament_wins(player, back_command=lambda: self._toggle_hof_tournaments(player, False))
        
        # Back button
        back_frame = tk.Frame(self.root, bg="#ecf0f1")
        back_frame.pack(fill="x", padx=20, pady=15)
        
        tk.Button(
            back_frame, 
            text="🏛️ Back to Hall of Fame", 
            command=self.show_hall_of_fame, 
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            activebackground="#2980b9",
            activeforeground="white"
        ).pack()
        tk.Button(self.root, text="Back to Main Menu", command=self.build_main_menu, font=("Arial", 12)).pack(pady=2)

    def _toggle_hof_tournaments(self, player, show):
        self._show_tournaments = show
        self.show_hof_player_details(player)
        
    def show_achievements(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Modern header with background gradient effect
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=70)
        header_frame.pack(fill="x", pady=0)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🏆 All-Time Achievements", 
                font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(expand=True)

        # Get all available records and create mapping
        achievements = self.scheduler.records
        record_map = {}
        for record in achievements:
            title = record.get("title", record.get("type", "Unknown"))
            record_map[title] = record
        
        # Define the specific order for tabs as requested
        ordered_tabs = [
            "Most Tournament Wins",
            "Most Grand Slam Wins", 
            "Most Masters 1000 Wins",
            "Most Weeks at #1",
            "Most Weeks in Top 10",
            "Most Matches Won",
            "Most Matches Won - Hard",
            "Most Matches Won - Clay", 
            "Most Matches Won - Grass"
        ]
        
        # Filter to only show tabs that exist in records
        available_tabs = [tab for tab in ordered_tabs if tab in record_map]
        
        # Set default tab to first available record
        if not hasattr(self, 'current_achievements_tab') or self.current_achievements_tab not in record_map:
            self.current_achievements_tab = available_tabs[0] if available_tabs else "None"
        
        # Tab system with improved styling
        tab_container = tk.Frame(self.root, bg="#34495e", height=50)
        tab_container.pack(fill="x", pady=0)
        tab_container.pack_propagate(False)
        
        tab_frame = tk.Frame(tab_container, bg="#34495e")
        tab_frame.pack(expand=True)
        
        # Create tabs in the specified order (no scrolling)
        for i, tab_title in enumerate(available_tabs):
            is_active = tab_title == self.current_achievements_tab
            bg_color = "#3498db" if is_active else "#5d6d7e"
            fg_color = "white"
            
            btn = tk.Button(tab_frame, text=tab_title, bg=bg_color, fg=fg_color,
                          command=lambda t=tab_title: self.switch_achievements_tab(t),
                          font=("Arial", 9, "bold" if is_active else "normal"), 
                          relief="flat", bd=0, padx=8, pady=5,
                          activebackground="#2980b9", activeforeground="white")
            btn.pack(side="left", padx=1)

        # Display the current record's ranking with enhanced styling
        if self.current_achievements_tab in record_map:
            current_record = record_map[self.current_achievements_tab]
            
            # Content area with background
            content_frame = tk.Frame(self.root, bg="#ecf0f1")
            content_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Title for current record with icon
            title_frame = tk.Frame(content_frame, bg="#ecf0f1")
            title_frame.pack(fill="x", pady=(15, 10))
            
            record_icon = "🏆" if "Tournament" in self.current_achievements_tab else "🎾" if "Matches" in self.current_achievements_tab else "👑"
            tk.Label(title_frame, text=f"{record_icon} Top 10 - {current_record.get('title', 'Record')}", 
                    font=("Arial", 16, "bold"), bg="#ecf0f1", fg="#2c3e50").pack()

            # Scrollable frame for rankings with card-style design
            frame = tk.Frame(content_frame, bg="#ecf0f1")
            frame.pack(fill="both", expand=True, padx=10, pady=5)
            canvas = tk.Canvas(frame, bg="#ecf0f1", highlightthickness=0)
            scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            scroll_frame = tk.Frame(canvas, bg="#ecf0f1")
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

            # Display the ranking based on record type
            self._display_record_ranking(scroll_frame, current_record)
        else:
            tk.Label(self.root, text="No records available", font=("Arial", 12)).pack(pady=20)

        # Styled back button
        button_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        button_frame.pack(fill="x", pady=0)
        button_frame.pack_propagate(False)
        
        tk.Button(button_frame, text="← Back to Main Menu", command=self.build_main_menu, 
                 font=("Arial", 12, "bold"), bg="#3498db", fg="white", relief="flat",
                 activebackground="#2980b9", activeforeground="white", bd=0, padx=20, pady=8).pack(expand=True)
    
    def _display_record_ranking(self, parent_frame, record):
        """Display the ranking for a specific record type with enhanced card styling"""
        record_type = record.get("type", "")
        top10 = record.get("top10", [])
        
        for idx, entry in enumerate(top10):
            # Create card-like frame for each entry
            rank_colors = ["#f39c12", "#e67e22", "#d35400"]  # Gold, silver, bronze colors
            if idx < 3:
                bg_color = rank_colors[idx]
                fg_color = "white"
                font_weight = "bold"
            else:
                bg_color = "white"
                fg_color = "#2c3e50" 
                font_weight = "normal"
            
            entry_frame = tk.Frame(parent_frame, bg=bg_color, relief="raised", bd=1)
            entry_frame.pack(fill="x", padx=15, pady=3)
            
            # Format text based on record type
            if record_type == "most_t_wins":
                text = f"{idx+1}. {entry['name']} - {entry['t_wins']} Tournaments"
            elif record_type == "most_gs_wins":
                text = f"{idx+1}. {entry['name']} - {entry['gs_wins']} Grand Slams"
            elif record_type == "most_m1000_wins":
                text = f"{idx+1}. {entry['name']} - {entry['m1000_wins']} Masters 1000"
            elif record_type == "most_matches_won":
                text = f"{idx+1}. {entry['name']} - {entry['matches_won']} Matches"
            elif record_type.startswith("most_matches_won_"):
                surface = record_type.replace("most_matches_won_", "").capitalize()
                text = f"{idx+1}. {entry['name']} - {entry['matches_won']} Matches on {surface}"
            elif record_type == "most_weeks_at_1":
                text = f"{idx+1}. {entry['name']} - {entry['weeks']} Weeks at #1"
            elif record_type == "most_weeks_in_16":
                text = f"{idx+1}. {entry['name']} - {entry['weeks']} Weeks in Top 10"
            else:
                text = f"{idx+1}. {entry.get('name', 'Unknown')}"
                
            tk.Label(entry_frame, text=text, font=("Arial", 12, font_weight), 
                    bg=bg_color, fg=fg_color, anchor="w", padx=15, pady=8).pack(fill="x")

    def switch_achievements_tab(self, tab):
        self.current_achievements_tab = tab
        self.show_achievements()

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
        """Display tournaments with category tabs and modern styling"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Modern header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=70)
        header_frame.pack(fill="x", pady=0)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🏆 Current Week Tournaments", 
                font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(expand=True)

        # Tab system with modern styling
        tab_container = tk.Frame(self.root, bg="#34495e", height=50)
        tab_container.pack(fill="x", pady=0)
        tab_container.pack_propagate(False)
        
        tab_frame = tk.Frame(tab_container, bg="#34495e")
        tab_frame.pack(expand=True)
        
        # Content area with background
        content_frame = tk.Frame(self.root, bg="#ecf0f1")
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Get current week tournaments and extract categories
        tournaments = self.scheduler.get_current_week_tournaments()
        categories = sorted(set(t['category'] for t in tournaments))
        
        self.tournaments_current_tab = getattr(self, 'tournaments_current_tab', 'all')
        
        # Create tabs list
        tabs = [("All", 'all')]
        for category in categories:
            tabs.append((category, category))
        
        for tab_name, tab_id in tabs:
            is_active = tab_id == self.tournaments_current_tab
            bg_color = "#f39c12" if is_active else "#5d6d7e"  # Gold theme for tournaments
            
            btn = tk.Button(
                tab_frame,
                text=tab_name,
                bg=bg_color,
                fg="white",
                font=("Arial", 11, "bold" if is_active else "normal"),
                relief="flat",
                bd=0,
                padx=12,
                pady=8,
                activebackground="#e67e22",
                activeforeground="white",
                command=lambda t=tab_id: self.switch_tournaments_tab(t)
            )
            btn.pack(side="left", padx=2)
        
        # Content frame for tournament list
        self.tournaments_content_frame = tk.Frame(content_frame, bg="#ecf0f1")
        self.tournaments_content_frame.pack(fill="both", expand=True)
        
        # Show initial tab
        self.switch_tournaments_tab(self.tournaments_current_tab)
        
        # Styled back button
        button_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        button_frame.pack(fill="x", pady=0)
        button_frame.pack_propagate(False)
        
        tk.Button(button_frame, text="← Back to Main Menu", command=self.build_main_menu, 
                 font=("Arial", 12, "bold"), bg="#f39c12", fg="white", relief="flat",
                 activebackground="#e67e22", activeforeground="white", bd=0, padx=20, pady=8).pack(expand=True)

    def switch_tournaments_tab(self, tab_id):
        """Switch between tournament category tabs"""
        self.tournaments_current_tab = tab_id
        
        # Clear content
        for widget in self.tournaments_content_frame.winfo_children():
            widget.destroy()
        
        # Simulate all button
        tk.Button(
            self.tournaments_content_frame,
            text="Simulate All Tournaments This Week",
            font=("Arial", 12),
            command=self.simulate_all_current_week_tournaments
        ).pack(pady=4)
        
        # Get tournaments for this tab
        all_tournaments = self.scheduler.get_current_week_tournaments()
        if tab_id == 'all':
            tournaments = all_tournaments
        else:
            tournaments = [t for t in all_tournaments if t['category'] == tab_id]
        
        if not tournaments:
            tk.Label(self.tournaments_content_frame, 
                    text=f"No tournaments in category: {tab_id}", 
                    font=("Arial", 12)).pack(pady=20)
            return
        
        # Create scrollable tournament list
        frame = tk.Frame(self.tournaments_content_frame)
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
            # Create card-style tournament entry
            fav_t = self._tournament_has_favorite(t)
            
            # Tournament prestige-based styling
            if t['category'] == 'Grand Slam':
                bg_color = "#8e44ad"  # Purple for Grand Slams
                icon = "👑"
            elif 'Masters' in t['category']:
                bg_color = "#e67e22"  # Orange for Masters
                icon = "🏆"
            elif 'ATP 500' == t['category']:
                bg_color = "#f39c12"  # Gold for ATP 500
                icon = "🥇"
            elif 'ATP 250' == t['category']:
                bg_color = "#3498db"  # Blue for ATP 250
                icon = "🎾"
            else:
                bg_color = "#95a5a6"  # Gray for other tournaments
                icon = "🏟️"
            
            if fav_t:
                bg_color = "#e74c3c"  # Red highlight for tournaments with favorites
                icon = "⭐"
            
            # Main tournament card
            tournament_frame = tk.Frame(scroll_frame, bg=bg_color, relief="raised", bd=2)
            tournament_frame.pack(fill="x", padx=10, pady=5)
            
            # Tournament info section
            info_frame = tk.Frame(tournament_frame, bg=bg_color)
            info_frame.pack(fill="x", padx=15, pady=10)
            
            # Tournament name and details
            name_label = tk.Label(
                info_frame,
                text=f"{icon} {t['name']}",
                font=("Arial", 14, "bold"),
                bg=bg_color,
                fg="white",
                anchor="w"
            )
            name_label.pack(fill="x")
            
            details_label = tk.Label(
                info_frame,
                text=f"Category: {t['category']} • Surface: {t['surface']}",
                font=("Arial", 10),
                bg=bg_color,
                fg="#ecf0f1",
                anchor="w"
            )
            details_label.pack(fill="x", pady=(2, 0))
            
            # Button section
            button_frame = tk.Frame(tournament_frame, bg=bg_color)
            button_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            # View bracket button
            btn_manage = tk.Button(
                button_frame,
                text="🔍 View Bracket",
                font=("Arial", 11, "bold"),
                bg="white",
                fg=bg_color,
                relief="flat",
                bd=0,
                padx=15,
                pady=5,
                activebackground="#ecf0f1",
                activeforeground=bg_color,
                command=lambda tournament=t: self.show_tournament_bracket(tournament)
            )
            btn_manage.pack(side="left", padx=(0, 10))
            
            # Simulate tournament button
            btn_simulate = tk.Button(
                button_frame,
                text="⚡ Simulate Tournament",
                font=("Arial", 11, "bold"),
                bg="#2c3e50",
                fg="white",
                relief="flat",
                bd=0,
                padx=15,
                pady=5,
                activebackground="#34495e",
                activeforeground="white",
                command=functools.partial(self.simulate_entire_tournament_selected, [t])
            )
            btn_simulate.pack(side="left")

    def simulate_all_current_week_tournaments(self):
        tournaments = self.scheduler.get_current_week_tournaments()
        results = []
        for t in tournaments:
            if t.get('winner_id') is None:
                winner_id = self.scheduler.simulate_entire_tournament(t['id'])
                winner = next((p for p in self.scheduler.players if p['id'] == winner_id), None)
                results.append((t['name'], winner['name'] if winner else "Unknown"))

        # Show a summary popup and refresh the list
        popup = tk.Toplevel(self.root)
        popup.title("Weekly Simulation")
        if not results:
            msg = "No tournaments to simulate. All are already completed."
        else:
            lines = [f"- {name}: {winner}" for name, winner in results]
            msg = "Completed tournaments:\n" + "\n".join(lines)
        tk.Label(popup, text=msg, font=("Arial", 12), justify="left").pack(pady=10, padx=10)
        tk.Button(popup, text="OK", font=("Arial", 12),
                  command=lambda: [popup.destroy(), self.show_tournaments()]).pack(pady=6)

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
        
        # Modern header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Tournament prestige-based styling
        if tournament['category'] == 'Grand Slam':
            icon = "👑"
        elif 'Masters' in tournament['category']:
            icon = "🏆"
        elif 'ATP 500' == tournament['category']:
            icon = "🥇"
        elif 'ATP 250' == tournament['category']:
            icon = "🎾"
        else:
            icon = "🏟️"
        
        title_label = tk.Label(
            header_frame,
            text=f"{icon} {tournament['name']} Bracket",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(expand=True)
        
        # Modern control bar
        control_frame = tk.Frame(self.root, bg="#ecf0f1")
        control_frame.pack(fill="x", padx=20, pady=10)
        
        # Left navigation buttons
        left_nav = tk.Frame(control_frame, bg="#ecf0f1")
        left_nav.pack(side="left")
        
        tk.Button(
            left_nav, 
            text="↩️ Back to Tournaments", 
            command=self.show_tournaments, 
            font=("Arial", 11, "bold"),
            bg="#95a5a6",
            fg="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=6,
            activebackground="#7f8c8d",
            activeforeground="white"
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            left_nav, 
            text="🏠 Main Menu", 
            command=self.build_main_menu, 
            font=("Arial", 11, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=6,
            activebackground="#2980b9",
            activeforeground="white"
        ).pack(side="left")
        
        # Tournament info in center
        info_frame = tk.Frame(control_frame, bg="#ecf0f1")
        info_frame.pack(side="left", expand=True, padx=20)
        
        tk.Label(
            info_frame,
            text=f"{tournament['category']} • {tournament['surface']} Court",
            font=("Arial", 11),
            bg="#ecf0f1",
            fg="#7f8c8d"
        ).pack()
        
        # Right action button
        tk.Button(
            control_frame, 
            text="⚡ Simulate Current Round", 
            font=("Arial", 11, "bold"),
            bg="#e74c3c",
            fg="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=6,
            activebackground="#c0392b",
            activeforeground="white",
            command=lambda: self.simulate_current_round_bracket(tournament)
        ).pack(side="right")

        # Round-based tabs
        bracket = tournament.get('bracket', [])
        num_rounds = len(bracket)
        
        if num_rounds > 0:
            # Create round names based on tournament size
            round_names = self._get_round_names(num_rounds)
            
            # Modern tab system
            tab_container = tk.Frame(self.root, bg="#ecf0f1")
            tab_container.pack(fill="x", padx=20, pady=10)
            
            # Set default tab to show full bracket
            self.current_bracket_tab = getattr(self, 'current_bracket_tab', "Full Bracket")
            
            # Add "Full Bracket" option + individual rounds
            all_tabs = ["Full Bracket"] + round_names
            
            tab_frame = tk.Frame(tab_container, bg="#ecf0f1")
            tab_frame.pack()
            
            for tab in all_tabs:
                is_active = tab == self.current_bracket_tab
                
                btn = tk.Button(
                    tab_frame,
                    text=tab,
                    font=("Arial", 10, "bold" if is_active else "normal"),
                    bg="#e67e22" if is_active else "white",
                    fg="white" if is_active else "#2c3e50",
                    relief="flat",
                    bd=0,
                    padx=12,
                    pady=6,
                    activebackground="#d35400" if is_active else "#ecf0f1",
                    activeforeground="white" if is_active else "#2c3e50",
                    command=lambda t=tab: self.switch_bracket_tab(t, tournament)
                )
                btn.pack(side="left", padx=2)
        
        # Store tournament for tab switching
        self.current_tournament = tournament

        # Draw bracket based on selected tab
        self._draw_tournament_bracket(tournament)
    
    def _get_round_names(self, num_rounds):
        """Generate round names based on number of rounds"""
        if num_rounds == 1:
            return ["Final"]
        elif num_rounds == 2:
            return ["Semifinals", "Final"]
        elif num_rounds == 3:
            return ["Quarterfinals", "Semifinals", "Final"]
        elif num_rounds == 4:
            return ["Round of 16", "Quarterfinals", "Semifinals", "Final"]
        elif num_rounds == 5:
            return ["Round of 32", "Round of 16", "Quarterfinals", "Semifinals", "Final"]
        elif num_rounds == 6:
            return ["Round of 64", "Round of 32", "Round of 16", "Quarterfinals", "Semifinals", "Final"]
        elif num_rounds == 7:
            return ["Round of 128", "Round of 64", "Round of 32", "Round of 16", "Quarterfinals", "Semifinals", "Final"]
        else:
            # For very large tournaments, use generic round names
            names = []
            for i in range(num_rounds):
                if i == num_rounds - 1:
                    names.append("Final")
                elif i == num_rounds - 2:
                    names.append("Semifinals")
                elif i == num_rounds - 3:
                    names.append("Quarterfinals")
                else:
                    names.append(f"Round {i + 1}")
            return names
    
    def switch_bracket_tab(self, tab, tournament):
        """Switch between bracket view tabs"""
        self.current_bracket_tab = tab
        self.show_tournament_bracket(tournament)
    
    def _draw_tournament_bracket(self, tournament):
        """Draw the tournament bracket based on current tab selection"""
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
        match_gap = 100
        round_gap = 400
        y_offset = 40

        player_lookup = {p['id']: p for p in self.scheduler.players}
        def get_name_rank(pid):
            player = player_lookup.get(pid)
            if player:
                return f"{player['name']} ({player.get('rank', 'N/A')})"
            return "BYE"

        # Determine which rounds to display based on tab selection
        if self.current_bracket_tab == "Full Bracket":
            start_round = 0
            rounds_to_show = bracket
            display_offset = 0
        else:
            # Find which round corresponds to the selected tab
            round_names = self._get_round_names(num_rounds)
            if self.current_bracket_tab in round_names:
                start_round = round_names.index(self.current_bracket_tab)
                rounds_to_show = bracket[start_round:]
                display_offset = start_round
            else:
                # Fallback to full bracket
                start_round = 0
                rounds_to_show = bracket
                display_offset = 0

        # Store button references for command binding
        button_refs = []

        # Draw each round (starting from selected round)
        match_positions = []  # List of lists: match_positions[round][match_idx] = y

        for display_r, round_matches in enumerate(rounds_to_show):
            actual_round = start_round + display_r  # Actual round index in original bracket
            x = 40 + display_r * round_gap
            round_y_positions = []
            for m_idx, m in enumerate(round_matches):
                # For first displayed round, use regular spacing
                if display_r == 0:
                    y = y_offset + m_idx * (match_height + match_gap)
                else:
                    prev_y1 = match_positions[display_r-1][m_idx*2]
                    prev_y2 = match_positions[display_r-1][m_idx*2+1]
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

                p1_color = "blue" if (p1_id and player_lookup.get(p1_id, {}).get('favorite')) else "black"
                p2_color = "blue" if (p2_id and player_lookup.get(p2_id, {}).get('favorite')) else "black"

                # Player names (left aligned)
                canvas.create_text(x+10, y+match_height//2, anchor="w", text=p1, fill=p1_color,
                                   font=font_bold if winner_id == p1_id else font_normal)
                canvas.create_text(x+10, y+match_height+8+match_height//2, anchor="w", text=p2, fill=p2_color,
                                   font=font_bold if winner_id == p2_id else font_normal)

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

                if actual_round == tournament['current_round']:
                    btn_sim = tk.Button(canvas, text="Simulate", font=("Arial", 10),
                                    command=functools.partial(self.simulate_match_in_bracket, tournament, m_idx))
                    btn_watch = tk.Button(canvas, text="Watch", font=("Arial", 10),
                                      command=functools.partial(self.watch_match_in_bracket, tournament, m_idx))
                    btn_window_sim = canvas.create_window(x+10, y+2*match_height+18, anchor="nw", window=btn_sim)
                    btn_window_watch = canvas.create_window(x+80, y+2*match_height+18, anchor="nw", window=btn_watch)
                    button_refs.append((btn_sim, btn_watch))
                    
            match_positions.append(round_y_positions)
            # Draw lines to next round
            if display_r > 0:
                prev_x = 40 + (display_r-1) * round_gap
                for m_idx, y in enumerate(round_y_positions):
                    # Each match in this round comes from two matches in previous round
                    prev_y1 = match_positions[display_r-1][m_idx*2]
                    prev_y2 = match_positions[display_r-1][m_idx*2+1]
                    # Draw line from center of previous match 1 to center of this match
                    canvas.create_line(prev_x + rect_width, prev_y1 + match_height, x, y + match_height, fill=outline_color, width=2)
                    # Draw line from center of previous match 2 to center of this match
                    canvas.create_line(prev_x + rect_width, prev_y2 + match_height, x, y + match_height, fill=outline_color, width=2)
                    # Add Simulate/Watch buttons for current round matches
            
        max_x = 40 + len(rounds_to_show) * round_gap + rect_width + 100
        max_y = y_offset + (2 ** (len(rounds_to_show)-1 if rounds_to_show else 0)) * (match_height + match_gap)
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
        
        # Modern header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="📚 Tournament History",
            font=("Arial", 20, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(expand=True)
        
        # Modern tab system for tournament categories
        tab_container = tk.Frame(self.root, bg="#ecf0f1")
        tab_container.pack(fill="x", padx=20, pady=15)
        
        self.current_history_tab = getattr(self, 'current_history_tab', "All")
        
        # Get all tournament categories that exist
        tournaments_by_category = collections.defaultdict(list)
        for t in self.scheduler.tournaments:
            tournaments_by_category[t['category']].append(t)
        
        available_categories = ["All"] + [cat for cat in PRESTIGE_ORDER if cat in tournaments_by_category]
        
        tab_frame = tk.Frame(tab_container, bg="#ecf0f1")
        tab_frame.pack()
        
        for tab in available_categories:
            is_active = tab == self.current_history_tab
            
            btn = tk.Button(
                tab_frame,
                text=tab,
                font=("Arial", 11, "bold" if is_active else "normal"),
                bg="#3498db" if is_active else "white",
                fg="white" if is_active else "#2c3e50",
                relief="flat",
                bd=0,
                padx=15,
                pady=8,
                activebackground="#2980b9" if is_active else "#ecf0f1",
                activeforeground="white" if is_active else "#2c3e50",
                command=lambda t=tab: self.switch_history_tab(t)
            )
            btn.pack(side="left", padx=2)

        # Scrollable frame for tournament list
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

        # Display tournaments based on selected tab with card design
        def create_tournament_card(tournament):
            # Tournament prestige-based styling
            if tournament['category'] == 'Grand Slam':
                bg_color = "#8e44ad"  # Purple for Grand Slams
                icon = "👑"
            elif 'Masters' in tournament['category']:
                bg_color = "#e67e22"  # Orange for Masters
                icon = "🏆"
            elif 'ATP 500' == tournament['category']:
                bg_color = "#f39c12"  # Gold for ATP 500
                icon = "🥇"
            elif 'ATP 250' == tournament['category']:
                bg_color = "#3498db"  # Blue for ATP 250
                icon = "🎾"
            else:
                bg_color = "#95a5a6"  # Gray for other tournaments
                icon = "🏟️"
            
            # Main tournament card
            tournament_frame = tk.Frame(scroll_frame, bg=bg_color, relief="raised", bd=2)
            tournament_frame.pack(fill="x", padx=10, pady=5)
            
            # Tournament info section
            info_frame = tk.Frame(tournament_frame, bg=bg_color)
            info_frame.pack(fill="x", padx=15, pady=10)
            
            # Tournament name and surface
            name_label = tk.Label(
                info_frame,
                text=f"{icon} {tournament['name']}",
                font=("Arial", 14, "bold"),
                bg=bg_color,
                fg="white",
                anchor="w"
            )
            name_label.pack(fill="x")
            
            details_label = tk.Label(
                info_frame,
                text=f"Surface: {tournament['surface']} • Category: {tournament['category']}",
                font=("Arial", 10),
                bg=bg_color,
                fg="#ecf0f1",
                anchor="w"
            )
            details_label.pack(fill="x", pady=(2, 0))
            
            # History stats
            history = tournament.get('history', [])
            years_held = len(history)
            if history:
                recent_winner = sorted(history, key=lambda x: x['year'], reverse=True)[0].get('winner', 'Unknown')
                history_text = f"Years held: {years_held} • Last winner: {recent_winner}"
            else:
                history_text = "No tournament history yet"
            
            history_label = tk.Label(
                info_frame,
                text=history_text,
                font=("Arial", 9),
                bg=bg_color,
                fg="#bdc3c7",
                anchor="w"
            )
            history_label.pack(fill="x")
            
            # View history button
            button_frame = tk.Frame(tournament_frame, bg=bg_color)
            button_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            btn_history = tk.Button(
                button_frame,
                text="📖 View Complete History",
                font=("Arial", 11, "bold"),
                bg="white",
                fg=bg_color,
                relief="flat",
                bd=0,
                padx=15,
                pady=5,
                activebackground="#ecf0f1",
                activeforeground=bg_color,
                command=lambda tournament=tournament: self.show_tournament_history_details(tournament)
            )
            btn_history.pack(side="left")
        
        if self.current_history_tab == "All":
            # Show all categories with section headers
            for category in PRESTIGE_ORDER:
                if category in tournaments_by_category:
                    # Category header
                    category_frame = tk.Frame(scroll_frame, bg="#34495e")
                    category_frame.pack(fill="x", padx=10, pady=(15, 5))
                    
                    tk.Label(
                        category_frame,
                        text=f"📂 {category}",
                        font=("Arial", 13, "bold"),
                        bg="#34495e",
                        fg="white",
                        padx=15,
                        pady=8
                    ).pack(fill="x")
                    
                    for t in sorted(tournaments_by_category[category], key=lambda x: x['name']):
                        create_tournament_card(t)
        else:
            # Show specific category
            if self.current_history_tab in tournaments_by_category:
                for t in sorted(tournaments_by_category[self.current_history_tab], key=lambda x: x['name']):
                    create_tournament_card(t)
        
        # Modern back button
        back_frame = tk.Frame(self.root, bg="#ecf0f1")
        back_frame.pack(fill="x", padx=20, pady=15)
        
        tk.Button(
            back_frame, 
            text="🏠 Back to Main Menu", 
            command=self.build_main_menu, 
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            activebackground="#2980b9",
            activeforeground="white"
        ).pack()

    def switch_history_tab(self, tab):
        self.current_history_tab = tab
        self.show_history()
        
    def show_tournament_history_details(self, tournament):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Modern header with tournament styling
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Tournament prestige-based styling
        if tournament['category'] == 'Grand Slam':
            icon = "👑"
        elif 'Masters' in tournament['category']:
            icon = "🏆"
        elif 'ATP 500' == tournament['category']:
            icon = "🥇"
        elif 'ATP 250' == tournament['category']:
            icon = "🎾"
        else:
            icon = "🏟️"
        
        title_label = tk.Label(
            header_frame,
            text=f"{icon} {tournament['name']} History",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(expand=True)
        
        # Tournament info
        info_frame = tk.Frame(self.root, bg="#ecf0f1")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(
            info_frame,
            text=f"{tournament['category']} • {tournament['surface']} Court",
            font=("Arial", 12),
            bg="#ecf0f1",
            fg="#7f8c8d"
        ).pack()
        
        # Main content area
        main_frame = tk.Frame(self.root, bg="#ecf0f1")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        # Winners across the years
        history = tournament.get('history', [])
        
        if history:
            # Championship Roll Card
            history_card = tk.Frame(main_frame, bg="white", relief="raised", bd=2)
            history_card.pack(fill="both", expand=True, pady=(0, 10))
            
            tk.Label(
                history_card,
                text="📚 Championship Roll",
                font=("Arial", 14, "bold"),
                bg="#3498db",
                fg="white",
                padx=15,
                pady=8
            ).pack(fill="x")
            
            # Scrollable content for winners
            history_container = tk.Frame(history_card, bg="white")
            history_container.pack(fill="both", expand=True)
            
            canvas = tk.Canvas(history_container, bg="white", height=300)
            scrollbar = tk.Scrollbar(history_container, orient="vertical", command=canvas.yview)
            history_scroll_frame = tk.Frame(canvas, bg="white")
            
            history_scroll_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=history_scroll_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            scrollbar.pack(side="right", fill="y")
            
            # Display winners by year
            for entry in sorted(history, key=lambda x: x['year'], reverse=True):
                winner_name = entry.get('winner', 'Unknown')
                year = entry['year']
                
                winner_frame = tk.Frame(history_scroll_frame, bg="#f8f9fa", relief="solid", bd=1)
                winner_frame.pack(fill="x", padx=5, pady=2)
                
                year_label = tk.Label(
                    winner_frame,
                    text=str(year),
                    font=("Arial", 11, "bold"),
                    bg="#f8f9fa",
                    fg="#3498db",
                    width=6
                )
                year_label.pack(side="left", padx=10, pady=5)
                
                tk.Label(
                    winner_frame,
                    text=f"🏆 {winner_name}",
                    font=("Arial", 11),
                    bg="#f8f9fa",
                    fg="#2c3e50",
                    anchor="w"
                ).pack(side="left", fill="x", expand=True, padx=(0, 10), pady=5)
            
            # Mouse wheel scrolling
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
            
            # Record holders section
            win_counts = collections.Counter(entry.get('winner', 'Unknown') for entry in history)
            if win_counts:
                max_wins = max(win_counts.values())
                top_winners = [(name, count) for name, count in win_counts.items() if count == max_wins]
                
                records_card = tk.Frame(main_frame, bg="white", relief="raised", bd=2)
                records_card.pack(fill="x", pady=(0, 10))
                
                tk.Label(
                    records_card,
                    text="👑 Tournament Records",
                    font=("Arial", 14, "bold"),
                    bg="#f39c12",
                    fg="white",
                    padx=15,
                    pady=8
                ).pack(fill="x")
                
                records_content = tk.Frame(records_card, bg="white")
                records_content.pack(fill="x", padx=15, pady=10)
                
                tk.Label(
                    records_content,
                    text=f"Most Titles: {max_wins}",
                    font=("Arial", 12, "bold"),
                    bg="white",
                    fg="#2c3e50"
                ).pack(anchor="w", pady=(0, 5))
                
                for name, count in top_winners:
                    record_frame = tk.Frame(records_content, bg="#fff3cd")
                    record_frame.pack(fill="x", pady=2)
                    
                    tk.Label(
                        record_frame,
                        text=f"🏆 {name} ({count} titles)",
                        font=("Arial", 11, "bold"),
                        bg="#fff3cd",
                        fg="#856404",
                        padx=10,
                        pady=5
                    ).pack(anchor="w")
        else:
            # No history message
            no_history_frame = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
            no_history_frame.pack(fill="x", pady=50)
            tk.Label(
                no_history_frame, 
                text="📚 No tournament history available yet", 
                font=("Arial", 14), 
                bg="white", 
                fg="#7f8c8d", 
                pady=30
            ).pack()
        # Navigation buttons
        nav_frame = tk.Frame(self.root, bg="#ecf0f1")
        nav_frame.pack(fill="x", padx=20, pady=15)
        
        button_container = tk.Frame(nav_frame, bg="#ecf0f1")
        button_container.pack()
        
        tk.Button(
            button_container, 
            text="↩️ Back to History", 
            command=self.show_history, 
            font=("Arial", 12, "bold"),
            bg="#95a5a6",
            fg="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            activebackground="#7f8c8d",
            activeforeground="white"
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            button_container, 
            text="🏠 Back to Main Menu", 
            command=self.build_main_menu, 
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            activebackground="#2980b9",
            activeforeground="white"
        ).pack(side="left")

    def show_world_crown(self):
        """Display World Crown tournament interface"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Modern header with World Crown styling
        header_frame = tk.Frame(self.root, bg="#9b59b6", height=80)  # Purple for World Crown
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🌍 World Crown Tournament",
            font=("Arial", 20, "bold"),
            bg="#9b59b6",
            fg="white"
        )
        title_label.pack(expand=True)
        
        # Main container
        notebook_frame = tk.Frame(self.root, bg="#ecf0f1")
        notebook_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Modern tab system
        tab_container = tk.Frame(notebook_frame, bg="#ecf0f1")
        tab_container.pack(fill="x", pady=(0, 15))
        
        self.world_crown_current_tab = getattr(self, 'world_crown_current_tab', 'bracket')  # Default tab
        
        tabs = [
            ("🏆 Current Bracket", 'bracket'),
            ("⚡ Current Matches", 'matches'),
            ("🏴 Current Teams", 'teams'),
            ("📚 Winners History", 'history')
        ]
        
        tab_frame = tk.Frame(tab_container, bg="#ecf0f1")
        tab_frame.pack()
        
        # Store tab button references for later updates
        self.world_crown_tab_buttons = []
        
        for tab_name, tab_id in tabs:
            is_active = tab_id == self.world_crown_current_tab
            
            btn = tk.Button(
                tab_frame,
                text=tab_name,
                font=("Arial", 11, "bold" if is_active else "normal"),
                bg="#9b59b6" if is_active else "white",
                fg="white" if is_active else "#2c3e50",
                relief="flat",
                bd=0,
                padx=15,
                pady=8,
                activebackground="#8e44ad" if is_active else "#ecf0f1",
                activeforeground="white" if is_active else "#2c3e50",
                command=lambda t=tab_id: self.switch_world_crown_tab(t)
            )
            btn.pack(side="left", padx=2)
            self.world_crown_tab_buttons.append(btn)
        
        # Content frame with border
        content_container = tk.Frame(notebook_frame, bg="white", relief="raised", bd=2)
        content_container.pack(fill="both", expand=True)
        
        self.world_crown_content_frame = tk.Frame(content_container, bg="white")
        self.world_crown_content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Show initial tab
        self.switch_world_crown_tab(self.world_crown_current_tab)
        
        # Modern back button
        back_frame = tk.Frame(self.root, bg="#ecf0f1")
        back_frame.pack(fill="x", padx=20, pady=15)
        
        tk.Button(
            back_frame, 
            text="🏠 Back to Main Menu", 
            command=self.build_main_menu, 
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=8,
            activebackground="#2980b9",
            activeforeground="white"
        ).pack()

    def switch_world_crown_tab(self, tab_id):
        """Switch between World Crown tabs"""
        self.world_crown_current_tab = tab_id
        
        # Update tab button appearances
        self.update_world_crown_tabs()
        
        # Clear content
        for widget in self.world_crown_content_frame.winfo_children():
            widget.destroy()
        
        if tab_id == 'bracket':
            self.show_world_crown_bracket()
        elif tab_id == 'matches':
            self.show_world_crown_matches()
        elif tab_id == 'teams':
            self.show_world_crown_teams()
        elif tab_id == 'history':
            self.show_world_crown_history()
    
    def update_world_crown_tabs(self):
        """Update the appearance of World Crown tab buttons"""
        if hasattr(self, 'world_crown_tab_buttons'):
            tabs = [
                ("🏆 Current Bracket", 'bracket'),
                ("⚡ Current Matches", 'matches'),
                ("🏴 Current Teams", 'teams'),
                ("📚 Winners History", 'history')
            ]
            
            for i, (tab_name, tab_id) in enumerate(tabs):
                if i < len(self.world_crown_tab_buttons):
                    btn = self.world_crown_tab_buttons[i]
                    is_active = tab_id == self.world_crown_current_tab
                    
                    btn.config(
                        font=("Arial", 11, "bold" if is_active else "normal"),
                        bg="#9b59b6" if is_active else "white",
                        fg="white" if is_active else "#2c3e50",
                        activebackground="#8e44ad" if is_active else "#ecf0f1",
                        activeforeground="white" if is_active else "#2c3e50"
                    )

    def show_world_crown_bracket(self):
        """Show current World Crown bracket"""
        bracket = self.scheduler.world_crown.get('current_bracket', {})
        
        if not bracket:
            tk.Label(self.world_crown_content_frame, 
                    text="No World Crown tournament active for this year.", 
                    font=("Arial", 12)).pack(pady=20)
            return
        
        # Create scrollable frame
        canvas = tk.Canvas(self.world_crown_content_frame)
        scrollbar = tk.Scrollbar(self.world_crown_content_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Quarterfinals
        tk.Label(scroll_frame, text="QUARTERFINALS", font=("Arial", 14, "bold")).pack(pady=(10, 5))
        
        qf_frame = tk.Frame(scroll_frame)
        qf_frame.pack(fill="x", padx=20, pady=5)
        
        for qf_id, qf_data in bracket.get('quarterfinals', {}).items():
            qf_item = tk.Frame(qf_frame, relief="ridge", bd=1)
            qf_item.pack(fill="x", pady=2)
            
            # Match info
            team1 = qf_data['team1']
            team2 = qf_data['team2']
            week = qf_data['week']
            winner = qf_data.get('winner')
            
            if winner:
                result_text = f"{team1} vs {team2} (Week {week}) → Winner: {winner}"
                if 'team1_wins' in qf_data and 'team2_wins' in qf_data:
                    result_text += f" ({qf_data['team1_wins']}-{qf_data['team2_wins']})"
            else:
                result_text = f"{team1} vs {team2} (Week {week}) - Not played yet"
            
            tk.Label(qf_item, text=result_text, font=("Arial", 10)).pack(anchor="w", padx=5, pady=2)
        
        # Semifinals
        tk.Label(scroll_frame, text="SEMIFINALS", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        
        sf_frame = tk.Frame(scroll_frame)
        sf_frame.pack(fill="x", padx=20, pady=5)
        
        for sf_id, sf_data in bracket.get('semifinals', {}).items():
            sf_item = tk.Frame(sf_frame, relief="ridge", bd=1)
            sf_item.pack(fill="x", pady=2)
            
            team1 = sf_data['team1'] or "TBD"
            team2 = sf_data['team2'] or "TBD"
            week = sf_data['week']
            winner = sf_data.get('winner')
            
            if winner:
                result_text = f"{team1} vs {team2} (Week {week}) → Winner: {winner}"
                if 'team1_wins' in sf_data and 'team2_wins' in sf_data:
                    result_text += f" ({sf_data['team1_wins']}-{sf_data['team2_wins']})"
            else:
                result_text = f"{team1} vs {team2} (Week {week}) - Not played yet"
            
            tk.Label(sf_item, text=result_text, font=("Arial", 10)).pack(anchor="w", padx=5, pady=2)
        
        # Final
        tk.Label(scroll_frame, text="FINAL", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        
        final_frame = tk.Frame(scroll_frame)
        final_frame.pack(fill="x", padx=20, pady=5)
        
        final_data = bracket.get('final', {}).get('final', {})
        if final_data:
            final_item = tk.Frame(final_frame, relief="ridge", bd=1)
            final_item.pack(fill="x", pady=2)
            
            team1 = final_data['team1'] or "TBD"
            team2 = final_data['team2'] or "TBD"
            week = final_data['week']
            winner = final_data.get('winner')
            
            if winner:
                result_text = f"{team1} vs {team2} (Week {week}) → CHAMPION: {winner}"
                if 'team1_wins' in final_data and 'team2_wins' in final_data:
                    result_text += f" ({final_data['team1_wins']}-{final_data['team2_wins']})"
            else:
                result_text = f"{team1} vs {team2} (Week {week}) - Not played yet"
            
            tk.Label(final_item, text=result_text, font=("Arial", 10)).pack(anchor="w", padx=5, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_world_crown_matches(self):
        """Show current and recent World Crown matches"""
        current_week = self.scheduler.current_week
        matches = self.scheduler.get_world_crown_matches_for_week(current_week)
        
        # Header
        header_frame = tk.Frame(self.world_crown_content_frame, bg="white")
        header_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(header_frame, 
                text=f"World Crown Matches - Week {current_week}", 
                font=("Arial", 14, "bold"),
                bg="white").pack(pady=10)
        
        # Create scrollable container
        container_frame = tk.Frame(self.world_crown_content_frame, bg="white")
        container_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(container_frame, bg="white")
        scrollbar = tk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        # Temporarily change content frame to scrollable frame
        original_content_frame = self.world_crown_content_frame
        self.world_crown_content_frame = scrollable_frame
        
        try:
            # If no matches this week, look for completed matches in the bracket
            if not matches:
                recent_matches = []
                bracket = self.scheduler.world_crown.get('current_bracket', {})
                
                # Check all rounds for completed matches (in reverse order for most recent first)
                for round_type in ['final', 'semifinals', 'quarterfinals']:
                    if round_type in bracket:
                        for tie_id, tie_data in bracket[round_type].items():
                            if tie_data.get('winner') and tie_data.get('matches'):
                                recent_matches.append((round_type, tie_id, tie_data, tie_data.get('week', current_week)))
                
                if recent_matches:
                    tk.Label(scrollable_frame, 
                            text="📊 Recent World Crown Results", 
                            font=("Arial", 12, "bold"),
                            bg="white",
                            fg="#2c3e50").pack(pady=10)
                    
                    for round_type, tie_id, tie_data, match_week in recent_matches:
                        self._display_world_crown_tie_result(round_type, tie_id, tie_data, match_week)
                else:
                    no_matches_frame = tk.Frame(scrollable_frame, bg="#f8f9fa", relief="solid", bd=1)
                    no_matches_frame.pack(fill="x", padx=20, pady=50)
                    
                    tk.Label(no_matches_frame, 
                            text="⏰ No World Crown matches scheduled for this week", 
                            font=("Arial", 12),
                            bg="#f8f9fa",
                            fg="#6c757d",
                            pady=20).pack()
            else:
                # Show current matches
                tk.Label(scrollable_frame, 
                        text="⚡ Current World Crown Matches", 
                        font=("Arial", 12, "bold"),
                        bg="white",
                        fg="#2c3e50").pack(pady=10)
                
                for round_type, tie_id, tie_data in matches:
                    self._display_world_crown_tie(round_type, tie_id, tie_data)
        
        finally:
            # Restore original content frame
            self.world_crown_content_frame = original_content_frame
    
    def _display_world_crown_tie_result(self, round_type, tie_id, tie_data, week):
        """Display a completed World Crown tie result"""
        tie_frame = tk.Frame(self.world_crown_content_frame, relief="ridge", bd=2, bg="white")
        tie_frame.pack(fill="x", padx=20, pady=10)
        
        # Title with week info
        title_frame = tk.Frame(tie_frame, bg="#4caf50")
        title_frame.pack(fill="x")
        
        round_name = round_type.replace('_', ' ').title()
        tk.Label(title_frame, 
                text=f"✅ {round_name} (Week {week}): {tie_data['team1']} vs {tie_data['team2']}", 
                font=("Arial", 12, "bold"),
                bg="#4caf50",
                fg="white",
                pady=8).pack()
        
        # Get team rosters for player identification
        team1_players = self.scheduler.world_crown['current_year_teams'].get(tie_data['team1'], [])
        team2_players = self.scheduler.world_crown['current_year_teams'].get(tie_data['team2'], [])
        
        # Show match results
        if 'matches' in tie_data and tie_data['matches']:
            results_header = tk.Frame(tie_frame, bg="#2196f3")
            results_header.pack(fill="x", padx=10, pady=(10, 5))
            tk.Label(results_header, 
                    text="🏆 INDIVIDUAL MATCH RESULTS", 
                    font=("Arial", 11, "bold"),
                    bg="#2196f3",
                    fg="white",
                    pady=5).pack()
            
            matches_frame = tk.Frame(tie_frame, bg="white")
            matches_frame.pack(fill="x", padx=10, pady=5)
            
            for i, match in enumerate(tie_data['matches'], 1):
                match_result_frame = tk.Frame(matches_frame, bg="#f8f9fa", relief="solid", bd=1)
                match_result_frame.pack(fill="x", pady=2)
                
                winner_name = match['winner']
                loser_name = match['player1'] if match['winner'] == match['player2'] else match['player2']
                
                # Determine which team each player belongs to
                winner_team = tie_data['team1'] if winner_name in [p['name'] for p in team1_players] else tie_data['team2']
                loser_team = tie_data['team1'] if loser_name in [p['name'] for p in team1_players] else tie_data['team2']
                
                match_text = f"Match {i}: {winner_name} ({winner_team}) def. {loser_name} ({loser_team}) - {match['score']}"
                
                tk.Label(match_result_frame, 
                        text=match_text, 
                        font=("Arial", 10, "bold"),
                        bg="#f8f9fa",
                        anchor="w").pack(fill="x", padx=10, pady=5)
            
            # Show final result
            final_result_frame = tk.Frame(tie_frame, bg="#d4edda", relief="solid", bd=2)
            final_result_frame.pack(fill="x", padx=10, pady=10)
            
            tk.Label(final_result_frame, 
                    text=f"🏆 TIE WINNER: {tie_data['winner']} ({tie_data.get('team1_wins', 0)}-{tie_data.get('team2_wins', 0)})", 
                    font=("Arial", 12, "bold"),
                    bg="#d4edda",
                    fg="#155724").pack(pady=8)
    
    def _display_world_crown_tie(self, round_type, tie_id, tie_data):
        """Display a World Crown tie (current week)"""
        tie_frame = tk.Frame(self.world_crown_content_frame, relief="ridge", bd=2, bg="white")
        tie_frame.pack(fill="x", padx=20, pady=10)
        
        # Title with flags/colors
        title_frame = tk.Frame(tie_frame, bg="#9b59b6")
        title_frame.pack(fill="x")
        
        round_name = round_type.replace('_', ' ').title()
        tk.Label(title_frame, 
                text=f"🌍 {round_name}: {tie_data['team1']} 🆚 {tie_data['team2']}", 
                font=("Arial", 14, "bold"),
                bg="#9b59b6",
                fg="white",
                pady=8).pack()
        
        # Teams with better visual separation
        team1_players = self.scheduler.world_crown['current_year_teams'].get(tie_data['team1'], [])
        team2_players = self.scheduler.world_crown['current_year_teams'].get(tie_data['team2'], [])
        
        teams_container = tk.Frame(tie_frame, bg="white")
        teams_container.pack(fill="x", padx=15, pady=10)
        
        # Team 1 (Left side)
        team1_frame = tk.Frame(teams_container, bg="#e3f2fd", relief="solid", bd=1)
        team1_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Team 1 header
        team1_header = tk.Frame(team1_frame, bg="#2196f3")
        team1_header.pack(fill="x")
        tk.Label(team1_header, 
                text=f"🏴 {tie_data['team1']} National Team", 
                font=("Arial", 11, "bold"),
                bg="#2196f3",
                fg="white",
                pady=5).pack()
        
        # Team 1 players
        for i, player in enumerate(team1_players[:5], 1):
            player_frame = tk.Frame(team1_frame, bg="#e3f2fd")
            player_frame.pack(fill="x", padx=5, pady=2)
            tk.Label(player_frame, 
                    text=f"{i}. {player['name']} (#{player.get('rank', '???')})", 
                    font=("Arial", 10),
                    bg="#e3f2fd",
                    anchor="w").pack(fill="x")
        
        # VS separator
        vs_frame = tk.Frame(teams_container, bg="white", width=40)
        vs_frame.pack(side="left", fill="y")
        tk.Label(vs_frame, 
                text="🆚", 
                font=("Arial", 20, "bold"),
                bg="white",
                fg="#9b59b6").pack(expand=True)
        
        # Team 2 (Right side)
        team2_frame = tk.Frame(teams_container, bg="#fff3e0", relief="solid", bd=1)
        team2_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        # Team 2 header
        team2_header = tk.Frame(team2_frame, bg="#ff9800")
        team2_header.pack(fill="x")
        tk.Label(team2_header, 
                text=f"🏴 {tie_data['team2']} National Team", 
                font=("Arial", 11, "bold"),
                bg="#ff9800",
                fg="white",
                pady=5).pack()
        
        # Team 2 players
        for i, player in enumerate(team2_players[:5], 1):
            player_frame = tk.Frame(team2_frame, bg="#fff3e0")
            player_frame.pack(fill="x", padx=5, pady=2)
            tk.Label(player_frame, 
                    text=f"{i}. {player['name']} (#{player.get('rank', '???')})", 
                    font=("Arial", 10),
                    bg="#fff3e0",
                    anchor="w").pack(fill="x")
        
        # Show matches or simulate button
        if 'matches' in tie_data and tie_data['matches']:
            # Matches have been played - show results
            results_header = tk.Frame(tie_frame, bg="#4caf50")
            results_header.pack(fill="x", padx=10, pady=(10, 5))
            tk.Label(results_header, 
                    text="🏆 MATCH RESULTS", 
                    font=("Arial", 12, "bold"),
                    bg="#4caf50",
                    fg="white",
                    pady=5).pack()
            
            matches_frame = tk.Frame(tie_frame, bg="white")
            matches_frame.pack(fill="x", padx=10, pady=5)
            
            for i, match in enumerate(tie_data['matches'], 1):
                match_result_frame = tk.Frame(matches_frame, bg="#f8f9fa", relief="solid", bd=1)
                match_result_frame.pack(fill="x", pady=2)
                
                winner_name = match['winner']
                loser_name = match['player1'] if match['winner'] == match['player2'] else match['player2']
                
                # Determine which team each player belongs to
                winner_team = tie_data['team1'] if winner_name in [p['name'] for p in team1_players] else tie_data['team2']
                loser_team = tie_data['team1'] if loser_name in [p['name'] for p in team1_players] else tie_data['team2']
                
                match_text = f"Match {i}: {winner_name} ({winner_team}) def. {loser_name} ({loser_team}) - {match['score']}"
                
                tk.Label(match_result_frame, 
                        text=match_text, 
                        font=("Arial", 10, "bold"),
                        bg="#f8f9fa",
                        anchor="w").pack(fill="x", padx=10, pady=5)
            
            # Show final result
            final_result_frame = tk.Frame(tie_frame, bg="#d4edda" if tie_data.get('winner') else "#f8f9fa", 
                                        relief="solid", bd=2)
            final_result_frame.pack(fill="x", padx=10, pady=10)
            
            if tie_data.get('winner'):
                tk.Label(final_result_frame, 
                        text=f"🏆 TIE WINNER: {tie_data['winner']} ({tie_data.get('team1_wins', 0)}-{tie_data.get('team2_wins', 0)})", 
                        font=("Arial", 12, "bold"),
                        bg="#d4edda",
                        fg="#155724").pack(pady=8)
        else:
            # Matches not played yet - show simulate button
            button_frame = tk.Frame(tie_frame, bg="white")
            button_frame.pack(fill="x", padx=10, pady=10)
            
            btn = tk.Button(button_frame, 
                           text=f"⚡ Simulate {tie_data['team1']} vs {tie_data['team2']}", 
                           command=lambda rt=round_type, ti=tie_id: self.simulate_world_crown_tie(rt, ti),
                           font=("Arial", 11, "bold"),
                           bg="#f44336",
                           fg="white",
                           relief="flat",
                           bd=0,
                           padx=15,
                           pady=8,
                           activebackground="#d32f2f",
                           activeforeground="white")
            btn.pack()

    def simulate_world_crown_tie(self, round_type, tie_id):
        """Simulate a World Crown tie and refresh the display"""
        self.scheduler.simulate_world_crown_tie(round_type, tie_id)
        self.switch_world_crown_tab('matches')  # Refresh the matches view

    def show_world_crown_history(self):
        """Show World Crown winners history"""
        tk.Label(self.world_crown_content_frame, 
                text="World Crown Winners History", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        history = self.scheduler.world_crown.get('winners_history', [])
        
        if not history:
            tk.Label(self.world_crown_content_frame, 
                    text="No World Crown winners yet.", 
                    font=("Arial", 12)).pack(pady=20)
            return
        
        # Create scrollable frame
        canvas = tk.Canvas(self.world_crown_content_frame)
        scrollbar = tk.Scrollbar(self.world_crown_content_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Winners list
        for entry in sorted(history, key=lambda x: x['year'], reverse=True):
            winner_frame = tk.Frame(scroll_frame, relief="ridge", bd=1)
            winner_frame.pack(fill="x", padx=10, pady=2)
            
            year = entry['year']
            winner = entry['winner']
            score = entry.get('final_score', 'N/A')
            
            tk.Label(winner_frame, 
                    text=f"Year {year}: {winner} (Final: {score})", 
                    font=("Arial", 11)).pack(anchor="w", padx=5, pady=3)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_world_crown_teams(self):
        """Show current World Crown national teams and their players"""
        tk.Label(self.world_crown_content_frame, 
                text="World Crown National Teams", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        teams = self.scheduler.world_crown.get('current_year_teams', {})
        
        if not teams:
            tk.Label(self.world_crown_content_frame, 
                    text="No teams selected for this year yet.", 
                    font=("Arial", 12)).pack(pady=20)
            return
        
        # Create scrollable frame
        canvas = tk.Canvas(self.world_crown_content_frame)
        scrollbar = tk.Scrollbar(self.world_crown_content_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Display teams in a grid layout (2 columns)
        teams_container = tk.Frame(scroll_frame)
        teams_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Sort countries alphabetically for consistent display
        sorted_countries = sorted(teams.keys())
        
        for i, country in enumerate(sorted_countries):
            players = teams[country]
            
            # Create frame for each team (2 columns layout)
            col = i % 2
            row = i // 2
            
            team_frame = tk.Frame(teams_container, relief="ridge", bd=2, bg="white")
            team_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Configure grid weights for responsive layout
            teams_container.grid_columnconfigure(col, weight=1)
            
            # Country header
            country_header = tk.Frame(team_frame, bg="#4a90e2")
            country_header.pack(fill="x")
            
            tk.Label(country_header, 
                    text=f"{country} National Team", 
                    font=("Arial", 12, "bold"), 
                    bg="#4a90e2", 
                    fg="white").pack(pady=5)
            
            # Team composition info
            if len(players) > 0:
                info_frame = tk.Frame(team_frame)
                info_frame.pack(fill="x", padx=5, pady=2)
                
                tk.Label(info_frame, 
                        text=f"Team Size: {len(players)}/5 players", 
                        font=("Arial", 10), 
                        fg="gray").pack(anchor="w")
            
            # Players list
            players_frame = tk.Frame(team_frame)
            players_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            if not players:
                tk.Label(players_frame, 
                        text="No players available", 
                        font=("Arial", 10, "italic"), 
                        fg="red").pack(anchor="w", pady=5)
            else:
                # Column headers
                headers_frame = tk.Frame(players_frame)
                headers_frame.pack(fill="x", pady=(0, 3))
                
                tk.Label(headers_frame, text="#", font=("Arial", 9, "bold"), width=3).pack(side="left")
                tk.Label(headers_frame, text="Rank", font=("Arial", 9, "bold"), width=6).pack(side="left")
                tk.Label(headers_frame, text="Player Name", font=("Arial", 9, "bold")).pack(side="left", anchor="w")
                
                # Players
                for j, player in enumerate(players, 1):
                    player_frame = tk.Frame(players_frame)
                    player_frame.pack(fill="x", pady=1)
                    
                    # Position number
                    tk.Label(player_frame, 
                            text=f"{j}.", 
                            font=("Arial", 9), 
                            width=3).pack(side="left")
                    
                    # Player ranking
                    rank = player.get('rank', '???')
                    rank_color = "black"
                    if isinstance(rank, int):
                        if rank <= 10:
                            rank_color = "gold"
                        elif rank <= 50:
                            rank_color = "blue"
                        elif rank <= 100:
                            rank_color = "green"
                    
                    tk.Label(player_frame, 
                            text=f"#{rank}", 
                            font=("Arial", 9), 
                            fg=rank_color,
                            width=6).pack(side="left")
                    
                    # Player name - clickable to see details
                    name_color = "blue" if player.get('favorite', False) else "black"
                    name_btn = tk.Button(player_frame, 
                                        text=player['name'], 
                                        font=("Arial", 9), 
                                        fg=name_color,
                                        relief="flat",
                                        anchor="w",
                                        command=lambda p=player: self.show_player_details(p))
                    name_btn.pack(side="left", anchor="w")
                
                # Team statistics
                if players:
                    stats_frame = tk.Frame(team_frame, bg="#f0f0f0")
                    stats_frame.pack(fill="x", padx=5, pady=(5, 0))
                    
                    # Calculate team stats
                    ranks = [p.get('rank', 999) for p in players if isinstance(p.get('rank'), int)]
                    if ranks:
                        avg_rank = sum(ranks) / len(ranks)
                        best_rank = min(ranks)
                        
                        tk.Label(stats_frame, 
                                text=f"Team Stats: Best Player #{best_rank} | Average Rank: #{avg_rank:.1f}", 
                                font=("Arial", 8), 
                                bg="#f0f0f0",
                                fg="gray").pack(pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling support
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
if __name__ == "__main__":
    root = tk.Tk()
    root.title("TennisGM")
    app = TennisGMApp(root)
    root.mainloop()