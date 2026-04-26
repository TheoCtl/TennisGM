#!/usr/bin/env python
import sys
sys.path.insert(0, 'src')
from sim.game_engine import GameEngine

# Test that surface effects are consistent across multiple runs
player1 = {
    'id': 1, 'name': 'Player 1', 'archetype': 'baseliner',
    'skills': {'serve': 70, 'forehand': 75, 'backhand': 60, 'volley': 40,
               'dropshot': 45, 'lift': 55, 'slice': 45, 'cross': 70, 'straight': 60,
               'speed': 65, 'stamina': 60, 'mental': 60, 'iq': 55}
}

player2 = {
    'id': 2, 'name': 'Player 2', 'archetype': 'net-player',
    'skills': {'serve': 65, 'forehand': 60, 'backhand': 55, 'volley': 70,
               'dropshot': 50, 'lift': 40, 'slice': 50, 'cross': 65, 'straight': 75,
               'speed': 60, 'stamina': 50, 'mental': 65, 'iq': 60}
}

print("FACEOFF STAT DISPLAY CONSISTENCY TEST")
print("=" * 70)
print(f"Player 1: serve={player1['skills']['serve']}, forehand={player1['skills']['forehand']}, stamina={player1['skills']['stamina']}")
print(f"Player 2: serve={player2['skills']['serve']}, forehand={player2['skills']['forehand']}, stamina={player2['skills']['stamina']}")
print()

# Run multiple GameEngine initializations (each gets different random form)
print("Running 10 GameEngine instances (each with different random form):")
print("-" * 70)

results = []
for i in range(10):
    engine = GameEngine(player1, player2, surface='hard', sets_to_win=2)
    
    # Check the surface effects
    p1_serve = engine.p1_surface_fx.get('serve_power', 1.0)
    p2_serve = engine.p2_surface_fx.get('serve_power', 1.0)
    p1_forehand = engine.p1_surface_fx.get('forehand_power', 1.0)
    p2_forehand = engine.p2_surface_fx.get('forehand_power', 1.0)
    p1_stamina = engine.p1_surface_fx.get('stamina_drain', 1.0)
    p2_stamina = engine.p2_surface_fx.get('stamina_drain', 1.0)
    
    results.append({
        'p1_serve': p1_serve,
        'p2_serve': p2_serve,
        'p1_forehand': p1_forehand,
        'p2_forehand': p2_forehand,
        'p1_stamina': p1_stamina,
        'p2_stamina': p2_stamina,
    })
    
    print(f"Run {i+1}: P1[serve:{p1_serve}, fh:{p1_forehand}, sta:{p1_stamina}] | P2[serve:{p2_serve}, fh:{p2_forehand}, sta:{p2_stamina}]")

print()
print("CONSISTENCY CHECK:")
print("-" * 70)

# Check if all results are identical
all_same = all(r == results[0] for r in results)

if all_same:
    print("✓ PASS: All 10 runs produced IDENTICAL surface effects")
    print(f"  P1 serve boost: {results[0]['p1_serve']} (Player 1 has higher serve: {player1['skills']['serve']} > {player2['skills']['serve']})")
    print(f"  P2 serve boost: {results[0]['p2_serve']} (Player 2 has lower serve)")
    print(f"  P1 forehand boost: {results[0]['p1_forehand']} (Player 1 has higher forehand: {player1['skills']['forehand']} > {player2['skills']['forehand']})")
    print(f"  P2 forehand boost: {results[0]['p2_forehand']} (Player 2 has lower forehand)")
    print(f"  P1 stamina boost: {results[0]['p1_stamina']} (Player 1 has higher stamina: {player1['skills']['stamina']} > {player2['skills']['stamina']})")
    print(f"  P2 stamina boost: {results[0]['p2_stamina']} (Player 2 has lower stamina)")
else:
    print("✗ FAIL: Results are INCONSISTENT (form multipliers are affecting the comparison)")
    for i, r in enumerate(results):
        if r != results[0]:
            print(f"  Run {i+1} differs: {r}")
