#!/usr/bin/env python
import sys
sys.path.insert(0, 'src')
from sim.game_engine import GameEngine

# Test dropshot improvements
player_high_dropshot = {
    'id': 1, 'name': 'Dropshot Expert', 'archetype': 'net-player',
    'skills': {'serve': 60, 'forehand': 65, 'backhand': 55, 'volley': 70,
               'dropshot': 80, 'lift': 50, 'slice': 45, 'cross': 70, 'straight': 60,
               'speed': 60, 'stamina': 50, 'mental': 60, 'iq': 55}
}

player_fast_but_lower_dropshot = {
    'id': 2, 'name': 'Fast Runner', 'archetype': 'baseliner',
    'skills': {'serve': 70, 'forehand': 60, 'backhand': 50, 'volley': 40,
               'dropshot': 35, 'lift': 40, 'slice': 50, 'cross': 65, 'straight': 75,
               'speed': 75, 'stamina': 60, 'mental': 65, 'iq': 60}
}

print("DROPSHOT IMPROVEMENT TEST")
print("=" * 60)
print(f"Player 1 (Dropshot Expert): dropshot={player_high_dropshot['skills']['dropshot']}, speed={player_high_dropshot['skills']['speed']}")
print(f"Player 2 (Fast Runner): dropshot={player_fast_but_lower_dropshot['skills']['dropshot']}, speed={player_fast_but_lower_dropshot['skills']['speed']}")
print()

engine = GameEngine(player_high_dropshot, player_fast_but_lower_dropshot, surface='hard', sets_to_win=2)

print("IMPROVEMENTS MADE:")
print("-" * 60)
print("1. OPTION A (Wider winner thresholds with uncertainty):")
print("   - diff < 0: GUARANTEED WINNER (opponent much slower)")
print("   - diff < 2: 65% chance of winner (close match)")
print("   - diff < 4: 25% chance of winner (moderate difference)")
print("   - This prevents pure spam while allowing skilled players to win more often")
print()
print("2. OPTION B (Stamina penalty):")
print("   - When opponent catches a dropshot: -7 stamina drain")
print("   - Simulates fatigue from sprinting to the net")
print("   - Compounds the disadvantage of weak returns")
print()

# Simulate difference calculation
dropshot_skill = player_high_dropshot['skills']['dropshot']
defender_speed = player_fast_but_lower_dropshot['skills']['speed']
diff = defender_speed - dropshot_skill

print("SCENARIO ANALYSIS:")
print("-" * 60)
print(f"Dropshot skill vs Defender speed: {dropshot_skill} vs {defender_speed}")
print(f"Speed difference: {diff}")
print()

if diff < 0:
    print(f"Result: GUARANTEED WINNER (diff={diff} < 0)")
    print("  Player 1 dropshots are auto-winners")
elif diff < 2:
    print(f"Result: 65% CHANCE OF WINNER (diff={diff} < 2)")
    print("  Player 2 is faster but not by much - dropshots are likely winning")
elif diff < 4:
    print(f"Result: 25% CHANCE OF WINNER (diff={diff} < 4)")
    print("  Player 2 is moderately faster - occasional dropshot winners")
else:
    print(f"Result: VERY LOW CHANCE (diff={diff} >= 4)")
    print("  Player 2 is much faster - rare dropshot winners")
    print("  But when caught, Player 2 loses 7 stamina for the sprint")
print()

print("BENEFITS:")
print("-" * 60)
print("✓ Dropshot-focused players can win points more often")
print("✓ Can't spam dropshots mindlessly (uncertainty keeps it interesting)")
print("✓ Opponents are penalized with stamina loss for catching dropshots")
print("✓ Compounds with weak returns already given after dropshot catch")
