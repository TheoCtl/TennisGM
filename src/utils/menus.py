def main_menu():
    print("\n--- Tennis GM ---")
    print("1. New Game")
    print("2. Load Game")
    print("3. Exit")
    choice = input("Select an option: ")
    return choice

def tournament_menu():
    print("\n--- Tournament ---")
    print("1. Simulate Next Round")
    print("2. View Standings")
    print("3. Back to Main Menu")
    return input("Select an option: ")