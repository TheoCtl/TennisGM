from schedule import TournamentScheduler
from math import log2, ceil
import json

def main():
    scheduler = TournamentScheduler(data_path='data/default_data.json')
    
    while True:
        print(f"\n--- Week {scheduler.current_week} ---")
        print("1. View current tournaments")
        print("2. Enter tournament")
        print("3. Advance to next week")
        print("4. Exit")
        
        choice = input("Select an option: ")
        
        if choice == "1":
            current_tournaments = scheduler.get_current_week_tournaments()
            for i, t in enumerate(current_tournaments, 1):
                status = "Completed" if 'winner_id' in t else f"Round {t.get('current_round', 0)+1}/{int(ceil(log2(t['draw_size'])))}"
                print(f"{i}. {t['name']} - {status}")
        
        elif choice == "2":
            current_tournaments = scheduler.get_current_week_tournaments()
            for i, t in enumerate(current_tournaments, 1):
                print(f"{i}. {t['name']}")
            
            tour_choice = int(input("Select tournament: ")) - 1
            tournament = current_tournaments[tour_choice]
            
            # First ensure players are assigned
            if 'participants' not in tournament:
                print("Assigning players to tournament...")
                scheduler.assign_players_to_tournaments()  # This will populate participants
        
            # Then generate bracket
            if 'bracket' not in tournament:
                print("Generating tournament bracket...")
                scheduler.generate_bracket(tournament['id'])
            
            while True:
                matches = [
                    {
                        'match_id' : 1,
                        'player1' : next((p for p in scheduler.players if p['id'] == m[0]), None) if m[0] else None,
                        'player2' : next((p for p in scheduler.players if p['id'] == m[1]), None) if m[1] else None,
                        'winner' : next((p for p in scheduler.players if p['id'] == m[2]), None) if m[2] else None
                    }
                    for i, m in enumerate(tournament['active_matches'])
                ]
                print(f"\n{tournament['name']} - Round {tournament['current_round']+1}")
    
                # Display current matches with proper numbering
                for i, m in enumerate(matches, 1):
                    p1 = m['player1']['name'] if m['player1'] else "BYE"
                    p2 = m['player2']['name'] if m['player2'] else "BYE"
                    status = f" -> {m['winner']['name']}" if m['winner'] else ""
                    print(f"{i}. {p1} vs {p2}{status}")
    
                print("\n0. Back to main menu")
                match_choice = input("Select match to simulate (or 0 to go back): ")
    
                if match_choice == "0":
                    break
    
                try:
                    match_choice = int(match_choice)
                    if not 1 <= match_choice <= len(matches):
                        raise ValueError("Invalid match number")
        
                    # Adjust for 0-based index
                    match_idx = match_choice - 1
        
                    # Check if match is already completed
                    if matches[match_idx].get('winner'):
                        print("This match has already been completed!")
                        continue
            
                    winner_id = scheduler.simulate_match(tournament['id'], match_idx)
                    winner = next(p for p in scheduler.players if p['id'] == winner_id)
                    print(f"\n{winner['name']} wins the match!")
        
                    # Check tournament completion
                    if 'winner_id' in tournament:
                        winner = next(p for p in scheduler.players if p['id'] == tournament['winner_id'])
                        print(f"\nTOURNAMENT CHAMPION: {winner['name']}!")
                        break
    
                except ValueError as e:
                    print(f"Invalid selection: {e}. Please enter a number between 1 and {len(matches)} or 0 to go back.")
                except IndexError:
                    print(f"Invalid match number. Please select between 1 and {len(matches)}")
                except Exception as e:
                    print(f"An error occurred: {str(e)}")
        
        elif choice == "3":
            scheduler.assign_players_to_tournaments()
            new_week = scheduler.advance_week()
            print(f"\nAdvanced to week {new_week}")
        
        elif choice == "4":
            break

if __name__ == "__main__":
    print("Script started - calling main()")  # Debug
    main()
    print("Script finished")  # Debug