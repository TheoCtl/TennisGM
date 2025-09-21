import random
import math

def calculate_ball_trajectory(start_pos, end_pos, power, precision, num_points=30):
    """Calculate points along the ball trajectory"""
    # Convert power (0-100) to trajectory height
    max_height = 30 + (power / 100) * 60  # Higher power = higher arc
    
    # Add randomness based on precision (0-100)
    precision_factor = precision / 100
    random_x = random.uniform(-30 * (1 - precision_factor), 30 * (1 - precision_factor))
    random_y = random.uniform(-30 * (1 - precision_factor), 30 * (1 - precision_factor))
    end_pos = (end_pos[0] + random_x, end_pos[1] + random_y)
    
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        
        # Use cubic Bezier curve for smoother trajectory
        # Control points for the curve
        cp1_x = start_pos[0] + (end_pos[0] - start_pos[0]) * 0.4
        cp1_y = start_pos[1] - max_height
        cp2_x = start_pos[0] + (end_pos[0] - start_pos[0]) * 0.6
        cp2_y = start_pos[1] - max_height
        
        # Cubic Bezier formula
        x = (1-t)**3 * start_pos[0] + \
            3 * (1-t)**2 * t * cp1_x + \
            3 * (1-t) * t**2 * cp2_x + \
            t**3 * end_pos[0]
            
        y = (1-t)**3 * start_pos[1] + \
            3 * (1-t)**2 * t * cp1_y + \
            3 * (1-t) * t**2 * cp2_y + \
            t**3 * end_pos[1]
        
        points.append((x, y))
    
    return points