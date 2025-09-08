import json
import random
import sys

NATIONALITIES = [
    "Arcton", "Halcyon", "Rin", "Hethrion", "Haran", "Loknig", "Jeonguk", "Bleak"
]

def assign_nationalities_to_save(save_path):
    with open(save_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    changed = False
    
    # Check if data has players key (save file format) or is a direct list
    if isinstance(data, dict) and 'players' in data:
        players = data['players']
    elif isinstance(data, list):
        players = data
    else:
        print("Error: Could not find players in the save file.")
        return
    
    for player in players:
        if 'nationality' not in player or not player['nationality']:
            player['nationality'] = random.choice(NATIONALITIES)
            changed = True
    
    if changed:
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Nationalities assigned and saved to {save_path}")
    else:
        print("All players already have a nationality.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python assign_nationalities.py <save_file_path>")
        sys.exit(1)
    assign_nationalities_to_save(sys.argv[1])
