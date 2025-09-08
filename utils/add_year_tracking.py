import json
import sys

def add_year_tracking_to_players(save_path):
    with open(save_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    changed = False
    
    # Check if data has players key (save file format) or is a direct list
    if isinstance(data, dict) and 'players' in data:
        players = data['players']
        current_year = data.get('current_year', 1)
    elif isinstance(data, list):
        players = data
        current_year = 1
    else:
        print("Error: Could not find players in the save file.")
        return
    
    for player in players:
        if 'year_start_rankings' not in player:
            player['year_start_rankings'] = {}
            # Initialize with current ranking for previous years if we have any year context
            if current_year > 1:
                player['year_start_rankings'][str(current_year - 1)] = player.get('rank', 999)
            changed = True
    
    if changed:
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Year tracking added to all players and saved to {save_path}")
    else:
        print("All players already have year tracking.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python add_year_tracking.py <save_file_path>")
        sys.exit(1)
    add_year_tracking_to_players(sys.argv[1])
