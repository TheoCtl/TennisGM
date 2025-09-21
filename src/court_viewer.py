import tkinter as tk

class TennisCourtViewer:
    SURFACE_COLORS = {
        'grass': '#1F4A0C',    # Darker green
        'hard': '#1E4785',     # Dark blue
        'clay': '#A85A1C',     # Darker orange
        'indoor': '#1A365F',   # Darker indoor blue
        'neutral': '#404040'   # Darker grey
    }

    def __init__(self, master, width=800, height=400, surface='grass'):
        self.master = master
        self.width = width
        self.height = height
        self.surface = surface
        
        # Create canvas for drawing
        bg_color = self.SURFACE_COLORS.get(surface.lower(), self.SURFACE_COLORS['neutral'])
        self.canvas = tk.Canvas(master, width=width, height=height, bg=bg_color)
        self.canvas.pack(expand=True)
        
        # Court dimensions with accurate tennis court proportions
        self.court_margin = 20  # Reduced margin to use more canvas space
        
        # Standard tennis court is 78ft x 36ft (27ft singles width)
        # We want to maintain this 78:36 ratio (approximately 2.17:1)
        court_ratio = 78/36  # Approximately 2.17
        
        # Use full width and calculate height to maintain ratio
        self.court_width = width - 2 * self.court_margin
        self.court_height = self.court_width / court_ratio
        
        # If height exceeds canvas, scale both down
        if self.court_height > height - 2 * self.court_margin:
            self.court_height = height - 2 * self.court_margin
            self.court_width = self.court_height * court_ratio
            
        # Standard tennis court proportions
        self.baseline_margin = 30  # Smaller space behind baseline
        self.alley_width = self.court_height * (4.5/36)  # Doubles alley is 4.5ft of 36ft total
        self.service_box_depth = self.court_width * (21/78)  # Service box is 21ft of 78ft length
        
        # Player positions (initialized at baseline)
        self.player1_pos = [10, height / 2]
        self.player2_pos = [1190, height / 2]
        
        # Ball position
        self.ball_pos = [width / 2, height / 2]
        
        # Initialize scoreboard data
        self.player1_name = ""
        self.player2_name = ""
        self.score = {"sets": [], "current_game": "0-0"}
        
        self.draw_court()
        self.draw_ball()
    
    def draw_court(self):
        """Draw the tennis court lines with accurate proportions"""
        # Main court outline (doubles court)
        doubles_court = self.canvas.create_rectangle(
            self.court_margin, self.court_margin,
            self.width - self.court_margin, self.height - self.court_margin,
            outline='white', width=2
        )
        
        # Make alleys narrower - standard tennis court proportions
        # Singles court is 27ft wide, doubles adds 4.5ft on each side
        # So alleys should be about 1/6 of the singles court width
        self.alley_width = self.court_width * 0.075  # Reduced from 0.111
        
        # Singles court lines (top and bottom of singles court)
        singles_top = self.court_margin + self.alley_width
        singles_bottom = self.height - self.court_margin - self.alley_width
        self.canvas.create_line(
            self.court_margin, singles_top,
            self.width - self.court_margin, singles_top,
            fill='white', width=2
        )
        self.canvas.create_line(
            self.court_margin, singles_bottom,
            self.width - self.court_margin, singles_bottom,
            fill='white', width=2
        )
        
        # Center line (net) - now extends full height
        center_x = self.width / 2
        self.canvas.create_line(
            center_x, 0,  # Extend to top
            center_x, self.height,  # Extend to bottom
            fill='white', width=2
        )
        
        # Service boxes - front line (same distance from net on both sides)
        service_distance = self.court_height * 0.25  # Distance from net to service line
        service_line_left = center_x - service_distance
        service_line_right = center_x + service_distance
        
        # Service box lines
        
        # Service box lines
        # Calculate quarter points of court width for service lines
        quarter_court = self.court_width / 4
        service_line_left = self.court_margin + quarter_court
        service_line_right = self.width - self.court_margin - quarter_court
        court_midpoint = singles_top + ((singles_bottom - singles_top) / 2)

        # Vertical service lines at 1/4 and 3/4 of court width
        self.canvas.create_line(
            service_line_left, singles_top,
            service_line_left, singles_bottom,
            fill='white', width=2
        )
        self.canvas.create_line(
            service_line_right, singles_top,
            service_line_right, singles_bottom,
            fill='white', width=2
        )
        
        # Horizontal service line at mid-court
        self.canvas.create_line(
            service_line_left, court_midpoint,
            service_line_right, court_midpoint,
            fill='white', width=2
        )
        
        # Center service line connecting both service boxes
        self.canvas.create_line(
            center_x, service_line_left,
            center_x, service_line_right,
            fill='white', width=2
        )
        
        # Baseline markers (for serve positioning)
        marker_width = 10
        # Top baseline markers
        self.canvas.create_line(
            self.court_margin, singles_top - marker_width,
            self.court_margin, singles_top + marker_width,
            fill='white', width=2
        )
        self.canvas.create_line(
            self.width - self.court_margin, singles_top - marker_width,
            self.width - self.court_margin, singles_top + marker_width,
            fill='white', width=2
        )
        # Bottom baseline markers
        self.canvas.create_line(
            self.court_margin, singles_bottom - marker_width,
            self.court_margin, singles_bottom + marker_width,
            fill='white', width=2
        )
        self.canvas.create_line(
            self.width - self.court_margin, singles_bottom - marker_width,
            self.width - self.court_margin, singles_bottom + marker_width,
            fill='white', width=2
        )
        
    def draw_ball(self):
        """Draw the tennis ball"""
        ball_size = 5
        self.canvas.delete('ball')
        self.canvas.create_oval(
            self.ball_pos[0] - ball_size, self.ball_pos[1] - ball_size,
            self.ball_pos[0] + ball_size, self.ball_pos[1] + ball_size,
            fill='yellow', tags='ball'
        )
        
    def animate_ball(self, start, end, max_height=100, spin=0, duration=500):
        """Animate the ball along a curved trajectory"""
        start_x, start_y = start
        end_x, end_y = end
        steps = 20
        shadow_size = 3
        
        def bezier(t, p0, p1, p2, p3):
            return (1-t)**3 * p0 + 3*(1-t)**2 * t * p1 + 3*(1-t) * t**2 * p2 + t**3 * p3
            
        # Create control points for curved trajectory
        mid_x = (start_x + end_x) / 2
        cp1_x = start_x + (mid_x - start_x) / 2
        cp2_x = end_x - (end_x - mid_x) / 2
        
        # Add curve based on spin
        curve_offset = spin * 50  # Adjust spin influence
        cp1_y = start_y - max_height + curve_offset
        cp2_y = end_y - max_height - curve_offset
        
        def move_ball(step):
            if step >= steps:
                self.ball_pos = [end_x, end_y]
                self.draw_ball()
                return
                
            t = step / steps
            # Calculate position along Bezier curve
            x = bezier(t, start_x, cp1_x, cp2_x, end_x)
            y = bezier(t, start_y, cp1_y, cp2_y, end_y)
            
            # Update ball position
            self.ball_pos = [x, y]
            
            # Draw shadow (gets larger as ball gets higher)
            height_factor = 1 - abs(2 * t - 1)  # 0 at start/end, 1 at apex
            shadow_y = end_y + 5  # Slight offset for visual effect
            self.canvas.delete('shadow')
            self.canvas.create_oval(
                x - shadow_size, shadow_y - shadow_size,
                x + shadow_size, shadow_y + shadow_size,
                fill='gray', tags='shadow'
            )
            
            self.draw_ball()
            
            # Schedule next frame
            ms_per_step = duration / steps
            self.master.after(int(ms_per_step), lambda: move_ball(step + 1))
            
        move_ball(0)
        
    def reset_positions(self):
        """Reset ball and player positions to their starting locations"""
        self.player1_pos = [self.court_margin + self.baseline_margin, self.height / 2]
        self.player2_pos = [self.width - self.court_margin - self.baseline_margin, self.height / 2]
        self.ball_pos = [self.width / 2, self.height / 2]
        self.draw_ball()
            
    def update_ball_position(self, x, y):
        """Update the ball's position"""
        self.ball_pos = [x, y]
        self.draw_ball()
    
    def clear_ball(self):
        """Remove the ball from the court"""
        self.canvas.delete('ball')