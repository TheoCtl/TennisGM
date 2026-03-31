"""
Head-only chibi pixel-art face generator for TennisGM (v4.1).
16x18 grid rendered as chunky rectangles on a Tkinter Canvas.

Key layout (0-indexed rows/cols):
  Head  : rows 4-16, cols 3-12 (with rounding at top/bottom)
  Hair  : top rows overlap head rows 4-5; sides start at row 4
  Brows : row 8
  Eyes  : rows 9-10
  Nose  : row 12
  Mouth : row 14
"""

import random
import hashlib
import tkinter as tk

# ---------------------------------------------------------------------------
# Colour palettes
# ---------------------------------------------------------------------------

SKIN_PALETTES = [
    # (base, shadow, outline)
    ("#FDDCB5", "#E8B88A", "#C4946A"),   # very light
    ("#F5C8A0", "#D9A87A", "#B8845A"),   # light
    ("#E8B88A", "#C89868", "#A07850"),   # light-medium
    ("#D4A574", "#B88A58", "#906A40"),   # medium
    ("#C08A5A", "#A07040", "#785028"),   # medium-dark
    ("#A07040", "#805828", "#604018"),   # dark
    ("#804820", "#603010", "#402008"),   # very dark
    ("#603818", "#482808", "#301808"),   # deepest
]

HAIR_COLORS = [
    # (base, shadow, highlight)
    ("#1A1A1A", "#0A0A0A", "#3A3A3A"),   # black
    ("#3B2216", "#25140C", "#553828"),   # dark brown
    ("#6B4226", "#4A2E18", "#8B5A36"),   # brown
    ("#8B6A3E", "#6B4E28", "#AB8A5E"),   # light brown
    ("#C8A050", "#A88030", "#E8C070"),   # dirty blonde
    ("#E8C868", "#C8A848", "#F8E888"),   # blonde
    ("#D04020", "#B02010", "#F06040"),   # red/auburn
    ("#F06820", "#D04810", "#F88840"),   # ginger
    ("#A0A0A0", "#808080", "#C8C8C8"),   # grey/silver
    ("#F0E0C0", "#D8C8A0", "#F8F0E0"),   # platinum blonde
]

EYE_COLORS = [
    "#3A2820",  # dark brown
    "#5A4030",  # brown
    "#4A6A30",  # green
    "#3060A0",  # blue
    "#2040A0",  # dark blue
    "#6A4020",  # hazel
    "#202020",  # near-black
    "#508050",  # light green
    "#4080C0",  # light blue
]

# ---------------------------------------------------------------------------
# Grid constants
# ---------------------------------------------------------------------------

GRID_W, GRID_H = 16, 18
HEAD_LEFT = 3
HEAD_RIGHT = 12   # inclusive
HEAD_TOP = 4

# Row-by-row insets: (left_offset, right_offset) from HEAD_LEFT / HEAD_RIGHT
HEAD_SHAPE = {
    4:  (2, 2),   # top crown  - cols 5-10  (6 wide)
    5:  (0, 0),   # full width - cols 3-12 (10 wide)
    6:  (0, 0),
    7:  (0, 0),
    8:  (0, 0),
    9:  (0, 0),
    10: (0, 0),
    11: (0, 0),
    12: (0, 0),
    13: (0, 0),
    14: (0, 0),
    15: (1, 1),   # jaw  - cols 4-11  (8 wide)
    16: (2, 2),   # chin - cols 5-10  (6 wide)
}

# ---------------------------------------------------------------------------
# Hair style templates
#
# "top" : list of 16-char strings drawn so that the LAST TWO rows overlap
#         head rows 4-5.  Formula:  start_row = HEAD_TOP + 2 - len(top)
#
# "sides_l" / "sides_r" : per-row segments starting at HEAD_TOP (row 4).
#         Left side is drawn right-aligned to HEAD_LEFT; right side left-
#         aligned from HEAD_RIGHT+1.
#
# Character legend:  .=transparent  1=shadow  2=base  3=highlight
# ---------------------------------------------------------------------------

