import tkinter as tk


class TennisCourtViewer:
    SURFACE_COLORS = {
        'grass': '#1F4A0C',
        'hard': '#1E4785',
        'clay': '#A85A1C',
        'indoor': '#1A365F',
        'neutral': '#404040'
    }

    # Court coordinate constants (matches game_engine 1200x600 space)
    P1_BASELINE_X = 30       # Player 1 baseline (left side)
    P2_BASELINE_X = 1170     # Player 2 baseline (right side)
    P1_VOLLEY_X = 450        # Player 1 volley position (near net)
    P2_VOLLEY_X = 750        # Player 2 volley position (near net)
    NET_X = 600               # Net x position
    CENTER_Y = 300            # Vertical center
    MIN_Y = 80                # Top court boundary for players
    MAX_Y = 520               # Bottom court boundary for players
    PLAYER_RADIUS = 14        # Player circle radius

    def __init__(self, master, width=1200, height=600, surface='grass'):
        self.master = master
        self.width = width
        self.height = height
        self.surface = surface

        bg_color = self.SURFACE_COLORS.get(surface.lower(), self.SURFACE_COLORS['neutral'])
        self.canvas = tk.Canvas(master, width=width, height=height, bg=bg_color)
        self.canvas.pack(expand=True)

        # Court dimensions
        self.court_margin = 20
        court_ratio = 78 / 36
        self.court_width = width - 2 * self.court_margin
        self.court_height = self.court_width / court_ratio
        if self.court_height > height - 2 * self.court_margin:
            self.court_height = height - 2 * self.court_margin
            self.court_width = self.court_height * court_ratio
        self.alley_width = self.court_height * (4.5 / 36)

        # Player state
        self.p1_pos = [self.P1_BASELINE_X, self.CENTER_Y]
        self.p2_pos = [self.P2_BASELINE_X, self.CENTER_Y]
        self.p1_name = "Player 1"
        self.p2_name = "Player 2"

        # Stamina state (0.0 – 1.0)
        self.p1_stamina_pct = 1.0
        self.p2_stamina_pct = 1.0

        # Ball state
        self.ball_pos = [self.width // 2, self.height // 2]
        self.ball_visible = False

        # Animation tracking
        self._anim_ids = []

        self.draw_court()
        self.draw_players()

    # ------------------------------------------------------------------
    # Court drawing
    # ------------------------------------------------------------------
    def draw_court(self):
        """Draw tennis court lines."""
        m = self.court_margin
        w = self.width
        h = self.height

        # Doubles court outline
        self.canvas.create_rectangle(m, m, w - m, h - m, outline='white', width=2)

        # Singles sidelines
        aw = self.court_width * 0.075
        singles_top = m + aw
        singles_bottom = h - m - aw
        self.canvas.create_line(m, singles_top, w - m, singles_top, fill='white', width=2)
        self.canvas.create_line(m, singles_bottom, w - m, singles_bottom, fill='white', width=2)

        # Net
        cx = w / 2
        self.canvas.create_line(cx, 0, cx, h, fill='white', width=2)

        # Service box lines
        qc = self.court_width / 4
        sl_left = m + qc
        sl_right = w - m - qc
        mid_y = singles_top + (singles_bottom - singles_top) / 2

        self.canvas.create_line(sl_left, singles_top, sl_left, singles_bottom, fill='white', width=2)
        self.canvas.create_line(sl_right, singles_top, sl_right, singles_bottom, fill='white', width=2)
        self.canvas.create_line(sl_left, mid_y, sl_right, mid_y, fill='white', width=2)
        self.canvas.create_line(cx, sl_left, cx, sl_right, fill='white', width=2)

        # Baseline tick marks
        mw = 10
        for x in (m, w - m):
            for y in (singles_top, singles_bottom):
                self.canvas.create_line(x, y - mw, x, y + mw, fill='white', width=2)

    # ------------------------------------------------------------------
    # Player drawing
    # ------------------------------------------------------------------
    # Stamina bar visual constants
    STAMINA_BAR_W = 30       # total bar width in pixels
    STAMINA_BAR_H = 5        # bar height
    STAMINA_BAR_OFFSET_Y = 8 # gap between bar bottom and circle top

    @staticmethod
    def _stamina_color(pct):
        """Return a fill colour for the stamina bar based on percentage."""
        if pct > 0.55:
            return '#2ecc71'   # green
        if pct > 0.25:
            return '#f39c12'   # orange
        return '#e74c3c'       # red

    def _draw_stamina_bar(self, cx, cy, pct, tag):
        """Draw a small horizontal stamina bar centred at (cx, cy-offset)."""
        w = self.STAMINA_BAR_W
        h = self.STAMINA_BAR_H
        r = self.PLAYER_RADIUS
        top = cy - r - self.STAMINA_BAR_OFFSET_Y - h
        left = cx - w // 2
        # background (dark)
        self.canvas.create_rectangle(left, top, left + w, top + h,
                                     fill='#2c3e50', outline='#1a252f', width=1, tags=tag)
        # filled portion
        fill_w = max(0, int(w * max(0.0, min(1.0, pct))))
        if fill_w > 0:
            self.canvas.create_rectangle(left, top, left + fill_w, top + h,
                                         fill=self._stamina_color(pct), outline='', tags=tag)

    def draw_players(self):
        """Draw both players as coloured circles with stamina bars."""
        self.canvas.delete('p1_sprite', 'p1_label', 'p2_sprite', 'p2_label')
        r = self.PLAYER_RADIUS

        # Player 1 – blue
        x1, y1 = self.p1_pos
        self.canvas.create_oval(x1 - r, y1 - r, x1 + r, y1 + r,
                                fill='#3498db', outline='white', width=2, tags='p1_sprite')
        self._draw_stamina_bar(x1, y1, self.p1_stamina_pct, 'p1_label')

        # Player 2 – red
        x2, y2 = self.p2_pos
        self.canvas.create_oval(x2 - r, y2 - r, x2 + r, y2 + r,
                                fill='#e74c3c', outline='white', width=2, tags='p2_sprite')
        self._draw_stamina_bar(x2, y2, self.p2_stamina_pct, 'p2_label')

    # ------------------------------------------------------------------
    # Ball drawing
    # ------------------------------------------------------------------
    def draw_ball(self):
        """Draw the tennis ball at its current position (or hide it)."""
        self.canvas.delete('ball')
        if self.ball_visible:
            r = 6
            x, y = self.ball_pos
            self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                    fill='yellow', outline='white', width=1, tags='ball')

    def show_ball_at(self, x, y):
        """Instantly place and show the ball at (x, y)."""
        self.ball_pos = [x, y]
        self.ball_visible = True
        self.draw_ball()

    def hide_ball(self):
        self.ball_visible = False
        self.draw_ball()

    def draw_rebound_mark(self, x, y):
        """Draw a small grey circle marking the first rebound location."""
        r = 5
        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                fill='#888888', outline='#aaaaaa', width=1, tags='rebound')

    def draw_winner_mark(self, x, y):
        """Draw a red circle marking the winning shot rebound location."""
        r = 7
        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                fill='#e74c3c', outline='#c0392b', width=2, tags='rebound')

    def clear_marks(self):
        """Remove all rebound marks from the court."""
        self.canvas.delete('rebound')

    # ------------------------------------------------------------------
    # Animation helpers
    # ------------------------------------------------------------------
    def _schedule(self, ms, fn):
        """Schedule *fn* after *ms* milliseconds, tracking the id."""
        aid = self.master.after(ms, fn)
        self._anim_ids.append(aid)
        return aid

    def cancel_animations(self):
        """Cancel every pending animation callback."""
        for aid in self._anim_ids:
            try:
                self.master.after_cancel(aid)
            except Exception:
                pass
        self._anim_ids.clear()

    # ------------------------------------------------------------------
    # Ball animation – straight line
    # ------------------------------------------------------------------
    def animate_ball_to(self, target_x, target_y, duration_ms=1000, callback=None):
        """Animate ball in a straight line from current pos to target."""
        sx, sy = self.ball_pos
        steps = max(1, duration_ms // 16)          # ~60 fps
        dx = (target_x - sx) / steps
        dy = (target_y - sy) / steps
        self.ball_visible = True
        interval = max(1, duration_ms // steps)

        def _step(i):
            if i >= steps:
                self.ball_pos = [target_x, target_y]
                self.draw_ball()
                if callback:
                    callback()
                return
            self.ball_pos = [sx + dx * i, sy + dy * i]
            self.draw_ball()
            self._schedule(interval, lambda: _step(i + 1))

        _step(0)

    def animate_ball_through(self, mid_x, mid_y, end_x, end_y,
                             duration_ms=1000, mid_callback=None, callback=None,
                             winner=False):
        """Animate ball from current pos through (mid) to (end).

        A rebound mark is placed when the ball reaches *mid*.  If *winner*
        is True the mark is red; otherwise grey.  *mid_callback*
        fires at that moment.  *callback* fires when the ball reaches *end*.
        The total travel time is *duration_ms*; the mid-point is reached
        proportionally based on distance."""
        import math
        sx, sy = self.ball_pos
        d1 = math.hypot(mid_x - sx, mid_y - sy)
        d2 = math.hypot(end_x - mid_x, end_y - mid_y)
        total = d1 + d2
        if total < 1:
            self.ball_pos = [end_x, end_y]
            self.draw_ball()
            if callback:
                callback()
            return
        frac1 = d1 / total
        ms1 = max(1, int(duration_ms * frac1))
        ms2 = max(1, duration_ms - ms1)

        def _phase2():
            if winner:
                self.draw_winner_mark(mid_x, mid_y)
            else:
                self.draw_rebound_mark(mid_x, mid_y)
            if mid_callback:
                mid_callback()
            self.animate_ball_to(end_x, end_y, ms2, callback)

        self.animate_ball_to(mid_x, mid_y, ms1, _phase2)

    # ------------------------------------------------------------------
    # Player animation – move to target position
    # ------------------------------------------------------------------
    def animate_player_to(self, player_num, target_x, target_y,
                          duration_ms=900, callback=None):
        """Smoothly move a player to (target_x, target_y)."""
        pos = self.p1_pos if player_num == 1 else self.p2_pos
        sx, sy = pos
        steps = max(1, duration_ms // 16)
        dx = (target_x - sx) / steps
        dy = (target_y - sy) / steps
        interval = max(1, duration_ms // steps)

        def _step(i):
            if i >= steps:
                new = [target_x, target_y]
                if player_num == 1:
                    self.p1_pos = new
                else:
                    self.p2_pos = new
                self.draw_players()
                if callback:
                    callback()
                return
            new = [sx + dx * i, sy + dy * i]
            if player_num == 1:
                self.p1_pos = new
            else:
                self.p2_pos = new
            self.draw_players()
            self._schedule(interval, lambda: _step(i + 1))

        _step(0)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def set_player_names(self, name1, name2):
        self.p1_name = name1
        self.p2_name = name2
        self.draw_players()

    def update_stamina(self, player_num, pct):
        """Update stamina fraction (0.0-1.0) for player 1 or 2 and redraw."""
        if player_num == 1:
            self.p1_stamina_pct = max(0.0, min(1.0, pct))
        else:
            self.p2_stamina_pct = max(0.0, min(1.0, pct))
        self.draw_players()

    def reset_positions(self):
        """Return both players to baseline centre, reset stamina bars and hide ball."""
        self.p1_pos = [self.P1_BASELINE_X, self.CENTER_Y]
        self.p2_pos = [self.P2_BASELINE_X, self.CENTER_Y]
        self.p1_stamina_pct = 1.0
        self.p2_stamina_pct = 1.0
        self.ball_visible = False
        self.clear_marks()
        self.draw_players()
        self.draw_ball()

    def update_ball_position(self, x, y):
        self.ball_pos = [x, y]
        self.ball_visible = True
        self.draw_ball()

    def clear_ball(self):
        self.ball_visible = False
        self.canvas.delete('ball')