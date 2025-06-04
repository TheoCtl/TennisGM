import curses
import traceback
from schedule import TournamentScheduler
from ranking import RankingSystem
from sim.game_engine import GameEngine
from records import RecordsManager
ESCAPE_KEYS = {27, 46}
UP_KEYS = {curses.KEY_UP, ord('z'), ord('Z')}
DOWN_KEYS = {curses.KEY_DOWN, ord('s'), ord('S')}
PRESTIGE_ORDER = TournamentScheduler.PRESTIGE_ORDER

def main_menu(stdscr, scheduler):
    curses.curs_set(0)  # Hide the cursor
    current_row = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        if not hasattr(scheduler, 'news_feed') or not scheduler.news_feed:
            scheduler.generate_news_feed()
        try:
            stdscr.addstr(0, 0, f"└─── Year {scheduler.current_year}, Week {scheduler.current_week} ───┘", curses.A_BOLD)
            news_start_row = 2
            menu_start_row = news_start_row
            menu = ["Tournaments", "ATP Rankings", "Hall of Fame", "Achievements", "News Feed"]
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
        if key in UP_KEYS and current_row > 0:
            current_row -= 1
        elif key in DOWN_KEYS and current_row < len(menu) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            if menu[current_row] == "Achievements":
                show_achievements(stdscr, scheduler)
            elif menu[current_row] == "Tournaments":
                enter_tournament(stdscr, scheduler)
            elif menu[current_row] == "ATP Rankings":
                show_rankings(stdscr, scheduler)
            elif menu[current_row] == "Hall of Fame":
                show_hall_of_fame(stdscr, scheduler)
            elif menu[current_row] == "News Feed":
                show_news_feed(stdscr, scheduler)
            elif menu[current_row] == "Advance to next week":
                scheduler.advance_week()
                scheduler.news_feed = []
                stdscr.addstr(len(menu) + 5, 0, "Advanced to next week!", curses.A_BOLD)
                stdscr.refresh()
                stdscr.getch()
                current_row = 0
            elif menu[current_row] == "Exit":
                break
 
def show_news_feed(stdscr, scheduler):
    current_row = 0
    news = scheduler.news_feed if hasattr(scheduler, 'news_feed') else []
    section_titles = []
    section_indices = []
    # Identify section headers for navigation (lines starting with "- ")
    for idx, line in enumerate(news):
        if line.startswith("- "):
            section_titles.append(line)
            section_indices.append(idx)
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "News Feed", curses.A_BOLD)
        # Show all news, paginated if needed
        height, width = stdscr.getmaxyx()
        lines_per_page = height - 3
        start = max(0, current_row - lines_per_page // 2)
        end = min(len(news), start + lines_per_page)
        for i, line in enumerate(news[start:end], start):
            if i == current_row:
                stdscr.addstr(i - start + 2, 0, line)
            else:
                stdscr.addstr(i - start + 2, 0, line)
        stdscr.addstr(height - 1, 0, "ESC: return")
        stdscr.refresh()
        key = stdscr.getch()
        if key in ESCAPE_KEYS:
            break 

def show_achievements(stdscr, scheduler):
    current_row = 0
    achievements = scheduler.records
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "All-Time Achievements", curses.A_BOLD)
        for idx, record in enumerate(achievements):
            title = record.get("title", record.get("type", "Unknown"))
            if idx == current_row:
                stdscr.addstr(idx + 2, 0, title, curses.color_pair(1))
            else:
                stdscr.addstr(idx + 2, 0, title)
        stdscr.addstr(len(achievements) + 3, 0, "Press ESC to return, ENTER to view details.")
        stdscr.refresh()
        key = stdscr.getch()
        if key in UP_KEYS and current_row > 0:
            current_row -= 1
        elif key in DOWN_KEYS and current_row < len(achievements) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            show_record_details(stdscr, achievements[current_row])
        elif key in ESCAPE_KEYS:
            break

