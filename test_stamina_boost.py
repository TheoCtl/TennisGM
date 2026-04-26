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

print("Testing clay surface effects with inverted stamina_drain logic:")
print(f"Player 1 base stamina: {player1['skills']['stamina']}")
print(f"Player 2 base stamina: {player2['skills']['stamina']}")
print(f"Player 1 base lift: {player1['skills']['lift']}")
print(f"Player 2 base dropshot: {player2['skills']['dropshot']}")
print()

# Create a test game engine to get surface effects
engine = GameEngine(player1, player2, surface='clay', sets_to_win=2)

print(f"Clay SURFACE_EFFECTS: {SURFACE_EFFECTS['clay']}")
print(f"P1 surface effects (dynamic): {engine.p1_surface_fx}")
print(f"P2 surface effects (dynamic): {engine.p2_surface_fx}")
print()

# Simulate the boosted value calculation (what the faceoff screen would show)
def get_boosted_skill_value(base_skill, skill_name, surface_fx):
    boost = 1.0
    for effect_key, effect_multiplier in surface_fx.items():
        if skill_name in ["speed", "stamina"]:
            if effect_key == "speed" and skill_name == "speed":
                boost = effect_multiplier
                break
            elif effect_key == "stamina_drain" and skill_name == "stamina":
                # Invert stamina_drain: lower drain = higher effective stamina
                boost = 1.0 / effect_multiplier
                break
        elif skill_name == "lift" and effect_key == "lift_power":
            boost = effect_multiplier
            break
        elif skill_name == "dropshot" and effect_key == "dropshot_power":
            boost = effect_multiplier
            break
    return int(base_skill * boost)

p1_stamina_boosted = get_boosted_skill_value(player1['skills']['stamina'], 'stamina', engine.p1_surface_fx)
p2_stamina_boosted = get_boosted_skill_value(player2['skills']['stamina'], 'stamina', engine.p2_surface_fx)
p1_lift_boosted = get_boosted_skill_value(player1['skills']['lift'], 'lift', engine.p1_surface_fx)
p2_dropshot_boosted = get_boosted_skill_value(player2['skills']['dropshot'], 'dropshot', engine.p2_surface_fx)

print(f"P1 boosted stamina: {p1_stamina_boosted} (base: {player1['skills']['stamina']}, expected: ~62 with boost 1.25)")
print(f"P2 boosted stamina: {p2_stamina_boosted} (base: {player2['skills']['stamina']}, expected: ~56 with boost 1.25)")
print(f"P1 boosted lift: {p1_lift_boosted} (base: {player1['skills']['lift']}, expected: 55 with boost 1.1)")
print(f"P2 boosted dropshot: {p2_dropshot_boosted} (base: {player2['skills']['dropshot']}, expected: 60 with boost 1.1)")
print()

# Verify the inversions work
expected_p1_stamina = int(player1['skills']['stamina'] * 1.25)  # 1/0.8 = 1.25
expected_p2_stamina = int(player2['skills']['stamina'] * 1.25)  # 1/0.8 = 1.25

if p1_stamina_boosted == expected_p1_stamina and p2_stamina_boosted == expected_p2_stamina:
    print(f"✓ PASS: Stamina boosted correctly (inverted stamina_drain)")
else:
    print(f"✗ FAIL: Stamina boost incorrect (expected {expected_p1_stamina} and {expected_p2_stamina}, got {p1_stamina_boosted} and {p2_stamina_boosted})")