HAIR_STYLES = {
    # ---- SHORT ----
    "buzz": {
        "top": [
            "....22222222....",
            "...2233332222...",
            "..222222222222..",
            "..222222222222..",
            "..111111111111..",
        ],
        "sides_l": ["1", "1", "."],
        "sides_r": ["1", "1", "."],
    },
    "crew": {
        "top": [
            "....22222222....",
            "...2233222222...",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
            "..221111111122..",
        ],
        "sides_l": ["2", "1", "1", "."],
        "sides_r": ["2", "1", "1", "."],
    },
    "short_neat": {
        "top": [
            "...2222222222...",
            "..22233322222...",
            "..222333222222..",
            "..222222222222..",
            "..222222222222..",
            "..222111111222..",
        ],
        "sides_l": ["2", "2", "1", "1", "."],
        "sides_r": ["2", "2", "1", "1", "."],
    },
    "textured_crop": {
        "top": [
            "...3223223223...",
            "..32232232232...",
            "..222322322322..",
            "..322222222223..",
            "..222222222222..",
            "..222211112222..",
        ],
        "sides_l": ["2", "1", "1", "."],
        "sides_r": ["2", "1", "1", "."],
    },
    "side_part": {
        "top": [
            "..3332222222....",
            "..333222222222..",
            "..332222222222..",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
        ],
        "sides_l": ["2", "2", "1", "1", "."],
        "sides_r": ["2", "1", "1", "."],
    },
    "fade": {
        "top": [
            "....33332233....",
            "...2222222222...",
            "..222222222222..",
            "..222222222222..",
            "..221111111122..",
        ],
        "sides_l": ["1", "1", ".", "."],
        "sides_r": ["1", "1", ".", "."],
    },
    "spiky": {
        "top": [
            "..2.22.33..22...",
            "..22222332222...",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
            "..222111111222..",
        ],
        "sides_l": ["2", "1", "1", "."],
        "sides_r": ["2", "1", "1", "."],
    },
    "flat_top": {
        "top": [
            "..222222222222..",
            "..222222222222..",
            "..222233222222..",
            "..222222222222..",
            "..222222222222..",
            "..222111111222..",
        ],
        "sides_l": ["2", "2", "1", "1", "."],
        "sides_r": ["2", "2", "1", "1", "."],
    },

    # ---- MEDIUM ----
    "medium_wavy": {
        "top": [
            "..332233223322..",
            "..223322332233..",
            "..332233223322..",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
        ],
        "sides_l": ["22", "22", "21", "21", "11", "1."],
        "sides_r": ["22", "22", "12", "12", "11", ".1"],
    },
    "medium_swept": {
        "top": [
            "..333222222222..",
            "..332222222222..",
            "..322222222222..",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
        ],
        "sides_l": ["22", "22", "21", "11", "1.", "."],
        "sides_r": ["22", "12", "11", "1.", ".", "."],
    },
    "shaggy": {
        "top": [
            "..323232323232..",
            "..232323232323..",
            "..323232323232..",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
        ],
        "sides_l": ["22", "22", "21", "21", "11", "1.", ".1"],
        "sides_r": ["22", "22", "12", "12", "11", ".1", "1."],
    },
    "pompadour": {
        "top": [
            "...3333333333...",
            "..333233323332..",
            "..333222222333..",
            "..222222222222..",
            "..222222222222..",
            "..222111111222..",
        ],
        "sides_l": ["2", "1", "1", ".", "."],
        "sides_r": ["2", "1", "1", ".", "."],
    },
    "slick_back": {
        "top": [
            "...2222222222...",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
            "..222111111222..",
        ],
        "sides_l": ["2", "2", "1", "1", "1", "."],
        "sides_r": ["2", "2", "1", "1", "1", "."],
    },
    "undercut": {
        "top": [
            "..222233222222..",
            "..222233222222..",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
        ],
        "sides_l": ["1", ".", "."],
        "sides_r": ["1", ".", "."],
    },
    "curtains": {
        "top": [
            "..222222222222..",
            "..222233322222..",
            "..222222222222..",
            "..2222....2222..",
            "..222......222..",
            "..22........22..",
        ],
        "sides_l": ["22", "22", "22", "21", "11", "1."],
        "sides_r": ["22", "22", "22", "12", "11", ".1"],
    },
    "messy": {
        "top": [
            ".2.222.3232.22..",
            "..223232322322..",
            "..322322322232..",
            "..222222222222..",
            "..222222222222..",
            "..222122212221..",
        ],
        "sides_l": ["22", "21", "12", "11", "1.", "."],
        "sides_r": ["22", "12", "21", "11", ".1", "."],
    },

    # ---- LONG ----
    "long_straight": {
        "top": [
            "..222222222222..",
            "..222333222222..",
            "..222333322222..",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
        ],
        "sides_l": ["22", "22", "22", "22", "21", "21", "21", "11", "11", "1."],
        "sides_r": ["22", "22", "22", "22", "12", "12", "12", "11", "11", ".1"],
    },
    "long_wavy": {
        "top": [
            "..322322322322..",
            "..232232232232..",
            "..322322322322..",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
        ],
        "sides_l": ["22", "22", "22", "22", "21", "12", "21", "12", "11", "1."],
        "sides_r": ["22", "22", "22", "22", "12", "21", "12", "21", "11", ".1"],
    },
    "curly": {
        "top": [
            "..232323232323..",
            "..323232323232..",
            "..232323232323..",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
        ],
        "sides_l": ["22", "23", "32", "23", "21", "12", "1.", ".1"],
        "sides_r": ["22", "32", "23", "32", "12", "21", ".1", "1."],
    },
    "afro": {
        "top": [
            "..232323232323..",
            ".2323232323232.",
            ".3232323232323.",
            ".2323232323232.",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
        ],
        "sides_l": ["232", "323", "232", "323", "212", "121", "1.1", ".1."],
        "sides_r": ["232", "323", "232", "323", "212", "121", "1.1", ".1."],
    },
    "bowl_cut": {
        "top": [
            "...2222222222...",
            "..222222222222..",
            "..222233222222..",
            "..222222222222..",
            "..222222222222..",
            "..222222222222..",
        ],
        "sides_l": ["22", "22", "22", "22", "11", "."],
        "sides_r": ["22", "22", "22", "22", "11", "."],
    },
    "mohawk": {
        "top": [
            ".....333333.....",
            "....33322233....",
            "....22222222....",
            "...2222222222...",
            "..222222222222..",
            "................",
        ],
        "sides_l": ["1", "."],
        "sides_r": ["1", "."],
    },

    # ---- NONE ----
    "bald": {
        "top": [],
        "sides_l": [],
        "sides_r": [],
    },
}

