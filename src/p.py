import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

DEF_PATH = Path("data/save.json")

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

    for p in players:
        # Remove legacy surface fields (no longer used — surface boosts are global now)
        if "favorite_surface" in p:
            p.pop("favorite_surface", None)
            removed_count += 1
        if "surface_modifiers" in p:
            p.pop("surface_modifiers", None)
            removed_count += 1

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Done. Players processed: {len(players)}")
    print(f"- Surface fields removed: {removed_count}")

if __name__ == "__main__":
    # Optional custom path: python migrate_surface_mods.py path\to\save.json
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEF_PATH
    migrate(target)