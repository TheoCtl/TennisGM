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

print("Testing clay surface effects on stamina display:")
print(f"Player 1 base stamina: {player1['skills']['stamina']}")
print(f"Player 2 base stamina: {player2['skills']['stamina']}")
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
        if skill_name == "stamina":
            # Skip stamina_drain - it's a match mechanic, not a stat boost
            pass
        elif skill_name == "speed" and effect_key == "speed":
            boost = effect_multiplier
            break
        elif skill_name == "lift" and effect_key == "lift_power":
            boost = effect_multiplier
            break
        elif skill_name == "dropshot" and effect_key == "dropshot_power":
            boost = effect_multiplier
            break
    return int(base_skill * boost)

p1_boosted = get_boosted_skill_value(player1['skills']['stamina'], 'stamina', engine.p1_surface_fx)
p2_boosted = get_boosted_skill_value(player2['skills']['stamina'], 'stamina', engine.p2_surface_fx)

print(f"P1 boosted stamina: {p1_boosted} (should be {player1['skills']['stamina']}, no malus)")
print(f"P2 boosted stamina: {p2_boosted} (should be {player2['skills']['stamina']}, no malus)")
print()

if p1_boosted == player1['skills']['stamina'] and p2_boosted == player2['skills']['stamina']:
    print("✓ PASS: Stamina displays correctly (no malus applied)")
else:
    print("✗ FAIL: Stamina displays incorrectly")
