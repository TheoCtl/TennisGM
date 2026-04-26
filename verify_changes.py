import re
with open('src/main_tk.py') as f:
    content = f.read()
    count = content.count('Kings Cup Titles')
    print(f'✓ "Kings Cup Titles" appears {count} times in main_tk.py')

with open('src/schedule.py') as f:
    content = f.read()
    if 'pts += 60  # Most prestigious competition of the year' in content:
        print('✓ HOF weighting increased to 60 points for Kings Cup')
    else:
        print('✗ HOF weighting not found')
