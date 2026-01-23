import tkinter as tk
from schedule import TournamentScheduler
from sim.game_engine import GameEngine
from court_viewer import TennisCourtViewer
from utils.logo_utils import tournament_logo_manager
import collections
import sys
from io import StringIO
import functools
from archetypes import ARCTYPE_MAP, get_archetype_for_player

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
            # Ensure every active player has an archetype (added for backward compatibility)
            if 'archetype' not in p or 'archetype_key' not in p:
                try:
                    name, desc, key = get_archetype_for_player(p)
                    p['archetype'] = name
                    p['archetype_key'] = tuple(key)
                    changed = True
                except Exception:
                    # If archetype calculation fails, set a safe default
                    p.setdefault('archetype', 'Balanced Player')
                    p.setdefault('archetype_key', tuple())
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
            bg="#223e50",
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
            bg="#76e9e1",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=15,
            activebackground="#2980b9",
            activeforeground="white",
            command=lambda: self.handle_menu("Tournaments")
        )
        tournaments_btn.grid(row=1, column=0, columnspan=2, padx=10, pady=8, sticky="ew")
                
        # Row 2: ATP Rankings and Prospects
        rankings_btn = tk.Button(
            content_frame,
            text="🏅 ATP Rankings",
            font=("Arial", 12, "bold"),
            bg="#253138",
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
            bg="#376583",
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
            bg="#223e50",
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
            bg="#223e50",
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
                bg="#223e50",
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
                bg="#223e50",
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
        self.menu_options = ["News Feed", "Tournaments", "ATP Rankings", 
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
                return (5 * (round(sum(mods.values()), 3)))
            # Fallback if missing: neutral 1.0 each
            return 40.0

        def calc_fut(p):
            return (0.5*(round(calc_overall(p) + (22.5 * p.get("potential_factor", 1.0)) + calc_surface_sum(p), 1)))

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
        
        # Create two-column layout
        content_frame = tk.Frame(main_frame, bg="#ecf0f1")
        content_frame.pack(fill="both", expand=True)
        
        left_column = tk.Frame(content_frame, bg="#ecf0f1")
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        right_column = tk.Frame(content_frame, bg="#ecf0f1")
        right_column.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Configure grid weights for equal columns
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Left Column: Basic Info Card
        info_card = tk.Frame(left_column, bg="white", relief="raised", bd=2)
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
        
        # Right Column: Start with Archetype Card
        archetype_card = tk.Frame(right_column, bg="white", relief="raised", bd=2)
        archetype_card.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            archetype_card,
            text="🎭 Playing Style",
            font=("Arial", 14, "bold"),
            bg="#8e44ad",
            fg="white",
            padx=15,
            pady=8
        ).pack(fill="x")
        
        archetype_content = tk.Frame(archetype_card, bg="white")
        archetype_content.pack(fill="x", padx=15, pady=10)
        
        # Get player's archetype based on top 3 skills
        archetype, description = self._get_player_archetype(player)
        
        # Display archetype name
        tk.Label(
            archetype_content,
            text=archetype,
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#8e44ad",
            wraplength=350,
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        # Display archetype description
        tk.Label(
            archetype_content,
            text=description,
            font=("Arial", 11),
            bg="white",
            fg="#7f8c8d",
            wraplength=350,
            justify="left",
            anchor="w"
        ).pack(fill="x")
        
        # Calculate current ELO points for display
        current_elo_points = self.scheduler.ranking_system.get_elo_points(player, self.scheduler.current_date)
        
        basic_info = [
            ("🏆 Current Rank/ELO", f"#{player.get('rank', 'N/A')}/{current_elo_points}"),
            ("🎯 Highest Ranking/ELO", f"#{player.get('highest_ranking', 'N/A')}/{player.get('highest_elo', 'N/A')}"),
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
        surface_card = tk.Frame(left_column, bg="white", relief="raised", bd=2)
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
        skills_card = tk.Frame(right_column, bg="white", relief="raised", bd=2)
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
            label = tk.Label(row, text=f"{icon} {skill_name.capitalize()}:", font=("Arial", 11, "bold"), bg="white", fg="#2c3e50", anchor="w")
            label.pack(side="left")
            tk.Label(row, text=f"{val}{suffix}", font=("Arial", 11), bg="white", fg="#7f8c8d", anchor="w").pack(side="right")
                    
        # Career stats card
        stats_card = tk.Frame(left_column, bg="white", relief="raised", bd=2)
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
            ("🏅 Weeks at #1", player.get('w1', 0)),
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
                else:
                    text.insert("end", f"• {line}\n", "normal")
            
            # Configure text tags for styling
            text.tag_configure("winner", foreground="#27ae60", font=("Arial", 12, "bold"))
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
                    
                    # Tournament info with logo
                    tournament_info_frame = tk.Frame(info_frame, bg=win_frame['bg'])
                    tournament_info_frame.pack(side="left", fill="x", expand=True)
                    
                    # Try to find tournament ID from current tournaments for logo
                    tournament_logo = None
                    try:
                        for t in self.scheduler.tournaments:
                            if t.get('name') == tname:
                                tournament_logo = tournament_logo_manager.get_tournament_logo(t.get('id'))
                                break
                    except:
                        pass
                    
                    if tournament_logo:
                        # Display with logo
                        logo_label = tk.Label(tournament_info_frame, image=tournament_logo, bg=win_frame['bg'])
                        logo_label.pack(side="left", padx=(0, 8))
                        logo_label.image = tournament_logo  # Keep reference
                        
                        tk.Label(
                            tournament_info_frame,
                            text=f"{count}x {tname}",
                            font=("Arial", 11, "bold" if is_recent_win else "normal"),
                            bg=win_frame['bg'],
                            fg="#2c3e50",
                            anchor="w"
                        ).pack(side="left", fill="x", expand=True)
                    else:
                        # Fallback to trophy emoji
                        tk.Label(
                            tournament_info_frame,
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
        if hof_points >= 20:
            status_icon = "👑"  # Legend
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
                ("🎯 Highest Ranking/ELO", f"#{player.get('highest_ranking', 'N/A')}/{player.get('highest_elo', 'No Data')}"),
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

    def _get_player_archetype(self, player):
        """Return (archetype_name, archetype_description) using stored archetype when present.

        Preference order:
        1. If the player has an `archetype_key` and it exists in ARCTYPE_MAP, use that.
        2. If the player has an `archetype` name, look it up in ARCTYPE_MAP by name.
        3. Fallback to computing from current skills using `get_archetype_for_player`.
        """
        # 1) Use stored archetype_key when available
        ak = player.get('archetype_key')
        if ak:
            try:
                key = tuple(ak)
                if key in ARCTYPE_MAP:
                    name, desc = ARCTYPE_MAP[key]
                    return name, desc
            except Exception:
                pass

        # 2) Use stored archetype name to find description
        if 'archetype' in player:
            a_name = player['archetype']
            for k, (n, d) in ARCTYPE_MAP.items():
                if n == a_name:
                    return n, d
            # If name not found, return stored name with a short fallback description
            return a_name, "A defined archetype assigned at generation."

        # 3) Fallback: compute from current stats
        try:
            name, desc, key = get_archetype_for_player(player)
            return name, desc
        except Exception:
            return "Balanced Player", (
                "A well-rounded player who does not strongly fit any single archetype. "
                "They combine steady technique, tactical awareness, and adaptable physical traits to navigate matches."
            )
        
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
            elif 'Masters' in t['category']:
                bg_color = "#e67e22"  # Orange for Masters
            elif 'ATP 500' == t['category']:
                bg_color = "#f39c12"  # Gold for ATP 500
            elif 'ATP 250' == t['category']:
                bg_color = "#3498db"  # Blue for ATP 250
            else:
                bg_color = "#95a5a6"  # Gray for other tournaments
            
            if fav_t:
                bg_color = "#e74c3c"  # Red highlight for tournaments with favorites
            
            # Main tournament card
            tournament_frame = tk.Frame(scroll_frame, bg=bg_color, relief="raised", bd=2)
            tournament_frame.pack(fill="x", padx=10, pady=5)
            
            # Tournament info section
            info_frame = tk.Frame(tournament_frame, bg=bg_color)
            info_frame.pack(fill="x", padx=15, pady=10)
            
            # Tournament name with logo
            name_frame = tk.Frame(info_frame, bg=bg_color)
            name_frame.pack(fill="x")
            
            # Try to get tournament logo
            logo = tournament_logo_manager.get_tournament_logo(t.get('id'))
            
            if logo:
                # Display logo
                logo_label = tk.Label(name_frame, image=logo, bg=bg_color)
                logo_label.pack(side="left", padx=(0, 8))
                logo_label.image = logo  # Keep reference
            else:
                # Fallback to emoji based on category
                if t['category'] == 'Grand Slam':
                    icon = "👑"
                elif 'Masters' in t['category']:
                    icon = "🏆"
                elif 'ATP 500' == t['category']:
                    icon = "🥇"
                elif 'ATP 250' == t['category']:
                    icon = "🎾"
                else:
                    icon = "🏟️"
                
                if fav_t:
                    icon = "⭐"
                    
                icon_label = tk.Label(
                    name_frame,
                    text=icon,
                    font=("Arial", 16),
                    bg=bg_color,
                    fg="white"
                )
                icon_label.pack(side="left", padx=(0, 8))
            
            # Tournament name
            name_label = tk.Label(
                name_frame,
                text=t['name'],
                font=("Arial", 14, "bold"),
                bg=bg_color,
                fg="white",
                anchor="w"
            )
            name_label.pack(side="left", fill="x", expand=True)
            
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
    
    def get_player_seed(self, player_id, tournament):
        """Calculate the seed of a player in a tournament based on ranking."""
        participant_ids = tournament.get('participants', [])
        if not participant_ids:
            return None
        
        # Convert participant IDs to player objects
        participants = []
        for pid in participant_ids:
            player = next((p for p in self.scheduler.players if p['id'] == pid), None)
            if player:
                participants.append(player)
        
        if not participants:
            return None
        
        # Sort participants by ranking (lower ranking number = better)
        sorted_participants = sorted(
            participants,
            key=lambda p: p.get('ranking', float('inf'))
        )
        
        # Find player position
        for seed, participant in enumerate(sorted_participants, 1):
            if participant['id'] == player_id:
                return seed
        return None
    
    def get_player_last_tournament_won(self, player):
        """Get the last tournament won by a player."""
        # Check if the player has tournament_wins list and it's not empty
        if 'tournament_wins' in player and player['tournament_wins']:
            # Get the last (most recent) tournament win
            last_win = player['tournament_wins'][-1]
            return last_win.get('name', 'Unknown Tournament')
        return "None"
    
    def show_player_faceoff_bracket(self, player1, player2, tournament, match_idx):
        """Display a professional face-off screen between two players before the match (for bracket tournaments)."""
        # Clear screen
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_frame = tk.Frame(self.root, bg="#1a2332")
        main_frame.pack(fill="both", expand=True)
        
        # Header with title
        header_frame = tk.Frame(main_frame, bg="#2c3e50", height=80)
        header_frame.pack(fill="x", pady=0)
        header_frame.pack_propagate(False)
        
        title = tk.Label(
            header_frame,
            text="MATCH PREVIEW",
            font=("Arial", 24, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=20
        )
        title.pack()
        
        # Get player data
        p1_ranking = player1.get('rank', 'N/A')
        p2_ranking = player2.get('rank', 'N/A')
        p1_age = player1.get('age', 'N/A')
        p2_age = player2.get('age', 'N/A')
        p1_elo = self.scheduler.ranking_system.get_elo_points(player1, self.scheduler.current_date)
        p2_elo = self.scheduler.ranking_system.get_elo_points(player2, self.scheduler.current_date)
        
        # Skill abbreviation mapping
        skill_abbreviations = {
            'serve': 'SRV',
            'forehand': 'FRH',
            'backhand': 'BKH',
            'cross': 'CRS',
            'straight': 'STR',
            'speed': 'SPD',
            'stamina': 'STA',
            'dropshot': 'DRP',
            'volley': 'VOL'
        }
        
        # Helper function to create skill bars
        def create_skill_bar(parent, skill_name, p1_val, p2_val, max_val=100):
            bar_frame = tk.Frame(parent, bg="#1a2332")
            bar_frame.pack(fill="x", pady=15)
            
            # P1 bar and value
            p1_container = tk.Frame(bar_frame, bg="#1a2332")
            p1_container.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            p1_bar_frame = tk.Frame(p1_container, bg="#34495e", height=12, relief="sunken", bd=1)
            p1_bar_frame.pack(fill="x")
            p1_bar_frame.pack_propagate(False)
            
            p1_fill_width = int(610 * (p1_val / 100)) if p1_val > 0 else 0
            p1_fill = tk.Frame(p1_bar_frame, bg="#3498db" if p1_val > p2_val else "#7f8c8d", height=12)
            p1_fill.pack(side="right", fill="y")
            p1_fill.pack_propagate(False)
            if p1_fill_width > 0:
                p1_fill.config(width=p1_fill_width)
            
            tk.Label(bar_frame, text=f"{p1_val}", font=("Arial", 9, "bold"), 
                    bg="#1a2332", fg="#3498db" if p1_val > p2_val else "#ecf0f1", width=3, anchor="e").pack(side="left", padx=2)
            
            # Skill abbreviation label (replacing "VS")
            skill_abbr = skill_abbreviations.get(skill_name, skill_name[:3].upper())
            tk.Label(bar_frame, text=skill_abbr, font=("Arial", 9, "bold"), 
                bg="#1a2332", fg="#ffffff", padx=5).pack(side="left")
            
            # P2 value and bar
            tk.Label(bar_frame, text=f"{p2_val}", font=("Arial", 9, "bold"), 
                    bg="#1a2332", fg="#e74c3c" if p2_val > p1_val else "#ecf0f1", width=3, anchor="w").pack(side="left", padx=2)
            
            p2_container = tk.Frame(bar_frame, bg="#1a2332")
            p2_container.pack(side="left", fill="x", expand=True, padx=(5, 0))
            
            p2_bar_frame = tk.Frame(p2_container, bg="#34495e", height=12, relief="sunken", bd=1)
            p2_bar_frame.pack(fill="x")
            p2_bar_frame.pack_propagate(False)
            
            p2_fill_width = int(610 * (p2_val / 100)) if p2_val > 0 else 0
            p2_fill = tk.Frame(p2_bar_frame, bg="#e74c3c" if p2_val > p1_val else "#7f8c8d", height=12)
            p2_fill.pack(side="left", fill="y")
            p2_fill.pack_propagate(False)
            if p2_fill_width > 0:
                p2_fill.config(width=p2_fill_width)
        
        # Main content area with top section (two player bios side by side)
        content_frame = tk.Frame(main_frame, bg="#1a2332")
        content_frame.pack(fill="both", expand=False, padx=30, pady=(20, 0))
        
        # Left player info panel
        p1_panel = tk.Frame(content_frame, bg="#2c3e50", relief="raised", bd=2)
        p1_panel.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        # Player 1 name header
        p1_header = tk.Frame(p1_panel, bg="#3498db", height=50)
        p1_header.pack(fill="x")
        p1_header.pack_propagate(False)
        
        tk.Label(p1_header, text=player1['name'], font=("Arial", 16, "bold"), 
                bg="#3498db", fg="white", padx=15, pady=10).pack(side="left", fill="x", expand=True)
        
        p1_content = tk.Frame(p1_panel, bg="#2c3e50")
        p1_content.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Player 1 basic info only (no skills)
        p1_info_text = f"""Ranking: #{p1_ranking} - ELO: {p1_elo}
Archetype: {player1.get('archetype', 'N/A')}
Last Title: {self.get_player_last_tournament_won(player1)}
{p1_age}yo"""
        
        tk.Label(p1_content, text=p1_info_text, font=("Arial", 10), 
                bg="#2c3e50", fg="#ecf0f1", justify="left", anchor="w").pack(fill="x")
        
        # Center "VS" divider
        center_frame = tk.Frame(content_frame, bg="#1a2332", width=80)
        center_frame.pack(side="left", fill="both", padx=10)
        center_frame.pack_propagate(False)
        
        vs_label = tk.Label(center_frame, text="VS", font=("Arial", 20, "bold"), 
                          bg="#1a2332", fg="#f39c12")
        vs_label.pack(expand=True)
        
        # Right player info panel
        p2_panel = tk.Frame(content_frame, bg="#2c3e50", relief="raised", bd=2)
        p2_panel.pack(side="left", fill="both", expand=True, padx=(15, 0))
        
        # Player 2 name header
        p2_header = tk.Frame(p2_panel, bg="#e74c3c", height=50)
        p2_header.pack(fill="x")
        p2_header.pack_propagate(False)
        
        tk.Label(p2_header, text=player2['name'], font=("Arial", 16, "bold"), 
                bg="#e74c3c", fg="white", padx=15, pady=10).pack(side="right", fill="x", expand=True, anchor="e")
        
        p2_content = tk.Frame(p2_panel, bg="#2c3e50")
        p2_content.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Player 2 basic info only (no skills)
        p2_info_text = f"""Ranking: #{p2_ranking} - ELO: {p2_elo}
Archetype: {player2.get('archetype', 'N/A')}
Last Title: {self.get_player_last_tournament_won(player2)}
{p2_age}yo"""
        
        tk.Label(p2_content, text=p2_info_text, font=("Arial", 10), 
                bg="#2c3e50", fg="#ecf0f1", justify="left", anchor="w").pack(fill="x")
        
        # Centered skills comparison section below
        p1_skills = player1.get('skills', {})
        p2_skills = player2.get('skills', {})
        max_skill = max(
            max(p1_skills.values()) if p1_skills else 0,
            max(p2_skills.values()) if p2_skills else 0,
            100
        )
        
        skills_frame = tk.Frame(main_frame, bg="#1a2332")
        skills_frame.pack(fill="both", expand=True, padx=100, pady=20)
        
        tk.Label(skills_frame, text="SKILLS COMPARISON", font=("Arial", 12, "bold"), 
                bg="#1a2332", fg="#f39c12").pack(anchor="center", pady=(0, 15))
        
        for skill in ['serve', 'forehand', 'backhand', 'cross', 'straight', 'speed', 'stamina', 'dropshot', 'volley']:
            p1_val = p1_skills.get(skill, 0)
            p2_val = p2_skills.get(skill, 0)
            create_skill_bar(skills_frame, skill, p1_val, p2_val, max_skill)
        
        # Button frame at bottom
        button_frame = tk.Frame(main_frame, bg="#2c3e50", height=80)
        button_frame.pack(fill="x", pady=0)
        button_frame.pack_propagate(False)
        
        def start_match():
            # Simulate and save the match - get the exact same data to visualize
            result = self.scheduler.simulate_through_match(tournament['id'], match_idx)
            
            # Unpack the returned tuple: (winner_id, match_log, point_events)
            if isinstance(result, tuple) and len(result) == 3:
                winner_id, match_log, all_point_events = result
            else:
                # Fallback if returns just winner_id
                winner_id = result
                match_log = []
                all_point_events = []
            
            # Refresh tournament display with the saved result
            self.manage_tournament(tournament)
            
            # Get the final score from the match we just saved
            match = self.scheduler.get_current_matches(tournament['id'])[match_idx]
            final_score = match[3] if len(match) > 3 else ""
            
            # Create a GameEngine object for display purposes (to access player data)
            sets_to_win = 3 if tournament.get('category') == "Grand Slam" else 2
            game_engine = GameEngine(player1, player2, tournament['surface'], sets_to_win=sets_to_win)
            game_engine.final_score = final_score  # Store the final score
            
            # Display the visualization using the SAME data that was saved
            self.display_simple_match_log(match_log, tournament, all_point_events, player1, player2, game_engine)
        
        tk.Button(
            button_frame,
            text="▶️ START MATCH",
            font=("Arial", 14, "bold"),
            bg="#27ae60",
            fg="white",
            padx=30,
            pady=15,
            relief="raised",
            bd=0,
            command=start_match
        ).pack(side="left", padx=20, expand=True)
        
        tk.Button(
            button_frame,
            text="⬅️ BACK",
            font=("Arial", 14, "bold"),
            bg="#95a5a6",
            fg="white",
            padx=30,
            pady=15,
            relief="raised",
            bd=0,
            command=lambda: self.show_tournament_bracket(tournament)
        ).pack(side="left", padx=20, expand=True)
        
        # Force screen update to ensure faceoff screen is displayed
        self.root.update()

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

        # Check for BYE match
        if not match['player1'] or not match['player2']:
            match_log = ["BYE - Player advances automatically"]
            winner = match['player1'] or match['player2']  # Get the non-None player
            tournament['active_matches'][match_idx][2] = winner['id']
            self.display_simple_match_log(match_log, tournament, None)
            return

        # Get player data
        player1 = next(p for p in self.scheduler.players if p['id'] == match['player1']['id'])
        player2 = next(p for p in self.scheduler.players if p['id'] == match['player2']['id'])
        
        # Show face-off screen - simulation will happen when user clicks "Start Match"
        self.show_player_faceoff(player1, player2, tournament, match_idx)

    def display_simple_match_log(self, match_log, tournament, point_events=None, player1=None, player2=None, game_engine=None):
        idx = 0
        canvas = None  # Keep canvas reference for cleanup
        
        # Store animation control
        self.animation_active = True  # Flag to control animation
        self.pending_callbacks = []  # Store callback IDs to cancel them
        self.current_point_idx = 0  # Track current point for keyboard navigation
        self.max_points = len(match_log) if match_log else 0  # Track max points
        self.scheduled_advance_idx = -1  # Track if auto-advance is scheduled
        
        def cleanup_bindings():
            # Clean up mouse wheel bindings
            if canvas:
                try:
                    canvas.unbind_all('<MouseWheel>')
                    canvas.unbind_all('<Button-4>')
                    canvas.unbind_all('<Button-5>')
                except:
                    pass
            # Cancel any pending callbacks safely
            callbacks_to_remove = []
            for callback_id in self.pending_callbacks:
                try:
                    self.root.after_cancel(callback_id)
                    callbacks_to_remove.append(callback_id)
                except Exception:
                    # Callback may have already executed or been cancelled
                    callbacks_to_remove.append(callback_id)
            # Remove processed callbacks from list
            for callback_id in callbacks_to_remove:
                self.pending_callbacks.remove(callback_id)
        
        # Court is now drawn by TennisCourtViewer
            
        def draw_ball_positions(canvas, events, header_frame, next_idx=None):
            # Get score info and count shots
            num_shots = 0
            score_info = None
            for event in events:
                if event['type'] == 'shot':
                    num_shots += 1
                elif event['type'] == 'score':
                    score_info = event
            
            # Flatten all ball positions into a single list with their properties
            all_shots = []
            for i, event in enumerate(events):
                if event['type'] == 'shot':
                    ball_positions = event.get('ball_positions', [])
                    for ball_pos in ball_positions:
                        all_shots.append({
                            'x': ball_pos['x'],
                            'y': ball_pos['y'],
                            'power': ball_pos['power'],
                            'is_serve': event['shot_type'] == 'serve'
                        })
            
            def animate_shot(shot_index=0):
                if shot_index < len(all_shots):
                    # Clear previous balls
                    canvas.delete("ball")
                    
                    # Draw only the current ball
                    shot = all_shots[shot_index]
                    x, y = shot['x'], shot['y']
                    power = shot['power']
                    size = min(10, 5 + (power / 20))
                                        
                    # Choose ball color: red for last shot, yellow for serves, white for regular shots
                    if shot_index == len(all_shots) - 1:
                        ball_color = "red"  # Last ball is always red
                    else:
                        ball_color = "yellow" if shot['is_serve'] else "white"
                    
                    canvas.create_oval(x-size, y-size, x+size, y+size,
                                    fill=ball_color,
                                    outline="white",
                                    tags="ball")
                    
                    # Schedule next ball after 1 second if animation is active
                    if self.animation_active:
                        if shot_index == len(all_shots) - 1:
                            # For the last ball, update score
                            def update_header():
                                if score_info:
                                    # Clear previous score label
                                    for widget in header_frame.winfo_children():
                                        widget.destroy()
                                    
                                    # Create simple scoreboard - only player names and scores
                                    sets = score_info['sets']
                                    current_set = score_info['current_set']
                                    p1_name = score_info['player1_name']
                                    p2_name = score_info['player2_name']
                                    
                                    score_frame = tk.Frame(header_frame, bg="#34495e")
                                    score_frame.pack(fill="x", padx=100)
                                    
                                    # Determine which sets each player won
                                    set_winners = []
                                    for set_idx, set_tuple in enumerate(sets):
                                        p1_games, p2_games = set_tuple
                                        # A set is won when someone reaches 6+ games with 2+ game lead
                                        if p1_games >= 6 and p1_games - p2_games >= 2:
                                            set_winners.append(1)  # Player 1 won
                                        elif p2_games >= 6 and p2_games - p1_games >= 2:
                                            set_winners.append(2)  # Player 2 won
                                        elif p1_games == 7 and p2_games == 6:
                                            set_winners.append(1)
                                        elif p2_games == 7 and p1_games == 6:
                                            set_winners.append(2)
                                        else:
                                            set_winners.append(0)  # Set still in progress
                                    
                                    # Player 1 row
                                    p1_row = tk.Frame(score_frame, bg="#3498db")
                                    p1_row.pack(fill="x", pady=2)
                                    
                                    # Create a frame to hold all score elements with mixed formatting
                                    p1_score_frame = tk.Frame(p1_row, bg="#3498db")
                                    p1_score_frame.pack(padx=10, pady=5)
                                    
                                    # Add player name
                                    tk.Label(p1_score_frame, text=p1_name + "  ", font=("Arial", 11, "bold"), bg="#3498db", fg="white").pack(side="left")
                                    
                                    # Add each completed set score with appropriate formatting
                                    for set_idx, set_tuple in enumerate(sets):
                                        score_val = str(set_tuple[0])
                                        is_winner = set_idx < len(set_winners) and set_winners[set_idx] == 1
                                        font = ("Arial", 11, "bold") if is_winner else ("Arial", 11)
                                        tk.Label(p1_score_frame, text=score_val + "  ", font=font, bg="#3498db", fg="white").pack(side="left")
                                    
                                    # Add current set in progress
                                    tk.Label(p1_score_frame, text=str(current_set['player1']), font=("Arial", 11, "bold"), bg="#3498db", fg="white").pack(side="left")
                                    
                                    # Player 2 row
                                    p2_row = tk.Frame(score_frame, bg="#e74c3c")
                                    p2_row.pack(fill="x", pady=2)
                                    
                                    # Create a frame to hold all score elements with mixed formatting
                                    p2_score_frame = tk.Frame(p2_row, bg="#e74c3c")
                                    p2_score_frame.pack(padx=10, pady=5)
                                    
                                    # Add player name
                                    tk.Label(p2_score_frame, text=p2_name + "  ", font=("Arial", 11, "bold"), bg="#e74c3c", fg="white").pack(side="left")
                                    
                                    # Add each completed set score with appropriate formatting
                                    for set_idx, set_tuple in enumerate(sets):
                                        score_val = str(set_tuple[1])
                                        is_winner = set_idx < len(set_winners) and set_winners[set_idx] == 2
                                        font = ("Arial", 11, "bold") if is_winner else ("Arial", 11)
                                        tk.Label(p2_score_frame, text=score_val + "  ", font=font, bg="#e74c3c", fg="white").pack(side="left")
                                    
                                    # Add current set in progress
                                    tk.Label(p2_score_frame, text=str(current_set['player2']), font=("Arial", 11, "bold"), bg="#e74c3c", fg="white").pack(side="left")
                            # Update score after all shots
                            callback_id = canvas.after(2000, update_header)
                            self.pending_callbacks.append(callback_id)
                            
                            # Schedule auto-advance after the animation completes (2 seconds)
                            if next_idx is not None and next_idx < len(match_log):
                                # Use after_idle to safely schedule the screen transition after current event processing
                                def safe_advance():
                                    try:
                                        if self.animation_active:
                                            show_screen(next_idx)
                                    except Exception as e:
                                        print(f"Error in auto-advance: {e}")
                                
                                callback_id = canvas.after(2000, lambda: self.root.after_idle(safe_advance))
                                self.pending_callbacks.append(callback_id)
                        callback_id = canvas.after(1000, lambda: animate_shot(shot_index + 1))
                        self.pending_callbacks.append(callback_id)
            
            # Start the animation if it's active
            if self.animation_active:
                # Start ball animation
                animate_shot()
        
        def show_screen(i):
            # Cancel any pending callbacks and clean up before transitioning
            cleanup_bindings()
            # Unbind keyboard events to prevent callback conflicts
            try:
                self.root.unbind("<Right>")
            except:
                pass
            
            # Check if match is finished (we're at or past the last point)
            is_match_finished = i >= len(point_events) if point_events else True
            
            # Process any pending events before destroying widgets
            try:
                self.root.update_idletasks()
            except:
                pass
            
            # Safely destroy all child widgets - do this multiple times to ensure cleanup
            try:
                for attempt in range(3):  # Try multiple times to ensure complete cleanup
                    for widget in list(self.root.winfo_children()):
                        try:
                            widget.destroy()
                        except:
                            pass
                    if not self.root.winfo_children():  # If no children left, we're done
                        break
                    self.root.update_idletasks()  # Process updates between attempts
            except:
                pass
            
            # Force update to clear any visual artifacts
            try:
                self.root.update()
            except:
                pass
                
            # Create main container
            main_frame = tk.Frame(self.root)
            main_frame.pack(fill="both", expand=True)
            
            # Header with score - only show during match, not after
            if not is_match_finished:
                header_frame = tk.Frame(main_frame, bg="#2c3e50", relief="raised", bd=2)
                header_frame.pack(fill="x", padx=10, pady=10)
                
                if point_events and i < len(point_events):
                    events = point_events[i]['events']
                    for event in events:
                        if event['type'] == 'score':
                            sets = event['sets']
                            current_set = event['current_set']
                            p1_name = event['player1_name']
                            p2_name = event['player2_name']
                            
                            # Create simple scoreboard - only player names and completed/current sets
                            score_frame = tk.Frame(header_frame, bg="#34495e")
                            score_frame.pack(fill="x", padx=100)
                            
                            # Determine which sets each player won
                            set_winners = []
                            for set_idx, set_tuple in enumerate(sets):
                                p1_games, p2_games = set_tuple
                                # A set is won when someone reaches 6+ games with 2+ game lead
                                if p1_games >= 6 and p1_games - p2_games >= 2:
                                    set_winners.append(1)  # Player 1 won
                                elif p2_games >= 6 and p2_games - p1_games >= 2:
                                    set_winners.append(2)  # Player 2 won
                                elif p1_games == 7 and p2_games == 6:
                                    set_winners.append(1)
                                elif p2_games == 7 and p1_games == 6:
                                    set_winners.append(2)
                                else:
                                    set_winners.append(0)  # Set still in progress
                            
                            # Build set scores display - only completed sets + current
                            # Player 1 row
                            p1_row = tk.Frame(score_frame, bg="#3498db")
                            p1_row.pack(fill="x", pady=2)
                            
                            # Create a frame to hold all score elements with mixed formatting
                            p1_score_frame = tk.Frame(p1_row, bg="#3498db")
                            p1_score_frame.pack(padx=10, pady=5)
                            
                            # Add player name
                            tk.Label(p1_score_frame, text=p1_name + "  ", font=("Arial", 11, "bold"), bg="#3498db", fg="white").pack(side="left")
                            
                            # Add each completed set score with appropriate formatting
                            for set_idx, set_tuple in enumerate(sets):
                                score_val = str(set_tuple[0])
                                is_winner = set_idx < len(set_winners) and set_winners[set_idx] == 1
                                font = ("Arial", 11, "bold") if is_winner else ("Arial", 11)
                                tk.Label(p1_score_frame, text=score_val + "  ", font=font, bg="#3498db", fg="white").pack(side="left")
                            
                            # Add current set in progress
                            tk.Label(p1_score_frame, text=str(current_set['player1']), font=("Arial", 11, "bold"), bg="#3498db", fg="white").pack(side="left")
                            
                            # Player 2 row
                            p2_row = tk.Frame(score_frame, bg="#e74c3c")
                            p2_row.pack(fill="x", pady=2)
                            
                            # Create a frame to hold all score elements with mixed formatting
                            p2_score_frame = tk.Frame(p2_row, bg="#e74c3c")
                            p2_score_frame.pack(padx=10, pady=5)
                            
                            # Add player name
                            tk.Label(p2_score_frame, text=p2_name + "  ", font=("Arial", 11, "bold"), bg="#e74c3c", fg="white").pack(side="left")
                            
                            # Add each completed set score with appropriate formatting
                            for set_idx, set_tuple in enumerate(sets):
                                score_val = str(set_tuple[1])
                                is_winner = set_idx < len(set_winners) and set_winners[set_idx] == 2
                                font = ("Arial", 11, "bold") if is_winner else ("Arial", 11)
                                tk.Label(p2_score_frame, text=score_val + "  ", font=font, bg="#e74c3c", fg="white").pack(side="left")
                            
                            # Add current set in progress
                            tk.Label(p2_score_frame, text=str(current_set['player2']), font=("Arial", 11, "bold"), bg="#e74c3c", fg="white").pack(side="left")
            else:
                # Create empty header frame to maintain layout spacing
                header_frame = tk.Frame(main_frame, bg="#1a2332", height=1)
                header_frame.pack(fill="x", padx=10, pady=0)
                header_frame.pack_propagate(False)
            
            # Court visualization using TennisCourtViewer
            canvas_frame = tk.Frame(main_frame)
            canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            if not is_match_finished:
                # Show court during match
                nonlocal canvas
                court_viewer = TennisCourtViewer(canvas_frame, width=1200, height=600, surface=tournament['surface'])
                canvas = court_viewer.canvas
            else:
                # Match finished - show final scoreboard centered
                final_board = tk.Frame(canvas_frame, bg="#1a2332")
                final_board.pack(fill="both", expand=True)
                
                # Vertical centering frame
                center_wrapper = tk.Frame(final_board, bg="#1a2332")
                center_wrapper.pack(fill="both", expand=True)
                
                # Spacer to center vertically
                tk.Frame(center_wrapper, bg="#1a2332", height=80).pack()
                
                # Scoreboard panel
                score_panel = tk.Frame(center_wrapper, bg="#2c3e50", relief="raised", bd=3)
                score_panel.pack(fill="x", padx=200, pady=20)
                
                # Get final scores from game_engine
                if game_engine:
                    p1_name = player1['name']
                    p2_name = player2['name']
                    winner_name = p1_name if game_engine.sets['player1'] > game_engine.sets['player2'] else p2_name
                    
                    # Build final sets list
                    final_sets = game_engine.set_scores.copy()
                    
                    # Add current set if there are games played
                    if game_engine.games['player1'] > 0 or game_engine.games['player2'] > 0:
                        final_sets.append((game_engine.games['player1'], game_engine.games['player2']))
                    
                    # Determine which sets each player won
                    set_winners = []
                    for set_idx, set_tuple in enumerate(final_sets):
                        p1_games, p2_games = set_tuple
                        if p1_games >= 6 and p1_games - p2_games >= 2:
                            set_winners.append(1)
                        elif p2_games >= 6 and p2_games - p1_games >= 2:
                            set_winners.append(2)
                        elif p1_games == 7 and p2_games == 6:
                            set_winners.append(1)
                        elif p2_games == 7 and p1_games == 6:
                            set_winners.append(2)
                        else:
                            set_winners.append(0)
                    
                    # Player 1 row
                    p1_bg = "#27ae60" if winner_name == p1_name else "#3498db"
                    p1_row = tk.Frame(score_panel, bg=p1_bg)
                    p1_row.pack(fill="x", pady=5)
                    
                    p1_score_frame = tk.Frame(p1_row, bg=p1_bg)
                    p1_score_frame.pack(padx=20, pady=10)
                    
                    tk.Label(p1_score_frame, text=p1_name + "  ", font=("Arial", 14, "bold"), bg=p1_bg, fg="white").pack(side="left")
                    
                    for set_idx, set_tuple in enumerate(final_sets):
                        score_val = str(set_tuple[0])
                        is_winner = set_idx < len(set_winners) and set_winners[set_idx] == 1
                        font = ("Arial", 14, "bold") if is_winner else ("Arial", 14)
                        tk.Label(p1_score_frame, text=score_val + "  ", font=font, bg=p1_bg, fg="white").pack(side="left")
                    
                    # Player 2 row
                    p2_bg = "#27ae60" if winner_name == p2_name else "#e74c3c"
                    p2_row = tk.Frame(score_panel, bg=p2_bg)
                    p2_row.pack(fill="x", pady=5)
                    
                    p2_score_frame = tk.Frame(p2_row, bg=p2_bg)
                    p2_score_frame.pack(padx=20, pady=10)
                    
                    tk.Label(p2_score_frame, text=p2_name + "  ", font=("Arial", 14, "bold"), bg=p2_bg, fg="white").pack(side="left")
                    
                    for set_idx, set_tuple in enumerate(final_sets):
                        score_val = str(set_tuple[1])
                        is_winner = set_idx < len(set_winners) and set_winners[set_idx] == 2
                        font = ("Arial", 14, "bold") if is_winner else ("Arial", 14)
                        tk.Label(p2_score_frame, text=score_val + "  ", font=font, bg=p2_bg, fg="white").pack(side="left")
                                
            # Player stats display (after court visualization) - only show during match
            if not is_match_finished:
                # Create a frame for player stats with two columns
                stats_frame = tk.Frame(main_frame, bg="#ecf0f1")
                stats_frame.pack(fill="x", padx=20, pady=(0, 10))

                # Helper function to calculate the new stats
                def calculate_new_stats(skills):
                    # Serve (as is)
                    serve = skills.get('serve', 0)

                    # Base Shots (average of forehand and backhand)
                    forehand = skills.get('forehand', 0)
                    backhand = skills.get('backhand', 0)
                    base_shots = round((forehand + backhand) / 2) if forehand + backhand > 0 else 0

                    # Special Shots (average of volleys and dropshots)
                    volley = skills.get('volley', 0)
                    dropshot = skills.get('dropshot', 0)
                    special_shots = round((volley + dropshot) / 2) if volley + dropshot > 0 else 0

                    # Physicality (average of speed and stamina)
                    speed = skills.get('speed', 0)
                    stamina = skills.get('stamina', 0)
                    physicality = round((speed + stamina) / 2) if speed + stamina > 0 else 0

                    # Precision (average of cross and straight)
                    cross = skills.get('cross', 0)
                    straight = skills.get('straight', 0)
                    precision = round((cross + straight) / 2) if cross + straight > 0 else 0

                    # Overall (average of all previous values)
                    overall = round((serve + base_shots + special_shots + physicality + precision) / 5)

                    return {
                        'Serve': serve,
                        'Base Shots': base_shots,
                        'Special Shots': special_shots,
                        'Physicality': physicality,
                        'Precision': precision,
                        'Overall': overall
                    }

                # Get stats for both players
                p1_stats = calculate_new_stats(game_engine.p1['skills'])
                p2_stats = calculate_new_stats(game_engine.p2['skills'])

                # Left column for Player 1
                p1_stats_card = tk.Frame(stats_frame, bg="white", relief="raised", bd=2)
                p1_stats_card.pack(side="left", fill="both", expand=True, padx=(0, 5))

                tk.Label(
                    p1_stats_card,
                    text=f"⬅️ {player1['name']} (P1)",
                    font=("Arial", 11, "bold"),
                    bg="#3498db",
                    fg="white",
                    padx=10,
                    pady=5
                ).pack(fill="x")

                p1_stats_content = tk.Frame(p1_stats_card, bg="white")
                p1_stats_content.pack(fill="both", expand=True, padx=8, pady=8)

                # Display player1's new stats
                for stat_name, stat_value in p1_stats.items():
                    tk.Label(
                        p1_stats_content,
                        text=f"{stat_name}: {stat_value}",
                        font=("Arial", 9),
                        bg="white",
                        fg="#2c3e50",
                        anchor="w"
                           ).pack(fill="x", pady=1)
    
                # Right column for Player 2
                p2_stats_card = tk.Frame(stats_frame, bg="white", relief="raised", bd=2)
                p2_stats_card.pack(side="right", fill="both", expand=True, padx=(5, 0))

                tk.Label(
                    p2_stats_card,
                    text=f"{player2['name']} (P2) ➡️",
                    font=("Arial", 11, "bold"),
                    bg="#e74c3c",
                    fg="white",
                    padx=10,
                    pady=5
                ).pack(fill="x")

                p2_stats_content = tk.Frame(p2_stats_card, bg="white")
                p2_stats_content.pack(fill="both", expand=True, padx=8, pady=8)

                # Display player2's new stats
                for stat_name, stat_value in p2_stats.items():
                    tk.Label(
                        p2_stats_content,
                        text=f"{stat_name}: {stat_value}",
                        font=("Arial", 9),
                        bg="white",
                        fg="#2c3e50",
                        anchor="w"
                    ).pack(fill="x", pady=1)
                                    
                # If this is the last point, automatically advance to final scoreboard after 2 seconds
                if i >= self.max_points - 1:
                    # Store the current index and schedule auto-advance
                    self.scheduled_advance_idx = i + 1
                    self.root.after(2000, lambda: (self.scheduled_advance_idx == i + 1 and show_screen(i + 1)) or None)
            
            # Control buttons
            control_frame = tk.Frame(main_frame)
            control_frame.pack(fill="x", padx=20, pady=(0, 10))            
            
            # Draw ball positions if available (only during active match)
            next_idx = i + 1
            if not is_match_finished and point_events and i < len(point_events):
                draw_ball_positions(canvas, point_events[i]['events'], header_frame, next_idx)
            
            # Navigation buttons (Previous button only, Next is keyboard/auto)
            button_frame = tk.Frame(main_frame)
            button_frame.pack(pady=10)
            
            if is_match_finished:
                # Match is finished, show back button
                tk.Button(button_frame, text="Back to Tournament", font=("Arial", 12),
                         command=lambda: (self.show_tournament_bracket(tournament) if tournament else None)).pack(side="left", padx=10)
            elif next_idx >= len(match_log):
                # Last point but match not finished, show back button
                tk.Button(button_frame, text="Back to Tournament", font=("Arial", 12),
                         command=lambda: (self.show_tournament_bracket(tournament) if tournament else None)).pack(side="left", padx=10)
            
            # Keyboard binding for right arrow to go to next point
            # Use instance variables instead of closure to avoid stale references
            self.current_point_idx = i
            self.max_points = len(match_log) if match_log else 0
            
            # Unbind any previous right arrow binding to avoid conflicts
            try:
                self.root.unbind("<Right>")
            except:
                pass
            
            def on_right_arrow(event):
                # Don't advance if match is finished or at the end
                if is_match_finished or self.current_point_idx >= self.max_points - 1:
                    return
                # Only advance if there's a valid next point
                if self.current_point_idx + 1 < self.max_points:
                    try:
                        # Set scheduled advance to invalid so any pending auto-advance doesn't trigger
                        self.scheduled_advance_idx = -1
                        # Add a small delay to ensure clean widget destruction
                        self.root.after(50, lambda: show_screen(self.current_point_idx + 1))
                    except:
                        pass
            
            self.root.bind("<Right>", on_right_arrow)
                         
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
        header_frame = tk.Frame(self.root, bg="#ffffff", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Create header content frame
        header_content = tk.Frame(header_frame, bg="#ffffff")
        header_content.pack(expand=True, fill="both")
        
        # Try to get tournament logo
        logo = tournament_logo_manager.get_tournament_logo(tournament.get('id'), size=(48, 48))
        
        if logo:
            # Create centered container for logo and title
            title_container = tk.Frame(header_content, bg="#ffffff")
            title_container.pack(expand=True)
            
            # Display logo next to tournament name
            logo_label = tk.Label(title_container, image=logo, bg="#ffffff")
            logo_label.pack(side="left", padx=(0, 10))
            logo_label.image = logo  # Keep reference
            
            # Tournament name
            title_label = tk.Label(
                title_container,
                text=f"{tournament['name']} Bracket",
                font=("Arial", 18, "bold"),
                bg="#ffffff",
                fg="black"
            )
            title_label.pack(side="left")
        else:
            # Fallback to emoji based on category
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
                header_content,
                text=f"{icon} {tournament['name']} Bracket",
                font=("Arial", 18, "bold"),
                bg="#ffffff",
                fg="white"
            )
            title_label.pack(expand=True, pady=10)
        
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
            self.current_bracket_tab = getattr(self, 'current_bracket_tab', round_names[0])
            
            # Add "Full Bracket" option + individual rounds
            all_tabs = round_names
            
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
            return ["1st Round", "Quarterfinals", "Semifinals", "Final"]
        elif num_rounds == 5:
            return ["1st Round", "2nd Round", "Quarterfinals", "Semifinals", "Final"]
        elif num_rounds == 6:
            return ["1st Round", "2nd Round", "3rd Round", "Quarterfinals", "Semifinals", "Final"]
        elif num_rounds == 7:
            return ["1st Round", "2nd Round", "3rd Round", "4th Round", "Quarterfinals", "Semifinals", "Final"]
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

        round_names = self._get_round_names(num_rounds)
        # Determine which rounds to display based on tab selection
        if self.current_bracket_tab == round_names[0]:
            start_round = 0
            rounds_to_show = bracket
            display_offset = 0
        else:
            # Find which round corresponds to the selected tab
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
        
        # Check for BYE match
        if not match['player1'] or not match['player2']:
            match_log = ["BYE - Player advances automatically"]
            winner = match['player1'] or match['player2']  # Get the non-None player
            tournament['active_matches'][match_idx][2] = winner['id']
            self.display_simple_match_log(match_log, tournament, None)
            return

        # Get player data
        player1 = next((p for p in self.scheduler.players if p['id'] == match['player1']['id']), None)
        player2 = next((p for p in self.scheduler.players if p['id'] == match['player2']['id']), None)
        
        # Show face-off screen - simulation will happen when user clicks "Start Match"
        self.show_player_faceoff_bracket(player1, player2, tournament, match_idx)

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
        
        self.current_history_tab = getattr(self, 'current_history_tab', "Special")
        
        # Get all tournament categories that exist
        tournaments_by_category = collections.defaultdict(list)
        for t in self.scheduler.tournaments:
            tournaments_by_category[t['category']].append(t)
        
        available_categories = [cat for cat in PRESTIGE_ORDER if cat in tournaments_by_category]
        
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
            elif 'Masters' in tournament['category']:
                bg_color = "#e67e22"  # Orange for Masters
            elif 'ATP 500' == tournament['category']:
                bg_color = "#f39c12"  # Gold for ATP 500
            elif 'ATP 250' == tournament['category']:
                bg_color = "#3498db"  # Blue for ATP 250
            else:
                bg_color = "#95a5a6"  # Gray for other tournaments
            
            # Main tournament card
            tournament_frame = tk.Frame(scroll_frame, bg=bg_color, relief="raised", bd=2)
            tournament_frame.pack(fill="x", padx=10, pady=5)
            
            # Tournament info section
            info_frame = tk.Frame(tournament_frame, bg=bg_color)
            info_frame.pack(fill="x", padx=15, pady=10)
            
            # Tournament name with logo
            name_frame = tk.Frame(info_frame, bg=bg_color)
            name_frame.pack(fill="x")
            
            # Try to get tournament logo
            logo = tournament_logo_manager.get_tournament_logo(tournament.get('id'))
            
            if logo:
                # Display logo
                logo_label = tk.Label(name_frame, image=logo, bg=bg_color)
                logo_label.pack(side="left", padx=(0, 8))
                logo_label.image = logo  # Keep reference
            else:
                # Fallback to emoji based on category
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
                
                icon_label = tk.Label(
                    name_frame,
                    text=icon,
                    font=("Arial", 16),
                    bg=bg_color,
                    fg="white"
                )
                icon_label.pack(side="left", padx=(0, 8))
            
            # Tournament name
            name_label = tk.Label(
                name_frame,
                text=tournament['name'],
                font=("Arial", 14, "bold"),
                bg=bg_color,
                fg="white",
                anchor="w"
            )
            name_label.pack(side="left", fill="x", expand=True)
            
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
        
        # Create header content frame
        header_content = tk.Frame(header_frame, bg="#ffffff")
        header_content.pack(expand=True, fill="both")
        
        # Navigation buttons on the left
        nav_buttons = tk.Frame(header_content, bg="#ffffff")
        nav_buttons.pack(side="left", padx=(20, 0), pady=10)
        
        tk.Button(
            nav_buttons, 
            text="↩️ Back to History", 
            command=self.show_history, 
            font=("Arial", 10, "bold"),
            bg="#95a5a6",
            fg="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=6,
            activebackground="#ffffff",
            activeforeground="white"
        ).pack(pady=(0, 5))
        
        tk.Button(
            nav_buttons, 
            text="🏠 Main Menu", 
            command=self.build_main_menu, 
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=6,
            activebackground="#ffffff",
            activeforeground="white"
        ).pack()
        
        # Try to get tournament logo
        logo = tournament_logo_manager.get_tournament_logo(tournament.get('id'), size=(48, 48))
        
        if logo:
            # Create centered container for logo and title
            title_container = tk.Frame(header_content, bg="#ffffff")
            title_container.pack(expand=True)
            
            # Display logo next to tournament name
            logo_label = tk.Label(title_container, image=logo, bg="#ffffff")
            logo_label.pack(side="left", padx=(0, 10))
            logo_label.image = logo  # Keep reference
            
            # Tournament name
            title_label = tk.Label(
                title_container,
                text=f"{tournament['name']} History",
                font=("Arial", 18, "bold"),
                bg="#ffffff",
                fg="black"
            )
            title_label.pack(side="left")
        else:
            # Fallback to emoji based on category
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
                header_content,
                text=f"{icon} {tournament['name']} History",
                font=("Arial", 18, "bold"),
                bg="#ffffff",
                fg="white"
            )
            title_label.pack(expand=True, pady=10)
        
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
        
if __name__ == "__main__":
    root = tk.Tk()
    root.title("TennisGM")
    app = TennisGMApp(root)
    root.mainloop()