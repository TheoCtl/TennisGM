import json
from collections import defaultdict
from statistics import mean, median

# Load the save file
with open('data/save.json', 'r') as f:
    data = json.load(f)

tournaments = data.get('tournaments', [])
clay = 0
grass = 0
indoor = 0
hard = 0
special = 0

for tournament in tournaments:
    category = tournament.get('category')
    if category == 'Split':
        surface = tournament.get('surface')
        if surface == 'clay':
            clay += 1
        elif surface == 'grass':
            grass += 1
        elif surface == 'indoor':
            indoor += 1
        elif surface == 'hard':
            hard += 1
        else:
            special += 1
        
print(f"clay: {clay}, grass: {grass}, indoor: {indoor}, hard: {hard}, special: {special}")