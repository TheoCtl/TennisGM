import tkinter as tk
import math
import random


class TennisCourtViewer:
    SURFACE_COLORS = {
        'grass': '#1F4A0C',
        'hard': '#1E4785',
        'clay': '#A85A1C',
        'indoor': '#1A365F',
        'neutral': '#404040'
    }

    # Lighter inner-court color per surface (inside the lines)
    INNER_COURT_COLORS = {
        'grass': '#2D6B12',
        'hard': '#2A5DA8',
        'clay': '#C06A20',
        'indoor': '#244A7A',
        'neutral': '#555555'
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
    PLAYER_RADIUS = 14        # Player circle radius (kept for compat)

    # Sprite sizing
    SPRITE_SCALE = 1.5        # Global multiplier for player sprite size

    # Ball trail
    BALL_TRAIL_LENGTH = 6     # Number of trailing ghost-balls
    BALL_TRAIL_FADE = 4       # Radius shrink per trail step

    def __init__(self, master, width=1200, height=600, surface='grass'):
        self.master = master
        self.width = width
        self.height = height
        self.surface = surface

        bg_color = self.SURFACE_COLORS.get(surface.lower(), self.SURFACE_COLORS['neutral'])
        self.canvas = tk.Canvas(master, width=width, height=height, bg=bg_color,
                                highlightthickness=0)
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
        # Facing direction: 1 = facing right, -1 = facing left
        self.p1_facing = 1
        self.p2_facing = -1
        # Player pose: 'ready', 'serve', 'hit_forehand', 'hit_backhand', 'celebrate', 'dejected'
        self.p1_pose = 'ready'
        self.p2_pose = 'ready'

        # Stamina state (0.0 – 1.0)
        self.p1_stamina_pct = 1.0
        self.p2_stamina_pct = 1.0

        # Ball state
        self.ball_pos = [self.width // 2, self.height // 2]
        self.ball_visible = False
        self.ball_shot_type = None  # Current shot type for color coding
        self._ball_trail = []  # list of recent (x, y) positions for trail effect

        # Animation tracking
        self._anim_ids = []

        self.draw_court()
        self.draw_players()

    # ------------------------------------------------------------------
    # Easing
    # ------------------------------------------------------------------
    @staticmethod
    def _ease_in_out(t):
        """Smooth ease-in-out (cubic)."""
        if t < 0.5:
            return 4 * t * t * t
        return 1 - (-2 * t + 2) ** 3 / 2

    # ------------------------------------------------------------------
    # Court drawing
    # ------------------------------------------------------------------
    def draw_court(self):
        """Draw tennis court lines with inner fill for depth."""
        m = self.court_margin
        w = self.width
        h = self.height
        inner = self.INNER_COURT_COLORS.get(self.surface.lower(),
                                            self.INNER_COURT_COLORS['neutral'])

        # Inner court fill
        self.canvas.create_rectangle(m, m, w - m, h - m, fill=inner, outline='')

        # Doubles court outline
        self.canvas.create_rectangle(m, m, w - m, h - m, outline='white', width=2)

        # Singles sidelines
        aw = self.court_width * 0.075
        singles_top = m + aw
        singles_bottom = h - m - aw
        self.canvas.create_line(m, singles_top, w - m, singles_top, fill='white', width=2)
        self.canvas.create_line(m, singles_bottom, w - m, singles_bottom, fill='white', width=2)

        # Net — thicker, with posts
        cx = w / 2
        self.canvas.create_line(cx, m - 5, cx, h - m + 5, fill='#dddddd', width=3)
        # Net posts
        post_r = 4
        for py in (m - 5, h - m + 5):
            self.canvas.create_oval(cx - post_r, py - post_r, cx + post_r, py + post_r,
                                    fill='#cccccc', outline='#999999', width=1)

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
    # Player sprite drawing
    # ------------------------------------------------------------------
    STAMINA_BAR_W = 30
    STAMINA_BAR_H = 5
    STAMINA_BAR_OFFSET_Y = 8

    @staticmethod
    def _stamina_color(pct):
        if pct > 0.55:
            return '#2ecc71'
        if pct > 0.25:
            return '#f39c12'
        return '#e74c3c'

    def _draw_stamina_bar(self, cx, cy, pct, tag):
        w = int(self.STAMINA_BAR_W * self.SPRITE_SCALE)
        h = int(self.STAMINA_BAR_H * self.SPRITE_SCALE)
        top = cy - 32 * self.SPRITE_SCALE - self.STAMINA_BAR_OFFSET_Y
        left = cx - w // 2
        self.canvas.create_rectangle(left, top, left + w, top + h,
                                     fill='#2c3e50', outline='#1a252f', width=1, tags=tag)
        fill_w = max(0, int(w * max(0.0, min(1.0, pct))))
        if fill_w > 0:
            self.canvas.create_rectangle(left, top, left + fill_w, top + h,
                                         fill=self._stamina_color(pct), outline='', tags=tag)

    def _draw_player_sprite(self, cx, cy, facing, color, outline_color, tag, pose='ready'):
        """Draw a humanoid player sprite centred at (cx, cy).

        facing: 1 = facing right, -1 = facing left.
        pose: 'ready', 'serve', 'hit_forehand', 'hit_backhand', 'celebrate', 'dejected'
        """
        s = self.SPRITE_SCALE
        f = facing  # 1 or -1

        # -- Shadow (ellipse on ground) --
        shadow_rx = 12 * s
        shadow_ry = 4 * s
        self.canvas.create_oval(cx - shadow_rx, cy + 14 * s - shadow_ry,
                                cx + shadow_rx, cy + 14 * s + shadow_ry,
                                fill='#333333', outline='', tags=tag)

        # Body reference points
        body_top = cy - 10 * s
        body_bot = cy + 2 * s
        body_w = 7 * s
        shoulder_y = body_top + 3 * s
        leg_spread = 5 * s

        # ---- Pose-specific limb geometry ----
        if pose == 'serve':
            # Toss arm high, racket arm cocked back
            back_arm_end = (cx - f * 1 * s, shoulder_y - 20 * s)
            rack_arm_end = (cx + f * 2 * s, shoulder_y + 8 * s)
            racket_end = (rack_arm_end[0] - f * 2 * s, rack_arm_end[1] - 14 * s)
            leg_back = ((cx - f * leg_spread * 0.8, cy + 2 * s),
                        (cx - f * leg_spread * 0.4, cy + 14 * s))
            leg_front = ((cx + f * leg_spread * 0.5, cy + 2 * s),
                         (cx + f * leg_spread * 1.8, cy + 14 * s))
        elif pose == 'hit_forehand':
            # Racket arm extended forward (follow-through)
            back_arm_end = (cx - f * 10 * s, shoulder_y - 4 * s)
            rack_arm_end = (cx + f * 16 * s, shoulder_y + 1 * s)
            racket_end = (rack_arm_end[0] + f * 7 * s, rack_arm_end[1] - 2 * s)
            leg_back = ((cx - f * leg_spread, cy + 2 * s),
                        (cx - f * leg_spread * 1.5, cy + 14 * s))
            leg_front = ((cx + f * leg_spread * 0.5, cy + 2 * s),
                         (cx + f * leg_spread * 2, cy + 14 * s))
        elif pose == 'hit_backhand':
            # Racket arm crosses body to non-facing side
            back_arm_end = (cx - f * 4 * s, shoulder_y + 2 * s)
            rack_arm_end = (cx - f * 10 * s, shoulder_y - 3 * s)
            racket_end = (rack_arm_end[0] - f * 6 * s, rack_arm_end[1] - 4 * s)
            leg_back = ((cx + f * leg_spread * 0.3, cy + 2 * s),
                        (cx + f * leg_spread * 0.5, cy + 14 * s))
            leg_front = ((cx - f * leg_spread * 0.5, cy + 2 * s),
                         (cx - f * leg_spread * 1.8, cy + 14 * s))
        elif pose == 'celebrate':
            # Both arms raised high
            back_arm_end = (cx - f * 7 * s, shoulder_y - 16 * s)
            rack_arm_end = (cx + f * 7 * s, shoulder_y - 16 * s)
            racket_end = (rack_arm_end[0] + f * 3 * s, rack_arm_end[1] - 8 * s)
            leg_back = ((cx - f * leg_spread, cy + 2 * s),
                        (cx - f * leg_spread * 1.3, cy + 14 * s))
            leg_front = ((cx + f * leg_spread * 0.3, cy + 2 * s),
                         (cx + f * leg_spread * 1.3, cy + 14 * s))
        elif pose == 'dejected':
            # Arms drooping down, slumped posture
            back_arm_end = (cx - f * 6 * s, shoulder_y + 12 * s)
            rack_arm_end = (cx + f * 6 * s, shoulder_y + 12 * s)
            racket_end = (rack_arm_end[0] + f * 2 * s, rack_arm_end[1] + 6 * s)
            leg_back = ((cx - f * leg_spread * 0.4, cy + 2 * s),
                        (cx - f * leg_spread * 0.5, cy + 14 * s))
            leg_front = ((cx + f * leg_spread * 0.4, cy + 2 * s),
                         (cx + f * leg_spread * 0.5, cy + 14 * s))
        else:  # 'ready'
            back_arm_end = (cx - f * 10 * s, shoulder_y + 5 * s)
            rack_arm_end = (cx + f * 12 * s, shoulder_y - 2 * s)
            racket_end = (rack_arm_end[0] + f * 8 * s, rack_arm_end[1] - 3 * s)
            leg_back = ((cx - f * leg_spread, cy + 2 * s),
                        (cx - f * leg_spread * 1.2, cy + 14 * s))
            leg_front = ((cx + f * leg_spread * 0.3, cy + 2 * s),
                         (cx + f * leg_spread * 1.5, cy + 14 * s))

        # -- Legs --
        lw = max(2, int(3 * s))
        self.canvas.create_line(*leg_back[0], *leg_back[1],
                                fill=outline_color, width=lw, tags=tag)
        self.canvas.create_line(*leg_front[0], *leg_front[1],
                                fill=outline_color, width=lw, tags=tag)

        # -- Torso --
        self.canvas.create_rectangle(cx - body_w / 2, body_top,
                                     cx + body_w / 2, body_bot,
                                     fill=color, outline=outline_color, width=1, tags=tag)

        # -- Arms --
        aw = max(2, int(2.5 * s))
        self.canvas.create_line(cx - f * 3 * s, shoulder_y, *back_arm_end,
                                fill=outline_color, width=aw, tags=tag)
        self.canvas.create_line(cx + f * 3 * s, shoulder_y, *rack_arm_end,
                                fill=outline_color, width=aw, tags=tag)

        # -- Racket --
        self.canvas.create_line(*rack_arm_end, *racket_end,
                                fill='#8B4513', width=max(1, int(2 * s)), tags=tag)
        rr = 5 * s
        self.canvas.create_oval(racket_end[0] - rr * 0.7, racket_end[1] - rr,
                                racket_end[0] + rr * 0.7, racket_end[1] + rr,
                                fill='', outline=outline_color,
                                width=max(1, int(1.5 * s)), tags=tag)

        # -- Head --
        head_r = 6 * s
        head_y = body_top - head_r
        if pose == 'dejected':
            head_y += 2 * s
        self.canvas.create_oval(cx - head_r, head_y - head_r,
                                cx + head_r, head_y + head_r,
                                fill='#F5D6B8', outline=outline_color, width=1, tags=tag)
        # Cap
        cap_r = head_r * 0.75
        cap_offset_x = f * 2 * s
        self.canvas.create_arc(cx + cap_offset_x - cap_r, head_y - cap_r,
                               cx + cap_offset_x + cap_r, head_y + cap_r * 0.3,
                               start=0, extent=180, fill=color, outline='', tags=tag)

    def _draw_name_label(self, cx, cy, name, tag):
        """Draw a small name label below the player."""
        label_y = cy + 20 * self.SPRITE_SCALE
        font_size = max(8, int(8 * self.SPRITE_SCALE))
        self.canvas.create_text(cx, label_y, text=name, fill='white',
                                font=('Arial', font_size, 'bold'), tags=tag)

    def draw_players(self):
        """Draw both players as humanoid sprites with stamina bars and names."""
        self.canvas.delete('p1_sprite', 'p1_label', 'p2_sprite', 'p2_label')

        # Player 1 – blue
        x1, y1 = self.p1_pos
        self._draw_player_sprite(x1, y1, self.p1_facing,
                                 '#3498db', '#2471a3', 'p1_sprite', self.p1_pose)
        self._draw_stamina_bar(x1, y1, self.p1_stamina_pct, 'p1_label')
        self._draw_name_label(x1, y1, self.p1_name, 'p1_label')

        # Player 2 – red
        x2, y2 = self.p2_pos
        self._draw_player_sprite(x2, y2, self.p2_facing,
                                 '#e74c3c', '#c0392b', 'p2_sprite', self.p2_pose)
        self._draw_stamina_bar(x2, y2, self.p2_stamina_pct, 'p2_label')
        self._draw_name_label(x2, y2, self.p2_name, 'p2_label')

    def set_player_pose(self, player_num, pose):
        """Set the pose for a player and redraw."""
        if player_num == 1:
            self.p1_pose = pose
        else:
            self.p2_pose = pose
        self.draw_players()

    # ------------------------------------------------------------------
    # Ball drawing (with shadow and trail)
    # ------------------------------------------------------------------
    def draw_ball(self):
        """Draw the tennis ball with shadow and fading trail."""
        self.canvas.delete('ball', 'ball_trail', 'ball_shadow')
        if not self.ball_visible:
            return
        x, y = self.ball_pos

        # Determine ball colors based on shot type
        if self.ball_shot_type == 'lift':
            ball_fill = '#00aaff'   # Blue
            ball_outline = '#0088cc'
            ball_highlight = '#88ddff'
            trail_r, trail_g, trail_b = 0, 170, 255
        elif self.ball_shot_type == 'slice':
            ball_fill = '#ff8800'   # Orange
            ball_outline = '#cc6600'
            ball_highlight = '#ffbb66'
            trail_r, trail_g, trail_b = 255, 136, 0
        else:
            ball_fill = '#ccff00'   # Default green-yellow
            ball_outline = '#aadd00'
            ball_highlight = '#eeff88'
            trail_r, trail_g, trail_b = 204, 255, 0

        # Trail — fading ghost balls
        trail_len = min(len(self._ball_trail), self.BALL_TRAIL_LENGTH)
        for i, (tx, ty) in enumerate(self._ball_trail[-trail_len:]):
            alpha_i = i / max(1, trail_len)  # 0..1
            tr = max(1, int(5 - self.BALL_TRAIL_FADE * (1 - alpha_i)))
            fade = 1 - alpha_i
            cr = min(255, int(trail_r + (255 - trail_r) * fade))
            cg = min(255, int(trail_g + (255 - trail_g) * fade))
            cb = min(255, int(trail_b + (255 - trail_b) * fade))
            trail_color = f'#{cr:02x}{cg:02x}{cb:02x}'
            self.canvas.create_oval(tx - tr, ty - tr, tx + tr, ty + tr,
                                    fill=trail_color, outline='', tags='ball_trail')

        # Shadow
        sr = 5
        sy_off = 8
        self.canvas.create_oval(x - sr, y + sy_off - 2, x + sr, y + sy_off + 2,
                                fill='#1a1a1a', outline='', tags='ball_shadow')

        # Ball
        r = 6
        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                fill=ball_fill, outline=ball_outline, width=1, tags='ball')
        # Highlight dot
        self.canvas.create_oval(x - 2, y - 3, x + 1, y - 1,
                                fill=ball_highlight, outline='', tags='ball')

    def _update_trail(self):
        """Append current ball position to trail, keeping it bounded."""
        self._ball_trail.append(tuple(self.ball_pos))
        max_trail = self.BALL_TRAIL_LENGTH + 4
        if len(self._ball_trail) > max_trail:
            self._ball_trail = self._ball_trail[-max_trail:]

    def show_ball_at(self, x, y):
        self.ball_pos = [x, y]
        self.ball_visible = True
        self._ball_trail.clear()
        self.draw_ball()

    def hide_ball(self):
        self.ball_visible = False
        self.ball_shot_type = None
        self._ball_trail.clear()
        self.draw_ball()

    # ------------------------------------------------------------------
    # Rebound / winner marks
    # ------------------------------------------------------------------
    def draw_rebound_mark(self, x, y):
        r = 5
        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                fill='#888888', outline='#aaaaaa', width=1, tags='rebound')

    def draw_winner_mark(self, x, y):
        """Draw a red starburst at the winning shot location."""
        # Outer glow
        for gr in (14, 10):
            alpha = '#e74c3c' if gr == 10 else '#c0392b'
            self.canvas.create_oval(x - gr, y - gr, x + gr, y + gr,
                                    fill='', outline=alpha,
                                    width=2, tags='rebound')
        # Inner mark
        r = 7
        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                fill='#e74c3c', outline='#c0392b', width=2, tags='rebound')
        # Star lines
        for angle_deg in range(0, 360, 45):
            rad = math.radians(angle_deg)
            x1 = x + math.cos(rad) * (r + 2)
            y1 = y + math.sin(rad) * (r + 2)
            x2 = x + math.cos(rad) * (r + 7)
            y2 = y + math.sin(rad) * (r + 7)
            self.canvas.create_line(x1, y1, x2, y2,
                                    fill='#e74c3c', width=2, tags='rebound')

    def clear_marks(self):
        self.canvas.delete('rebound')

    # ------------------------------------------------------------------
    # Impact flash effect
    # ------------------------------------------------------------------
    def _flash_impact(self, x, y, color='#ffffff', max_r=20, tag='impact'):
        """Animate a fast expanding ring at (x, y) for bounce impacts."""
        self.canvas.delete(tag)
        steps = 5
        interval = 18

        def _ring(i):
            self.canvas.delete(tag)
            if i >= steps:
                return
            t = i / steps
            r = int(max_r * t)
            w = max(1, int(2 * (1 - t)))
            self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                    fill='', outline=color, width=w, tags=tag)
            self._schedule(interval, lambda: _ring(i + 1))

        _ring(0)

    # ------------------------------------------------------------------
    # Animation helpers
    # ------------------------------------------------------------------
    def _schedule(self, ms, fn):
        aid = self.master.after(ms, fn)
        self._anim_ids.append(aid)
        return aid

    def cancel_animations(self):
        for aid in self._anim_ids:
            try:
                self.master.after_cancel(aid)
            except Exception:
                pass
        self._anim_ids.clear()

    # ------------------------------------------------------------------
    # Ball animation – straight line with trail & easing
    # ------------------------------------------------------------------
    def animate_ball_to(self, target_x, target_y, duration_ms=1000, callback=None):
        """Animate ball from current position to target with trail."""
        sx, sy = self.ball_pos
        steps = max(1, duration_ms // 16)
        self.ball_visible = True
        interval = max(1, duration_ms // steps)

        def _step(i):
            if i >= steps:
                self.ball_pos = [target_x, target_y]
                self._update_trail()
                self.draw_ball()
                self._flash_impact(target_x, target_y, '#ffffff', 14)
                if callback:
                    callback()
                return
            t = self._ease_in_out(i / steps)
            bx = sx + (target_x - sx) * t
            by = sy + (target_y - sy) * t
            self.ball_pos = [bx, by]
            if i % 2 == 0:
                self._update_trail()
            self.draw_ball()
            self._schedule(interval, lambda: _step(i + 1))

        _step(0)

    def animate_ball_through(self, mid_x, mid_y, end_x, end_y,
                             duration_ms=1000, mid_callback=None, callback=None,
                             winner=False):
        """Animate ball continuously from current pos through (mid) to (end).

        Uses a single seamless animation — no pause at the midpoint.
        A rebound mark is drawn as the ball passes through the midpoint."""
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

        frac_mid = d1 / total  # fraction of total distance at which mid is reached
        steps = max(1, duration_ms // 16)
        interval = max(1, duration_ms // steps)
        self.ball_visible = True
        mid_drawn = [False]

        # Arc heights: first leg (hitter→bounce) has full arc, second leg
        # (bounce→defender) has a smaller arc since the ball is lower after bounce

        def _step(i):
            if i >= steps:
                self.ball_pos = [end_x, end_y]
                self._update_trail()
                self.draw_ball()
                # Draw rebound mark if it wasn't drawn during animation
                # (happens when frac_mid is so close to 1.0 that no
                # intermediate step reached it before completion)
                if not mid_drawn[0]:
                    mid_drawn[0] = True
                    if winner:
                        self.draw_winner_mark(mid_x, mid_y)
                    else:
                        self.draw_rebound_mark(mid_x, mid_y)
                    if mid_callback:
                        mid_callback()
                if winner:
                    self._flash_impact(end_x, end_y, '#e74c3c', 18)
                else:
                    self._flash_impact(end_x, end_y, '#ffffff', 14)
                if callback:
                    callback()
                return

            t = i / steps  # linear progress 0..1

            # Determine position: before or after midpoint
            if t <= frac_mid:
                # First leg: start → mid
                leg_t = t / frac_mid if frac_mid > 0 else 1.0
                bx = sx + (mid_x - sx) * leg_t
                by = sy + (mid_y - sy) * leg_t
            else:
                # Second leg: mid → end
                leg_t = (t - frac_mid) / (1 - frac_mid) if frac_mid < 1 else 1.0
                bx = mid_x + (end_x - mid_x) * leg_t
                by = mid_y + (end_y - mid_y) * leg_t

            self.ball_pos = [bx, by]

            # Draw rebound mark exactly once when we cross the midpoint
            if t >= frac_mid and not mid_drawn[0]:
                mid_drawn[0] = True
                if winner:
                    self.draw_winner_mark(mid_x, mid_y)
                else:
                    self.draw_rebound_mark(mid_x, mid_y)
                if mid_callback:
                    mid_callback()

            if i % 2 == 0:
                self._update_trail()
            self.draw_ball()
            self._schedule(interval, lambda: _step(i + 1))

        _step(0)

    # ------------------------------------------------------------------
    # Player animation – eased movement
    # ------------------------------------------------------------------
    def animate_player_to(self, player_num, target_x, target_y,
                          duration_ms=900, callback=None):
        pos = self.p1_pos if player_num == 1 else self.p2_pos
        sx, sy = pos
        steps = max(1, duration_ms // 16)
        interval = max(1, duration_ms // steps)

        # Update facing direction based on movement
        dx_total = target_x - sx
        if player_num == 1:
            self.p1_facing = 1 if dx_total >= 0 else -1
        else:
            self.p2_facing = -1 if dx_total <= 0 else 1

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
            t = self._ease_in_out(i / steps)
            new = [sx + (target_x - sx) * t, sy + (target_y - sy) * t]
            if player_num == 1:
                self.p1_pos = new
            else:
                self.p2_pos = new
            self.draw_players()
            self._schedule(interval, lambda: _step(i + 1))

        _step(0)

    # ------------------------------------------------------------------
    # Convenience helpers (unchanged API)
    # ------------------------------------------------------------------
    def set_player_names(self, name1, name2):
        self.p1_name = name1
        self.p2_name = name2
        self.draw_players()

    def update_stamina(self, player_num, pct):
        if player_num == 1:
            self.p1_stamina_pct = max(0.0, min(1.0, pct))
        else:
            self.p2_stamina_pct = max(0.0, min(1.0, pct))
        self.draw_players()

    def reset_positions(self):
        self.p1_pos = [self.P1_BASELINE_X, self.CENTER_Y]
        self.p2_pos = [self.P2_BASELINE_X, self.CENTER_Y]
        self.p1_facing = 1
        self.p2_facing = -1
        self.p1_pose = 'ready'
        self.p2_pose = 'ready'
        self.p1_stamina_pct = 1.0
        self.p2_stamina_pct = 1.0
        self.ball_visible = False
        self._ball_trail.clear()
        self.clear_marks()
        self.draw_players()
        self.draw_ball()

    def update_ball_position(self, x, y):
        self.ball_pos = [x, y]
        self.ball_visible = True
        self._update_trail()
        self.draw_ball()

    def clear_ball(self):
        self.ball_visible = False
        self._ball_trail.clear()
        self.canvas.delete('ball', 'ball_trail', 'ball_shadow')