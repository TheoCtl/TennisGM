import curses
import traceback
from schedule import TournamentScheduler
from ranking import RankingSystem

def main_menu(stdscr, scheduler):
    curses.curs_set(0)  # Hide the cursor
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, f"--- Year {scheduler.current_year}, Week {scheduler.current_week} ---", curses.A_BOLD)
        menu = ["View current tournaments", "Enter tournament", "See ATP Rankings"]

        # Check if all tournaments for the current week are completed
        current_tournaments = scheduler.get_current_week_tournaments()
        incomplete_tournaments = [t for t in current_tournaments if t['winner_id'] is None]
        if len(incomplete_tournaments) == 0:
            menu.append("Advance to next week")
        menu.append("Exit")

        # Display menu options
        for idx, row in enumerate(menu):
            if idx == current_row:
                stdscr.addstr(idx + 2, 0, row, curses.color_pair(1))  # Highlight current row
            else:
                stdscr.addstr(idx + 2, 0, row)

        stdscr.refresh()

        # Handle user input
        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            if menu[current_row] == "View current tournaments":
                view_tournaments(stdscr, scheduler)
            elif menu[current_row] == "Enter tournament":
                enter_tournament(stdscr, scheduler)
            elif menu[current_row] == "See ATP Rankings":
                show_rankings(stdscr, scheduler)
            elif menu[current_row] == "Advance to next week":
                scheduler.advance_week()
                stdscr.addstr(len(menu) + 3, 0, "Advanced to next week!", curses.A_BOLD)
                stdscr.refresh()
                stdscr.getch()
            elif menu[current_row] == "Exit":
                break

def show_rankings(stdscr, scheduler):
    current_row = 0
    search_query = ""
    searching = False
    
    ranked_players = scheduler.ranking_system.get_ranked_players(
        scheduler.players,
        scheduler.current_date
    )
    
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "ATP Rankings", curses.A_BOLD)
        
        if searching:
            stdscr.addstr(1, 0, f"Search: {search_query}_", curses.A_UNDERLINE)
        
        # Filter if searching
        display_players = ranked_players
        if search_query:
            display_players = [p for p in ranked_players if search_query.lower() in p[0]['name'].lower()]
        
        # Display players (top 50 or filtered results)
        start_idx = max(0, current_row - 15)  # Keep some context above
        for i, (player, points) in enumerate(display_players[start_idx:start_idx+30], start_idx+1):
            if i-1 == current_row:
                stdscr.addstr(i+2-start_idx, 0, f"{i}. {player['name']}: {points} pts", curses.color_pair(1))
            else:
                stdscr.addstr(i+2-start_idx, 0, f"{i}. {player['name']}: {points} pts")
        
        stdscr.addstr(34, 0, "Press ESC to return, arrows to scroll, 's' to search")
        stdscr.refresh()
        
        key = stdscr.getch()
        if searching:
            if key == 27:  # ESC
                searching = False
                search_query = ""
            elif key == curses.KEY_BACKSPACE or key == 127:
                search_query = search_query[:-1]
            elif 32 <= key <= 126:  # Printable characters
                search_query += chr(key)
        else:
            if key == ord('s'):
                searching = True
                search_query = ""
            elif key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(display_players)-1:
                current_row += 1
            elif key == 27:  # ESC
                break

def view_tournaments(stdscr, scheduler):
    stdscr.clear()
    stdscr.addstr(0, 0, "Current Tournaments:", curses.A_BOLD)
    current_tournaments = scheduler.get_current_week_tournaments()

    for idx, t in enumerate(current_tournaments, 1):
        if t['winner_id'] is not None:
            winner = next((p['name'] for p in scheduler.players if p['id'] == t['winner_id']), "Unknown")
            # Fetch the final score from the tournament data
            status = f"Winner: {winner}"
        else:
            status = "Not completed"
        stdscr.addstr(idx + 1, 0, f"{idx}. {t['name']} ({t['category']}) - {status}")

    stdscr.addstr(len(current_tournaments) + 3, 0, "Press any key to return to the main menu.")
    stdscr.refresh()
    stdscr.getch()

def enter_tournament(stdscr, scheduler):
    current_tournaments = scheduler.get_current_week_tournaments()
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Select a Tournament:", curses.A_BOLD)

        # Display tournaments
        for idx, t in enumerate(current_tournaments):
            if idx == current_row:
                stdscr.addstr(idx + 1, 0, f"{t['name']} ({t['category']})", curses.color_pair(1))
            else:
                stdscr.addstr(idx + 1, 0, f"{t['name']} ({t['category']})")

        stdscr.addstr(len(current_tournaments) + 2, 0, "Press ESC to exit menu.")
        stdscr.refresh()

        # Handle user input
        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(current_tournaments) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            tournament = current_tournaments[current_row]
            manage_tournament(stdscr, scheduler, tournament)
        elif key == 27:
            break

