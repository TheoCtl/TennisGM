from schedule import TournamentScheduler
from math import log2, ceil
import json

def main():
    scheduler = TournamentScheduler(data_path='data/default_data.json')
    
    while True:
        print(f"\n--- Week {scheduler.current_week} ---")
        print("1. View current tournaments")
        print("2. Enter tournament")
        
        # Check if all tournaments for the current week are completed
        current_tournaments = scheduler.get_current_week_tournaments()
        incomplete_tournaments = [t for t in current_tournaments if t['winner_id'] is None]

        # Only display "Advance to next week" if all tournaments are completed
        if len(incomplete_tournaments) == 0:
            print("3. Advance to next week")
            print("4. Exit")
        
        print("3. Exit")
        
        choice = input("Select an option: ")
        
        if choice == "1":
            for i, t in enumerate(current_tournaments, 1):
                if t['winner_id'] is not None:
                    winner = next((p['name'] for p in scheduler.players if p['id'] == t['winner_id']), "Unknown")
                    status = f"Winner: {winner}"
                else:
                    status = "Not completed"
                print(f"{i}. {t['name']} ({t['category']}) - {status}")
        
        elif choice == "2":
            for i, t in enumerate(current_tournaments, 1):
                print(f"{i}. {t['name']} ({t['category']})")
            
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
                # Show previous rounds results first
                if tournament['current_round'] > 0:
                    print("\nPrevious rounds results:")
                    for r in range(tournament['current_round']):
                        print(f"Round {r+1}:")
                        for m in tournament['bracket'][r]:
                            p1 = next((p['name'] for p in scheduler.players if p['id'] == m[0]), "BYE")
                            p2 = next((p['name'] for p in scheduler.players if p['id'] == m[1]), "BYE")
                            winner = next((p['name'] for p in scheduler.players if p['id'] == m[2]), None)
                            if winner:
                                print(f"  {p1} vs {p2} -> {winner}")
                
                # Display current round matches
                matches = [
                    {
                        'match_id': i,
                        'player1': next((p for p in scheduler.players if p['id'] == m[0]), None) if m[0] else None,
                        'player2': next((p for p in scheduler.players if p['id'] == m[1]), None) if m[1] else None,
                        'winner': next((p for p in scheduler.players if p['id'] == m[2]), None) if m[2] else None
                    }
                    for i, m in enumerate(tournament['active_matches'])
                ]
                print(f"\n{tournament['name']} - Round {tournament['current_round']+1} of {len(tournament['bracket'])}")
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
                    match_idx = int(match_choice) - 1
                    if match_idx < 0 or match_idx >= len(matches):
                        raise ValueError("Invalid match number")
        
                    # Simulate all matches up to and including the selected match
                    for idx in range(match_idx + 1):
                        # Refresh matches to reflect the latest state
                        matches = [
                            {
                                'match_id': i,
                                'player1': next((p for p in scheduler.players if p['id'] == m[0]), None) if m[0] else None,
                                'player2': next((p for p in scheduler.players if p['id'] == m[1]), None) if m[1] else None,
                                'winner': next((p for p in scheduler.players if p['id'] == m[2]), None) if m[2] else None
                            }
                            for i, m in enumerate(tournament['active_matches'])
                        ]

                        if matches[idx]['winner']:
                            continue  # Skip already completed matches
                        
                        winner_id = scheduler.simulate_through_match(tournament['id'], idx)
                        winner = next(p for p in scheduler.players if p['id'] == winner_id)
                        print(f"\n{winner['name']} wins match {idx + 1}!")
                    
                    # Check if the round is complete
                    if all(m['winner'] for m in matches):
                        print("\nAll matches in this round are complete!")
                        tournament['current_round'] += 1
                        if tournament['current_round'] < len(tournament['bracket']):
                            print(f"\nProceeding to Round {tournament['current_round'] + 1}...")
                        else:
                            # Tournament is complete
                            winner = next(p for p in scheduler.players if p['id'] == winner_id)
                            print(f"\nTOURNAMENT CHAMPION: {winner['name']}!")
                            tournament['winner_id'] = winner_id  # Mark tournament as complete
                            break

                except ValueError as e:
                    print(f"Invalid selection: {e}. Please enter a number between 1 and {len(matches)} or 0 to go back.")
                except IndexError as e:
                    print(f"Invalid match number: {e}. Please select between 1 and {len(matches)}")
                except Exception as e:
                    print(f"An error occurred: {str(e)}")  # Log the error details
        
        elif choice == "3":
            if len(incomplete_tournaments) > 0:
                break
            else:
                # This option will only appear if all tournaments are completed
                scheduler.assign_players_to_tournaments()
                new_week = scheduler.advance_week()
                print(f"\nAdvanced to week {new_week}")
        
        elif choice == "4":
            break

if __name__ == "__main__":
    print("Script started - calling main()")  # Debug
    main()
    print("Script finished")  # Debug