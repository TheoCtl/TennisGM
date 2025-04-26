import json
import os

def load_json(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json(data, file_path):
    """Save JSON data to a file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def copy_default_save(save_path):
    """Copy default_data.json to a new save file."""
    default_data = load_json(os.path.join('data', 'default_data.json'))
    save_json(default_data, save_path)