def manage_tournament(stdscr, scheduler, tournament):
    current_row = 0
    start_line = 0  # Track the first visible line for scrolling
    show_previous_rounds = False

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Managing Tournament: {tournament['name']} ({tournament['category']})", curses.A_BOLD)

        # Ensure players are assigned
        if 'participants' not in tournament:
            scheduler.assign_players_to_tournaments()

        # Generate bracket if not already generated
        if 'bracket' not in tournament:
            scheduler.generate_bracket(tournament['id'])

        # Prepare content to display
        content = []
        if show_previous_rounds:
            content.append("Previous Rounds Results: (Press 'p' to hide)")
            if tournament['current_round'] > 0:
                for r in range(tournament['current_round']):
                    content.append(f"Round {r + 1}:")
                    for m in tournament['bracket'][r]:
                        p1 = next((f"{p['name']} ({p['rank']})" for p in scheduler.players if p['id'] == m[0]), "BYE")
                        p2 = next((f"{p['name']} ({p['rank']})" for p in scheduler.players if p['id'] == m[1]), "BYE")
                        winner = next((f"{p['name']} ({p['rank']})" for p in scheduler.players if p['id'] == m[2]), None)
                        final_score = m[3] if len(m) > 3 else "N/A"
                        if winner:
                            content.append(f"  {p1} vs {p2} -> {winner} | Score: {final_score}")
                        else:
                            content.append(f"  {p1} vs {p2}")
        else:
            content.append("Press 'p' to show previous rounds results.")

        content.append(f"Round {tournament['current_round'] + 1} Matches:")
        matches = scheduler.get_current_matches(tournament['id'])
        for idx, match in enumerate(matches):
            p1 = f"{match['player1']['name']} ({match['player1']['rank']})" if match['player1'] else "BYE"
            p2 = f"{match['player2']['name']} ({match['player2']['rank']})" if match['player2'] else "BYE"
            if match['winner']:
                final_score = tournament['active_matches'][idx][3] if len(tournament['active_matches'][idx]) == 4 else "N/A"
                status = f" -> {match['winner']['name']} ({match['winner']['rank']}) | Score: {final_score}"
            else:
                status = ""
            if idx == current_row:
                content.append(f"{idx + 1}. {p1} vs {p2}{status} *")
            else:
                content.append(f"{idx + 1}. {p1} vs {p2}{status}")

        content.append("Press ESC to exit menu, Enter to simulate a match or 'w' to watch it.")

        # Get terminal dimensions
        height, width = stdscr.getmaxyx()

        #Adjust start_line to ensure the current row is visible
        if current_row < start_line:
            start_line = current_row
        elif current_row >= start_line + height - 2:
            start_line = current_row - height + 2

        # Display visible content
        visible_content = content[start_line:start_line + height - 1]
        for i, line_content in enumerate(visible_content):
            stdscr.addstr(i + 1, 0, line_content[:width])  # Ensure the line fits within the terminal width

        stdscr.refresh()

        # Handle user input
        key = stdscr.getch()
        if key == curses.KEY_UP:
            if current_row > 0:
                current_row -= 1
        elif key == curses.KEY_DOWN:
            if current_row < len(matches) - 1:
                current_row += 1
        elif key == ord('p'):
            show_previous_rounds = not show_previous_rounds
        elif key == curses.KEY_ENTER or key in [10, 13]:
            # Simulate the selected match
            match = matches[current_row]
            if match['winner']:
                stdscr.addstr(height - 1, 0, "Match already completed. Press any key to continue.")
                stdscr.refresh()
                stdscr.getch()
            else:
                winner_id = scheduler.simulate_through_match(tournament['id'], current_row)
                winner = next(p for p in scheduler.players if p['id'] == winner_id)
                stdscr.addstr(height - 1, 0, f"{winner['name']} wins the match! Press any key to continue.")
                if all(len(m) == 3 for m in tournament['active_matches']):
                    current_row = 0
                stdscr.refresh()
                stdscr.getch()

                # Refresh matches and rebuild content
                matches = scheduler.get_current_matches(tournament['id'])
                content = []  # Rebuild content
        elif key == ord('w'):
            # Watch the selected match
            match = matches[current_row]
            if match['winner']:
                stdscr.addstr(height - 1, 0, "Match already completed. Press any key to continue.")
                stdscr.refresh()
                stdscr.getch()
            else:
                # Initialize the game engine
                player1 = match['player1']
                player2 = match['player2']
        
                # Redirect print statements to a buffer we can display
                import sys
                from io import StringIO
                old_stdout = sys.stdout
                sys.stdout = mystdout = StringIO()
        
                # Simulate the match while capturing output
                winner_id = scheduler.simulate_through_match(tournament['id'], current_row)
        
                # Restore stdout
                sys.stdout = old_stdout
        
                # Get the captured output and split into lines
                output = mystdout.getvalue()
                lines = output.split('\n')
        
                # Display the match log line by line
                stdscr.clear()
                for i, line in enumerate(lines):
                    if i >= 1:  # Prevent writing beyond screen bounds
                        stdscr.addstr(height - 2, 0, "-- Press any key to continue --")
                        stdscr.refresh()
                        stdscr.getch()
                        stdscr.clear()
                        i = 0  # Reset counter for new screen
                
                    stdscr.addstr(i, 0, line)
                    stdscr.refresh()
                    curses.napms(500)
        
                # Update the match result in the tournament
                scheduler.update_match_result(tournament['id'], current_row, winner_id)
                winner = next(p for p in scheduler.players if p['id'] == winner_id)
        
                # Prompt to return to tournament view
                stdscr.addstr(height - 1, 0, "Match complete! Press any key to continue...")
                if all(len(m) == 3 for m in tournament['active_matches']):
                    current_row = 0
                stdscr.refresh()
                stdscr.getch()
                matches = scheduler.get_current_matches(tournament['id'])
                content = []
        elif key == 27:
            break

def main(stdscr):
    try:
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlighted text
        scheduler = TournamentScheduler(data_path='data/default_data.json')
        main_menu(stdscr, scheduler)
    except Exception as e:
        # Print the error and stack trace to help debug
        with open("error_log.txt", "w") as f:
            f.write(traceback.format_exc())
        stdscr.addstr(0, 0, "An error occurred. Check error_log.txt for details.")
        stdscr.refresh()
        stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)