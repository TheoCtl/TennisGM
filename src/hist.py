import json

def find_tournament(tournaments, name):
    for t in tournaments:
        if t['name'] == name:
            return t
    return None

def add_to_history(save_data, player_list):
    for player in save_data[player_list]:
        name = player.get('name')
        for win in player.get('tournament_wins', []):
            tournament_name = win['name']
            year = win['year']
            tournament = find_tournament(save_data['tournaments'], tournament_name)
            if tournament is not None:
                if 'history' not in tournament:
                    tournament['history'] = []
                # Avoid duplicates
                already = any(h.get('winner') == name and h.get('year') == year for h in tournament['history'])
                if not already:
                    tournament['history'].append({'winner': name, 'year': year})

# Load save file
with open('data/save.json', 'r') as f:
    save_data = json.load(f)

add_to_history(save_data, 'players')
add_to_history(save_data, 'hall_of_fame')

# Save back to file
with open('data/save.json', 'w') as f:
    json.dump(save_data, f, indent=2)