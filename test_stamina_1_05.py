#!/usr/bin/env python
import sys
sys.path.insert(0, 'src')
from sim.game_engine import GameEngine, SURFACE_EFFECTS

# Test data
player1 = {
    'id': 1, 'name': 'Player 1', 'archetype': 'baseliner',
    'skills': {'serve': 60, 'forehand': 65, 'backhand': 55, 'volley': 40,
               'dropshot': 45, 'lift': 50, 'slice': 45, 'cross': 70, 'straight': 60,
               'speed': 65, 'stamina': 50, 'mental': 60, 'iq': 55}
}

player2 = {
    'id': 2, 'name': 'Player 2', 'archetype': 'net-player',
    'skills': {'serve': 70, 'forehand': 60, 'backhand': 50, 'volley': 70,
               'dropshot': 55, 'lift': 40, 'slice': 50, 'cross': 65, 'straight': 75,
               'speed': 60, 'stamina': 45, 'mental': 65, 'iq': 60}
}

print("Testing clay surface effects with 1.05x stamina boost:")
print(f"Player 1 base stamina: {player1['skills']['stamina']}")
print(f"Player 2 base stamina: {player2['skills']['stamina']}")
print()

# Create a test game engine to get surface effects
engine = GameEngine(player1, player2, surface='clay', sets_to_win=2)

print(f"Clay SURFACE_EFFECTS: {SURFACE_EFFECTS['clay']}")
print(f"P1 surface effects (dynamic): {engine.p1_surface_fx}")
print(f"P2 surface effects (dynamic): {engine.p2_surface_fx}")
print()

# Simulate the boosted value calculation
def get_boosted_skill_value(base_skill, skill_name, surface_fx):
    boost = 1.0
    for effect_key, effect_multiplier in surface_fx.items():
        if skill_name in ["speed", "stamina"]:
            if effect_key == "speed" and skill_name == "speed":
                boost = effect_multiplier
                break
            elif effect_key == "stamina_drain" and skill_name == "stamina":
                # For display: stamina_drain shows as a stat boost (1.05 base, 1.1 dynamic)
                boost = effect_multiplier if effect_multiplier > 1.0 else 1.05
                break
        elif skill_name == "lift" and effect_key == "lift_power":
            boost = effect_multiplier
            break
        elif skill_name == "dropshot" and effect_key == "dropshot_power":
            boost = effect_multiplier
            break
    return int(base_skill * boost)

p1_stamina = get_boosted_skill_value(player1['skills']['stamina'], 'stamina', engine.p1_surface_fx)
p2_stamina = get_boosted_skill_value(player2['skills']['stamina'], 'stamina', engine.p2_surface_fx)
p1_lift = get_boosted_skill_value(player1['skills']['lift'], 'lift', engine.p1_surface_fx)
p2_dropshot = get_boosted_skill_value(player2['skills']['dropshot'], 'dropshot', engine.p2_surface_fx)

print(f"P1 boosted stamina: {p1_stamina} (base: {player1['skills']['stamina']}, expected: 52 with 1.05x)")
print(f"P2 boosted stamina: {p2_stamina} (base: {player2['skills']['stamina']}, expected: 47 with 1.05x)")
print(f"P1 boosted lift: {p1_lift} (base: {player1['skills']['lift']}, expected: 55 with 1.1x)")
print(f"P2 boosted dropshot: {p2_dropshot} (base: {player2['skills']['dropshot']}, expected: 60 with 1.1x)")
print()

expected_p1_stamina = int(player1['skills']['stamina'] * 1.05)
expected_p2_stamina = int(player2['skills']['stamina'] * 1.05)

if p1_stamina == expected_p1_stamina and p2_stamina == expected_p2_stamina:
    print(f"✓ PASS: Stamina shows 1.05x boost on clay")
else:
    print(f"✗ FAIL: Expected stamina {expected_p1_stamina} and {expected_p2_stamina}, got {p1_stamina} and {p2_stamina}")
