#!/usr/bin/env python3
"""
Utility to reset tournament history, hall of fame, and achievements in save.json
This allows starting a new game while keeping current player data and rankings.
"""

import json
import sys
from pathlib import Path

def reset_history(save_path='data/save.json'):
    """Clear tournament history, hall of fame, and records from save.json"""
    
    try:
        # Load the save file
        with open(save_path, 'r') as f:
            data = json.load(f)
        
        print(f"Loaded save from {save_path}")
        print(f"Current year: {data['current_year']}, Week: {data['current_week']}")
        
        # Count before reset
        num_tournaments = len([t for t in data.get('tournaments', []) if t])
        num_hof_players = len(data.get('hall_of_fame', []))
        num_records = len(data.get('records', []))
        
        print(f"\nBefore reset:")
        print(f"  Tournaments: {num_tournaments}")
        print(f"  Hall of Fame entries: {num_hof_players}")
        print(f"  Records: {num_records}")
        
        # Clear tournament history and coordinates sections only
        print(f"\nClearing tournament history and coordinates...")
        for tournament in data.get('tournaments', []):
            if 'history' in tournament:
                del tournament['history']
            if 'coordinates' in tournament:
                del tournament['coordinates']
        
        # Clear hall of fame
        print(f"Clearing hall of fame...")
        data['hall_of_fame'] = []
        
        # Clear records
        print(f"Clearing records...")
        data['records'] = []
                
        # Save the modified data
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✓ Reset complete!")
        print(f"\nAfter reset:")
        print(f"  Hall of Fame entries: {len(data['hall_of_fame'])}")
        print(f"  Records: {len(data['records'])}")
        print(f"  Tournament history/coordinates cleared from all tournaments")
        
    except FileNotFoundError:
        print(f"Error: Could not find {save_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: {save_path} is not valid JSON")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    save_file = 'data/save.json'
    
    # Allow custom path as argument
    if len(sys.argv) > 1:
        save_file = sys.argv[1]
    
    # Confirm before resetting
    print("=" * 60)
    print("TOURNAMENT HISTORY RESET UTILITY")
    print("=" * 60)
    print(f"\nThis will clear:")
    print("  • Tournament history and coordinates sections")
    print("  • Hall of Fame entries")
    print("  • All achievements/records")
    print("  • Player tournament wins and histories")
    print(f"\nFile: {save_file}")
    print("\nYour players will be kept with current ratings.")
    print("=" * 60)
    
    response = input("\nAre you sure? Type 'YES' to confirm: ").strip()
    
    if response.upper() == "YES":
        reset_history(save_file)
    else:
        print("Reset cancelled.")
        sys.exit(0)
