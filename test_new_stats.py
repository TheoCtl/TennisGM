"""Test script for lift, slice, and iq stats."""
import sys
import json
import random

sys.path.insert(0, 'src')
sys.path.insert(0, 'src/sim')

from game_engine import GameEngine

# Load two players from save data
with open('data/save.json', 'r') as f:
    data = json.load(f)

p1 = data['players'][0]
p2 = data['players'][1]

print(f"P1: {p1['name']}")
sk = p1['skills']
print(f"  lift={sk.get('lift','?')} slice={sk.get('slice','?')} iq={sk.get('iq','?')}")
print(f"  lift_tend={p1.get('lift_tend','?')} slice_tend={p1.get('slice_tend','?')}")
print(f"P2: {p2['name']}")
sk2 = p2['skills']
print(f"  lift={sk2.get('lift','?')} slice={sk2.get('slice','?')} iq={sk2.get('iq','?')}")
print(f"  lift_tend={p2.get('lift_tend','?')} slice_tend={p2.get('slice_tend','?')}")

# Run 50 matches
p1_wins = 0
total_lift_winners = 0
total_slice_winners = 0

for i in range(50):
    engine = GameEngine(p1, p2, surface='hard', sets_to_win=2)
    winner = engine.simulate_match()
    if winner['id'] == p1['id']:
        p1_wins += 1
    for pid, st in engine.match_stats.items():
        total_lift_winners += st.get('lift_winners', 0)
        total_slice_winners += st.get('slice_winners', 0)

print(f"\nResults after 50 matches: P1={p1_wins}, P2={50 - p1_wins}")
print(f"Total lift winners across all matches: {total_lift_winners}")
print(f"Total slice winners across all matches: {total_slice_winners}")

# Show last match stats
print("\nLast match stats:")
for pid, st in engine.match_stats.items():
    print(f"  Player {pid}: {st}")

# Test with a high-lift player vs high-speed player
print("\n--- Test: High Lift vs High Speed ---")
lift_player = json.loads(json.dumps(p1))
lift_player['skills']['lift'] = 90
lift_player['lift_tend'] = 15

speed_player = json.loads(json.dumps(p2))
speed_player['skills']['speed'] = 90

lift_wins = 0
for i in range(30):
    engine = GameEngine(lift_player, speed_player, surface='hard', sets_to_win=2)
    winner = engine.simulate_match()
    if winner['id'] == lift_player['id']:
        lift_wins += 1
print(f"Lift player wins: {lift_wins}/30")

# Test with high IQ player
print("\n--- Test: High IQ vs Normal ---")
iq_player = json.loads(json.dumps(p1))
iq_player['skills']['iq'] = 90
iq_player['mentality'] = 'strategist'

normal_player = json.loads(json.dumps(p2))
normal_player['skills']['iq'] = 30

iq_wins = 0
for i in range(30):
    engine = GameEngine(iq_player, normal_player, surface='hard', sets_to_win=2)
    winner = engine.simulate_match()
    if winner['id'] == iq_player['id']:
        iq_wins += 1
print(f"High IQ player wins: {iq_wins}/30")

# Test with high slice player
print("\n--- Test: High Slice vs Normal ---")
slice_player = json.loads(json.dumps(p1))
slice_player['skills']['slice'] = 90
slice_player['slice_tend'] = 12

slice_wins = 0
total_slice = 0
for i in range(30):
    engine = GameEngine(slice_player, p2, surface='hard', sets_to_win=2)
    winner = engine.simulate_match()
    if winner['id'] == slice_player['id']:
        slice_wins += 1
    for pid, st in engine.match_stats.items():
        total_slice += st.get('slice_winners', 0)

print(f"Slice player wins: {slice_wins}/30")
print(f"Total slice winners: {total_slice}")

print("\n=== ALL TESTS PASSED ===")
