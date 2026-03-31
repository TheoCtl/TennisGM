"""Quick gallery to preview all face styles side by side."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import tkinter as tk
from face_generator import generate_face, create_face_canvas, HAIR_STYLES, SKIN_PALETTES, HAIR_COLORS

root = tk.Tk()
root.title("Face Gallery v4")
root.configure(bg="#2c3e50")

# Scrollable canvas
outer = tk.Canvas(root, bg="#2c3e50", highlightthickness=0)
scrollbar = tk.Scrollbar(root, orient="vertical", command=outer.yview)
outer.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")
outer.pack(side="left", fill="both", expand=True)

frame = tk.Frame(outer, bg="#2c3e50")
outer.create_window((0, 0), window=frame, anchor="nw")

COLS = 6
row_frame = None
styles = list(HAIR_STYLES.keys())
for i, style_name in enumerate(styles):
    if i % COLS == 0:
        row_frame = tk.Frame(frame, bg="#2c3e50")
        row_frame.pack(padx=10, pady=5, anchor="w")

    cell = tk.Frame(row_frame, bg="#34495e", relief="raised", bd=1)
    cell.pack(side="left", padx=5, pady=5)

    face = generate_face(player_id=i * 1000 + 42)
    face["hair_style"] = style_name
    # vary skin/hair to see range
    face["skin_idx"] = i % len(SKIN_PALETTES)
    face["hair_color_idx"] = i % len(HAIR_COLORS)

    c = create_face_canvas(cell, face, width=120, height=120, bg="#34495e")
    c.pack(padx=4, pady=(4, 0))
    tk.Label(cell, text=style_name, font=("Consolas", 8), bg="#34495e",
             fg="white").pack(pady=(0, 4))

frame.update_idletasks()
outer.configure(scrollregion=outer.bbox("all"))
root.geometry("820x600")
root.mainloop()
