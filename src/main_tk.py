import tkinter as tk
from schedule import TournamentScheduler
from sim.game_engine import GameEngine, SURFACE_EFFECTS
from court_viewer import TennisCourtViewer
from utils.logo_utils import tournament_logo_manager
import collections
import math
import sys
from io import StringIO
import functools
from archetypes import ARCTYPE_MAP, get_archetype_for_player
from commentary import generate_commentary
from face_generator import generate_face, create_face_canvas

PRESTIGE_ORDER = ["Special", "Grand Slam", "Masters 1000", "ATP 500", "ATP 250", "Challenger 175", "Challenger 125", "Challenger 100", "Challenger 75", "Challenger 50", "ITF", "Juniors"]

class TennisGMApp:
    def __init__(self, root):
        self.root = root
        self.scheduler = TournamentScheduler()
        self._migrate_favorites()
        self.menu_options = [
            "News Feed", "Tournaments", "ATP Rankings", "Hall of Fame", "Achievements", "Advance to next week", "Exit"
        ]
        # State tracking for rankings screen
        self.rankings_search_query = ""
        self.rankings_scroll_position = 0.0
        # Track matplotlib figures to close them when navigating away
        self.current_figure = None
        self._update_window_title()
        self.build_main_menu()

    def _update_window_title(self):
        """Update window title to show current game state."""
        year = getattr(self.scheduler, 'current_year', '?')
        week = getattr(self.scheduler, 'current_week', '?')
        self.root.title(f"TennisGM  \u2014  Year {year}, Week {week}")

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
            # Ensure every player has a mentality (neutral/opportunist/strategist)
            if 'mentality' not in p:
                import random
                p['mentality'] = random.choices(
                    ["neutral", "opportunist", "strategist"],
                    weights=[50, 25, 25], k=1
                )[0]
                changed = True
            # Ensure every player has a 'mental' skill (backfill for existing saves)
            if 'mental' not in p.get('skills', {}):
                skills = p.get('skills', {})
                if skills:
                    avg_skill = round(sum(skills.values()) / max(1, len(skills)))
                    skills['mental'] = avg_skill
                else:
                    skills['mental'] = 50
                changed = True
            # Ensure every player has lift, slice, iq skills (backfill for existing saves)
            for new_skill in ('lift', 'slice', 'iq'):
                if new_skill not in p.get('skills', {}):
                    skills = p.get('skills', {})
                    if skills:
                        other_vals = [v for k, v in skills.items() if k != new_skill]
                        skills[new_skill] = round(sum(other_vals) / max(1, len(other_vals)))
                    else:
                        skills[new_skill] = 50
                    changed = True
            # Ensure every player has lift_tend, slice_tend
            if 'lift_tend' not in p:
                import random
                p['lift_tend'] = random.randint(3, 20)
                changed = True
            if 'slice_tend' not in p:
                import random
                p['slice_tend'] = random.randint(3, 20)
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
        # Close any previously opened matplotlib figures
        self._close_matplotlib_figures()
        
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
        # News Feed centered at top (with unread count badge)
        news_count = len(self.scheduler.news_feed) if hasattr(self.scheduler, 'news_feed') else 0
        news_badge = f"  ({news_count})" if news_count > 0 else ""
        news_btn = tk.Button(
            content_frame,
            text=f"📰 News Feed{news_badge}",
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
        
        # Row 3: History and Achievements
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
        history_btn.grid(row=3, column=0, padx=10, pady=8, sticky="ew")
        
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
        
        # Row 4: Hall of Fame and Exhibition
        current_row = 4
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
        hall_btn.grid(row=current_row, column=0, padx=10, pady=8, sticky="ew")
        
        exhibition_btn = tk.Button(
            content_frame,
            text="🎭 Exhibition",
            font=("Arial", 12, "bold"),
            bg="#8e44ad",
            fg="white",
            relief="flat",
            bd=0,
            padx=20,
            pady=15,
            activebackground="#7d3c98",
            activeforeground="white",
            command=lambda: self.handle_menu("Exhibition")
        )
        exhibition_btn.grid(row=current_row, column=1, padx=10, pady=8, sticky="ew")
        current_row += 1
        
        # Row 5: Advance to next week (if available)
        current_tournaments = self.scheduler.get_current_week_tournaments()
        incomplete_tournaments = [t for t in current_tournaments if t['winner_id'] is None]
        
        if len(incomplete_tournaments) == 0:
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
            advance_btn.grid(row=current_row, column=0, columnspan=2, padx=10, pady=8, sticky="ew")
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
                           "Prospects", "Hall of Fame", "Achievements", "History", "Exhibition"]
        if len(incomplete_tournaments) == 0:
            self.menu_options.append("Advance to next week")
        self.menu_options.append("Save & Quit")
        
        # Configure grid weights for responsive design
        for i in range(2):
            content_frame.grid_columnconfigure(i, weight=1)

    def handle_menu(self, option):
        if option == "Advance to next week":
            self.scheduler.advance_week()
            self._update_window_title()
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
        elif option == "Exhibition":
            self.show_exhibition_setup()
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
        
        tabs = ["All", "Junior Ranking", "19", "18", "17", "16"]
        for tab in tabs:
            is_active = tab == self.current_prospects_tab
            bg_color = "#e67e22" if is_active else "#5d6d7e"  # Orange for prospects
            
            btn = tk.Button(tab_frame, text=f"{tab} years" if tab not in ["All", "Junior Ranking"] else tab, 
                          bg=bg_color, fg="white",
                          command=lambda t=tab: self.switch_prospects_tab(t),
                          font=("Arial", 11, "bold" if is_active else "normal"), 
                          relief="flat", bd=0, padx=12, pady=8,
                          activebackground="#d35400", activeforeground="white")
            btn.pack(side="left", padx=2)

        # Compute FUT = overall + potential_factor
        def calc_overall(p):
            skills = p.get("skills", {})
            if not skills:
                return 0.0
            return round(sum(skills.values()) / max(1, len(skills)), 2)

        def calc_fut(p):
            return (0.5*(round(calc_overall(p) + (22.5 * p.get("potential_factor", 1.0)), 1)))

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
                ranked = sorted(((p, calc_fut(p)) for p in u20), key=lambda x: x[1], reverse=True)
                filtered = [(p, fut) for (p, fut) in ranked if query in p.get('name', '').lower()]
                display_field = "FUT"
            elif self.current_prospects_tab == "Junior Ranking":
                # Filter players aged 16-19 with junior_ranking > 0
                u20 = [p for p in self.scheduler.players if 16 <= p.get("age", 99) <= 19 and p.get("junior_ranking", 0) > 0]
                ranked = sorted(((p, p.get("junior_ranking", 0)) for p in u20), key=lambda x: x[1], reverse=True)
                filtered = [(p, jr) for (p, jr) in ranked if query in p.get('name', '').lower()]
                display_field = "JR"
            else:
                target_age = int(self.current_prospects_tab)
                u20 = [p for p in self.scheduler.players if p.get("age", 99) == target_age]
                ranked = sorted(((p, calc_fut(p)) for p in u20), key=lambda x: x[1], reverse=True)
                filtered = [(p, fut) for (p, fut) in ranked if query in p.get('name', '').lower()]
                display_field = "FUT"
            
            for idx, (player, score) in enumerate(filtered, 1):
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
                
                text = f"{rank_icon} {idx}. {player['name']} - {display_field} {score} | {player.get('age', 1.0)}yo"
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
        # Close any previously opened matplotlib figures
        self._close_matplotlib_figures()
        
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

        # Top bar: navigation buttons (left) + favorite toggle (center)
        def _toggle_fav(pl):
            pl['favorite'] = not pl.get('favorite', False)
            try:
                self.scheduler.save_game()
            except Exception:
                pass
            self._render_player_details(pl, back_label, back_func)

        top_bar = tk.Frame(self.root, bg="#ecf0f1")
        top_bar.pack(fill="x", padx=20, pady=10)
        
        # Left: nav buttons
        nav_left = tk.Frame(top_bar, bg="#ecf0f1")
        nav_left.pack(side="left")
        
        tk.Button(
            nav_left, 
            text=f"↩️ {back_label}", 
            command=back_func, 
            font=("Arial", 11, "bold"),
            bg="#95a5a6",
            fg="white",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            activebackground="#7f8c8d",
            activeforeground="white"
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            nav_left, 
            text="🏠 Main Menu", 
            command=self.build_main_menu, 
            font=("Arial", 11, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            activebackground="#2980b9",
            activeforeground="white"
        ).pack(side="left")
        
        # Center: favorite button
        fav_state = bool(player.get('favorite'))
        fav_btn_text = "⭐ Remove from Favorites" if fav_state else "⭐ Add to Favorites"
        fav_color = "#e74c3c" if fav_state else "#f39c12"
        
        fav_btn = tk.Button(
            top_bar, 
            text=fav_btn_text, 
            font=("Arial", 12, "bold"),
            bg=fav_color,
            fg="white",
            relief="flat",
            bd=0,
            padx=15,
            pady=6,
            activebackground="#c0392b" if fav_state else "#e67e22",
            activeforeground="white",
            command=lambda: _toggle_fav(player)
        )
        fav_btn.pack(expand=True)

        # Format surface modifiers
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
        
        # Create three-column layout
        content_frame = tk.Frame(main_frame, bg="#ecf0f1")
        content_frame.pack(fill="both", expand=True)
        
        left_column = tk.Frame(content_frame, bg="#ecf0f1")
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        middle_column = tk.Frame(content_frame, bg="#ecf0f1")
        middle_column.grid(row=0, column=1, sticky="nsew", padx=(10, 10))
        
        right_column = tk.Frame(content_frame, bg="#ecf0f1")
        right_column.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        
        # Configure grid weights for three equal columns
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_columnconfigure(2, weight=1)
        
        # Left Column: Face Card
        # Ensure the player has a v4 head-only face (migration for old/missing saves)
        face_data = player.get('face', {})
        needs_face = (
            'face' not in player
            or face_data.get('version', 0) < 4
        )
        if needs_face:
            player['face'] = generate_face(player_id=player.get('id'), nationality=player.get('nationality'))

        face_card = tk.Frame(left_column, bg="white", relief="raised", bd=2)
        face_card.pack(fill="x", pady=(0, 10))

        face_canvas = create_face_canvas(face_card, player['face'], width=160, height=160, bg="white")
        face_canvas.pack(padx=10, pady=10)

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
        
        # Right Column: Start with Archetype Card (moved to middle)
        archetype_card = tk.Frame(middle_column, bg="white", relief="raised", bd=2)
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
            ("🧠 Mentality", player.get('mentality', 'neutral').capitalize()),
        ]
        
        for label, value in basic_info:
            row = tk.Frame(info_content, bg="white")
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{label}:", font=("Arial", 11, "bold"), bg="white", fg="#2c3e50", anchor="w").pack(side="left")
            tk.Label(row, text=str(value), font=("Arial", 11), bg="white", fg="#7f8c8d", anchor="w").pack(side="right")
                
        # Skills card - in middle column
        skills_card = tk.Frame(middle_column, bg="white", relief="raised", bd=2)
        skills_card.pack(fill="x", pady=(0, 10))
        
        # Compute OVR (average of all skills)
        _skills_vals = list(player.get('skills', {}).values())
        _ovr = round(sum(_skills_vals) / max(1, len(_skills_vals)), 1) if _skills_vals else 0
        
        tk.Label(
            skills_card,
            text=f"⚡ Skills ({_ovr})",
            font=("Arial", 14, "bold"),
            bg="#9b59b6",
            fg="white",
            padx=15,
            pady=8
        ).pack(fill="x")
        
        skills_content = tk.Frame(skills_card, bg="white")
        skills_content.pack(fill="x", padx=15, pady=10)
        
        # Build skill display with visual bars and caps
        age = player.get('age', 0)
        use_prog = age < 28
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
            
            # Skill name label on its own line
            tk.Label(row, text=skill_name.capitalize(), font=("Arial", 10, "bold"),
                     bg="white", fg="#2c3e50", anchor="w").pack(fill="x")
            
            # Bar container below the label
            bar_outer = tk.Frame(row, bg="#ecf0f1", height=18, relief="sunken", bd=1)
            bar_outer.pack(fill="x", padx=(0, 5))
            bar_outer.pack_propagate(False)
            
            # Smooth gradient: red -> orange -> yellow -> green -> blue
            if val >= 80:
                bar_color = "#2980b9"  # Blue
            elif val <= 40:
                bar_color = "#e74c3c"  # Red
            else:
                # 4-segment gradient across 40-80
                # 40-50: red (#e74c3c) -> orange (#e67e22)
                # 50-60: orange (#e67e22) -> yellow (#f1c40f)
                # 60-70: yellow (#f1c40f) -> green (#27ae60)
                # 70-80: green (#27ae60) -> blue (#2980b9)
                if val < 50:
                    t = (val - 40) / 10.0
                    r = int(231 + t * (230 - 231))
                    g = int(76 + t * (126 - 76))
                    b = int(60 + t * (34 - 60))
                elif val < 60:
                    t = (val - 50) / 10.0
                    r = int(230 + t * (241 - 230))
                    g = int(126 + t * (196 - 126))
                    b = int(34 + t * (15 - 34))
                elif val < 70:
                    t = (val - 60) / 10.0
                    r = int(241 + t * (39 - 241))
                    g = int(196 + t * (174 - 196))
                    b = int(15 + t * (96 - 15))
                else:
                    t = (val - 70) / 10.0
                    r = int(39 + t * (41 - 39))
                    g = int(174 + t * (128 - 174))
                    b = int(96 + t * (185 - 96))
                bar_color = f"#{r:02x}{g:02x}{b:02x}"   
            
            bar_fill = tk.Frame(bar_outer, bg=bar_color, height=16)
            # Use place for precise percentage width
            bar_fill.place(relwidth=max(0.02, val / 100.0), relheight=1.0)
            
            # Value text on top of bar
            val_label = tk.Label(bar_outer, text=f"{val}{suffix}", font=("Arial", 9, "bold"),
                                 bg=bar_color if val >= 30 else "#ecf0f1",
                                 fg="white" if val >= 30 else "#2c3e50", anchor="w")
            val_label.place(x=4, rely=0.5, anchor="w")
        
        # Right Column: Ranking Evolution Graph (full height)
        ranking_card = tk.Frame(right_column, bg="white", relief="raised", bd=2)
        ranking_card.pack(fill="both", expand=True, pady=(0, 10))
        
        tk.Label(
            ranking_card,
            text="📈 Ranking Evolution",
            font=("Arial", 14, "bold"),
            bg="#e74c3c",
            fg="white",
            padx=15,
            pady=8
        ).pack(fill="x")
        
        ranking_content = tk.Frame(ranking_card, bg="white")
        ranking_content.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Create ranking evolution graph
        self._create_ranking_graph(ranking_content, player)
        
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

        tk.Label(header_frame, text="\U0001F4F0 News Feed",
                font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack(expand=True)

        news = self.scheduler.news_feed if hasattr(self.scheduler, 'news_feed') else []

        # Content area
        content_frame = tk.Frame(self.root, bg="#ecf0f1")
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        if not news:
            no_news_frame = tk.Frame(content_frame, bg="white", relief="solid", bd=1)
            no_news_frame.pack(fill="x", padx=20, pady=50)
            tk.Label(no_news_frame, text="\U0001F4F0 No news this week.", font=("Arial", 14),
                    bg="white", fg="#7f8c8d", pady=30).pack()
        else:
            frame = tk.Frame(content_frame, bg="#ecf0f1")
            frame.pack(fill="both", expand=True, padx=10, pady=10)

            text = tk.Text(frame, wrap="word", font=("Arial", 11), height=35,
                          bg="#ecf0f1", fg="#2c3e50", relief="flat", bd=0, padx=10, pady=10)
            text.pack(side="left", fill="both", expand=True)

            # Configure text tags for styled rendering
            text.tag_configure("header", font=("Arial", 14, "bold"), foreground="#2c3e50",
                              spacing1=10, spacing3=5, justify="center")
            text.tag_configure("subheader", font=("Arial", 10), foreground="#7f8c8d",
                              spacing3=10, justify="center")
            text.tag_configure("title", font=("Arial", 12, "bold"), foreground="#2c3e50",
                              spacing1=15, spacing3=3)
            text.tag_configure("content", font=("Arial", 11), foreground="#34495e",
                              spacing3=2, lmargin1=10, lmargin2=10)
            text.tag_configure("tweet_title", font=("Arial", 12, "bold"), foreground="#3498db",
                              spacing1=15, spacing3=3)
            text.tag_configure("tweet_content", font=("Arial", 11, "italic"), foreground="#2980b9",
                              spacing3=2, lmargin1=10, lmargin2=10)
            text.tag_configure("showcase_title", font=("Arial", 13, "bold"), foreground="#d4a017",
                              spacing1=15, spacing3=5)
            text.tag_configure("showcase_content", font=("Arial", 11), foreground="#b8860b",
                              spacing3=2, lmargin1=10, lmargin2=10)
            text.tag_configure("separator", font=("Arial", 6), foreground="#bdc3c7",
                              spacing1=5, spacing3=5, justify="center")

            # Week header
            text.insert("end", "\u2605 TENNIS WEEKLY \u2605\n", "header")
            text.insert("end",
                f"Year {self.scheduler.current_year}, Week {self.scheduler.current_week}\n",
                "subheader")

            for i, item in enumerate(news):
                if i > 0:
                    text.insert("end", "\u2500" * 60 + "\n", "separator")

                item_type = item.get('type', '')
                if item_type == 'showcase':
                    title_tag = "showcase_title"
                    body_tag = "showcase_content"
                elif item_type == 'tweet':
                    title_tag = "tweet_title"
                    body_tag = "tweet_content"
                else:
                    title_tag = "title"
                    body_tag = "content"

                text.insert("end", f"{item['title']}\n", title_tag)

                if isinstance(item['content'], list):
                    for line in item['content']:
                        text.insert("end", f"{line}\n", body_tag)
                else:
                    text.insert("end", f"{item['content']}\n", body_tag)

            text.config(state="disabled")
            scrollbar = tk.Scrollbar(frame, command=text.yview)
            scrollbar.pack(side="right", fill="y")
            text.config(yscrollcommand=scrollbar.set)

        # Styled back button
        button_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        button_frame.pack(fill="x", pady=0)
        button_frame.pack_propagate(False)

        tk.Button(button_frame, text="\u2190 Back to Main Menu", command=self.build_main_menu,
                 font=("Arial", 12, "bold"), bg="#3498db", fg="white", relief="flat",
                 activebackground="#2980b9", activeforeground="white", bd=0, padx=20, pady=8).pack(expand=True)

    def show_rankings(self):
        # Close any previously opened matplotlib figures
        self._close_matplotlib_figures()
        
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
        
        tabs = ["All Players", "By OVR", "Favorites"]
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
        search_var = tk.StringVar(value=self.rankings_search_query)
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
            query = search_var.get().lower().strip()
            # Save search query for next time
            self.rankings_search_query = query
            for widget in scroll_frame.winfo_children():
                widget.destroy()
            
            # Determine sorting mode
            use_ovr = self.current_rankings_tab == "By OVR"
            
            if use_ovr:
                # Sort all players by OVR (average of skills)
                def _calc_ovr(p):
                    vals = list(p.get('skills', {}).values())
                    return round(sum(vals) / max(1, len(vals)), 1) if vals else 0
                ovr_ranked = sorted(
                    ((p, _calc_ovr(p)) for p in self.scheduler.players),
                    key=lambda x: x[1], reverse=True
                )
                ranked_players = ovr_ranked
            else:
                ranked_players = self.scheduler.ranking_system.get_ranked_players(
                    self.scheduler.players,
                    self.scheduler.current_date
                )
            
            # Check if query is an age filter (e.g., "<25", ">20", "=18")
            age_filter = None
            age_operator = None
            if query and query[0] in ['<', '>', '=']:
                try:
                    age_operator = query[0]
                    age_value = int(query[1:])
                    age_filter = age_value
                except (ValueError, IndexError):
                    pass
            
            filtered_players = []
            for ranking_pos, (player, points) in enumerate(ranked_players, 1):
                # Tab-based filtering
                if self.current_rankings_tab == "Favorites" and not player.get('favorite', False):
                    continue
                
                # Age filter
                if age_filter is not None:
                    player_age = player.get('age', 0)
                    if age_operator == '<' and not (player_age < age_filter):
                        continue
                    elif age_operator == '>' and not (player_age > age_filter):
                        continue
                    elif age_operator == '=' and not (player_age == age_filter):
                        continue
                # Name search
                elif query and query not in player['name'].lower():
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
                    text=f"{rank_icon} {ranking_pos}. {player['name']} - {points}{' OVR' if use_ovr else ' pts'}",
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
            
            # Save scroll position after rendering
            self.root.after(10, lambda: self._save_rankings_scroll_position(canvas))

        # Store update function for tab switching
        self.update_rankings_list = update_list
        
        # Initial population
        update_list()
        search_var.trace_add("write", update_list)
        
        # Restore scroll position after initial render
        self.root.after(50, lambda: self._restore_rankings_scroll_position(canvas))

        # Styled back button
        button_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        button_frame.pack(fill="x", pady=0)
        button_frame.pack_propagate(False)
        
        tk.Button(button_frame, text="← Back to Main Menu", command=self.build_main_menu, 
                 font=("Arial", 12, "bold"), bg="#3498db", fg="white", relief="flat",
                 activebackground="#2980b9", activeforeground="white", bd=0, padx=20, pady=8).pack(expand=True)

    def _save_rankings_scroll_position(self, canvas):
        """Save the current scroll position of the rankings canvas."""
        try:
            self.rankings_scroll_position = canvas.yview()[0]
        except:
            pass

    def _close_matplotlib_figures(self):
        """Close any open matplotlib figures to free memory."""
        try:
            import matplotlib.pyplot as plt
            if self.current_figure is not None:
                plt.close(self.current_figure)
                self.current_figure = None
        except:
            pass

    def _restore_rankings_scroll_position(self, canvas):
        """Restore the saved scroll position of the rankings canvas."""
        try:
            canvas.yview_moveto(self.rankings_scroll_position)
        except:
            pass

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

        # Highlight tournaments where this player is the most recent winner (last history entry).
        recent_wins_keys = set()
        try:
            player_name = player.get('name', '')
            for t in self.scheduler.tournaments:
                history = t.get('history', [])
                if history and history[-1].get('winner') == player_name:
                    recent_wins_keys.add((t.get('name', ''), t.get('category', '')))
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
                elif 'Challenger' in category:
                    cat_color = "#27ae60"  # Green
                    cat_icon = "🏟️"
                elif category == 'ITF':
                    cat_color = "#7f8c8d"  # Dark gray
                    cat_icon = "🏟️"
                elif category == 'Juniors':
                    cat_color = "#1abc9c"  # Teal
                    cat_icon = "🏟️"
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

    def _calculate_hof_points(self, player):
        """Delegate to TournamentScheduler's shared formula."""
        from schedule import TournamentScheduler
        return TournamentScheduler.calculate_hof_points(player)

    def show_hall_of_fame(self):
        # Close any previously opened matplotlib figures
        self._close_matplotlib_figures()
        
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
                
                if hof_points >= 500:
                    tier_color = "#504001"  # Gold for legends
                    tier_icon = "👑"
                    tier_name = "LEGEND"
                elif hof_points >= 100:
                    tier_color = "#5c1d16"  # Deep red for hall of fame
                    tier_icon = "🏆"
                    tier_name = "INDUCTEE"
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
                best_rank = player.get('highest_ranking', 'N/A')
                w1_val = player.get('w1') or 0
                w16_val = player.get('w16') or 0
                mawn_list = player.get('mawn') or [0,0,0,0,0]
                total_mw = sum(mawn_list) if isinstance(mawn_list, list) else 0
                stats_parts = [f"HOF: {hof_points}pts"]
                stats_parts.append(f"Best #{best_rank}")
                if wins:
                    stats_parts.append(f"{wins} titles")
                if w1_val:
                    stats_parts.append(f"{w1_val}w #1")
                if w16_val:
                    stats_parts.append(f"{w16_val}w top 10")
                if total_mw:
                    stats_parts.append(f"{total_mw}W")
                stats_label = tk.Label(
                    info_frame,
                    text=" • ".join(stats_parts),
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

        # Calculate hof_points for each player using comprehensive formula
        for player in self.scheduler.hall_of_fame:
            player['hof_points'] = self._calculate_hof_points(player)

        hof_members = sorted(
            self.scheduler.hall_of_fame,
            key=lambda x: (-x['hof_points'], x.get('highest_ranking', 999))
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
        # Close any previously opened matplotlib figures
        self._close_matplotlib_figures()
        
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
            # Scrollable main content area
            outer_frame = tk.Frame(self.root, bg="#ecf0f1")
            outer_frame.pack(fill="both", expand=True)
            canvas_scroll = tk.Canvas(outer_frame, bg="#ecf0f1", highlightthickness=0)
            scrollbar = tk.Scrollbar(outer_frame, orient="vertical", command=canvas_scroll.yview)
            main_frame = tk.Frame(canvas_scroll, bg="#ecf0f1")
            main_frame.bind("<Configure>", lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all")))
            canvas_scroll.create_window((0, 0), window=main_frame, anchor="nw", tags="main_frame")
            canvas_scroll.configure(yscrollcommand=scrollbar.set)
            canvas_scroll.pack(side="left", fill="both", expand=True, padx=20, pady=15)
            scrollbar.pack(side="right", fill="y")
            def _on_mousewheel(event):
                canvas_scroll.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas_scroll.bind_all("<MouseWheel>", _on_mousewheel)
            # Make main_frame fill canvas width
            def _resize_frame(event):
                canvas_scroll.itemconfig("main_frame", width=event.width)
            canvas_scroll.bind("<Configure>", _resize_frame)
            
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
            
            # Surface Wins Breakdown Card
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
            
            # Peak Skills Card
            peak_skills = player.get('peak_skills', {})
            if peak_skills:
                peak_card = tk.Frame(main_frame, bg="white", relief="raised", bd=2)
                peak_card.pack(fill="x", pady=(0, 10))
                
                peak_ovr = round(sum(peak_skills.values()) / len(peak_skills)) if peak_skills else 0
                tk.Label(
                    peak_card,
                    text=f"⚡ Peak Skills (Overall: {peak_ovr})",
                    font=("Arial", 14, "bold"),
                    bg="#8e44ad",
                    fg="white",
                    padx=15,
                    pady=8
                ).pack(fill="x")
                
                peak_content = tk.Frame(peak_card, bg="white")
                peak_content.pack(fill="x", padx=15, pady=10)
                
                skill_abbr = {
                    'serve': 'SRV', 'forehand': 'FRH', 'backhand': 'BKH',
                    'cross': 'CRS', 'straight': 'STR', 'speed': 'SPD',
                    'stamina': 'STA', 'mental': 'MNT', 'dropshot': 'DRP',
                    'volley': 'VOL', 'lift': 'LFT', 'slice': 'SLC', 'iq': 'IQ'
                }
                skill_groups = [
                    ("Base Shots", ['serve', 'forehand', 'backhand']),
                    ("Special Shots", ['volley', 'dropshot', 'lift', 'slice']),
                    ("Physicality", ['speed', 'stamina']),
                    ("Tactics", ['cross', 'straight', 'iq', 'mental']),
                ]
                for group_name, skills_list in skill_groups:
                    grp_frame = tk.Frame(peak_content, bg="white")
                    grp_frame.pack(fill="x", pady=(4, 0))
                    tk.Label(grp_frame, text=group_name, font=("Arial", 9, "bold"),
                            bg="white", fg="#95a5a6").pack(anchor="w")
                    for sk in skills_list:
                        val = peak_skills.get(sk, 0)
                        row = tk.Frame(peak_content, bg="white")
                        row.pack(fill="x", pady=1)
                        tk.Label(row, text=f"  {skill_abbr.get(sk, sk)}:", font=("Arial", 10, "bold"),
                                bg="white", fg="#2c3e50", anchor="w", width=6).pack(side="left")
                        # Skill bar
                        bar_bg = tk.Frame(row, bg="#ecf0f1", height=10, width=200)
                        bar_bg.pack(side="left", padx=(5, 5))
                        bar_bg.pack_propagate(False)
                        fill_w = max(1, int(200 * val / 100))
                        color = "#27ae60" if val >= 75 else "#f39c12" if val >= 60 else "#e74c3c"
                        tk.Frame(bar_bg, bg=color, height=10, width=fill_w).pack(side="left")
                        tk.Label(row, text=str(val), font=("Arial", 10),
                                bg="white", fg="#7f8c8d").pack(side="left")
            
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

    def _create_ranking_graph(self, parent_frame, player):
        """Create and display a ranking evolution graph using year_start_rankings data (last 10 years)."""
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        # Close any previously opened figures
        self._close_matplotlib_figures()
        
        # Get ranking data
        year_rankings = player.get('year_start_rankings', {})
        
        if not year_rankings:
            # No ranking data available
            tk.Label(parent_frame, text="No ranking history available.", 
                    font=("Arial", 10), bg="white", fg="#7f8c8d").pack(pady=10)
            return
        
        # Sort years and get rankings, then take only last 10 years
        years = sorted([int(y) for y in year_rankings.keys()])
        years = years[-8:]  # Keep only last 8 years
        rankings = [year_rankings[str(y)] for y in years]
        
        # Create figure with matplotlib
        fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor('white')
        
        # Store figure reference for later cleanup
        self.current_figure = fig
        
        # Plot the ranking evolution (inverted Y-axis so lower rank number is higher)
        ax.plot(years, rankings, marker='o', linewidth=2, markersize=6, 
               color='#e74c3c', markerfacecolor='#c0392b')
        
        # Invert Y-axis so rank 1 is at top
        ax.invert_yaxis()
        
        # Styling
        ax.set_ylabel('Ranking', fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Format Y-axis to show ranking positions
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        
        # Set reasonable Y-axis limits with some padding
        max_rank = max(rankings) if rankings else 100
        min_rank = min(rankings) if rankings else 1
        y_padding = (max_rank - min_rank) * 0.1 if (max_rank - min_rank) > 0 else 10
        ax.set_ylim(max_rank + y_padding, max(1, min_rank - y_padding))
        
        # Set X-axis limits
        if len(years) > 1:
            year_padding = (years[-1] - years[0]) * 0.05
            ax.set_xlim(years[0] - year_padding, years[-1] + year_padding)
        
        fig.tight_layout(pad=0.5)
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
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
        categories_set = set(t['category'] for t in tournaments)
        categories = sorted(categories_set, key=lambda c: PRESTIGE_ORDER.index(c) if c in PRESTIGE_ORDER else 999)
        
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
        # Sort tournaments by prestige order
        all_tournaments.sort(key=lambda t: PRESTIGE_ORDER.index(t['category']) if t['category'] in PRESTIGE_ORDER else 999)
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
            elif 'Challenger' in t['category']:
                bg_color = "#27ae60"  # Green for Challengers
            elif t['category'] == 'ITF':
                bg_color = "#7f8c8d"  # Dark gray for ITF
            elif t['category'] == 'Juniors':
                bg_color = "#1abc9c"  # Teal for Juniors
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
                
                icon_label = tk.Label(
                    name_frame,
                    text=icon,
                    font=("Arial", 16),
                    bg=bg_color,
                    fg="white"
                )
                icon_label.pack(side="left", padx=(0, 8))
            
            # Tournament name (with star if favorite player is in it)
            display_name = t['name'] + (" ⭐" if fav_t else "")
            name_label = tk.Label(
                name_frame,
                text=display_name,
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
        # Sort by prestige order so Juniors appear after ITFs
        def _prestige_key(t):
            cat = t.get('category', '')
            try:
                return PRESTIGE_ORDER.index(cat)
            except ValueError:
                return len(PRESTIGE_ORDER)
        tournaments.sort(key=_prestige_key)
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
            'mental': 'MNT',
            'dropshot': 'DRP',
            'volley': 'VOL',
            'lift': 'LFT',
            'slice': 'SLC',
            'iq': 'IQ'
        }
        
        # Helper function to create skill bars
        def create_skill_bar(parent, skill_name, p1_val, p2_val, max_val=100, abbr_color="#ffffff"):
            bar_frame = tk.Frame(parent, bg="#1a2332")
            bar_frame.pack(fill="x", pady=4)
            
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
            
            # Skill abbreviation label — colored by surface if affected
            skill_abbr = skill_abbreviations.get(skill_name, skill_name[:3].upper())
            tk.Label(bar_frame, text=skill_abbr, font=("Arial", 9, "bold"), 
                bg="#1a2332", fg=abbr_color, padx=5).pack(side="left")
            
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
        
        # Get surface effects for current tournament
        surface = tournament.get('surface', '')
        fx = SURFACE_EFFECTS.get(surface, {})
        # Map surface effect keys to the skill they affect
        _effect_to_skill = {
            "serve_power": "serve", "forehand_power": "forehand",
            "backhand_power": "backhand", "lift_power": "lift",
            "volley_power": "volley", "dropshot_power": "dropshot",
            "straight_prec": "straight", "cross_prec": "cross",
            "speed": "speed", "stamina_drain": "stamina",
            "slice_stamina": "slice",
        }
        affected_skills = {_effect_to_skill[k] for k in fx if k in _effect_to_skill}
        surface_color = {"clay": "#d35400", "grass": "#27ae60", "hard": "#2980b9", "indoor": "#8e44ad"}.get(surface, "#95a5a6")
        
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
        
        # Surface name below VS (effects are indicated by colored abbreviations in the skill bars)
        if surface:
            surface_icons = {"clay": "🟫", "grass": "🟢", "hard": "🔵", "indoor": "🏢"}
            tk.Label(center_frame, text=f"{surface_icons.get(surface, '🎾')} {surface.capitalize()}", 
                    font=("Arial", 10, "bold"), bg="#1a2332", fg=surface_color).pack(pady=(0, 4))
        
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
        
        # Centered skills comparison section below (raw skills — surface effects apply in-engine)
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
        
        # Skills grouped by subcategory (matching match visualization)
        skill_groups = [
            ("Base Shots", ['serve', 'forehand', 'backhand']),
            ("Special Shots", ['volley', 'dropshot', 'lift', 'slice']),
            ("Physicality", ['speed', 'stamina']),
            ("Tactics", ['cross', 'straight', 'iq', 'mental']),
        ]
        for group_name, skills in skill_groups:
            tk.Label(skills_frame, text=group_name, font=("Arial", 9, "bold"),
                    bg="#1a2332", fg="#95a5a6").pack(anchor="center", pady=(8, 2))
            for skill in skills:
                p1_val = p1_skills.get(skill, 0)
                p2_val = p2_skills.get(skill, 0)
                color = surface_color if skill in affected_skills else "#ffffff"
                create_skill_bar(skills_frame, skill, p1_val, p2_val, max_skill, abbr_color=color)
        
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
            
            # Create a GameEngine object for display purposes (to access player data)
            sets_to_win = 3 if tournament.get('category') == "Grand Slam" else 2
            game_engine = GameEngine(player1, player2, tournament['surface'], sets_to_win=sets_to_win)
            
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
        current_matches = self.scheduler.get_current_matches(tournament['id'])
        
        # Check if match_idx is still valid (tournament may have advanced)
        if match_idx >= len(current_matches):
            self.manage_tournament(tournament)
            return
        
        match = current_matches[match_idx]
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
        self.current_court_viewer = None  # Track court viewer for cleanup
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
            # Cancel court viewer animations
            if hasattr(self, 'current_court_viewer') and self.current_court_viewer:
                self.current_court_viewer.cancel_animations()
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
        
        # Court is now drawn by TennisCourtViewer with real-time animation

        def _update_score_header(header_frame, score_info):
            """Update the scoreboard header with score data after a point."""
            for widget in header_frame.winfo_children():
                widget.destroy()
            sets = score_info['sets']
            current_set = score_info['current_set']
            p1_name = score_info['player1_name']
            p2_name = score_info['player2_name']
            score_frame = tk.Frame(header_frame, bg="#34495e")
            score_frame.pack(fill="x", padx=100)
            set_winners = []
            for set_tuple in sets:
                p1g, p2g = set_tuple
                if p1g >= 6 and p1g - p2g >= 2:
                    set_winners.append(1)
                elif p2g >= 6 and p2g - p1g >= 2:
                    set_winners.append(2)
                elif p1g == 7 and p2g == 6:
                    set_winners.append(1)
                elif p2g == 7 and p1g == 6:
                    set_winners.append(2)
                else:
                    set_winners.append(0)
            # Player 1 row
            p1_row = tk.Frame(score_frame, bg="#3498db")
            p1_row.pack(fill="x", pady=2)
            p1sf = tk.Frame(p1_row, bg="#3498db")
            p1sf.pack(padx=10, pady=5)
            tk.Label(p1sf, text=p1_name + "  ", font=("Arial", 11, "bold"), bg="#3498db", fg="white").pack(side="left")
            for si, st in enumerate(sets):
                f = ("Arial", 11, "bold") if si < len(set_winners) and set_winners[si] == 1 else ("Arial", 11)
                tk.Label(p1sf, text=str(st[0]) + "  ", font=f, bg="#3498db", fg="white").pack(side="left")
            tk.Label(p1sf, text=str(current_set['player1']), font=("Arial", 11, "bold"), bg="#3498db", fg="white").pack(side="left")
            # Player 2 row
            p2_row = tk.Frame(score_frame, bg="#e74c3c")
            p2_row.pack(fill="x", pady=2)
            p2sf = tk.Frame(p2_row, bg="#e74c3c")
            p2sf.pack(padx=10, pady=5)
            tk.Label(p2sf, text=p2_name + "  ", font=("Arial", 11, "bold"), bg="#e74c3c", fg="white").pack(side="left")
            for si, st in enumerate(sets):
                f = ("Arial", 11, "bold") if si < len(set_winners) and set_winners[si] == 2 else ("Arial", 11)
                tk.Label(p2sf, text=str(st[1]) + "  ", font=f, bg="#e74c3c", fg="white").pack(side="left")
            tk.Label(p2sf, text=str(current_set['player2']), font=("Arial", 11, "bold"), bg="#e74c3c", fg="white").pack(side="left")

        def animate_point(cv, events, p1_id, p2_id, on_complete=None):
            """Animate a full point: ball moves in straight lines, players intercept."""
            import math
            from court_viewer import TennisCourtViewer as _CV
            P1_BL = _CV.P1_BASELINE_X
            P2_BL = _CV.P2_BASELINE_X
            P1_VL = _CV.P1_VOLLEY_X
            P2_VL = _CV.P2_VOLLEY_X
            NET_X = _CV.NET_X
            CTR_Y = _CV.CENTER_Y
            MIN_Y = _CV.MIN_Y
            MAX_Y = _CV.MAX_Y

            # Extract shots, score info and point summary from events
            shots = []
            score_info = None
            point_summary = None
            for ev in events:
                if ev['type'] == 'shot':
                    bp = ev.get('ball_positions', [{}])[0]
                    shots.append({
                        'hitter_id': ev['hitter_id'],
                        'x': bp.get('x', 600),
                        'y': bp.get('y', 300),
                        'power': bp.get('power', 50),
                        'shot_type': ev.get('shot_type', 'forehand'),
                        'is_final': ev.get('is_final', False),
                        'stamina': ev.get('stamina', {}),
                    })
                elif ev['type'] == 'score':
                    score_info = ev
                elif ev['type'] == 'point_summary':
                    point_summary = ev

            if not shots:
                if on_complete:
                    on_complete(score_info, point_summary)
                return

            # Mutable player-position state: (x, y) for each player
            state = {
                'p1_x': cv.p1_pos[0], 'p1_y': cv.p1_pos[1],
                'p2_x': cv.p2_pos[0], 'p2_y': cv.p2_pos[1],
                'p1_volley': False, 'p2_volley': False,
            }

            def _pnum(pid):
                return 1 if pid == p1_id else 2

            def _get_pos(pid):
                if pid == p1_id:
                    return (state['p1_x'], state['p1_y'])
                return (state['p2_x'], state['p2_y'])

            def _set_pos(pid, x, y):
                if pid == p1_id:
                    state['p1_x'] = x; state['p1_y'] = y
                else:
                    state['p2_x'] = x; state['p2_y'] = y

            def _set_volley(pid, flag):
                if pid == p1_id:
                    state['p1_volley'] = flag
                else:
                    state['p2_volley'] = flag

            def _is_volley(pid):
                return state['p1_volley'] if pid == p1_id else state['p2_volley']

            def _home_x(pid):
                """Return home X: volley position if in volley mode, else baseline."""
                if pid == p1_id:
                    return P1_VL if state['p1_volley'] else P1_BL
                return P2_VL if state['p2_volley'] else P2_BL

            def _baseline_x(pid):
                return P1_BL if pid == p1_id else P2_BL

            def _defender_id(hid):
                return p2_id if hid == p1_id else p1_id

            def _get_serve_stat(hid):
                """Look up the serve skill of the hitter."""
                if player1 and hid == player1.get('id'):
                    return player1.get('skills', {}).get('serve', 50)
                if player2 and hid == player2.get('id'):
                    return player2.get('skills', {}).get('serve', 50)
                return 50

            def _clamp_y(y):
                return max(MIN_Y, min(MAX_Y, y))

            def _intercept_y(hp, tx, ty, dbx):
                """Extend line hitter→target to baseline x dbx."""
                hx, hy = hp
                dx = tx - hx
                if abs(dx) < 1:
                    return _clamp_y(ty)
                slope = (ty - hy) / dx
                iy = hy + slope * (dbx - hx)
                return _clamp_y(iy)

            def _do_shot(idx):
                if not self.animation_active:
                    return
                if idx >= len(shots):
                    # Point complete – return players to baseline centre
                    cv.clear_marks()
                    state['p1_volley'] = False
                    state['p2_volley'] = False
                    cv.p1_stamina_pct = 1.0
                    cv.p2_stamina_pct = 1.0
                    done = [0]
                    def _home():
                        done[0] += 1
                        if done[0] >= 2:
                            cv.p1_pose = 'ready'
                            cv.p2_pose = 'ready'
                            cv.hide_ball()
                            if on_complete:
                                on_complete(score_info, point_summary)
                    cv.animate_player_to(1, P1_BL, CTR_Y, 400, _home)
                    cv.animate_player_to(2, P2_BL, CTR_Y, 400, _home)
                    return

                shot = shots[idx]
                tx, ty = shot['x'], shot['y']
                hid = shot['hitter_id']
                did = _defender_id(hid)
                h_num = _pnum(hid)
                d_num = _pnum(did)
                stype = shot['shot_type']

                # Update stamina bars from snapshot
                stam = shot.get('stamina', {})
                if stam:
                    if p1_id in stam:
                        cv.update_stamina(1, stam[p1_id])
                    if p2_id in stam:
                        cv.update_stamina(2, stam[p2_id])

                prev_hid = shots[idx - 1]['hitter_id'] if idx > 0 else None
                same_hitter = (hid == prev_hid)

                # Is this the winning / unreturnable shot?
                is_winner = (
                    idx == len(shots) - 1
                    or (idx + 1 < len(shots) and shots[idx + 1]['hitter_id'] == hid)
                )

                # Track volley mode
                if stype == 'volley':
                    _set_volley(hid, True)

                if same_hitter:
                    # Duplicate shot from engine (is_final marker) – skip it,
                    # the winner animation already handled everything.
                    _do_shot(idx + 1)
                    return

                # ---- Positions ----
                hp = _get_pos(hid)
                dp = _get_pos(did)
                d_home_x = _home_x(did)

                # Set player poses for this shot
                cv.set_player_pose(d_num, 'ready')
                if stype == 'serve':
                    cv.set_player_pose(h_num, 'serve')
                elif stype == 'backhand':
                    cv.set_player_pose(h_num, 'hit_backhand')
                else:
                    cv.set_player_pose(h_num, 'hit_forehand')

                # Place ball at hitter
                cv.ball_shot_type = stype
                cv.show_ball_at(hp[0], hp[1])

                # ---- Where does defender need to go? ----
                if stype == 'dropshot':
                    # Dropshot: defender needs to run diagonally toward the
                    # rebound position (near the net)
                    if is_winner:
                        # Can't reach – go only ~60 % of the way
                        def_target_x = dp[0] + 0.6 * (tx - dp[0])
                        def_target_y = dp[1] + 0.6 * (ty - dp[1])
                    else:
                        # Successfully reaches the ball at its rebound
                        def_target_x = tx
                        def_target_y = ty
                elif _is_volley(did):
                    # Defender is in volley mode – positioned near net,
                    # intercept the ball before it rebounds
                    iy = _intercept_y(hp, tx, ty, d_home_x)
                    def_target_x = d_home_x
                    def_target_y = iy if not is_winner else dp[1] + 0.6 * (iy - dp[1])
                else:
                    # Normal shot – defender moves on baseline (Y only)
                    dbx = _baseline_x(did)
                    iy = _intercept_y(hp, tx, ty, dbx)
                    def_target_x = dbx
                    if is_winner:
                        def_target_y = dp[1] + 0.6 * (iy - dp[1])
                    else:
                        def_target_y = iy

                # ---- Ball end-point ----
                if _is_volley(did) and not is_winner and stype != 'dropshot':
                    # Defender in volley mode intercepts before rebound –
                    # ball goes to defender position, no rebound mark
                    ball_end_x = def_target_x
                    ball_end_y = def_target_y
                    use_through = False
                elif stype == 'dropshot' and not is_winner:
                    # Successful dropshot: ball stops at rebound point
                    ball_end_x = tx
                    ball_end_y = ty
                    use_through = False
                elif is_winner:
                    # Winner: ball continues through rebound with red mark
                    dbx_w = _baseline_x(did)
                    iy_w = _intercept_y(hp, tx, ty, dbx_w)
                    ball_end_x = dbx_w
                    ball_end_y = iy_w
                    use_through = True
                else:
                    # Ball reaches defender's interception point
                    ball_end_x = def_target_x
                    ball_end_y = def_target_y
                    use_through = True

                # ---- Ball velocity (pixels / second) ----
                shot_power = shot.get('power', 50)
                if stype == 'serve':
                    # Scale by hitter's serve stat (35–90)
                    serve_stat = _get_serve_stat(hid)
                    serve_t = max(0.0, min(1.0, (serve_stat - 35) / 55.0))
                    ball_velocity = 900 + serve_t * 1500   # 900 .. 2400 px/s
                elif stype == 'dropshot':
                    # Dropshots are visibly slower
                    ball_velocity = 700  # px/s
                else:
                    # Regular / volley shots – based on power
                    power_t = max(0.0, min(1.0, shot_power / 100.0))
                    ball_velocity = 700 + power_t * 1500   # 700 .. 2200 px/s

                # Ball travel distance
                if use_through:
                    ball_dist = (math.hypot(tx - hp[0], ty - hp[1])
                                 + math.hypot(ball_end_x - tx, ball_end_y - ty))
                else:
                    ball_dist = math.hypot(ball_end_x - hp[0], ball_end_y - hp[1])

                dur = max(300, min(2000, int(ball_dist / ball_velocity * 1000)))

                # ---- Attacker replacement: move back toward home position ----
                att_home_x = _home_x(hid)
                att_home_y = CTR_Y
                _set_pos(hid, att_home_x, att_home_y)
                cv.animate_player_to(h_num, att_home_x, att_home_y, max(dur, 700), None)

                # ---- Defender movement (synchronised with ball) ----
                _set_pos(did, def_target_x, def_target_y)
                cv.animate_player_to(d_num, def_target_x, def_target_y, dur, None)

                # Capture is_winner for closure
                _winner = is_winner

                def _on_ball_done():
                    if _winner:
                        # Show end-of-point reactions
                        if point_summary:
                            w_id = point_summary.get('winner_id')
                            l_id = point_summary.get('loser_id')
                            if w_id:
                                cv.set_player_pose(_pnum(w_id), 'celebrate')
                            if l_id:
                                cv.set_player_pose(_pnum(l_id), 'dejected')
                        cv.hide_ball()
                        cv._schedule(800, lambda: _do_shot(idx + 1))
                    else:
                        _do_shot(idx + 1)

                if use_through:
                    cv.animate_ball_through(
                        tx, ty,
                        ball_end_x, ball_end_y,
                        dur, None, _on_ball_done,
                        winner=_winner
                    )
                else:
                    cv.animate_ball_to(ball_end_x, ball_end_y, dur, _on_ball_done)

            # Kick off
            if self.animation_active:
                _do_shot(0)

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
            
            # Header with score - show during and after match
            header_frame = tk.Frame(main_frame, bg="#2c3e50", relief="raised", bd=2)
            header_frame.pack(fill="x", padx=10, pady=10)
            
            # Function to display scoreboard
            def display_scoreboard():
                if not is_match_finished:
                    # During match: show previous point's score to avoid spoilers
                    if i > 0 and point_events and (i - 1) < len(point_events):
                        events = point_events[i - 1]['events']
                        for event in events:
                            if event['type'] == 'score':
                                sets = event['sets']
                                current_set = event['current_set']
                                p1_name = event['player1_name']
                                p2_name = event['player2_name']
                                break
                        else:
                            return False
                    elif i == 0:
                        # First point: show initial score
                        if point_events and len(point_events) > 0:
                            events = point_events[0]['events']
                            for event in events:
                                if event['type'] == 'score':
                                    # Subtract 1 from current_set to get pre-point state
                                    sets = event['sets']
                                    current_set = {'player1': 0, 'player2': 0}
                                    p1_name = event['player1_name']
                                    p2_name = event['player2_name']
                                    break
                            else:
                                return False
                        else:
                            return False
                    else:
                        return False
                else:
                    # End screen: use final data from the LAST point event
                    if point_events and len(point_events) > 0:
                        last_events = point_events[-1]['events']
                        for event in last_events:
                            if event['type'] == 'score':
                                sets = event['sets']
                                current_set = event['current_set']
                                p1_name = event['player1_name']
                                p2_name = event['player2_name']
                                break
                        else:
                            return False
                    else:
                        return False
                
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
                
                # Add current set in progress (always show, even if 0)
                if current_set is not None:
                    tk.Label(p1_score_frame, text=str(current_set.get('player1', 0)), font=("Arial", 11, "bold"), bg="#3498db", fg="white").pack(side="left")
                
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
                
                # Add current set in progress (always show, even if 0)
                if current_set is not None:
                    tk.Label(p2_score_frame, text=str(current_set.get('player2', 0)), font=("Arial", 11, "bold"), bg="#e74c3c", fg="white").pack(side="left")
                
                return True
            
            display_scoreboard()
            
            # Commentary label between scoreboard and court
            commentary_frame = tk.Frame(main_frame, bg="#1a252f")
            commentary_frame.pack(fill="x", padx=10, pady=(0, 2))
            commentary_label = tk.Label(
                commentary_frame, text=getattr(self, '_last_commentary', ''), font=("Arial", 10, "italic"),
                bg="#1a252f", fg="#f0e68c", wraplength=1100, pady=4, padx=10, anchor="center"
            )
            commentary_label.pack(fill="x")
            
            # Court visualization using TennisCourtViewer
            canvas_frame = tk.Frame(main_frame)
            canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            if not is_match_finished:
                # Show court during match
                nonlocal canvas
                court_viewer = TennisCourtViewer(canvas_frame, width=1200, height=600, surface=tournament['surface'])
                canvas = court_viewer.canvas
            else:
                # Match finished - show court as well, with click to go back
                court_viewer = TennisCourtViewer(canvas_frame, width=1200, height=600, surface=tournament['surface'])
                canvas = court_viewer.canvas
                # Add click binding to go back
                canvas.bind("<Button-1>", lambda e: self.show_tournament_bracket(tournament))

            # Player stats display (always show)
            # Create a frame for player stats with two columns
            stats_frame = tk.Frame(main_frame, bg="#ecf0f1")
            stats_frame.pack(fill="x", padx=20, pady=(0, 10))

            # Helper function to calculate the new stats
            def calculate_new_stats(skills):
                # Base Shots (average of serve, forehand, backhand)
                serve = skills.get('serve', 0)
                forehand = skills.get('forehand', 0)
                backhand = skills.get('backhand', 0)
                base_shots = round((serve + forehand + backhand) / 3) if serve + forehand + backhand > 0 else 0

                # Special Shots (average of volley, dropshot, lift, slice)
                volley = skills.get('volley', 0)
                dropshot = skills.get('dropshot', 0)
                lift = skills.get('lift', 0)
                slc = skills.get('slice', 0)
                special_shots = round((volley + dropshot + lift + slc) / 4) if volley + dropshot + lift + slc > 0 else 0

                # Physicality (average of speed, stamina)
                speed = skills.get('speed', 0)
                stamina = skills.get('stamina', 0)
                physicality = round((speed + stamina) / 2) if speed + stamina > 0 else 0

                # Tactics (average of cross, straight, iq, mental)
                cross = skills.get('cross', 0)
                straight = skills.get('straight', 0)
                iq = skills.get('iq', 0)
                mental = skills.get('mental', 50)
                tactics = round((cross + straight + iq + mental) / 4) if cross + straight + iq + mental > 0 else 0

                # Overall (average of all categories)
                overall = round((base_shots + special_shots + physicality + tactics) / 4)

                return {
                    'Base Shots': base_shots,
                    'Physicality': physicality,
                    'Tactics': tactics,
                    'Special Shots': special_shots,
                    'Overall': overall
                }

            # Get stats for both players
            p1_stats = calculate_new_stats(game_engine.p1['skills'])
            p2_stats = calculate_new_stats(game_engine.p2['skills'])

            # Create tab system for player stats
            tab_frame = tk.Frame(stats_frame, bg="#34495e")
            tab_frame.pack(fill="x", pady=(0, 5))
            
            # Initialize instance variable for stats tab if not already set
            if not hasattr(self, 'current_match_stats_tab'):
                self.current_match_stats_tab = "player_stats"
            
            def switch_stats_tab(tab_name):
                self.current_match_stats_tab = tab_name
                update_stats_display()
                # Update button colors
                stats_tab1_btn.config(bg="#3498db" if self.current_match_stats_tab == "player_stats" else "#7f8c8d")
                stats_tab2_btn.config(bg="#3498db" if self.current_match_stats_tab == "match_stats" else "#7f8c8d")
            
            # Tab buttons
            stats_tab1_btn = tk.Button(
                tab_frame,
                text="Player Stats",
                font=("Arial", 10, "bold"),
                bg="#3498db" if self.current_match_stats_tab == "player_stats" else "#7f8c8d",
                fg="white",
                relief="flat",
                bd=0,
                padx=10,
                pady=5,
                command=lambda: switch_stats_tab("player_stats")
            )
            stats_tab1_btn.pack(side="left", padx=2)
            
            stats_tab2_btn = tk.Button(
                tab_frame,
                text="Match Stats",
                font=("Arial", 10, "bold"),
                bg="#3498db" if self.current_match_stats_tab == "match_stats" else "#7f8c8d",
                fg="white",
                relief="flat",
                bd=0,
                padx=10,
                pady=5,
                command=lambda: switch_stats_tab("match_stats")
            )
            stats_tab2_btn.pack(side="left", padx=2)
            
            # Container for stats content
            stats_content_frame = tk.Frame(stats_frame, bg="white")
            stats_content_frame.pack(fill="both", expand=True)
            
            def update_stats_display():
                # Clear the content frame
                for widget in stats_content_frame.winfo_children():
                    widget.destroy()
                
                # Get match stats: during animation show PREVIOUS point's stats to avoid spoilers
                # After animation completes (at end screen), show final stats
                match_stats_p1 = None
                match_stats_p2 = None
                
                if not is_match_finished:
                    # During match: show previous point's stats (use point i-1 so current point doesn't spoil)
                    if i > 0 and point_events and (i - 1) < len(point_events) and 'events' in point_events[i - 1]:
                        events = point_events[i - 1]['events']
                        if events and 'match_stats' in events[0]:
                            match_stats_p1 = events[0]['match_stats']['player1']
                            match_stats_p2 = events[0]['match_stats']['player2']
                    elif i == 0:
                        # First point: no previous stats, show zeros
                        match_stats_p1 = {'aces': 0, 'breaks': 0, 'forehand_winners': 0, 'backhand_winners': 0, 'dropshot_winners': 0, 'volley_winners': 0}
                        match_stats_p2 = {'aces': 0, 'breaks': 0, 'forehand_winners': 0, 'backhand_winners': 0, 'dropshot_winners': 0, 'volley_winners': 0}
                else:
                    # End screen: use final stats from the LAST point event
                    if point_events and len(point_events) > 0:
                        last_events = point_events[-1]['events']
                        if last_events and 'match_stats' in last_events[0]:
                            match_stats_p1 = last_events[0]['match_stats']['player1']
                            match_stats_p2 = last_events[0]['match_stats']['player2']
                
                if self.current_match_stats_tab == "player_stats":
                    # Display player skills
                    display_frame = tk.Frame(stats_content_frame, bg="white")
                    display_frame.pack(fill="both", expand=True)
                    
                    # Left column for Player 1
                    p1_stats_card = tk.Frame(display_frame, bg="#3498db", relief="raised", bd=2)
                    p1_stats_card.pack(side="left", fill="both", expand=True, padx=(5, 2), pady=5)

                    p1_stats_content = tk.Frame(p1_stats_card, bg="#3498db")
                    p1_stats_content.pack(fill="both", expand=True, padx=8, pady=8)

                    # Display player1's new stats
                    for stat_name, stat_value in p1_stats.items():
                        tk.Label(
                            p1_stats_content,
                            text=f"{stat_name}: {stat_value}",
                            font=("Arial", 9),
                            bg="#3498db",
                            fg="white",
                            anchor="w"
                        ).pack(fill="x", pady=1)
        
                    # Right column for Player 2
                    p2_stats_card = tk.Frame(display_frame, bg="#e74c3c", relief="raised", bd=2)
                    p2_stats_card.pack(side="right", fill="both", expand=True, padx=(2, 5), pady=5)

                    p2_stats_content = tk.Frame(p2_stats_card, bg="#e74c3c")
                    p2_stats_content.pack(fill="both", expand=True, padx=8, pady=8)

                    # Display player2's new stats
                    for stat_name, stat_value in p2_stats.items():
                        tk.Label(
                            p2_stats_content,
                            text=f"{stat_name}: {stat_value}",
                            font=("Arial", 9),
                            bg="#e74c3c",
                            fg="white",
                            anchor="w"
                        ).pack(fill="x", pady=1)
                
                else:
                    # Display match stats (aces, breaks, winners)
                    if match_stats_p1 and match_stats_p2:
                        display_frame = tk.Frame(stats_content_frame, bg="white")
                        display_frame.pack(fill="both", expand=True)
                        
                        # Left column for Player 1
                        p1_match_card = tk.Frame(display_frame, bg="#3498db", relief="raised", bd=2)
                        p1_match_card.pack(side="left", fill="both", expand=True, padx=(5, 2), pady=5)

                        p1_match_content = tk.Frame(p1_match_card, bg="#3498db")
                        p1_match_content.pack(fill="both", expand=True, padx=8, pady=8)

                        # Display player1's match stats with combined labels
                        # Aces
                        aces_value = match_stats_p1.get('aces', 0)
                        tk.Label(
                            p1_match_content,
                            text=f"Aces: {aces_value}",
                            font=("Arial", 9),
                            bg="#3498db",
                            fg="white",
                            anchor="w"
                        ).pack(fill="x", pady=1)
                        
                        # Breaks
                        breaks_value = match_stats_p1.get('breaks', 0)
                        tk.Label(
                            p1_match_content,
                            text=f"Breaks: {breaks_value}",
                            font=("Arial", 9),
                            bg="#3498db",
                            fg="white",
                            anchor="w"
                        ).pack(fill="x", pady=1)
                        
                        # Spacing
                        tk.Label(p1_match_content, text="-- WINNERS --", bg="#3498db", fg="white").pack(fill="x", pady=2)
                        
                        # Forehand/Backhand winners
                        fh_value = match_stats_p1.get('forehand_winners', 0)
                        bh_value = match_stats_p1.get('backhand_winners', 0)
                        tk.Label(
                            p1_match_content,
                            text=f"FH / BH : {fh_value} / {bh_value}",
                            font=("Arial", 9),
                            bg="#3498db",
                            fg="white",
                            anchor="w"
                        ).pack(fill="x", pady=1)
                        
                        # Dropshot/Volley winners
                        ds_value = match_stats_p1.get('dropshot_winners', 0)
                        vol_value = match_stats_p1.get('volley_winners', 0)
                        tk.Label(
                            p1_match_content,
                            text=f"DP / VO : {ds_value} / {vol_value}",
                            font=("Arial", 9),
                            bg="#3498db",
                            fg="white",
                            anchor="w"
                        ).pack(fill="x", pady=1)
        
                        # Right column for Player 2
                        p2_match_card = tk.Frame(display_frame, bg="#e74c3c", relief="raised", bd=2)
                        p2_match_card.pack(side="right", fill="both", expand=True, padx=(2, 5), pady=5)

                        p2_match_content = tk.Frame(p2_match_card, bg="#e74c3c")
                        p2_match_content.pack(fill="both", expand=True, padx=8, pady=8)

                        # Display player2's match stats with combined labels
                        # Aces
                        aces_value = match_stats_p2.get('aces', 0)
                        tk.Label(
                            p2_match_content,
                            text=f"Aces: {aces_value}",
                            font=("Arial", 9),
                            bg="#e74c3c",
                            fg="white",
                            anchor="w"
                        ).pack(fill="x", pady=1)
                        
                        # Breaks
                        breaks_value = match_stats_p2.get('breaks', 0)
                        tk.Label(
                            p2_match_content,
                            text=f"Breaks: {breaks_value}",
                            font=("Arial", 9),
                            bg="#e74c3c",
                            fg="white",
                            anchor="w"
                        ).pack(fill="x", pady=1)
                        
                        # Spacing
                        tk.Label(p2_match_content, text="-- WINNERS --", bg="#e74c3c", fg="white").pack(fill="x", pady=2)
                        
                        # Forehand/Backhand winners
                        fh_value = match_stats_p2.get('forehand_winners', 0)
                        bh_value = match_stats_p2.get('backhand_winners', 0)
                        tk.Label(
                            p2_match_content,
                            text=f"FH / BH : {fh_value} / {bh_value}",
                            font=("Arial", 9),
                            bg="#e74c3c",
                            fg="white",
                            anchor="w"
                        ).pack(fill="x", pady=1)
                        
                        # Dropshot/Volley winners
                        ds_value = match_stats_p2.get('dropshot_winners', 0)
                        vol_value = match_stats_p2.get('volley_winners', 0)
                        tk.Label(
                            p2_match_content,
                            text=f"DP / VO : {ds_value} / {vol_value}",
                            font=("Arial", 9),
                            bg="#e74c3c",
                            fg="white",
                            anchor="w"
                        ).pack(fill="x", pady=1)
                    else:
                        # No match stats available yet
                        tk.Label(
                            stats_content_frame,
                            text="Match stats not yet available",
                            font=("Arial", 10),
                            bg="white",
                            fg="#7f8c8d"
                        ).pack(pady=20)
            
            # Initial display
            update_stats_display()
            
            # Control buttons
            control_frame = tk.Frame(main_frame)
            control_frame.pack(fill="x", padx=20, pady=(0, 10))            
            
            # Animate point with real-time player + ball movement
            next_idx = i + 1
            if not is_match_finished and point_events and i < len(point_events):
                court_viewer.set_player_names(player1['name'], player2['name'])
                self.current_court_viewer = court_viewer

                def on_point_complete(score_info, pt_summary=None, _next=next_idx):
                    if not self.animation_active:
                        return
                    if score_info:
                        _update_score_header(header_frame, score_info)
                    # Show commentary for the point that just finished
                    if pt_summary and player1 and player2:
                        ctext = generate_commentary(pt_summary, score_info, player1, player2, tournament)
                        self._last_commentary = ctext
                        try:
                            commentary_label.config(text=ctext)
                        except Exception:
                            pass
                    if _next is not None and _next < len(match_log):
                        def safe_advance():
                            try:
                                if self.animation_active:
                                    show_screen(_next)
                            except Exception as e:
                                print(f"Error in auto-advance: {e}")
                        cid = self.root.after(1500, lambda: self.root.after_idle(safe_advance))
                        self.pending_callbacks.append(cid)

                animate_point(court_viewer, point_events[i]['events'],
                              player1['id'], player2['id'], on_point_complete)
            
            # Navigation buttons
            button_frame = tk.Frame(main_frame)
            button_frame.pack(pady=10)
            
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
    
    def show_bracket_player_popup(self, player_id, tournament, event):
        """Show a popup with player info when clicked in bracket"""
        player = next((p for p in self.scheduler.players if p['id'] == player_id), None)
        if not player:
            return
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title(f"{player['name']}")
        popup.resizable(False, False)
        
        # Set popup size
        popup_width = 300
        popup_height = 220
        
        # Position popup near mouse cursor, but ensure it stays on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = event.x_root + 10
        y = event.y_root + 10
        
        # Adjust if popup would go off the right edge
        if x + popup_width > screen_width:
            x = event.x_root - popup_width - 10
        # Adjust if popup would go off the bottom edge
        if y + popup_height > screen_height:
            y = event.y_root - popup_height - 10
        
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        
        # Main frame with padding
        main_frame = tk.Frame(popup, bg="white", relief="solid", bd=1)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Player name header
        name_label = tk.Label(
            main_frame,
            text=player['name'],
            font=("Arial", 13, "bold"),
            bg="white",
            fg="#2c3e50"
        )
        name_label.pack(fill="x", pady=(0, 10))
        
        # Global rank/ELO/Age
        current_elo_points = self.scheduler.ranking_system.get_elo_points(player, self.scheduler.current_date)
        rank_text = f"Rank: #{player.get('rank', 'N/A')} | ELO: {current_elo_points} | Age: {player.get('age', 'N/A')}"
        rank_label = tk.Label(
            main_frame,
            text=rank_text,
            font=("Arial", 10),
            bg="white",
            fg="#7f8c8d"
        )
        rank_label.pack(fill="x", pady=5)
        
        # Archetype
        archetype, _ = self._get_player_archetype(player)
        archetype_label = tk.Label(
            main_frame,
            text=f"Archetype: {archetype}",
            font=("Arial", 10),
            bg="white",
            fg="#8e44ad",
            wraplength=280,
            justify="left"
        )
        archetype_label.pack(fill="x", pady=5)
        
        # Tournament wins count
        tournament_wins = sum(1 for win in player.get('tournament_wins', []) if win.get('name') == tournament['name'])
        wins_label = tk.Label(
            main_frame,
            text=f"Titles in {tournament['name']}: {tournament_wins}",
            font=("Arial", 10),
            bg="white",
            fg="#27ae60",
            wraplength=280,
            justify="left"
        )
        wins_label.pack(fill="x", pady=5)
        
        # Close button
        close_btn = tk.Button(
            main_frame,
            text="Close",
            font=("Arial", 9),
            bg="#95a5a6",
            fg="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            command=popup.destroy
        )
        close_btn.pack(pady=(10, 0))
    
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
        
        # Get all participant IDs and create a ranking by global rank
        all_participants = []
        for round_matches in bracket:
            for match in round_matches:
                if match[0]:  # p1_id
                    if match[0] not in [p[0] for p in all_participants]:
                        all_participants.append((match[0], player_lookup.get(match[0], {}).get('rank', 999)))
                if match[1]:  # p2_id
                    if match[1] not in [p[0] for p in all_participants]:
                        all_participants.append((match[1], player_lookup.get(match[1], {}).get('rank', 999)))
        
        # Sort by global rank to get participant rankings
        all_participants.sort(key=lambda x: x[1])
        participant_rank_map = {pid: idx + 1 for idx, (pid, _) in enumerate(all_participants)}
        
        def get_name_rank(pid):
            player = player_lookup.get(pid)
            if player:
                participant_rank = participant_rank_map.get(pid, 'N/A')
                return f"{player['name']} ({participant_rank})"
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

                # Player names (left aligned) - make clickable
                p1_text_id = canvas.create_text(x+10, y+match_height//2, anchor="w", text=p1, fill=p1_color,
                                   font=font_bold if winner_id == p1_id else font_normal, tags=f"player_{p1_id}")
                p2_text_id = canvas.create_text(x+10, y+match_height+8+match_height//2, anchor="w", text=p2, fill=p2_color,
                                   font=font_bold if winner_id == p2_id else font_normal, tags=f"player_{p2_id}")
                
                # Bind click events to player names (only if they have an ID)
                if p1_id:
                    canvas.tag_bind(f"player_{p1_id}", "<Button-1>", lambda e, pid=p1_id, t=tournament: self.show_bracket_player_popup(pid, t, e))
                if p2_id:
                    canvas.tag_bind(f"player_{p2_id}", "<Button-1>", lambda e, pid=p2_id, t=tournament: self.show_bracket_player_popup(pid, t, e))

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

    # ───────────────────────── Exhibition Tournament ─────────────────────────

    def show_exhibition_setup(self):
        """Exhibition tournament setup: surface, format, form toggle, draw size."""
        for widget in self.root.winfo_children():
            widget.destroy()

        header_frame = tk.Frame(self.root, bg="#8e44ad", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="🎭 Exhibition Tournament", font=("Arial", 22, "bold"),
                 bg="#8e44ad", fg="white").pack(expand=True)

        main_frame = tk.Frame(self.root, bg="#ecf0f1")
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # --- Options ---
        opts_frame = tk.Frame(main_frame, bg="#ecf0f1")
        opts_frame.pack(fill="x", pady=(0, 8))

        # Surface
        tk.Label(opts_frame, text="Surface:", font=("Arial", 11, "bold"),
                 bg="#ecf0f1", fg="#2c3e50").grid(row=0, column=0, padx=(0, 5), sticky="w")
        surface_var = tk.StringVar(value="hard")
        for idx, (srf, icon) in enumerate([("clay", "🟫"), ("grass", "🟢"), ("hard", "🔵"), ("indoor", "🏢"), ("neutral", "⚪")]):
            tk.Radiobutton(opts_frame, text=f"{icon} {srf.capitalize()}", variable=surface_var, value=srf,
                           font=("Arial", 10), bg="#ecf0f1", activebackground="#ecf0f1"
                           ).grid(row=0, column=1 + idx, padx=4)

        # Format
        tk.Label(opts_frame, text="Format:", font=("Arial", 11, "bold"),
                 bg="#ecf0f1", fg="#2c3e50").grid(row=1, column=0, padx=(0, 5), sticky="w", pady=(6, 0))
        format_var = tk.StringVar(value="bo3")
        tk.Radiobutton(opts_frame, text="Best of 3", variable=format_var, value="bo3",
                       font=("Arial", 10), bg="#ecf0f1", activebackground="#ecf0f1"
                       ).grid(row=1, column=1, padx=4, pady=(6, 0))
        tk.Radiobutton(opts_frame, text="Best of 5", variable=format_var, value="bo5",
                       font=("Arial", 10), bg="#ecf0f1", activebackground="#ecf0f1"
                       ).grid(row=1, column=2, columnspan=2, padx=4, pady=(6, 0))

        # Random form toggle
        form_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opts_frame, text="Apply random form (±2.5%)", variable=form_var,
                       font=("Arial", 10), bg="#ecf0f1", activebackground="#ecf0f1"
                       ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # Number of players
        max_players = min(50, len(self.scheduler.hall_of_fame))
        tk.Label(opts_frame, text="Players:", font=("Arial", 11, "bold"),
                 bg="#ecf0f1", fg="#2c3e50").grid(row=3, column=0, padx=(0, 5), sticky="w", pady=(6, 0))
        players_var = tk.IntVar(value=min(8, max_players))
        tk.Spinbox(opts_frame, from_=2, to=max_players, textvariable=players_var,
                   font=("Arial", 11), width=5
                   ).grid(row=3, column=1, padx=4, pady=(6, 0), sticky="w")
        tk.Label(opts_frame, text=f"(2–{max_players})", font=("Arial", 9),
                 bg="#ecf0f1", fg="#7f8c8d").grid(row=3, column=2, padx=4, pady=(6, 0), sticky="w")

        # --- Generate Bracket ---
        def _generate():
            from math import ceil, log2
            num_players = max(2, min(max_players, players_var.get()))
            surface = surface_var.get()
            sets_to_win = 3 if format_var.get() == "bo5" else 2
            apply_form = form_var.get()

            draw_size = 2 ** int(ceil(log2(num_players))) if num_players > 1 else 2
            num_byes = draw_size - num_players
            num_matches = draw_size // 2

            # Create slots: 'EMPTY' for player positions, None for BYEs
            slots = ['EMPTY'] * draw_size
            for i in range(num_byes):
                match_idx = num_matches - 1 - i
                slots[match_idx * 2 + 1] = None  # BYE as 2nd player in last matches

            self.exhibition_tournament = {
                'id': 'exhibition',
                'name': 'Exhibition Tournament',
                'surface': surface,
                'category': 'Exhibition',
                'sets_to_win': sets_to_win,
                'apply_form': apply_form,
                'draw_size': draw_size,
                'num_players': num_players,
                'bracket': [],
                'active_matches': [],
                'current_round': 0,
                'winner_id': None,
                'slots': slots,
                'all_filled': False,
                'player_data': {},
                'selected_hof_indices': set(),
            }
            self.exhibition_bracket_tab = None
            self.show_exhibition_bracket()

        btn_frame = tk.Frame(main_frame, bg="#ecf0f1")
        btn_frame.pack(fill="x", pady=15)

        tk.Button(btn_frame, text="▶️ GENERATE BRACKET", font=("Arial", 14, "bold"),
                  bg="#8e44ad", fg="white", relief="flat", bd=0, padx=30, pady=12,
                  activebackground="#7d3c98", activeforeground="white",
                  command=_generate).pack(side="left", expand=True)

        tk.Button(btn_frame, text="⬅️ BACK", font=("Arial", 14, "bold"),
                  bg="#95a5a6", fg="white", relief="flat", bd=0, padx=30, pady=12,
                  command=self.build_main_menu).pack(side="left", expand=True)

    def show_exhibition_bracket(self):
        """Show the exhibition tournament bracket."""
        for widget in self.root.winfo_children():
            widget.destroy()

        t = self.exhibition_tournament

        # Header
        header_frame = tk.Frame(self.root, bg="#8e44ad", height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        title = "Exhibition Tournament"
        if t.get('winner_id'):
            winner = t['player_data'].get(t['winner_id'], {})
            title += f" — Winner: {winner.get('name', '?')}"
        tk.Label(header_frame, text=f"🎭 {title}", font=("Arial", 18, "bold"),
                 bg="#8e44ad", fg="white").pack(expand=True)

        # Control bar
        ctrl_frame = tk.Frame(self.root, bg="#34495e", height=50)
        ctrl_frame.pack(fill="x")
        ctrl_frame.pack_propagate(False)
        ctrl_inner = tk.Frame(ctrl_frame, bg="#34495e")
        ctrl_inner.pack(expand=True)

        tk.Button(ctrl_inner, text="⬅️ Setup", font=("Arial", 11, "bold"),
                  bg="#95a5a6", fg="white", relief="flat", bd=0, padx=15, pady=6,
                  command=self.show_exhibition_setup).pack(side="left", padx=5)
        tk.Button(ctrl_inner, text="🏠 Main Menu", font=("Arial", 11, "bold"),
                  bg="#95a5a6", fg="white", relief="flat", bd=0, padx=15, pady=6,
                  command=self.build_main_menu).pack(side="left", padx=5)

        if t['all_filled'] and not t.get('winner_id'):
            # Shuffle button: only before any match in current round is played
            any_played = any(len(m) >= 4 and m[2] is not None for m in t.get('active_matches', [])
                             if m[0] is not None and m[1] is not None)
            if t['current_round'] == 0 and not any_played:
                tk.Button(ctrl_inner, text="🔀 Shuffle Draw", font=("Arial", 11, "bold"),
                          bg="#e67e22", fg="white", relief="flat", bd=0, padx=15, pady=6,
                          command=self._exhibition_shuffle_draw).pack(side="left", padx=5)
            # Simulate Round button
            has_unplayed = any((len(m) < 4 or m[2] is None) and m[0] is not None and m[1] is not None
                               for m in t.get('active_matches', []))
            if has_unplayed:
                tk.Button(ctrl_inner, text="⚡ Simulate Round", font=("Arial", 11, "bold"),
                          bg="#27ae60", fg="white", relief="flat", bd=0, padx=15, pady=6,
                          command=self._exhibition_simulate_round).pack(side="left", padx=5)
        elif not t['all_filled']:
            filled = sum(1 for s in t['slots'] if s not in ('EMPTY', None))
            total = t['num_players']
            tk.Label(ctrl_inner, text=f"Players: {filled}/{total} — Click 'Empty' slots to fill",
                     font=("Arial", 11), bg="#34495e", fg="#f39c12").pack(side="left", padx=15)

        # Round tabs (only in playing phase with multiple rounds)
        if t['bracket'] and len(t['bracket']) > 1:
            num_rounds = len(t['bracket'])
            round_names = self._get_round_names(num_rounds)
            tab_frame = tk.Frame(self.root, bg="#2c3e50", height=40)
            tab_frame.pack(fill="x")
            tab_frame.pack_propagate(False)
            tab_inner = tk.Frame(tab_frame, bg="#2c3e50")
            tab_inner.pack(expand=True)
            current_tab = getattr(self, 'exhibition_bracket_tab', None) or round_names[0]
            for rn in round_names:
                is_active = rn == current_tab
                bg_color = "#8e44ad" if is_active else "#5d6d7e"
                tk.Button(tab_inner, text=rn, bg=bg_color, fg="white",
                          command=lambda tn=rn: self._switch_exhibition_tab(tn),
                          font=("Arial", 10, "bold" if is_active else "normal"),
                          relief="flat", bd=0, padx=12, pady=5).pack(side="left", padx=2)

        # Draw the bracket
        self._draw_exhibition_bracket()

    def _switch_exhibition_tab(self, tab_name):
        self.exhibition_bracket_tab = tab_name
        self.show_exhibition_bracket()

    def _draw_exhibition_bracket(self):
        """Draw the exhibition tournament bracket on a scrollable canvas."""
        t = self.exhibition_tournament

        frame = tk.Frame(self.root, bg="white")
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame, bg="white", width=1300, height=1600, highlightthickness=0)
        vscroll = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        hscroll = tk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")
        hscroll.pack(side="bottom", fill="x")

        match_height = 40
        match_gap = 100
        round_gap = 400
        y_offset = 40
        rect_width = 300
        font_bold = ("Arial", 11, "bold")
        font_normal = ("Arial", 11)

        if not t['all_filled']:
            # ── FILLING PHASE: show first-round match slots ──
            slots = t['slots']
            num_matches = t['draw_size'] // 2

            for m_idx in range(num_matches):
                x = 40
                y = y_offset + m_idx * (match_height + match_gap)
                s1 = slots[m_idx * 2]
                s2 = slots[m_idx * 2 + 1]

                for slot_offset, s_val in enumerate([s1, s2]):
                    slot_idx = m_idx * 2 + slot_offset
                    sy = y if slot_offset == 0 else y + match_height + 8
                    is_empty = s_val == 'EMPTY'
                    is_bye = s_val is None

                    box_color = "#ffe0e0" if is_empty else "#f0f0f0"
                    outline = "#c0392b" if is_empty else "#888"

                    if is_bye:
                        name = "BYE"
                        text_color = "#999"
                    elif is_empty:
                        name = "Empty — click to fill"
                        text_color = "#c0392b"
                    else:
                        player = t['player_data'].get(s_val, {})
                        name = player.get('name', '?')
                        text_color = "black"

                    tag = f"slot_{slot_idx}"
                    canvas.create_rectangle(x, sy, x + rect_width, sy + match_height,
                                            fill=box_color, outline=outline, tags=tag)
                    canvas.create_text(x + 10, sy + match_height // 2, anchor="w",
                                       text=name, fill=text_color, font=font_normal, tags=tag)

                    if is_empty:
                        canvas.tag_bind(tag, "<Button-1>",
                                        lambda e, si=slot_idx: self._show_exhibition_player_picker(si))

            max_y = y_offset + num_matches * (match_height + match_gap)
            canvas.config(scrollregion=(0, 0, rect_width + 100, max_y))
        else:
            # ── PLAYING PHASE: show full bracket ──
            bracket = t.get('bracket', [])
            if not bracket:
                return
            num_rounds = len(bracket)
            round_names = self._get_round_names(num_rounds)
            current_tab = getattr(self, 'exhibition_bracket_tab', None) or round_names[0]

            if current_tab == round_names[0]:
                start_round = 0
                rounds_to_show = bracket
            elif current_tab in round_names:
                start_round = round_names.index(current_tab)
                rounds_to_show = bracket[start_round:]
            else:
                start_round = 0
                rounds_to_show = bracket

            match_positions = []

            for display_r, round_matches in enumerate(rounds_to_show):
                actual_round = start_round + display_r
                x = 40 + display_r * round_gap
                round_y_positions = []

                for m_idx, m in enumerate(round_matches):
                    if display_r == 0:
                        y = y_offset + m_idx * (match_height + match_gap)
                    else:
                        prev_y1 = match_positions[display_r - 1][m_idx * 2]
                        prev_y2 = match_positions[display_r - 1][m_idx * 2 + 1]
                        y = (prev_y1 + prev_y2) // 2
                    round_y_positions.append(y)

                    p1_id, p2_id = m[0], m[1]
                    winner_id = m[2] if len(m) > 2 else None
                    score = m[3] if len(m) > 3 else ""

                    p1_name = t['player_data'].get(p1_id, {}).get('name', 'BYE') if p1_id else 'BYE'
                    p2_name = t['player_data'].get(p2_id, {}).get('name', 'BYE') if p2_id else 'BYE'

                    # Parse scores
                    p1_sets, p2_sets, set_winners = [], [], []
                    if score and score != "BYE":
                        for s in score.split(","):
                            s = s.strip()
                            if "-" in s:
                                a, b = s.split("-")
                                a, b = int(a.strip()), int(b.strip())
                                p1_sets.append(a)
                                p2_sets.append(b)
                                set_winners.append(1 if a > b else (2 if b > a else 0))

                    box_color = "#f0f0f0"
                    outline_color = "#888"

                    canvas.create_rectangle(x, y, x + rect_width, y + match_height,
                                            fill=box_color, outline=outline_color)
                    canvas.create_rectangle(x, y + match_height + 8, x + rect_width,
                                            y + 2 * match_height + 8, fill=box_color, outline=outline_color)

                    canvas.create_text(x + 10, y + match_height // 2, anchor="w", text=p1_name,
                                       fill="black", font=font_bold if winner_id == p1_id else font_normal)
                    canvas.create_text(x + 10, y + match_height + 8 + match_height // 2, anchor="w",
                                       text=p2_name, fill="black",
                                       font=font_bold if winner_id == p2_id else font_normal)

                    # Draw scores
                    score_x = x + rect_width - 10
                    sx = score_x
                    for idx_s, val in enumerate(reversed(p1_sets)):
                        set_idx = len(p1_sets) - 1 - idx_s
                        sf = font_bold if set_winners and set_winners[set_idx] == 1 else font_normal
                        canvas.create_text(sx, y + match_height // 2, anchor="e",
                                           text=str(val), fill="black", font=sf)
                        sx -= 14
                    sx = score_x
                    for idx_s, val in enumerate(reversed(p2_sets)):
                        set_idx = len(p2_sets) - 1 - idx_s
                        sf = font_bold if set_winners and set_winners[set_idx] == 2 else font_normal
                        canvas.create_text(sx, y + match_height + 8 + match_height // 2, anchor="e",
                                           text=str(val), fill="black", font=sf)
                        sx -= 14

                    # Simulate / Watch buttons for current round unfinished non-BYE matches
                    if (actual_round == t['current_round'] and (len(m) < 4 or m[2] is None)
                            and not t.get('winner_id') and p1_id and p2_id):
                        btn_sim = tk.Button(canvas, text="Simulate", font=("Arial", 10),
                                            command=functools.partial(self._exhibition_simulate_match, m_idx))
                        btn_watch = tk.Button(canvas, text="Watch", font=("Arial", 10),
                                             command=functools.partial(self._exhibition_watch_match, m_idx))
                        canvas.create_window(x + 10, y + 2 * match_height + 18, anchor="nw", window=btn_sim)
                        canvas.create_window(x + 80, y + 2 * match_height + 18, anchor="nw", window=btn_watch)

                match_positions.append(round_y_positions)

                # Connecting lines
                if display_r > 0:
                    prev_x = 40 + (display_r - 1) * round_gap
                    for mc, yc in enumerate(round_y_positions):
                        if mc * 2 < len(match_positions[display_r - 1]) and mc * 2 + 1 < len(match_positions[display_r - 1]):
                            prev_y1 = match_positions[display_r - 1][mc * 2]
                            prev_y2 = match_positions[display_r - 1][mc * 2 + 1]
                            canvas.create_line(prev_x + rect_width, prev_y1 + match_height,
                                               x, yc + match_height, fill="#888", width=2)
                            canvas.create_line(prev_x + rect_width, prev_y2 + match_height,
                                               x, yc + match_height, fill="#888", width=2)

            max_x = 40 + len(rounds_to_show) * round_gap + rect_width + 100
            first_round_count = len(rounds_to_show[0]) if rounds_to_show else 1
            max_y = y_offset + first_round_count * (match_height + match_gap)
            canvas.config(scrollregion=(0, 0, max_x, max_y))

        # Scrolling bindings
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _on_shift_mousewheel(event):
            canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<Shift-MouseWheel>", _on_shift_mousewheel)

    # ── Player picker popup ──

    def _show_exhibition_player_picker(self, slot_idx):
        """Show a popup to pick a HOF player for the given slot."""
        t = self.exhibition_tournament

        popup = tk.Toplevel(self.root)
        popup.title("Select Player")
        popup.geometry("450x520")
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text="Select Player", font=("Arial", 14, "bold")).pack(pady=(10, 5))

        search_var = tk.StringVar()
        tk.Entry(popup, textvariable=search_var, font=("Arial", 11)).pack(fill="x", padx=10)

        hof = self.scheduler.hall_of_fame
        choices = []  # (label, hof_idx)
        for i, h in enumerate(hof):
            if i in t['selected_hof_indices']:
                continue
            pk = h.get('peak_skills', {})
            ovr = round(sum(pk.values()) / len(pk)) if pk else 0
            hof_pts = h.get('hof_points', 0)
            label = f"{h['name']}  (Peak {ovr}, HOF pts {hof_pts})"
            choices.append((label, i))
        choices.sort(key=lambda c: -hof[c[1]].get('hof_points', 0))

        listbox_frame = tk.Frame(popup)
        listbox_frame.pack(fill="both", expand=True, padx=10, pady=5)
        listbox = tk.Listbox(listbox_frame, font=("Arial", 10), exportselection=False)
        sb = tk.Scrollbar(listbox_frame, command=listbox.yview)
        listbox.config(yscrollcommand=sb.set)
        listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        filtered_choices = list(choices)

        def _filter(*_):
            nonlocal filtered_choices
            q = search_var.get().lower()
            listbox.delete(0, tk.END)
            filtered_choices = [c for c in choices if q in c[0].lower()]
            for lbl, _ in filtered_choices:
                listbox.insert(tk.END, lbl)

        search_var.trace_add("write", _filter)
        _filter()

        def _select():
            sel = listbox.curselection()
            if not sel:
                return
            _, hof_idx = filtered_choices[sel[0]]
            hof_entry = hof[hof_idx]

            player = self._build_exhibition_player(hof_entry)
            pid = player['id']
            t['slots'][slot_idx] = pid
            t['player_data'][pid] = player
            t['selected_hof_indices'].add(hof_idx)

            # Check if all non-BYE slots are filled
            if all(s != 'EMPTY' for s in t['slots']):
                t['all_filled'] = True
                self._exhibition_build_bracket()

            popup.destroy()
            self.show_exhibition_bracket()

        tk.Button(popup, text="✅ Select", font=("Arial", 12, "bold"),
                  bg="#8e44ad", fg="white", relief="flat", padx=20, pady=8,
                  command=_select).pack(pady=10)
        listbox.bind('<Double-Button-1>', lambda e: _select())

    # ── Bracket building & advancing ──

    def _exhibition_build_bracket(self):
        """Build the bracket structure from the filled slots."""
        from math import ceil, log2
        t = self.exhibition_tournament
        draw_size = t['draw_size']
        num_rounds = int(ceil(log2(draw_size)))

        first_round = []
        for i in range(0, draw_size, 2):
            p1 = t['slots'][i]
            p2 = t['slots'][i + 1]
            first_round.append((p1, p2, None))

        t['bracket'] = [[] for _ in range(num_rounds)]
        t['bracket'][0] = first_round
        t['active_matches'] = list(first_round)
        t['current_round'] = 0

        # Auto-resolve BYE matches
        self._exhibition_resolve_byes()

    def _exhibition_resolve_byes(self):
        """Auto-resolve BYE matches in the current round."""
        t = self.exhibition_tournament
        changed = False
        for i, match in enumerate(t['active_matches']):
            p1_id, p2_id = match[0], match[1]
            if (p1_id is None or p2_id is None) and (len(match) < 4 or match[2] is None):
                if p1_id is None and p2_id is None:
                    t['active_matches'][i] = (None, None, None, "BYE")
                elif p1_id is None:
                    t['active_matches'][i] = (None, p2_id, p2_id, "BYE")
                else:
                    t['active_matches'][i] = (p1_id, None, p1_id, "BYE")
                t['bracket'][t['current_round']][i] = t['active_matches'][i]
                changed = True

        if changed and all(len(m) >= 4 and m[2] is not None for m in t['active_matches']):
            self._exhibition_advance_round()

    def _exhibition_advance_round(self):
        """Advance the exhibition tournament to the next round."""
        t = self.exhibition_tournament
        current_round = t['current_round']
        next_round = current_round + 1

        if next_round >= len(t['bracket']):
            # Tournament finished
            for match in t['active_matches']:
                if len(match) > 2 and match[2] is not None:
                    t['winner_id'] = match[2]
                    break
            return

        winners = []
        for match in t['active_matches']:
            winners.append(match[2] if len(match) > 2 and match[2] is not None else None)

        next_matches = []
        for i in range(0, len(winners), 2):
            w1 = winners[i]
            w2 = winners[i + 1] if i + 1 < len(winners) else None
            next_matches.append((w1, w2, None))

        t['bracket'][next_round] = next_matches
        t['active_matches'] = next_matches
        t['current_round'] = next_round
        self._exhibition_resolve_byes()

    def _exhibition_check_round_complete(self):
        """Check if all matches in the current round are done; advance if so."""
        t = self.exhibition_tournament
        if all(len(m) >= 4 and m[2] is not None for m in t['active_matches']):
            self._exhibition_advance_round()

    # ── Match simulation ──

    def _exhibition_simulate_match_internal(self, match_idx):
        """Simulate a single exhibition match (core logic, no UI refresh)."""
        import copy
        from sim.game_engine import GameEngine
        t = self.exhibition_tournament
        match = t['active_matches'][match_idx]

        if len(match) >= 4 and match[2] is not None:
            return

        p1_id, p2_id = match[0], match[1]

        if not p1_id or not p2_id:
            winner_id = p1_id or p2_id
            t['active_matches'][match_idx] = (p1_id, p2_id, winner_id, "BYE")
            t['bracket'][t['current_round']][match_idx] = t['active_matches'][match_idx]
            return

        p1 = copy.deepcopy(t['player_data'][p1_id])
        p2 = copy.deepcopy(t['player_data'][p2_id])

        engine = GameEngine(p1, p2, t['surface'], sets_to_win=t['sets_to_win'])
        if not t['apply_form']:
            engine.p1["skills"] = {k: v for k, v in t['player_data'][p1_id]["skills"].items()}
            engine.p2["skills"] = {k: v for k, v in t['player_data'][p2_id]["skills"].items()}
            engine.speed[p1["id"]] = t['player_data'][p1_id]["skills"]["speed"]
            engine.speed[p2["id"]] = t['player_data'][p2_id]["skills"]["speed"]

        list(engine.simulate_match(visualize=False))
        winner_id = p1_id if engine.sets['player1'] > engine.sets['player2'] else p2_id
        score = engine.format_set_scores()

        t['active_matches'][match_idx] = (p1_id, p2_id, winner_id, score)
        t['bracket'][t['current_round']][match_idx] = t['active_matches'][match_idx]

    def _exhibition_simulate_match(self, match_idx):
        """Simulate one exhibition match and refresh the bracket view."""
        self._exhibition_simulate_match_internal(match_idx)
        self._exhibition_check_round_complete()
        self.show_exhibition_bracket()

    def _exhibition_simulate_round(self):
        """Simulate all unfinished matches in the current round."""
        t = self.exhibition_tournament
        for i in range(len(t['active_matches'])):
            self._exhibition_simulate_match_internal(i)
        self._exhibition_check_round_complete()
        self.show_exhibition_bracket()

    # ── Watch match (faceoff → visualization) ──

    def _exhibition_watch_match(self, match_idx):
        """Watch an exhibition match: show faceoff, then visualize."""
        t = self.exhibition_tournament
        match = t['active_matches'][match_idx]

        if len(match) >= 4 and match[2] is not None:
            self.show_exhibition_bracket()
            return

        p1_id, p2_id = match[0], match[1]
        if not p1_id or not p2_id:
            winner_id = p1_id or p2_id
            t['active_matches'][match_idx] = (p1_id, p2_id, winner_id, "BYE")
            t['bracket'][t['current_round']][match_idx] = t['active_matches'][match_idx]
            self._exhibition_check_round_complete()
            self.show_exhibition_bracket()
            return

        p1 = t['player_data'][p1_id]
        p2 = t['player_data'][p2_id]
        self._show_exhibition_faceoff(p1, p2, match_idx)

    def _show_exhibition_faceoff(self, player1, player2, match_idx):
        """Show a faceoff screen for an exhibition match."""
        for widget in self.root.winfo_children():
            widget.destroy()

        t = self.exhibition_tournament
        surface = t['surface']

        main_frame = tk.Frame(self.root, bg="#1a2332")
        main_frame.pack(fill="both", expand=True)

        # Header
        header_frame = tk.Frame(main_frame, bg="#2c3e50", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="MATCH PREVIEW", font=("Arial", 24, "bold"),
                 bg="#2c3e50", fg="white", pady=20).pack()

        # Surface effects
        from sim.game_engine import SURFACE_EFFECTS
        fx = SURFACE_EFFECTS.get(surface, {})
        _effect_to_skill = {
            "serve_power": "serve", "forehand_power": "forehand",
            "backhand_power": "backhand", "lift_power": "lift",
            "volley_power": "volley", "dropshot_power": "dropshot",
            "straight_prec": "straight", "cross_prec": "cross",
            "speed": "speed", "stamina_drain": "stamina",
            "slice_stamina": "slice",
        }
        affected_skills = {_effect_to_skill[k] for k in fx if k in _effect_to_skill}
        surface_color = {"clay": "#d35400", "grass": "#27ae60", "hard": "#2980b9",
                         "indoor": "#8e44ad"}.get(surface, "#95a5a6")

        skill_abbreviations = {
            'serve': 'SRV', 'forehand': 'FRH', 'backhand': 'BKH', 'cross': 'CRS',
            'straight': 'STR', 'speed': 'SPD', 'stamina': 'STA', 'mental': 'MNT',
            'dropshot': 'DRP', 'volley': 'VOL', 'lift': 'LFT', 'slice': 'SLC', 'iq': 'IQ'
        }

        def create_skill_bar(parent, skill_name, p1_val, p2_val, abbr_color="#ffffff"):
            bar_frame = tk.Frame(parent, bg="#1a2332")
            bar_frame.pack(fill="x", pady=4)
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
            skill_abbr = skill_abbreviations.get(skill_name, skill_name[:3].upper())
            tk.Label(bar_frame, text=skill_abbr, font=("Arial", 9, "bold"),
                     bg="#1a2332", fg=abbr_color, padx=5).pack(side="left")
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

        # Player info panels
        content_frame = tk.Frame(main_frame, bg="#1a2332")
        content_frame.pack(fill="both", expand=False, padx=30, pady=(20, 0))

        p1_panel = tk.Frame(content_frame, bg="#2c3e50", relief="raised", bd=2)
        p1_panel.pack(side="left", fill="both", expand=True, padx=(0, 15))
        p1_header = tk.Frame(p1_panel, bg="#3498db", height=50)
        p1_header.pack(fill="x")
        p1_header.pack_propagate(False)
        tk.Label(p1_header, text=player1['name'], font=("Arial", 16, "bold"),
                 bg="#3498db", fg="white", padx=15, pady=10).pack(side="left", fill="x", expand=True)
        p1_content = tk.Frame(p1_panel, bg="#2c3e50")
        p1_content.pack(fill="both", expand=True, padx=15, pady=15)
        p1_rank = player1.get('rank', 'N/A')
        p1_info = f"Best Ranking: #{p1_rank}\nArchetype: {player1.get('archetype', 'N/A')}"
        tk.Label(p1_content, text=p1_info, font=("Arial", 10),
                 bg="#2c3e50", fg="#ecf0f1", justify="left", anchor="w").pack(fill="x")

        center_frame = tk.Frame(content_frame, bg="#1a2332", width=80)
        center_frame.pack(side="left", fill="both", padx=10)
        center_frame.pack_propagate(False)
        tk.Label(center_frame, text="VS", font=("Arial", 20, "bold"),
                 bg="#1a2332", fg="#f39c12").pack(expand=True)
        if surface:
            surface_icons = {"clay": "🟫", "grass": "🟢", "hard": "🔵", "indoor": "🏢", "neutral": "⚪"}
            tk.Label(center_frame, text=f"{surface_icons.get(surface, '🎾')} {surface.capitalize()}",
                     font=("Arial", 10, "bold"), bg="#1a2332", fg=surface_color).pack(pady=(0, 4))

        p2_panel = tk.Frame(content_frame, bg="#2c3e50", relief="raised", bd=2)
        p2_panel.pack(side="left", fill="both", expand=True, padx=(15, 0))
        p2_header = tk.Frame(p2_panel, bg="#e74c3c", height=50)
        p2_header.pack(fill="x")
        p2_header.pack_propagate(False)
        tk.Label(p2_header, text=player2['name'], font=("Arial", 16, "bold"),
                 bg="#e74c3c", fg="white", padx=15, pady=10).pack(side="right", fill="x", expand=True, anchor="e")
        p2_content = tk.Frame(p2_panel, bg="#2c3e50")
        p2_content.pack(fill="both", expand=True, padx=15, pady=15)
        p2_rank = player2.get('rank', 'N/A')
        p2_info = f"Best Ranking: #{p2_rank}\nArchetype: {player2.get('archetype', 'N/A')}"
        tk.Label(p2_content, text=p2_info, font=("Arial", 10),
                 bg="#2c3e50", fg="#ecf0f1", justify="left", anchor="w").pack(fill="x")

        # Skills comparison
        p1_skills = player1.get('skills', {})
        p2_skills = player2.get('skills', {})

        skills_frame = tk.Frame(main_frame, bg="#1a2332")
        skills_frame.pack(fill="both", expand=True, padx=100, pady=20)
        tk.Label(skills_frame, text="SKILLS COMPARISON", font=("Arial", 12, "bold"),
                 bg="#1a2332", fg="#f39c12").pack(anchor="center", pady=(0, 15))

        skill_groups = [
            ("Base Shots", ['serve', 'forehand', 'backhand']),
            ("Special Shots", ['volley', 'dropshot', 'lift', 'slice']),
            ("Physicality", ['speed', 'stamina']),
            ("Tactics", ['cross', 'straight', 'iq', 'mental']),
        ]
        for group_name, skills in skill_groups:
            tk.Label(skills_frame, text=group_name, font=("Arial", 9, "bold"),
                     bg="#1a2332", fg="#95a5a6").pack(anchor="center", pady=(8, 2))
            for skill in skills:
                p1_val = p1_skills.get(skill, 0)
                p2_val = p2_skills.get(skill, 0)
                color = surface_color if skill in affected_skills else "#ffffff"
                create_skill_bar(skills_frame, skill, p1_val, p2_val, abbr_color=color)

        # Buttons
        button_frame = tk.Frame(main_frame, bg="#2c3e50", height=80)
        button_frame.pack(fill="x")
        button_frame.pack_propagate(False)

        def start_match():
            import copy
            from sim.game_engine import GameEngine

            p1_copy = copy.deepcopy(player1)
            p2_copy = copy.deepcopy(player2)
            engine = GameEngine(p1_copy, p2_copy, t['surface'], sets_to_win=t['sets_to_win'])

            if not t['apply_form']:
                engine.p1["skills"] = {k: v for k, v in player1["skills"].items()}
                engine.p2["skills"] = {k: v for k, v in player2["skills"].items()}
                engine.speed[p1_copy["id"]] = player1["skills"]["speed"]
                engine.speed[p2_copy["id"]] = player2["skills"]["speed"]

            point_events = []
            match_events = list(engine.simulate_match(visualize=True))
            match_log = engine.match_log

            for event in match_events:
                if event['type'] == 'point':
                    point_events.append(event)

            winner_id = player1['id'] if engine.sets['player1'] > engine.sets['player2'] else player2['id']
            score = engine.format_set_scores()

            # Update bracket
            t['active_matches'][match_idx] = (player1['id'], player2['id'], winner_id, score)
            t['bracket'][t['current_round']][match_idx] = t['active_matches'][match_idx]
            self._exhibition_check_round_complete()

            # Override show_tournament_bracket so back button returns to exhibition bracket
            original_show_bracket = self.show_tournament_bracket
            def _exh_back(_t):
                self.show_tournament_bracket = original_show_bracket
                self.show_exhibition_bracket()
            self.show_tournament_bracket = _exh_back

            self.display_simple_match_log(match_log, t, point_events, player1, player2, engine)

        tk.Button(button_frame, text="▶️ START MATCH", font=("Arial", 14, "bold"),
                  bg="#27ae60", fg="white", padx=30, pady=15, relief="raised", bd=0,
                  command=start_match).pack(side="left", padx=20, expand=True)
        tk.Button(button_frame, text="⬅️ BACK", font=("Arial", 14, "bold"),
                  bg="#95a5a6", fg="white", padx=30, pady=15, relief="raised", bd=0,
                  command=self.show_exhibition_bracket).pack(side="left", padx=20, expand=True)

    # ── Shuffle draw ──

    def _exhibition_shuffle_draw(self):
        """Shuffle the player positions in the draw."""
        import random
        t = self.exhibition_tournament

        player_ids = [s for s in t['slots'] if s is not None and s != 'EMPTY']
        random.shuffle(player_ids)

        p_idx = 0
        for i in range(len(t['slots'])):
            if t['slots'][i] is not None:  # not a BYE slot
                t['slots'][i] = player_ids[p_idx]
                p_idx += 1

        self._exhibition_build_bracket()
        self.show_exhibition_bracket()

    # ── Build exhibition player dict ──

    def _build_exhibition_player(self, hof_entry):
        """Build a player dict for GameEngine from a HOF entry."""
        import uuid
        return {
            'id': f"hof_{hof_entry.get('name', 'Unknown')}_{uuid.uuid4().hex[:6]}",
            'name': hof_entry.get('name', 'Unknown'),
            'hand': hof_entry.get('hand', 'Right'),
            'skills': {k: v for k, v in hof_entry.get('peak_skills', {}).items()},
            'archetype': hof_entry.get('archetype', 'All-Rounder'),
            'archetype_key': (),
            'rank': hof_entry.get('highest_ranking', 999),
            'age': 'HOF',
            'mentality': 'neutral',
            'cross_tend': 40, 'straight_tend': 40, 'dropshot_tend': 5,
            'volley_tend': 5, 'lift_tend': 5, 'slice_tend': 5,
        }
        
if __name__ == "__main__":
    root = tk.Tk()
    root.title("TennisGM")
    root.minsize(1200, 700)
    app = TennisGMApp(root)
    root.mainloop()