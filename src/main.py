from schedule import TournamentScheduler
from math import log2, ceil

def main():
    scheduler = TournamentScheduler()
    
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
            
            # Generate bracket if not already done
            if 'bracket' not in tournament:
                scheduler.generate_bracket(tournament['id'])
            
            while True:
                matches = scheduler.get_current_matches(tournament['id'])
                print(f"\n{tournament['name']} - Round {tournament['current_round']+1}")
                
                for i, m in enumerate(matches):
                    p1 = m['player1']['name'] if m['player1'] else "BYE"
                    p2 = m['player2']['name'] if m['player2'] else "BYE"
                    print(f"{i+1}. {p1} vs {p2}")
                
                print("\n0. Back to main menu")
                match_choice = input("Select match to simulate (or 0 to go back): ")
                
                if match_choice == "0":
                    break
                
                try:
                    match_choice = int(match_choice) - 1
                    winner_id = scheduler.simulate_match(tournament['id'], match_choice)
                    winner = next(p for p in scheduler.players if p['id'] == winner_id)
                    print(f"\n{winner['name']} wins the match!")
                    
                    # Check if tournament is complete
                    if 'winner_id' in tournament:
                        print(f"\nTOURNAMENT CHAMPION: {winner['name']}!")
                        break
                
                except (ValueError, IndexError):
                    print("Invalid selection")
        
        elif choice == "3":
            scheduler.assign_players_to_tournaments()
            new_week = scheduler.advance_week()
            print(f"\nAdvanced to week {new_week}")
        
        elif choice == "4":
            break