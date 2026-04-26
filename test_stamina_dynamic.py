#!/usr/bin/env python
import sys
sys.path.insert(0, 'src')
from sim.game_engine import GameEngine

# Test with P1 having better stamina
player1_high_stamina = {
    'id': 1, 'name': 'Player 1 (High STA)', 'archetype': 'marathonian',
    'skills': {'serve': 60, 'forehand': 65, 'backhand': 55, 'volley': 40,
               'dropshot': 45, 'lift': 50, 'slice': 45, 'cross': 70, 'straight': 60,
               'speed': 65, 'stamina': 60, 'mental': 60, 'iq': 55}  # 60 stamina
}

player2_low_stamina = {
    'id': 2, 'name': 'Player 2 (Low STA)', 'archetype': 'net-player',
    'skills': {'serve': 70, 'forehand': 60, 'backhand': 50, 'volley': 70,
               'dropshot': 55, 'lift': 40, 'slice': 50, 'cross': 65, 'straight': 75,
               'speed': 60, 'stamina': 45, 'mental': 65, 'iq': 60}  # 45 stamina
}

print("Testing dynamic stamina_drain boost on clay:")
print(f"Player 1 stamina: {player1_high_stamina['skills']['stamina']} (higher)")
print(f"Player 2 stamina: {player2_low_stamina['skills']['stamina']} (lower)")
print()

engine = GameEngine(player1_high_stamina, player2_low_stamina, surface='clay', sets_to_win=2)

print(f"P1 surface effects: {engine.p1_surface_fx}")
print(f"P2 surface effects: {engine.p2_surface_fx}")
print()

# Check stamina_drain values
p1_stamina_drain = engine.p1_surface_fx.get('stamina_drain', 1.0)
p2_stamina_drain = engine.p2_surface_fx.get('stamina_drain', 1.0)

print(f"P1 stamina_drain effect: {p1_stamina_drain} (expected: 1.1 since P1 has better stamina)")
print(f"P2 stamina_drain effect: {p2_stamina_drain} (expected: 1.05 since P2 has worse stamina)")
print()

# Simulate display logic
def get_boosted_skill_value(base_skill, skill_name, surface_fx):
    boost = 1.0
    for effect_key, effect_multiplier in surface_fx.items():
        if skill_name in ["speed", "stamina"]:
            if effect_key == "speed" and skill_name == "speed":
                boost = effect_multiplier
                break
            elif effect_key == "stamina_drain" and skill_name == "stamina":
                boost = effect_multiplier if effect_multiplier > 1.0 else 1.05
                break
        elif skill_name == "lift" and effect_key == "lift_power":
            boost = effect_multiplier
            break
    return int(base_skill * boost)

p1_display = get_boosted_skill_value(player1_high_stamina['skills']['stamina'], 'stamina', engine.p1_surface_fx)
p2_display = get_boosted_skill_value(player2_low_stamina['skills']['stamina'], 'stamina', engine.p2_surface_fx)

print(f"P1 displayed stamina: {p1_display} (base: {player1_high_stamina['skills']['stamina']}, expected: {int(player1_high_stamina['skills']['stamina'] * 1.1)} with 1.1x)")
print(f"P2 displayed stamina: {p2_display} (base: {player2_low_stamina['skills']['stamina']}, expected: {int(player2_low_stamina['skills']['stamina'] * 1.05)} with 1.05x)")
print()

if p1_display == int(player1_high_stamina['skills']['stamina'] * 1.1) and p2_display == int(player2_low_stamina['skills']['stamina'] * 1.05):
    print("✓ PASS: Stamina displays with dynamic 1.1x/1.05x boost based on skill comparison")
else:
    print(f"✗ FAIL: Expected {int(player1_high_stamina['skills']['stamina'] * 1.1)} and {int(player2_low_stamina['skills']['stamina'] * 1.05)}, got {p1_display} and {p2_display}")
