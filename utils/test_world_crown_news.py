#!/usr/bin/env python3
"""
Test script for World Crown news announcements across different weeks
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from schedule import TournamentScheduler

def test_world_crown_news():
    """Test World Crown news generation for different weeks"""
    print("Testing World Crown News Generation")
    print("=" * 50)
    
    scheduler = TournamentScheduler()
    
    # Test weeks where World Crown news should appear
    test_weeks = [11, 13, 18, 20, 47, 48]
    
    for week in test_weeks:
        print(f"\n--- Testing Week {week} ---")
        scheduler.current_week = week
        
        # Initialize World Crown if not already done
        if not scheduler.world_crown.get('current_bracket'):
            print(f"  Initializing World Crown for week {week}")
            scheduler.initialize_world_crown_year()
        else:
            print(f"  World Crown already initialized")
        
        # For week 48 test, add a winner to history
        if week == 48 and not scheduler.world_crown.get('winners_history'):
            scheduler.world_crown['winners_history'].append({
                'year': scheduler.current_year,
                'winner': 'Arcton',
                'final_score': '3-2'
            })
        
        # Debug: Check bracket state
        bracket = scheduler.world_crown.get('current_bracket', {})
        print(f"  Bracket exists: {bool(bracket)}")
        if bracket:
            qf = bracket.get('quarterfinals', {})
            print(f"  Quarterfinals: {len(qf)} matches")
            for qf_id, qf_data in qf.items():
                print(f"    {qf_id}: Week {qf_data.get('week')}, Winner: {qf_data.get('winner')}")
        
        # Debug: Check if matches are found
        matches = scheduler.get_world_crown_matches_for_week(week)
        print(f"  Matches found for week {week}: {len(matches)}")
        for match in matches:
            round_type, tie_id, tie_data = match
            print(f"    {round_type}: {tie_data.get('team1', 'None')} vs {tie_data.get('team2', 'None')}")
        
        news_items = scheduler._generate_world_crown_announcements()
        
        if news_items:
            for item in news_items:
                print(f"✓ {item['title']}")
                if isinstance(item['content'], list):
                    for line in item['content']:
                        print(f"  {line}")
                else:
                    print(f"  {item['content']}")
        else:
            print(f"✗ No news generated for week {week}")
    
    print(f"\n" + "=" * 50)
    print("World Crown news test completed!")

if __name__ == "__main__":
    test_world_crown_news()
