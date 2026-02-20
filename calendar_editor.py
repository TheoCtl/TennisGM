"""
Tournament Calendar Viewer & Week Swapper
=========================================
Displays the weekly breakdown of tournaments by category,
and lets you swap weeks to reorder the calendar.
"""

import json
import os
from collections import defaultdict

SAVE_PATH = os.path.join(os.path.dirname(__file__), "data", "save.json")

# Display order and short labels for categories
CATEGORY_ORDER = [
    "Grand Slam",
    "Masters 1000",
    "ATP 500",
    "ATP 250",
    "Challenger 175",
    "Challenger 125",
    "Challenger 100",
    "Challenger 75",
    "Challenger 50",
    "ITF",
    "Juniors",
    "Special",
]

SHORT = {
    "Grand Slam":     "GS",
    "Masters 1000":   "M1000",
    "ATP 500":        "500",
    "ATP 250":        "250",
    "Challenger 175": "C175",
    "Challenger 125": "C125",
    "Challenger 100": "C100",
    "Challenger 75":  "C75",
    "Challenger 50":  "C50",
    "ITF":            "ITF",
    "Juniors":        "Jun",
    "Special":        "Spc",
}


def load_data():
    with open(SAVE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_week_grid(tournaments):
    """Return {week: {category: [tournament_names]}}"""
    grid = defaultdict(lambda: defaultdict(list))
    for t in tournaments:
        grid[t["week"]][t["category"]].append(t["name"])
    return grid


def present_categories(tournaments):
    """Return only the categories that actually appear, in display order."""
    present = set(t["category"] for t in tournaments)
    return [c for c in CATEGORY_ORDER if c in present]


def print_calendar(tournaments):
    grid = build_week_grid(tournaments)
    cats = present_categories(tournaments)
    short_labels = [SHORT.get(c, c[:5]) for c in cats]

    # Column widths
    week_col = 6
    col_w = 6

    # Header
    header = f"{'Week':<{week_col}}" + "".join(f"{s:>{col_w}}" for s in short_labels) + f"  {'Total':>5}"
    sep = "-" * len(header)
    print()
    print(header)
    print(sep)

    all_weeks = sorted(grid.keys())
    for w in all_weeks:
        row = f"{'W'+str(w):<{week_col}}"
        total = 0
        for cat in cats:
            n = len(grid[w].get(cat, []))
            total += n
            cell = str(n) if n else "."
            row += f"{cell:>{col_w}}"
        row += f"  {total:>5}"
        print(row)

    print(sep)

    # Totals row
    row = f"{'Total':<{week_col}}"
    grand = 0
    for cat in cats:
        n = sum(len(grid[w].get(cat, [])) for w in all_weeks)
        grand += n
        row += f"{n:>{col_w}}"
    row += f"  {grand:>5}"
    print(row)
    print()


def print_week_detail(tournaments, week):
    """Print all tournaments in a given week."""
    week_t = [t for t in tournaments if t["week"] == week]
    if not week_t:
        print(f"  No tournaments in week {week}.")
        return
    week_t.sort(key=lambda t: CATEGORY_ORDER.index(t["category"]) if t["category"] in CATEGORY_ORDER else 99)
    print(f"\n  Week {week} — {len(week_t)} tournament(s):")
    for t in week_t:
        print(f"    {t['category']:<18} {t['name']:<30} ({t['surface']}, draw {t['draw_size']})")
    print()


def swap_weeks(tournaments, w1, w2):
    """Swap the week value of all tournaments in week w1 and w2."""
    count1 = count2 = 0
    for t in tournaments:
        if t["week"] == w1:
            t["week"] = w2
            count1 += 1
        elif t["week"] == w2:
            t["week"] = w1
            count2 += 1
    return count1, count2


def main():
    data = load_data()
    tournaments = data["tournaments"]

    print("=" * 60)
    print("  TOURNAMENT CALENDAR EDITOR")
    print("=" * 60)

    while True:
        print_calendar(tournaments)

        print("Commands:")
        print("  [V] View week detail   (e.g. V 12)")
        print("  [S] Swap two weeks     (e.g. S 3 17)")
        print("  [W] Save changes")
        print("  [Q] Quit (without saving)")
        print()

        cmd = input(">>> ").strip()
        if not cmd:
            continue

        parts = cmd.split()
        action = parts[0].upper()

        if action == "Q":
            print("Exiting without saving.")
            break

        elif action == "W":
            save_data(data)
            print("Saved to", SAVE_PATH)

        elif action == "V":
            if len(parts) == 2 and parts[1].isdigit():
                print_week_detail(tournaments, int(parts[1]))
            else:
                try:
                    week = int(input("  Which week? "))
                    print_week_detail(tournaments, week)
                except ValueError:
                    print("  Invalid week number.")

        elif action == "S":
            if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                w1, w2 = int(parts[1]), int(parts[2])
            else:
                try:
                    w1 = int(input("  First week:  "))
                    w2 = int(input("  Second week: "))
                except ValueError:
                    print("  Invalid week number.")
                    continue

            if w1 == w2:
                print("  Same week — nothing to swap.")
                continue

            c1, c2 = swap_weeks(tournaments, w1, w2)
            print(f"  Swapped week {w1} ({c1} tournaments) <-> week {w2} ({c2} tournaments).")

        else:
            print("  Unknown command. Use V, S, W, or Q.")


if __name__ == "__main__":
    main()
