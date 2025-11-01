import random
import math
from archetypes import ARCTYPE_MAP, get_archetype_for_player

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

    @staticmethod
    def develop_skill(current_value, chance):
        return min(current_value + 1 if random.random() < chance else current_value, 100)

    @staticmethod
    def regress_skill(current_value, chance):
        return max(current_value - 1 if random.random() < chance else current_value, 0)

    @staticmethod
    def _ensure_skill_caps(player):
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
    def develop_player_weekly(player, archetype_func=None):
        age = player.get('age', 20)
        if age >= 40 or player.get('retired', False):
            return

        skills = player.get('skills', {})
        caps = PlayerDevelopment._ensure_skill_caps(player)

        # Determine archetype skills. Priority:
        # 1) Use provided archetype_func (if given)
        # 2) Use player's stored archetype_key or archetype name
        # 3) Fallback to computing from skills
        archetype_skills = set()
        if archetype_func is not None:
            # archetype_func should return (archetype_name, description, key_skills)
            result = archetype_func(player)
            if isinstance(result, tuple) and len(result) >= 3:
                key_skills = result[2]
                if isinstance(key_skills, (list, tuple, set)):
                    archetype_skills = set(key_skills)
        else:
            # Try stored archetype key first
            ak = player.get('archetype_key')
            if ak:
                try:
                    key = tuple(ak)
                    if key in ARCTYPE_MAP:
                        archetype_skills = set(key)
                except Exception:
                    pass
            # If not found, try matching stored archetype name
            if not archetype_skills and player.get('archetype'):
                an = player['archetype']
                for k, (n, d) in ARCTYPE_MAP.items():
                    if n == an:
                        archetype_skills = set(k)
                        break
            # Final fallback: compute from skills
            if not archetype_skills:
                try:
                    _, _, key = get_archetype_for_player(player)
                    archetype_skills = set(key)
                except Exception:
                    archetype_skills = set()

        for skill_name, current_value in skills.items():
            cap = caps.get(skill_name, {'progcap': 0, 'regcap': 0})
            if age < 28:
                if cap['progcap'] >= 5:
                    continue
                pf = player.get('potential_factor', 1.0)
                chance = PlayerDevelopment.calculate_improvement_chance(age, current_value, pf) / 12.0
                if skill_name == player.get('bonus'):
                    chance *= 1.1
                if skill_name in archetype_skills:
                    chance *= 1.1
                if random.random() < chance and current_value < 100:
                    skills[skill_name] = current_value + 1
                    cap['progcap'] += 1
            else:
                if cap['regcap'] >= 5:
                    continue
                chance = PlayerDevelopment.calculate_regression_chance(age, current_value) / 12.0
                if random.random() < chance and current_value > 0:
                    skills[skill_name] = current_value - 1
                    cap['regcap'] += 1

            caps[skill_name] = cap

    @staticmethod
    def reset_caps(scheduler):
        """
        Reset all players' progcap/regcap to 0 at mid-season checkpoints (weeks 26 and 52).
        """
        for player in scheduler.players:
            if player.get('retired', False):
                continue
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

    @staticmethod
    def seasonal_development(scheduler):
        if scheduler.current_week in [26, 52]:
            PlayerDevelopment.reset_caps(scheduler)
