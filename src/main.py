import os
from utils.menus import main_menu
from utils.json_utils import load_json, save_json, copy_default_save

def new_game():
    save_name = input("Enter a save name: ")
    save_path = f"data/saved_games/{save_name}.json"
    copy_default_save(save_path)
    print(f"New game created: {save_name}")
    return save_path

def load_game():
    save_files = os.listdir("data/saved_games")
    print("\nSaved Games:")
    for i, file in enumerate(save_files):
        print(f"{i+1}. {file.replace('.json', '')}")
    choice = int(input("Select a game: ")) - 1
    return f"data/saved_games/{save_files[choice]}"

def run():
    while True:
        choice = main_menu()
        if choice == "1":
            game_data = new_game()
        elif choice == "2":
            game_data = load_game()
        elif choice == "3":
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    run()