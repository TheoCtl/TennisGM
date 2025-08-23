import json
import math
import random
import shutil
import sys
from datetime import datetime
from pathlib import Path

DEF_PATH = Path("data/save.json")

def generate_surface_modifiers():
    # Match NewGenGenerator.generate_surface_modifiers
    mods = {s: round(random.uniform(0.95, 1.05), 3) for s in ["clay", "grass", "hard", "indoor"]}
    total = sum(mods.values())
    if total < 3.9:
        deficit = 3.9 - total
        steps = math.ceil(deficit / 0.01)
        best_key = max(mods, key=mods.get)
        mods[best_key] = round(mods[best_key] + steps * 0.01, 3)
    return mods

def migrate(path: Path):
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    # Backup
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_suffix(path.suffix + f".bak.{ts}")
    shutil.copy2(path, backup)
    print(f"Backup created: {backup}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    players = data.get("players")
    if not isinstance(players, list):
        print("No players array found in save.json")
        sys.exit(1)

    removed_count = 0
    added_count = 0
    kept_count = 0

    for p in players:
        # Remove legacy field if present
        if "favorite_surface" in p:
            p.pop("favorite_surface", None)
            removed_count += 1

        # Add modifiers if missing; keep existing if already present
        if not isinstance(p.get("surface_modifiers"), dict):
            p["surface_modifiers"] = generate_surface_modifiers()
            added_count += 1
        else:
            kept_count += 1

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Done. Players processed: {len(players)}")
    print(f"- favorite_surface removed: {removed_count}")
    print(f"- surface_modifiers added: {added_count}")
    print(f"- surface_modifiers already present (kept): {kept_count}")

if __name__ == "__main__":
    # Optional custom path: python migrate_surface_mods.py path\to\save.json
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEF_PATH
    migrate(target)