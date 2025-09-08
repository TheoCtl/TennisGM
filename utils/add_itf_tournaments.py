import json
import sys

def add_itf_tournaments():
    save_path = "data/save.json"
    
    # Load save file
    try:
        with open(save_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {save_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not parse {save_path}")
        return
    
    if 'tournaments' not in data:
        print("Error: No tournaments list found in save file")
        return
    
    # Find the highest existing tournament ID
    existing_ids = [t.get('id', 0) for t in data['tournaments']]
    next_id = max(existing_ids) + 1 if existing_ids else 328
    
    # Initialize counters
    surfaces = ["grass", "indoor", "clay", "hard"]
    surface_index = 0
    week = 1
    tournament_count = 0
    
    print("ITF Tournament Generator")
    print("Enter tournament names (press Enter with empty name to finish)")
    print("Format: Each name will become 'ITF {name}'")
    print("Surfaces will cycle: grass -> indoor -> clay -> hard")
    print("Week increases every 2 tournaments")
    print()
    
    tournaments_added = []
    
    while True:
        try:
            name = input(f"Tournament {tournament_count + 1} name (week {week}, {surfaces[surface_index]}): ").strip()
            
            if not name:
                break
            
            # Create tournament object
            tournament = {
                "id": next_id,
                "name": f"ITF {name}",
                "week": week,
                "surface": surfaces[surface_index],
                "category": "ITF",
                "draw_size": 16,
                "year": data.get("current_year", 2072),
                "winner_id": None,
                "participants": [],
                "bracket": [],
                "current_round": 0,
                "active_matches": [],
                "history": []
            }
            
            # Add to tournaments list
            data['tournaments'].append(tournament)
            tournaments_added.append(tournament)
            
            print(f"Added: {tournament['name']} (ID: {next_id}, Week: {week}, Surface: {surfaces[surface_index]})")
            
            # Update counters
            next_id += 1
            tournament_count += 1
            surface_index = (surface_index + 1) % 4
            
            # Increase week every 2 tournaments
            if tournament_count % 2 == 0:
                week += 1
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            break
    
    if tournaments_added:
        # Save the updated file
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\nSuccessfully added {len(tournaments_added)} tournaments to {save_path}")
            print("Summary:")
            for t in tournaments_added:
                print(f"  - {t['name']} (ID: {t['id']}, Week: {t['week']}, Surface: {t['surface']})")
        except Exception as e:
            print(f"Error saving file: {e}")
    else:
        print("No tournaments were added")

if __name__ == "__main__":
    add_itf_tournaments()
