#!/usr/bin/env python
import sys
sys.path.insert(0, 'src')
from newgen import NewGenGenerator
import random

gen = NewGenGenerator('data/names.json')
print('Sample full names (First Last):')
for _ in range(10):
    first = random.choice(gen.name_data["first_names"])
    last = gen.generate_procedural_last_name()
    print(f'  - {first} {last}')
