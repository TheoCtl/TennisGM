import curses
import traceback
from schedule import TournamentScheduler
from ranking import RankingSystem
ESCAPE_KEYS = {27, 46}

def main_menu(stdscr, scheduler):
    curses.curs_set(0)  # Hide the cursor
    current_row = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        if not hasattr(scheduler, 'news_feed') or not scheduler.news_feed:
            scheduler.generate_news_feed()
        try:
            stdscr.addstr(0, 0, f"--- Year {scheduler.current_year}, Week {scheduler.current_week} ---", curses.A_BOLD)
            news_start_row = 2
            max_news_items = min(12, (height - 10) // 2)
            if scheduler.news_feed:
                stdscr.addstr(news_start_row, 0, "News:", curses.A_UNDERLINE)
            news_lines_used = 0
            for i, news in enumerate(scheduler.news_feed[:max_news_items]):
                stdscr.addstr(news_start_row + i + 1, 0, f"- {news}")
                news_lines_used += 1
            menu_start_row = news_start_row + (2 if scheduler.news_feed else 0) + news_lines_used
            menu = ["View current tournaments", "Enter tournament", "See ATP Rankings", "See Hall of Fame"]
            # Check if all tournaments for the current week are completed
            current_tournaments = scheduler.get_current_week_tournaments()
            incomplete_tournaments = [t for t in current_tournaments if t['winner_id'] is None]
            if len(incomplete_tournaments) == 0:
                menu.append("Advance to next week")
            menu.append("Exit")
            for idx, row in enumerate(menu):
                if idx == current_row:
                    stdscr.addstr(menu_start_row + idx, 0, row, curses.color_pair(1))
                else:
                    stdscr.addstr(menu_start_row + idx, 0, row)
            stdscr.refresh()
        except curses.error:
            stdscr.refresh()
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
            elif menu[current_row] == "See Hall of Fame":
                show_hall_of_fame(stdscr, scheduler)
            elif menu[current_row] == "Advance to next week":
                scheduler.advance_week()
                scheduler.news_feed = []
                stdscr.addstr(len(menu) + max_news_items + 5, 0, "Advanced to next week!", curses.A_BOLD)
                stdscr.refresh()
                stdscr.getch()
            elif menu[current_row] == "Exit":
                break
            
def show_hall_of_fame(stdscr, scheduler):
    current_row = 0
    hof_members = sorted(
        scheduler.hall_of_fame,
        key=lambda x: (
            -sum(1 for win in x.get('tournament_wins', []) if win['category'] == "Grand Slam"),
            -sum(1 for win in x.get('tournament_wins', []) if win['category'] == "Masters 1000"),
            -sum(1 for win in x.get('tournament_wins', []) if win['category'] == "ATP 500"),
            -sum(1 for win in x.get('tournament_wins', []) if win['category'] == "ATP 250"),
            -sum(1 for win in x.get('tournament_wins', []) if win['category'].startswith("Challenger")),
            x['name'].lower()
        )
    )
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        try:
            stdscr.addstr(0, 0, "Hall of Fame", curses.A_BOLD)
            stdscr.addstr(1, 0, "Players are sorted by total wins (Grand Slams > Masters > ATP 500 > ATP 250 > Challengers)")
            
            # Display Hall of Fame members
            start_idx = max(0, current_row - 15)
            for i, player in enumerate(hof_members[start_idx:start_idx+30], start_idx+1):
                total_wins = len(player.get('tournament_wins', []))
                gs_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "Grand Slam")
                masters_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "Masters 1000")
                atp500_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "ATP 500")
                atp250_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "ATP 250")
                chal_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'].startswith("Challenger"))
                
                if i-1 == current_row:
                    stdscr.addstr(i+2-start_idx, 0, 
                        f"{i}. {player['name']}: {total_wins} wins ({gs_wins} GS, {masters_wins} M1000, {atp500_wins} ATP500, {atp250_wins} ATP250, {chal_wins} Challengers)", 
                        curses.color_pair(1))
                else:
                    stdscr.addstr(i+2-start_idx, 0, 
                        f"{i}. {player['name']}: {total_wins} wins ({gs_wins} GS, {masters_wins} M1000, {atp500_wins} ATP500, {atp250_wins} ATP250, {chal_wins} Challengers)")
            
            if height > 34 and width > 40:
                stdscr.addstr(height-1, 0, "Press ESC to return, arrows to scroll")
            
            stdscr.refresh()
            
        except curses.error:
            stdscr.refresh()
        
        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(hof_members)-1:
            current_row += 1
        elif key in ESCAPE_KEYS:  # ESC
            break

