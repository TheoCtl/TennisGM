import json
from collections import defaultdict
from statistics import mean, median

# Load the save file
with open('data/save.json', 'r') as f:
    data = json.load(f)

players = data.get('players', [])

# Extract mentality and ranking data
mentality_rankings = defaultdict(list)

for player in players:
    age = player.get('age')
    if 'mentality' not in player or 'rank' not in player:
        continue
    
    ##########################################
    # REMPLACER AGE PAR AGE MAXIMUM SOUHAITE #
    ##########################################
    if age > 16:
        continue
    
    mentality = player.get('mentality', 'Unknown')
    rank = player.get('rank')
    
    # Skip if rank is not a valid number
    if rank is None or rank == 'N/A':
        continue
    
    try:
        rank = int(rank)
        mentality_rankings[mentality].append(rank)
    except (ValueError, TypeError):
        continue

# Calculate stats for each mentality
print("\n" + "="*70)
print("MENTALITY BALANCE ANALYSIS")
print("="*70)
print(f"\n{'Mentality':<20} {'Count':<8} {'Avg Rank':<12} {'Median':<12} {'Range':<15}")
print("-"*70)

results = []
for mentality in sorted(mentality_rankings.keys()):
    rankings = sorted(mentality_rankings[mentality])
    count = len(rankings)
    avg = mean(rankings)
    med = median(rankings)
    min_rank = min(rankings)
    max_rank = max(rankings)
    
    results.append({
        'mentality': mentality,
        'count': count,
        'avg': avg,
        'median': med,
        'min': min_rank,
        'max': max_rank,
        'rankings': rankings
    })
    
    print(f"{mentality:<20} {count:<8} {avg:>10.1f}  {med:>10.1f}   #{min_rank}-#{max_rank}")

print("\n" + "="*70)
print("ANALYSIS & INEQUALITY DETECTION")
print("="*70)

# Sort by average ranking to find best/worst
sorted_by_avg = sorted(results, key=lambda x: x['avg'])
best = sorted_by_avg[0]
worst = sorted_by_avg[-1]

print(f"\nBest Performing Mentality: {best['mentality']}")
print(f"  Average Rank: #{best['avg']:.1f}")
print(f"  Median Rank: #{best['median']:.1f}")

print(f"\nWorst Performing Mentality: {worst['mentality']}")
print(f"  Average Rank: #{worst['avg']:.1f}")
print(f"  Median Rank: #{worst['median']:.1f}")

gap = worst['avg'] - best['avg']
print(f"\nAverage Ranking Gap: {gap:.1f} positions ({((gap/best['avg'])*100):.1f}%)")

print("\n" + "-"*70)
print("INEQUALITY REPORT:")
print("-"*70)

if gap > 10:
    print(f"⚠️  MAJOR IMBALANCE: {gap:.1f} position gap between best and worst!")
elif gap > 5:
    print(f"⚠️  MODERATE IMBALANCE: {gap:.1f} position gap between best and worst")
else:
    print(f"✓ Relatively balanced: {gap:.1f} position gap")

# Check if any mentality is significantly disadvantaged
print("\nDetailed Inequality Breakdown:")
for r in sorted_by_avg:
    deviation = r['avg'] - best['avg']
    if deviation > 5:
        print(f"  ⚠️  {r['mentality']}: {deviation:+.1f} positions worse than best")
    elif deviation > 2:
        print(f"  ! {r['mentality']}: {deviation:+.1f} positions worse than best")
    else:
        print(f"  ✓ {r['mentality']}: {deviation:+.1f} positions")

print("\n" + "="*70)