def show_record_details(stdscr, record):
    stdscr.clear()
    stdscr.addstr(0, 0, record.get("title", "Record Details"), curses.A_BOLD)
    if record["type"] == "most_t_wins":
        stdscr.addstr(2, 0, "Top 10 Tournament Winners:")
        for idx, entry in enumerate(record["top10"]):
            stdscr.addstr(3 + idx, 0, f"{idx+1}. {entry['name']} - {entry['t_wins']} Tournaments")
    elif record["type"] == "most_gs_wins":
        stdscr.addstr(2, 0, "Top 10 Grand Slam Winners:")
        for idx, entry in enumerate(record["top10"]):
            stdscr.addstr(3 + idx, 0, f"{idx+1}. {entry['name']} - {entry['gs_wins']} GS")
    elif record["type"] == "most_m1000_wins":
        stdscr.addstr(2, 0, "Top 10 Masters 1000 Winners:")
        for idx, entry in enumerate(record["top10"]):
            stdscr.addstr(3 + idx, 0, f"{idx+1}. {entry['name']} - {entry['m1000_wins']} Masters")
    elif record["type"] == "most_matches_won":
        stdscr.addstr(2, 0, "Top 10 Total Matches Won:")
        for idx, entry in enumerate(record["top10"]):
            stdscr.addstr(3 + idx, 0, f"{idx+1}. {entry['name']} - {entry['matches_won']} matches")
    elif record["type"].startswith("most_matches_won_"):
        surface = record["type"].replace("most_matches_won_", "").capitalize()
        stdscr.addstr(2, 0, f"Top 10 Matches Won on {surface}:")
        for idx, entry in enumerate(record["top10"]):
            stdscr.addstr(3 + idx, 0, f"{idx+1}. {entry['name']} - {entry['matches_won']} matches")
    elif record["type"] == "most_weeks_at_1":
        stdscr.addstr(2, 0, "Top 10 Most Weeks at #1:")
        for idx, entry in enumerate(record["top10"]):
            stdscr.addstr(3 + idx, 0, f"{idx+1}. {entry['name']} - {entry['weeks']} weeks")
    elif record["type"] == "most_weeks_in_16":
        stdscr.addstr(2, 0, "Top 10 Most Weeks in Top 16:")
        for idx, entry in enumerate(record["top10"]):
            stdscr.addstr(3 + idx, 0, f"{idx+1}. {entry['name']} - {entry['weeks']} weeks")
    stdscr.addstr(15, 0, "Press any key to return.")
    stdscr.refresh()
    stdscr.getch()
            
def show_hall_of_fame(stdscr, scheduler):
    current_row = 0
    search_query = ""
    searching = False
    for player in scheduler.hall_of_fame:
        player['hof_points'] = 0
        for win in player.get('tournament_wins', []):
            if win['category'] == 'Special':
                player['hof_points'] += 50
            elif win['name'] == "ATP Finals":
                player['hof_points'] += 30
            elif win['name'] == "Nextgen Finals":
                player['hof_points'] += 5
            elif win['category'] == "Grand Slam":
                player['hof_points'] += 40
            elif win['category'] == "Masters 1000":
                player['hof_points'] += 20
            elif win['category'] == "ATP 500":
                player['hof_points'] += 10
            elif win['category'] == "ATP 250":
                player['hof_points'] += 5
            elif win['category'].startswith("Challenger"):
                player['hof_points'] += 1

    # Sort by HOF points (descending) and then alphabetically
    hof_members = sorted(
        scheduler.hall_of_fame,
        key=lambda x: (-x['hof_points'], len(x.get('tournament_wins', [])))
    )
    
    hof_members = hof_members[:100]

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        try:
            stdscr.addstr(0, 0, "Hall of Fame", curses.A_BOLD)

            if search_query:
                if searching:
                    stdscr.addstr(1, 0, f"Search: {search_query}_", curses.A_UNDERLINE)
                else:
                    stdscr.addstr(1, 0, f"Search: {search_query}", curses.A_UNDERLINE)
            else:
                if searching:
                    stdscr.addstr(1, 0, f"Search: {search_query}_", curses.A_UNDERLINE)
                else:
                    stdscr.addstr(1, 0, f"Search: Press 'a' to search a player", curses.A_UNDERLINE)

            # Filter if searching
            display_hof = hof_members
            if search_query:
                display_hof = [p for p in hof_members if search_query.lower() in p['name'].lower()]

            # Display Hall of Fame members
            start_idx = max(0, current_row - 15)
            for i, player in enumerate(display_hof[start_idx:start_idx+30], start_idx+1):
                total_wins = len(player.get('tournament_wins', []))
                if i-1 == current_row:
                    stdscr.addstr(i+2-start_idx, 0, 
                        f"{i}. {player['name']}: {player['hof_points']} HOF, {total_wins} wins", 
                        curses.color_pair(1))
                else:
                    stdscr.addstr(i+2-start_idx, 0, 
                        f"{i}. {player['name']}: {player['hof_points']} HOF, {total_wins} wins")

            if height > 34 and width > 40:
                stdscr.addstr(height-1, 0, "Press ESC to return, arrows to scroll, 'a' to search")

            stdscr.refresh()

        except curses.error:
            stdscr.refresh()

        key = stdscr.getch()
        if searching:
            if key == 27:  # ESC
                searching = False
                search_query = ""
            elif key == curses.KEY_ENTER or key in [10, 13]:
                searching = False
            elif key == curses.KEY_BACKSPACE or key == 8:
                search_query = search_query[:-1]
            elif 32 <= key <= 126:# Printable characters
                if key == 46:
                    searching = False
                    search_query = ""
                else:
                    search_query += chr(key)
        else:
            if searching:
                if key == 27:  # ESC
                    searching = False
                    search_query = ""
                elif key == curses.KEY_ENTER or key in [10, 13]:
                    searching = False  # Exit search mode, keep the query/filter
                elif key == curses.KEY_BACKSPACE or key == 8:
                    search_query = search_query[:-1]
                elif 32 <= key <= 126:  # Printable characters
                    if key == 46:
                        searching = False
                        search_query = ""
                    else:
                        search_query += chr(key)
            else:
                if key == ord('a'):
                    searching = True
                    search_query = ""
                    current_row = 0
                elif key in UP_KEYS and current_row > 0:
                    current_row -= 1
                elif key in DOWN_KEYS and current_row < len(display_hof)-1:
                    current_row += 1
                elif key == curses.KEY_ENTER or key in [10, 13]:
                    if display_hof:
                        show_hof_player_details(stdscr, display_hof[current_row])
                elif key in ESCAPE_KEYS:  # ESC
                    break

