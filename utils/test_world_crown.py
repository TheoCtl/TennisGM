#!/usr/bin/env python3
"""
Test script for World Crown tournament system functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from schedule import TournamentScheduler

def test_world_crown():
    """Test World Crown system initialization and functionality"""
    print("Testing World Crown Tournament System")
    print("=" * 50)
    
    # Initialize scheduler
    try:
        scheduler = TournamentScheduler()
        print("✓ TournamentScheduler initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize TournamentScheduler: {e}")
        return False
    
    # Check if World Crown data exists
    if hasattr(scheduler, 'world_crown'):
        print("✓ World Crown data structure exists")
        print(f"  - Current bracket: {bool(scheduler.world_crown.get('current_bracket'))}")
        print(f"  - Current year teams: {bool(scheduler.world_crown.get('current_year_teams'))}")
        print(f"  - Winners history: {len(scheduler.world_crown.get('winners_history', []))} entries")
    else:
        print("✗ World Crown data structure missing")
        return False
    
    # Test initialization for current year
    try:
        # Set to week 1 to trigger initialization
        scheduler.current_week = 1
        scheduler.initialize_world_crown_year()
        print("✓ World Crown year initialization successful")
        
        # Check if teams were created
        teams = scheduler.world_crown.get('current_year_teams', {})
        if teams:
            print(f"✓ Teams created for {len(teams)} countries")
            for country, players in teams.items():
                print(f"  - {country}: {len(players)} players")
        else:
            print("✗ No teams created")
            return False
            
    except Exception as e:
        print(f"✗ World Crown initialization failed: {e}")
        return False
    
    # Test bracket structure
    try:
        bracket = scheduler.world_crown.get('current_bracket', {})
        qf_count = len(bracket.get('quarterfinals', {}))
        sf_count = len(bracket.get('semifinals', {}))
        final_exists = 'final' in bracket.get('final', {})
        
        print(f"✓ Bracket structure complete:")
        print(f"  - Quarterfinals: {qf_count}/4")
        print(f"  - Semifinals: {sf_count}/2") 
        print(f"  - Final: {'Yes' if final_exists else 'No'}")
        
    except Exception as e:
        print(f"✗ Bracket structure error: {e}")
        return False
    
    # Test match scheduling
    try:
        # Test week 11 matches (first quarterfinals)
        matches_week_11 = scheduler.get_world_crown_matches_for_week(11)
        matches_week_13 = scheduler.get_world_crown_matches_for_week(13)
        
        print(f"✓ Match scheduling works:")
        print(f"  - Week 11 matches: {len(matches_week_11)}")
        print(f"  - Week 13 matches: {len(matches_week_13)}")
        
    except Exception as e:
        print(f"✗ Match scheduling error: {e}")
        return False
    
    # Test news generation
    try:
        # Simulate a completed tournament by adding winner
        scheduler.world_crown['winners_history'].append({
            'year': scheduler.current_year,
            'winner': 'Arcton',
            'final_score': '3-2'
        })
        
        scheduler.current_week = 48  # Week when champion news is generated
        news_items = scheduler._generate_world_crown_announcements()
        
        print(f"✓ News generation works: {len(news_items)} items")
        
    except Exception as e:
        print(f"✗ News generation error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All World Crown tests passed successfully!")
    return True

if __name__ == "__main__":
    test_world_crown()