# ---------------------------------------------------------------------------
# Facial feature templates
# ---------------------------------------------------------------------------

EYEBROW_STYLES = [
    ["11", "1."],          # 0  thin angled down
    ["111"],               # 1  thin straight 3px
    ["11", ".1"],          # 2  thin rising
    [".11", "11."],        # 3  thick angled down
    ["111", ".1."],        # 4  pointed / chevron
    ["11"],                # 5  minimal 2px
    [".11.", "1111"],      # 6  thick arched
    ["1111"],              # 7  thick straight 4px
    ["1.1"],               # 8  split / thin gap
    ["111", "1.."],        # 9  angry angled
]

EYE_STYLES = [
    {"w": 2, "h": 2, "pat": ["WE", "WE"]},       # 0  simple
    {"w": 2, "h": 2, "pat": ["WE", "EE"]},       # 1  looking down
    {"w": 3, "h": 2, "pat": ["WWE", "WEE"]},     # 2  wider
    {"w": 2, "h": 2, "pat": ["EW", "EW"]},       # 3  looking left
    {"w": 2, "h": 1, "pat": ["WE"]},              # 4  squinting
    {"w": 3, "h": 2, "pat": ["WEW", "WEE"]},     # 5  centred
    {"w": 2, "h": 2, "pat": ["WE", "WB"]},       # 6  with pupil
    {"w": 3, "h": 2, "pat": ["EWE", "EEE"]},     # 7  wide looking right
    {"w": 2, "h": 2, "pat": ["EE", "WE"]},       # 8  heavy-lidded
    {"w": 3, "h": 2, "pat": ["BWE", "EEE"]},     # 9  intense
]

NOSE_STYLES = [
    ["1"],               # 0  single dot
    ["1", "1"],          # 1  vertical 2px
    [".1", "1."],        # 2  angled left
    ["11"],              # 3  wide dot
    [".1", "11"],        # 4  small triangle
    ["1.", ".1"],        # 5  angled right
    ["1", "11"],         # 6  hook
    ["11", "11"],        # 7  wide / flat
]

MOUTH_STYLES = [
    ["111"],              # 0  neutral 3px
    ["1111"],             # 1  wide neutral
    [".11.", "1..1"],     # 2  slight smile
    ["111", ".1."],       # 3  neutral + chin
    ["11"],               # 4  small
    [".11", "11."],       # 5  smirk
    ["1..1", ".11."],     # 6  frown
    [".111.", "1...1"],   # 7  grin
    ["1.1"],              # 8  gap tooth
    ["1111", ".11."],     # 9  thick lips
]

# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def _seeded_random(player_id=None):
    """Return a seeded Random instance for deterministic faces."""
    if player_id is not None:
        h = hashlib.md5(str(player_id).encode()).hexdigest()
        return random.Random(int(h, 16))
    return random.Random()


def generate_face(player_id=None, nationality=None):
    """Generate a face config dict (JSON-serialisable)."""
    rng = _seeded_random(player_id)

    skin_idx = rng.randint(0, len(SKIN_PALETTES) - 1)
    hair_color_idx = rng.randint(0, len(HAIR_COLORS) - 1)
    eye_color_idx = rng.randint(0, len(EYE_COLORS) - 1)

    hair_style = rng.choice(list(HAIR_STYLES.keys()))
    eyebrow_style = rng.randint(0, len(EYEBROW_STYLES) - 1)
    eye_style = rng.randint(0, len(EYE_STYLES) - 1)
    nose_style = rng.randint(0, len(NOSE_STYLES) - 1)
    mouth_style = rng.randint(0, len(MOUTH_STYLES) - 1)

    # Facial hair (~30 % chance)
    facial_hair = rng.choice([
        "none", "none", "none", "none", "none",
        "none", "none", "stubble", "goatee", "beard",
    ])

    return {
        "version": 4,
        "skin_idx": skin_idx,
        "hair_color_idx": hair_color_idx,
        "eye_color_idx": eye_color_idx,
        "hair_style": hair_style,
        "eyebrow_style": eyebrow_style,
        "eye_style": eye_style,
        "nose_style": nose_style,
        "mouth_style": mouth_style,
        "facial_hair": facial_hair,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _hex_blend(c1, c2, t):
    """Linearly blend two hex colours.  t=0 -> c1, t=1 -> c2."""
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def create_face_canvas(parent, face, width=160, height=160, bg="#ecf0f1"):
    """Render a face dict onto a Tkinter Canvas and return the widget."""

    canvas = tk.Canvas(parent, width=width, height=height, bg=bg,
                       highlightthickness=0)

    px_w = width / GRID_W
    px_h = height / GRID_H

    # --- resolve palettes ---
    skin_base, skin_shadow, skin_outline = SKIN_PALETTES[face["skin_idx"] % len(SKIN_PALETTES)]
    hair_base, hair_shadow, hair_highlight = HAIR_COLORS[face["hair_color_idx"] % len(HAIR_COLORS)]
    eye_color = EYE_COLORS[face["eye_color_idx"] % len(EYE_COLORS)]

    hair_map = {"1": hair_shadow, "2": hair_base, "3": hair_highlight}

    # pixel buffer – later entries overwrite earlier ones at the same coord
    pixels = []

    def put(gx, gy, colour):
        if 0 <= gx < GRID_W and 0 <= gy < GRID_H:
            pixels.append((gx, gy, colour))

    # ------------------------------------------------------------------ HEAD
    head_pixels = set()
    for row, (lo, ro) in HEAD_SHAPE.items():
        for col in range(HEAD_LEFT + lo, HEAD_RIGHT - ro + 1):
            head_pixels.add((col, row))

    for (gx, gy) in head_pixels:
        left_in  = (gx - 1, gy) in head_pixels
        right_in = (gx + 1, gy) in head_pixels
        top_in   = (gx, gy - 1) in head_pixels
        bot_in   = (gx, gy + 1) in head_pixels

        is_edge = not (left_in and right_in and top_in and bot_in)

        if is_edge:
            put(gx, gy, skin_outline)
        elif not left_in or not right_in:
            put(gx, gy, skin_shadow)
        elif gy <= HEAD_TOP + 1:
            put(gx, gy, skin_shadow)
        else:
            put(gx, gy, skin_base)

    # ------------------------------------------------------------------ EARS
    ear_y = 9
    put(HEAD_LEFT - 1, ear_y,     skin_shadow)
    put(HEAD_LEFT - 1, ear_y + 1, skin_shadow)
    put(HEAD_RIGHT + 1, ear_y,     skin_shadow)
    put(HEAD_RIGHT + 1, ear_y + 1, skin_shadow)

    # ------------------------------------------------------------------ HAIR
    style_key = face.get("hair_style", "buzz")
    if style_key not in HAIR_STYLES:
        style_key = "buzz"
    style = HAIR_STYLES[style_key]

    # Top hair – last 2 rows overlap head rows HEAD_TOP and HEAD_TOP+1
    top_rows = style["top"]
    hair_start_row = HEAD_TOP + 2 - len(top_rows)

    for ri, row_str in enumerate(top_rows):
        gy = hair_start_row + ri
        offset = (GRID_W - len(row_str)) // 2
        for ci, ch in enumerate(row_str):
            if ch == '.':
                continue
            gx = offset + ci
            put(gx, gy, hair_map.get(ch, hair_base))

    # Side hair
    for ri, seg in enumerate(style.get("sides_l", [])):
        gy = HEAD_TOP + ri
        for ci, ch in enumerate(seg):
            if ch == '.':
                continue
            gx = HEAD_LEFT - len(seg) + ci
            put(gx, gy, hair_map.get(ch, hair_base))

    for ri, seg in enumerate(style.get("sides_r", [])):
        gy = HEAD_TOP + ri
        for ci, ch in enumerate(seg):
            if ch == '.':
                continue
            gx = HEAD_RIGHT + 1 + ci
            put(gx, gy, hair_map.get(ch, hair_base))

    # -------------------------------------------------------------- EYEBROWS
    brow_data = EYEBROW_STYLES[face["eyebrow_style"] % len(EYEBROW_STYLES)]
    eye_data  = EYE_STYLES[face["eye_style"] % len(EYE_STYLES)]
    ew = eye_data["w"]

    # Centre eyes symmetrically on the face (gap of 2 between them)
    left_eye_x  = 7 - ew       # w=2 -> col 5;  w=3 -> col 4
    right_eye_x = 9

    brow_row = 8
    for ri, row_str in enumerate(brow_data):
        rw = len(row_str)
        l_start = left_eye_x + (ew - rw) // 2
        r_start = right_eye_x + (ew - rw) // 2
        for ci, ch in enumerate(row_str):
            if ch == '1':
                put(l_start + ci, brow_row + ri, skin_outline)
                put(r_start + ci, brow_row + ri, skin_outline)

    # ------------------------------------------------------------------ EYES
    eye_row = 9
    color_map = {"E": eye_color, "W": "#FFFFFF", "B": "#000000"}

    for ri, row_str in enumerate(eye_data["pat"]):
        for ci, ch in enumerate(row_str):
            c = color_map.get(ch)
            if c:
                put(left_eye_x + ci,  eye_row + ri, c)
                put(right_eye_x + ci, eye_row + ri, c)

    # ------------------------------------------------------------------ NOSE
    nose_data = NOSE_STYLES[face["nose_style"] % len(NOSE_STYLES)]
    nose_color = _hex_blend(skin_shadow, skin_outline, 0.35)
    nose_row = 12

    for ri, row_str in enumerate(nose_data):
        rw = len(row_str)
        col = 8 - (rw + 1) // 2
        for ci, ch in enumerate(row_str):
            if ch == '1':
                put(col + ci, nose_row + ri, nose_color)

    # ----------------------------------------------------------------- MOUTH
    mouth_data = MOUTH_STYLES[face["mouth_style"] % len(MOUTH_STYLES)]
    lip_color = _hex_blend(skin_outline, "#802020", 0.4)
    mouth_row = 14

    for ri, row_str in enumerate(mouth_data):
        rw = len(row_str)
        col = 8 - (rw + 1) // 2
        for ci, ch in enumerate(row_str):
            if ch == '1':
                put(col + ci, mouth_row + ri, lip_color)

    # ----------------------------------------------------------- FACIAL HAIR
    fh = face.get("facial_hair", "none")
    fh_color = _hex_blend(hair_map["2"], skin_outline, 0.5)

    if fh == "stubble":
        for gx in range(4, 12):
            for gy in (13, 14, 15):
                if (gx, gy) in head_pixels and (gx + gy) % 2 == 0:
                    put(gx, gy, fh_color)
    elif fh == "goatee":
        for gx in range(6, 10):
            for gy in (14, 15, 16):
                if (gx, gy) in head_pixels:
                    put(gx, gy, fh_color)
    elif fh == "beard":
        for gx in range(4, 12):
            for gy in (13, 14, 15, 16):
                if (gx, gy) in head_pixels:
                    put(gx, gy, fh_color)

    # ----------------------------------------------------------- DRAW PIXELS
    for gx, gy, colour in pixels:
        x1 = gx * px_w
        y1 = gy * px_h
        canvas.create_rectangle(x1, y1, x1 + px_w + 1, y1 + px_h + 1,
                                fill=colour, outline="")

    return canvas
