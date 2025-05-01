import random
import math

class PlayerDevelopment:
    @staticmethod
    def calculate_improvement_chance(player_age, current_skill):
        """Tighter progression curve with earlier peak"""
        # Age factor - sharp peak at 18-21
        if player_age <= 18:
            age_factor = 1.0
        elif player_age <= 21:
            age_factor = 0.9
        elif player_age <= 24:
            age_factor = 0.7
        elif player_age <= 28:
            age_factor = 0.4
        else:
            age_factor = 0

        # Smoother skill difficulty curve
        skill_factor = 1 - (current_skill / 110) ** 1.3

        # Base chance with adjusted weights
        base_chance = 0.55 * age_factor * skill_factor
        
        return max(0.05, base_chance)

    @staticmethod
    def calculate_regression_chance(player_age, current_skill):
        """More aggressive regression curve"""
        if player_age < 30:  # Regression starts slightly earlier
            return 0
        
        # Sharper age-based regression
        age_factor = min(1, (player_age - 30)/5)  # Faster progression
        
        # Higher skills regress faster
        skill_factor = (current_skill / 100) ** 0.9
        
        return 0.5 * age_factor * skill_factor  # Higher base regression rate

    @staticmethod
    def develop_skill(current_value, chance):
        improvements = 0
        temp_chance = chance
        
        while improvements < 3:  # Reduced cap from 5 to 3
            if random.random() < temp_chance:
                improvements += 1
                temp_chance *= 0.6  # Harder successive improvements
            else:
                break
                
        return min(current_value + improvements, 100)

    @staticmethod
    def develop_player(player):
        age = player['age']
        
        if age >= 40 or player.get('retired', False):
            return
        
        # Tighter transition periods
        if age < 28:
            if age < 24:
                # Younger players focus on improvement
                chance_func = PlayerDevelopment.calculate_improvement_chance
                change_direction = 1
            else:
                # 24-27: 70% improve, 30% regress
                if random.random() < 0.7:
                    chance_func = PlayerDevelopment.calculate_improvement_chance
                    change_direction = 1
                else:
                    chance_func = PlayerDevelopment.calculate_regression_chance
                    change_direction = -1
        else:
            # 28+: Full regression mode
            chance_func = PlayerDevelopment.calculate_regression_chance
            change_direction = -1
        
        for skill in player['skills']:
            current_value = player['skills'][skill]
            chance = chance_func(age, current_value)
            
            if change_direction == 1:
                new_value = PlayerDevelopment.develop_skill(current_value, chance)
            else:
                # More aggressive regression - potential for multi-point loss
                if random.random() < chance:
                    regression_points = min(2, 1 + int(random.random() * (age/30)))
                    new_value = max(0, current_value - regression_points)
                else:
                    new_value = current_value
            
            player['skills'][skill] = new_value
            
    @staticmethod
    def seasonal_development(scheduler):
        """
        Process development for all players at season milestones (weeks 26 and 52)
        """
        current_week = scheduler.current_week
        
        # Only process at week 26 and 52
        if current_week not in [26, 52]:
            return
        
        for player in scheduler.players:
            # Skip retired players
            if player.get('retired', False):
                continue
                
            PlayerDevelopment.develop_player(player)
