import random
import math

class PlayerDevelopment:
    @staticmethod
    def calculate_improvement_chance(player_age, current_skill, potential_factor=1.0):
        """Tighter progression curve with earlier peak"""
        # Age factor - sharp peak at 18-21
        if player_age <= 20:
            age_factor = 1.3
        elif player_age <= 23:
            age_factor = 1.2
        elif player_age <= 26:
            age_factor = 1.1
        elif player_age <= 28:
            age_factor = 1
        else:
            age_factor = 0

        # Smoother skill difficulty curve
        skill_factor = 1.15 * math.exp(-0.045 * (current_skill - 25))
        skill_factor = max(0.01, min(1.0, skill_factor))

        # Base chance with adjusted weights
        base_chance = age_factor * skill_factor * potential_factor
        return max(0.01, base_chance)

    @staticmethod
    def calculate_regression_chance(player_age, current_skill):
        """More aggressive regression curve"""
        if player_age < 31:  # Regression starts slightly earlier
            return 0
        # Sharper age-based regression
        age_factor = min(1, (player_age - 30)/7)  # Faster progression
        return age_factor  # Higher base regression rate

    # Legacy multi-point methods are no longer used (kept for compatibility)
    @staticmethod
    def develop_skill(current_value, chance):
        return min(current_value + 1 if random.random() < chance else current_value, 100)

    @staticmethod
    def regress_skill(current_value, chance):
        return max(current_value - 1 if random.random() < chance else current_value, 0)

    @staticmethod
    def _ensure_skill_caps(player):
        """
        Ensure per-skill caps structure exists:
        player['skill_caps'] = { skill: {'progcap': int, 'regcap': int}, ... }
        """
        skills = player.get('skills', {})
        caps = player.setdefault('skill_caps', {})
        for skill in skills:
            if skill not in caps or not isinstance(caps[skill], dict):
                caps[skill] = {'progcap': 0, 'regcap': 0}
            else:
                caps[skill].setdefault('progcap', 0)
                caps[skill].setdefault('regcap', 0)
        return caps

    @staticmethod
    def develop_player_weekly(player):
        """
        Weekly development: each skill can change by at most +/-1.
        Chances are divided by 26 to spread development across the season.
        'progcap' and 'regcap' limit per half-season to max 5 changes per direction.
        """
        age = player.get('age', 20)
        if age >= 40 or player.get('retired', False):
            return

        skills = player.get('skills', {})
        caps = PlayerDevelopment._ensure_skill_caps(player)

        for skill_name, current_value in skills.items():
            cap = caps.get(skill_name, {'progcap': 0, 'regcap': 0})
            # Before peak: improve; after: regress (keeps previous behavior)
            if age < 28:
                if cap['progcap'] >= 5:
                    continue
                pf = player.get('potential_factor', 1.0)
                chance = PlayerDevelopment.calculate_improvement_chance(age, current_value, pf) / 26.0
                # Apply bonus if skill matches player's bonus
                if skill_name == player.get('bonus'):
                    chance *= 1.1
                if random.random() < chance and current_value < 100:
                    skills[skill_name] = current_value + 1
                    cap['progcap'] += 1
            else:
                if cap['regcap'] >= 5:
                    continue
                chance = PlayerDevelopment.calculate_regression_chance(age, current_value) / 26.0
                if random.random() < chance and current_value > 0:
                    skills[skill_name] = current_value - 1
                    cap['regcap'] += 1

            # persist updated cap back (dict is mutable, but ensure structure exists)
            caps[skill_name] = cap

    @staticmethod
    def reset_caps(scheduler):
        """
        Reset all players' progcap/regcap to 0 at mid-season checkpoints (weeks 26 and 52).
        """
        for player in scheduler.players:
            if player.get('retired', False):
                continue
            # Ensure structure exists for current skills, then zero all caps
            caps = PlayerDevelopment._ensure_skill_caps(player)
            for skill in caps:
                caps[skill]['progcap'] = 0
                caps[skill]['regcap'] = 0

    @staticmethod
    def weekly_development(scheduler):
        """
        Run weekly development for all players.
        """
        for player in scheduler.players:
            if player.get('retired', False):
                continue
            PlayerDevelopment.develop_player_weekly(player)

    # Deprecated: kept for compatibility; no longer used by scheduler
    @staticmethod
    def seasonal_development(scheduler):
        # Old entrypoint did full development at weeks 26 and 52.
        # Now it only resets caps at those weeks.
        if scheduler.current_week in [26, 52]:
            PlayerDevelopment.reset_caps(scheduler)