def show_player_details(stdscr, scheduler, player):
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        stdscr.addstr(0, 0, f"Player: {player['name']}", curses.A_BOLD)
        stdscr.addstr(1, 0, f"Rank: {player.get('rank', 'N/A')}")
        stdscr.addstr(2, 0, f"Age: {player.get('age', 'N/A')}")
        stdscr.addstr(3, 0, f"Hand: {player.get('hand', 'N/A')}")
        stdscr.addstr(4, 0, f"Surface: {player.get('favorite_surface', 'N/A')}")
        stdscr.addstr(6,0, "Player Stats:", curses.A_BOLD)
        if 'skills' in player:
            skills = player['skills']
            stdscr.addstr(7, 0, f"  Serve: {skills.get('serve', 'N/A')}")
            stdscr.addstr(8, 0, f"  Forehand: {skills.get('forehand', 'N/A')}")
            stdscr.addstr(9, 0, f"  Backhand: {skills.get('backhand', 'N/A')}")
            stdscr.addstr(10, 0, f"  Speed: {skills.get('speed', 'N/A')}")
            stdscr.addstr(11, 0, f"  Stamina: {skills.get('stamina', 'N/A')}")            
            stdscr.addstr(12, 0, f"  Straight: {skills.get('straight', 'N/A')}")
            stdscr.addstr(13, 0, f"  Cross: {skills.get('cross', 'N/A')}")

            
        stdscr.addstr(14,0, "Tournament History:", curses.A_BOLD)
        if 'tournament_wins' in player and player['tournament_wins']:
            sorted_wins = sorted(player['tournament_wins'], 
                key=lambda x: (
                    scheduler.PRESTIGE_ORDER.index(x['category'])
                    if x['category'] in scheduler.PRESTIGE_ORDER 
                    else len(scheduler.PRESTIGE_ORDER), 
                    x['name'].lower()
                ))
            current_category = None
            row = 15
            for win in sorted_wins:
                if win in sorted_wins:
                    if win['category'] != current_category:
                        if row < height -1:
                            stdscr.addstr(row, 0, f" {win['category']}:", curses.A_UNDERLINE)
                            row +=1
                        current_category = win['category']
                        
                    if row < height -1:
                        stdscr.addstr(row, 2, f"{win['year']}: {win['name']}")
                        row +=1
        else:
            stdscr.addstr(15, 0, "  No tournament wins yet")
        stdscr.addstr(height - 1, 0, "Press any key to return to ATP Rankings.")
        stdscr.refresh()
        
        key = stdscr.getch()
        if key:
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
            elif key == curses.KEY_ENTER or key in [10, 13]:
                if display_players and current_row < len(display_players):
                    player = display_players[current_row][0]
                    show_player_details(stdscr, scheduler, player)
            elif key in ESCAPE_KEYS:  # ESC
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
        stdscr.addstr(idx + 1, 0, f"{idx}. {t['name']} ({t['category']}, {t['surface']}) - {status}")

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
                stdscr.addstr(idx + 1, 0, f"{t['name']} ({t['category']}, {t['surface']})", curses.color_pair(1))
            else:
                stdscr.addstr(idx + 1, 0, f"{t['name']} ({t['category']}, {t['surface']})")

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
        elif key in ESCAPE_KEYS:
            break

def manage_tournament(stdscr, scheduler, tournament):
    current_row = 0
    start_line = 0  # Track the first visible line for scrolling
    show_previous_rounds = False

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Managing Tournament: {tournament['name']} ({tournament['category']}, {tournament['surface']})", curses.A_BOLD)

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
        elif key in ESCAPE_KEYS:
            break

def main(stdscr):
    try:
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlighted text
        scheduler = TournamentScheduler()
        try:
            main_menu(stdscr, scheduler)
        finally:
            scheduler.save_game()
            print("Game saved succesfully")
    except Exception as e:
        # Print the error and stack trace to help debug
        with open("error_log.txt", "w") as f:
            f.write(traceback.format_exc())
        stdscr.addstr(0, 0, "An error occurred. Check error_log.txt for details.")
        stdscr.refresh()
        stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)