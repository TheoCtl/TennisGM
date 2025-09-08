#!/usr/bin/env python3
"""
Test script for World Crown teams display functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from schedule import TournamentScheduler

def test_world_crown_teams():
    """Test World Crown teams structure and data"""
    print("Testing World Crown Teams Display")
    print("=" * 50)
    
    scheduler = TournamentScheduler()
    
    # Initialize World Crown if not already done
    if not scheduler.world_crown.get('current_year_teams'):
        print("Initializing World Crown teams...")
        scheduler.initialize_world_crown_year()
    
    teams = scheduler.world_crown.get('current_year_teams', {})
    
    if not teams:
        print("✗ No teams found!")
        return False
    
    print(f"✓ Found {len(teams)} national teams")
    
    total_players = 0
    for country, players in teams.items():
        print(f"\n--- {country} National Team ---")
        print(f"Team size: {len(players)}/5 players")
        
        if not players:
            print("  ⚠️  No players in team!")
            continue
        
        total_players += len(players)
        
        # Show player details
        for i, player in enumerate(players, 1):
            rank = player.get('rank', '???')
            name = player.get('name', 'Unknown')
            favorite = "★" if player.get('favorite', False) else " "
            print(f"  {i}. {favorite} #{rank:>3} {name}")
        
        # Team stats
        ranks = [p.get('rank', 999) for p in players if isinstance(p.get('rank'), int)]
        if ranks:
            avg_rank = sum(ranks) / len(ranks)
            best_rank = min(ranks)
            print(f"  📊 Best: #{best_rank} | Average: #{avg_rank:.1f}")
    
    print(f"\n" + "=" * 50)
    print(f"✓ Total players across all teams: {total_players}")
    print(f"✓ Expected teams: 8, Found: {len(teams)}")
    
    # Check if all countries are represented
    expected_countries = ["Arcton", "Halcyon", "Rin", "Hethrion", "Haran", "Loknig", "Jeonguk", "Bleak"]
    missing_countries = set(expected_countries) - set(teams.keys())
    extra_countries = set(teams.keys()) - set(expected_countries)
    
    if missing_countries:
        print(f"⚠️  Missing countries: {list(missing_countries)}")
    if extra_countries:
        print(f"⚠️  Extra countries: {list(extra_countries)}")
    
    if len(teams) == 8 and not missing_countries:
        print("✓ All expected countries have teams!")
        return True
    else:
        return False

if __name__ == "__main__":
    success = test_world_crown_teams()
    if success:
        print("\n🏆 World Crown teams test passed successfully!")
    else:
        print("\n❌ World Crown teams test failed!")