def display_tournament_wins(stdscr, player, start_row=3):
    import collections
    height, width = stdscr.getmaxyx()
    wins_by_category = collections.defaultdict(lambda: collections.defaultdict(int))
    for win in player.get('tournament_wins', []):
        wins_by_category[win['category']][win['name']] += 1
    row = start_row + 1
    any_win = False
    for category in PRESTIGE_ORDER:
        if category in wins_by_category:
            if row < height - 1:
                total_in_category = sum(wins_by_category[category].values())
                stdscr.addstr(row, 0, f"└─── {category} ({total_in_category}) ───┐", curses.A_UNDERLINE)
                row += 1
            for tname, count in sorted(wins_by_category[category].items()):
                if row < height - 1:
                    stdscr.addstr(row, 2, f"- {count}x {tname}")
                    row += 1
                    any_win = True
                else:
                    row += 1
                    break
    if not any_win:
        stdscr.addstr(row, 0, "  No tournament wins yet")
        row += 1
    return row

def show_hof_player_details(stdscr, player):
    show_tournaments = False
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        stdscr.addstr(0, 0, f"┌─── {player['name']} ───┘", curses.A_BOLD)
        stdscr.addstr(1, 0, f"│ Highest Ranking: {player.get('highest_ranking', 'N/A')}")
        stdscr.addstr(2, 0, f"└─────────────────────────────────────────┐")
        numwin = len(player.get('tournament_wins'))
        hofpoints = player.get('hof_points')
        
        if not show_tournaments:
            # Achievements section
            w1 = player.get('w1')
            w16 = player.get('w16')
            t_wins = sum(1 for win in player.get('tournament_wins', []))
            m1000_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "Masters 1000")
            gs_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "Grand Slam")
            stdscr.addstr(3, 0, f"┌─── ACHIEVEMENTS ────────────────────────┘", curses.A_BOLD)
            stdscr.addstr(4, 0, f"│ Total titles: {t_wins}")
            stdscr.addstr(5, 0, f"│ Grand Slam titles: {gs_wins}")
            stdscr.addstr(6, 0, f"│ Masters 1000 titles: {m1000_wins}")
            mawn =player.get('mawn', [0,0,0,0,0])
            stdscr.addstr(7, 0, f"│ Total Matches Won (clay, grass, hard, indoor): {sum(mawn)} ({mawn[0]}, {mawn[1]}, {mawn[2]}, {mawn[3]})")
            stdscr.addstr(8, 0, f"│ Weeks at #1 : {w1}w")
            stdscr.addstr(9, 0, f"│ Weeks in Top 16 : {w16}w")
            stdscr.addstr(10, 0, f"└─────────────────────┘")
            stdscr.addstr(height - 1, 0, "Press 'T' to view tournaments won, ESC to return.")
        else:
            if numwin < 10:
                if hofpoints < 10:
                    stdscr.addstr(3, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ────────────────────┘", curses.A_BOLD)
                elif 10 <= hofpoints < 100:
                    stdscr.addstr(3, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ───────────────────┘", curses.A_BOLD)
                else:
                    stdscr.addstr(3, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ──────────────────┘", curses.A_BOLD)
            elif 10 <= numwin < 100:
                if hofpoints < 10:
                    stdscr.addstr(3, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ───────────────────┘", curses.A_BOLD)
                elif 10 <= hofpoints < 100:
                    stdscr.addstr(3, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ──────────────────┘", curses.A_BOLD)
                elif 100 <= hofpoints < 1000:
                    stdscr.addstr(3, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ─────────────────┘", curses.A_BOLD)
                else:
                    stdscr.addstr(3, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ────────────────┘", curses.A_BOLD)
            else:
                if hofpoints < 10:
                    stdscr.addstr(3, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ──────────────────┘", curses.A_BOLD)
                elif 10 <= hofpoints < 100:
                    stdscr.addstr(3, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ─────────────────┘", curses.A_BOLD)
                elif 100 <= hofpoints < 1000:
                    stdscr.addstr(3, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ────────────────┘", curses.A_BOLD)
                else:
                    stdscr.addstr(3, 0, f"┌─ WINS ({numwin} W, {hofpoints} HOF) ────────────────┘", curses.A_BOLD)
            display_tournament_wins(stdscr, player, start_row=3)
            stdscr.addstr(height - 1, 0, "Press 'T' to view achievements, ESC to return.")

        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord('t'), ord('T')):
            show_tournaments = not show_tournaments
        elif key in ESCAPE_KEYS:
            break

def show_player_details(stdscr, scheduler, player):
    show_tournaments = False
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        player['hof_points'] = 0
        skills = player['skills']
        if skills:
            ovr = round(sum(skills.values()) / len(skills))
        else:
            ovr = "N/A"
        for win in player.get('tournament_wins', []):
            if win['category'] == "Special":
                player['hof_points'] += 50
            elif win['name'] == "ATP Finals":
                player['hof_points'] += 30
            elif win['name'] == "Nextgen Finals":
                player['hof_points'] += 5
            elif win['category'] == "Grand Slam":
                player['hof_points'] += 40
            elif win['category'] == "Masters 1000":
                player['hof_points'] += 20
            elif win['category'] == "ATP 500":
                player['hof_points'] += 10
            elif win['category'] == "ATP 250":
                player['hof_points'] += 5
            elif win['category'].startswith("Challenger"):
                player['hof_points'] += 1
        stdscr.addstr(0, 0, f"┌─── {player['name']} ───┘", curses.A_BOLD)
        stdscr.addstr(1, 0, f"│ Rank: {player.get('rank', 'N/A')} ¦ Highest Ranking: {player.get('highest_ranking', 'N/A')}")
        stdscr.addstr(2, 0, f"│ {player.get('age', 'N/A')}yo, {player.get('hand', 'N/A')}-handed")
        stdscr.addstr(3, 0, f"│ Favorite surface: {player.get('favorite_surface', 'N/A')}")
        stdscr.addstr(4, 0, f"└───────────────────────┐")
        stdscr.addstr(5,0, f"┌─── SKILLS ({ovr}ovr) ────┘", curses.A_BOLD)
        if 'skills' in player:
            skills = player['skills']
            stdscr.addstr(6, 0, f"│ Serve: {skills.get('serve', 'N/A')}")
            stdscr.addstr(7, 0, f"│ Forehand: {skills.get('forehand', 'N/A')}")
            stdscr.addstr(8, 0, f"│ Backhand: {skills.get('backhand', 'N/A')}")
            stdscr.addstr(9, 0, f"│ Speed: {skills.get('speed', 'N/A')}")
            stdscr.addstr(10, 0, f"│ Stamina: {skills.get('stamina', 'N/A')}")            
            stdscr.addstr(11, 0, f"│ Straight: {skills.get('straight', 'N/A')}")
            stdscr.addstr(12, 0, f"│ Cross: {skills.get('cross', 'N/A')}")
        stdscr.addstr(13, 0, f"└──────────────────────────┐")
        
        if not show_tournaments:
            w1 = player.get('w1')
            w16 = player.get('w16')
            t_wins = sum(1 for win in player.get('tournament_wins', []))
            m1000_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "Masters 1000")
            gs_wins = sum(1 for win in player.get('tournament_wins', []) if win['category'] == "Grand Slam")
            stdscr.addstr(14, 0, f"┌─── ACHIEVEMENTS ─────────┘", curses.A_BOLD)
            stdscr.addstr(15, 0, f"│ Total titles: {t_wins}")
            stdscr.addstr(16, 0, f"│ Grand Slam titles: {gs_wins}")
            stdscr.addstr(17, 0, f"│ Masters 1000 titles: {m1000_wins}")
            mawn =player.get('mawn', [0,0,0,0,0])
            stdscr.addstr(18, 0, f"│ Total Matches Won (clay, grass, hard, indoor): {sum(mawn)} ({mawn[0]}, {mawn[1]}, {mawn[2]}, {mawn[3]})")
            stdscr.addstr(19, 0, f"│ Weeks at #1 : {w1}w")
            stdscr.addstr(20, 0, f"│ Weeks in Top 16 : {w16}w")
            stdscr.addstr(21, 0, f"└─────────────────────┘")
            stdscr.addstr(height - 1, 0, "Press 'T' to view tournaments won, ESC to return.")
        else:
            numwin = len(player.get('tournament_wins'))
            hofpoints = player.get('hof_points')
            if numwin < 10:
                if hofpoints < 10:
                    stdscr.addstr(14, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ─────┘", curses.A_BOLD)
                elif 10 <= hofpoints < 100:
                    stdscr.addstr(14, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ────┘", curses.A_BOLD)
                else:
                    stdscr.addstr(14, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ───┘", curses.A_BOLD)
            elif 10 <= numwin < 100:
                if hofpoints < 10:
                    stdscr.addstr(14, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ────┘", curses.A_BOLD)
                elif 10 <= hofpoints < 100:
                    stdscr.addstr(14, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ───┘", curses.A_BOLD)
                elif 100 <= hofpoints < 1000:
                    stdscr.addstr(14, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ──┘", curses.A_BOLD)
                else:
                    stdscr.addstr(14, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ─┘", curses.A_BOLD)
            else:
                if hofpoints < 10:
                    stdscr.addstr(14, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ───┘", curses.A_BOLD)
                elif 10 <= hofpoints < 100:
                    stdscr.addstr(14, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ──┘", curses.A_BOLD)
                elif 100 <= hofpoints < 1000:
                    stdscr.addstr(14, 0, f"┌── WINS ({numwin} W, {hofpoints} HOF) ─┘", curses.A_BOLD)
                else:
                    stdscr.addstr(14, 0, f"┌─ WINS ({numwin} W, {hofpoints} HOF) ─┘", curses.A_BOLD)
            display_tournament_wins(stdscr, player, start_row=14)
            stdscr.addstr(height - 1, 0, "Press 'T' to view achievements, ESC to return.")
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord('t'), ord('T')):
            show_tournaments = not show_tournaments
        elif key in ESCAPE_KEYS:
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
        
        if search_query:
            if searching:
                stdscr.addstr(1, 0, f"Search: {search_query}_", curses.A_UNDERLINE)
            else:
                stdscr.addstr(1, 0, f"Search: {search_query}", curses.A_UNDERLINE)
        else:
            if searching:
                stdscr.addstr(1, 0, f"Search: {search_query}_", curses.A_UNDERLINE)
            else:
                stdscr.addstr(1, 0, f"Search: Press 'a' to search a player", curses.A_UNDERLINE)
        
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
        
        stdscr.addstr(34, 0, "Press ESC to return, arrows to scroll, 'a' to search")
        stdscr.refresh()
        
        key = stdscr.getch()
        if searching:
            if key == 27:  # ESC
                searching = False
                search_query = ""
            elif key == curses.KEY_ENTER or key in [10, 13]:
                searching = False
            elif key == curses.KEY_BACKSPACE or key == 8:
                search_query = search_query[:-1]
            elif 32 <= key <= 126:  # Printable characters
                if key == 46:
                    searching = False
                    search_query = ""
                else:
                    search_query += chr(key)
        else:
            if searching:
                if key == 27:  # ESC
                    searching = False
                    search_query = ""
                elif key == curses.KEY_ENTER or key in [10, 13]:
                    searching = False  # Exit search mode, keep the query/filter
                elif key == curses.KEY_BACKSPACE or key == 8:
                    search_query = search_query[:-1]
                elif 32 <= key <= 126:  # Printable characters
                    if key == 46:
                        searching = False
                        search_query = ""
                    else:
                        search_query += chr(key)
            else:
                if key == ord('a'):
                    current_row = 0
                    searching = True
                    search_query = ""
                elif key in UP_KEYS and current_row > 0:
                    current_row -= 1
                elif key in DOWN_KEYS and current_row < len(display_players)-1:
                    current_row += 1
                elif key == curses.KEY_ENTER or key in [10, 13]:
                    if display_players and current_row < len(display_players):
                        player = display_players[current_row][0]
                        show_player_details(stdscr, scheduler, player)
                elif key in ESCAPE_KEYS:  # ESC
                    break

def enter_tournament(stdscr, scheduler):
    current_tournaments = scheduler.get_current_week_tournaments()
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Press ENTER to manage, '+' to simulate entire tournament")

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
        if key in UP_KEYS and current_row > 0:
            current_row -= 1
        elif key in DOWN_KEYS and current_row < len(current_tournaments) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            tournament = current_tournaments[current_row]
            manage_tournament(stdscr, scheduler, tournament)
        elif key == ord('+'):
            tournament = current_tournaments[current_row]
            if tournament.get('winner_id'):
                stdscr.addstr(len(current_tournaments) + 4, 0, "Tournament already completed!")
                stdscr.refresh()
                stdscr.getch()
            else:
                stdscr.addstr(len(current_tournaments) + 4, 0, "Simulating tournament...")
                stdscr.refresh()
                winner_id = scheduler.simulate_entire_tournament(tournament['id'])
                winner = next((p for p in scheduler.players if p['id'] == winner_id), None)
                if winner:
                    stdscr.addstr(len(current_tournaments) + 5, 0, 
                                f"Tournament complete! Winner: {winner['name']}")
                else:
                    stdscr.addstr(len(current_tournaments) + 5, 0, 
                                "Tournament complete! (Winner unknown)")
                stdscr.refresh()
                stdscr.getch()
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

        # Calculate how many lines are available for matches (excluding header and footer)
        lines_for_matches = height - 3  # 1 for header, 1 for footer, 1 for buffer

        # Find the index in content where matches start
        matches_start_idx = 0
        for idx, line in enumerate(content):
            if line.startswith("Round"):
                matches_start_idx = idx + 1
                break

        # Only scroll the matches section, keep header/footer always visible
        num_matches = len(matches)
        if current_row < start_line:
            start_line = current_row
        elif current_row >= start_line + lines_for_matches:
            start_line = current_row - lines_for_matches + 1

        # Build visible content: header + visible matches + footer
        visible_content = content[:matches_start_idx]  # header and previous rounds
        visible_content += content[matches_start_idx + start_line : matches_start_idx + min(start_line + lines_for_matches, num_matches)]
        visible_content += content[matches_start_idx + num_matches:]  # footer

        for i, line_content in enumerate(visible_content):
            if i + 1 >= height:
                break  # Don't write past the bottom of the screen
            stdscr.addstr(i + 1, 0, line_content[:width - 1])

        stdscr.refresh()

        # Handle user input
        key = stdscr.getch()
        if key in UP_KEYS:
            if current_row > 0:
                current_row -= 1
        elif key in DOWN_KEYS:
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
        
                # Display the match log line by line
                stdscr.clear()
                screens = output.split("\n\n\na")
                for screen in screens:
                    stdscr.clear()
                    # Split the screen into lines and print each, respecting terminal height
                    for i, line in enumerate(screen.strip().split('\n')):
                            if i >= stdscr.getmaxyx()[0] - 1:
                                break  # Prevent writing beyond screen bounds
                            stdscr.addstr(i, 0, line[:stdscr.getmaxyx()[1] - 1])
                    stdscr.refresh()
                    stdscr.getch()
        
                # Update the match result in the tournament
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