"""
gen_tileset.py — generate per-terrain golf course tilesets.

Produces one PNG per terrain type (plus detail sprite sheets) in assets/tilemaps/.

Ground layer files (opaque RGB):
  golf_fairway.png   golf_rough.png      golf_green.png    golf_tee.png
  golf_bunker.png    golf_water.png      golf_deeprough.png golf_trees.png
  golf_path.png      golf_surfaces.png   golf_hazard.png

Detail layer files (RGBA, transparent background):
  golf_detail_trees.png   golf_detail_plants.png  golf_detail_rocks.png
  golf_detail_water.png   golf_detail_markers.png

Each ground file is 256x48 px (16 tiles wide x 3 rows of 16x16 tiles):
  Row 0: 4 plain variants | 4 edges vs primary neighbour (N/S/E/W)
          | 4 corners vs primary neighbour (NW/NE/SE/SW)
          | 4 inner corners vs primary neighbour
  Row 1: 4 edges vs secondary neighbour (N/S/E/W)
          | 4 corners vs secondary neighbour (NW/NE/SE/SW)
          | 4 extra variants or transitions
  Row 2: spare / additional variants

Run from the project root:
    python tools/gen_tileset.py
"""

import os
import random
from PIL import Image, ImageDraw

TILE = 16
COLS = 16          # tiles per row in each sheet
STRIP = 5          # edge blend width in pixels (outer terrain strip)
HALF  = TILE // 2  # half-tile for corner quadrants

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "tilemaps")
os.makedirs(OUT_DIR, exist_ok=True)

random.seed(42)

# ── Palette ────────────────────────────────────────────────────────────────────

FAIR    = (82, 158, 82)    # fairway base
FAIR_L  = (98, 174, 98)    # fairway light (stripe)
FAIR_D  = (66, 138, 66)    # fairway dark

ROUG    = (52, 108, 52)    # rough base
ROUG_D  = (38, 86, 38)
ROUG_T  = (30, 72, 30)     # tuft
ROUG_L  = (64, 122, 64)

GREE    = (104, 192, 104)  # putting green
GREE_L  = (120, 208, 120)
GREE_D  = (86, 168, 86)
GREE_S  = (112, 200, 112)  # stripe

TEE     = (90, 178, 110)   # tee box
TEE_L   = (106, 194, 126)
TEE_D   = (74, 156, 90)

SAND    = (218, 200, 130)  # bunker
SAND_L  = (236, 218, 152)
SAND_D  = (194, 174, 106)
SAND_S  = (174, 154, 86)

WATR    = (68, 128, 196)   # water
WATR_L  = (94, 156, 220)
WATR_D  = (50, 100, 164)
WATR_F  = (148, 196, 238)  # foam

DEEP    = (34, 74, 34)     # deep rough
DEEP_D  = (22, 54, 22)
DEEP_T  = (16, 44, 16)

TREE    = (22, 50, 22)     # trees / OOB
TREE_D  = (14, 36, 14)
TREE_L  = (34, 66, 34)
TREE_C  = (50, 90, 50)     # canopy highlight
TRUNK   = (100, 68, 36)

PATH    = (188, 178, 156)  # cart path
PATH_D  = (168, 158, 136)
PATH_E  = (144, 134, 112)

HAZ_Y   = (240, 210, 60)   # hazard stripe yellow
HAZ_B   = (40,  40,  40)   # hazard stripe black

DIRT    = (162, 134, 90)
DIRT_D  = (140, 112, 68)
ROCK    = (130, 124, 116)
ROCK_D  = (100,  96,  90)
ROCK_L  = (160, 154, 146)

WHITE   = (248, 248, 248)


# ── Low-level pixel helpers ────────────────────────────────────────────────────

def fill_tile(draw, col, row, color):
    x, y = col * TILE, row * TILE
    draw.rectangle([x, y, x + TILE - 1, y + TILE - 1], fill=color)


def scatter(draw, col, row, dot_color, density=0.12, seed_offset=0):
    rng = random.Random(col * 1000 + row * 100 + seed_offset)
    for ty in range(TILE):
        for tx in range(TILE):
            if rng.random() < density:
                draw.point((col * TILE + tx, row * TILE + ty), fill=dot_color)


def hstripes(draw, col, row, base, stripe, period=4, offset=0):
    for ty in range(TILE):
        c = stripe if ((ty + offset) % period) < period // 2 else base
        draw.line(
            [(col * TILE, row * TILE + ty), (col * TILE + TILE - 1, row * TILE + ty)],
            fill=c,
        )


def dstripes(draw, col, row, base, stripe, period=6, offset=0):
    for ty in range(TILE):
        for tx in range(TILE):
            c = stripe if ((tx + ty + offset) % period) < period // 2 else base
            draw.point((col * TILE + tx, row * TILE + ty), fill=c)


def wave_line(draw, col, row, y_base, color, amplitude=1):
    for tx in range(TILE):
        dy = int(amplitude * (1 if (tx % 6) < 3 else -1))
        wy = row * TILE + y_base + dy
        if 0 <= wy - row * TILE < TILE:
            draw.point((col * TILE + tx, wy), fill=color)


def dot_grid(draw, col, row, dot_color, spacing=4, offset=(1, 1)):
    ox, oy = offset
    for ty in range(0, TILE, spacing):
        for tx in range(0, TILE, spacing):
            rx = (tx + ox) % TILE
            ry = (ty + oy) % TILE
            draw.point((col * TILE + rx, row * TILE + ry), fill=dot_color)


# ── Terrain renderers (draw into a specific grid cell) ────────────────────────

def draw_fairway(draw, col, row, variant=0):
    hstripes(draw, col, row, FAIR, FAIR_L, period=4, offset=variant * 2)
    scatter(draw, col, row, FAIR_D, density=0.04, seed_offset=variant)


def draw_rough(draw, col, row, variant=0):
    fill_tile(draw, col, row, ROUG)
    scatter(draw, col, row, ROUG_D, density=0.18, seed_offset=variant)
    scatter(draw, col, row, ROUG_T, density=0.06, seed_offset=variant + 50)
    scatter(draw, col, row, ROUG_L, density=0.05, seed_offset=variant + 100)
    rng = random.Random(col * 777 + row * 333 + variant)
    for _ in range(4):
        tx = rng.randint(0, TILE - 1)
        ty = rng.randint(0, TILE - 2)
        draw.line(
            [(col * TILE + tx, row * TILE + ty), (col * TILE + tx, row * TILE + ty + 1)],
            fill=ROUG_T,
        )


def draw_green(draw, col, row, variant=0):
    if variant == 0:
        hstripes(draw, col, row, GREE, GREE_S, period=4, offset=0)
    elif variant == 1:
        dstripes(draw, col, row, GREE, GREE_S, period=6, offset=0)
    elif variant == 2:
        hstripes(draw, col, row, GREE, GREE_S, period=4, offset=2)
    else:
        fill_tile(draw, col, row, GREE)
        scatter(draw, col, row, GREE_L, density=0.05, seed_offset=variant)
    scatter(draw, col, row, GREE_D, density=0.03, seed_offset=variant + 200)


def draw_tee(draw, col, row, variant=0):
    hstripes(draw, col, row, TEE, TEE_L, period=4, offset=variant)
    scatter(draw, col, row, TEE_D, density=0.04, seed_offset=variant)
    if variant == 1:
        cx, cy = col * TILE + 7, row * TILE + 7
        for dx, dy in [(0, -1), (-1, 0), (1, 0)]:
            draw.point((cx + dx, cy + dy), fill=WHITE)
        draw.point((cx, cy), fill=(200, 180, 100))


def draw_bunker(draw, col, row, variant=0):
    fill_tile(draw, col, row, SAND)
    dot_grid(draw, col, row, SAND_D, spacing=3, offset=(variant, variant + 1))
    scatter(draw, col, row, SAND_L, density=0.06, seed_offset=variant)
    scatter(draw, col, row, SAND_D, density=0.06, seed_offset=variant + 10)
    if variant == 1:
        x, y = col * TILE, row * TILE
        draw.line([(x, y + TILE - 1), (x + TILE - 1, y + TILE - 1)], fill=SAND_S)
        draw.line([(x + TILE - 1, y), (x + TILE - 1, y + TILE - 1)], fill=SAND_S)


def draw_water(draw, col, row, variant=0):
    fill_tile(draw, col, row, WATR)
    for yo in [2, 6, 10, 14]:
        wave_line(draw, col, row, (yo + variant * 3) % TILE, WATR_L)
    scatter(draw, col, row, WATR_F, density=0.04, seed_offset=variant + 300)
    scatter(draw, col, row, WATR_D, density=0.06, seed_offset=variant + 400)


def draw_deeprough(draw, col, row, variant=0):
    fill_tile(draw, col, row, DEEP)
    scatter(draw, col, row, DEEP_D, density=0.28, seed_offset=variant)
    scatter(draw, col, row, DEEP_T, density=0.12, seed_offset=variant + 60)
    scatter(draw, col, row, ROUG_D, density=0.04, seed_offset=variant + 120)
    rng = random.Random(col * 541 + row * 211 + variant)
    for _ in range(6):
        tx = rng.randint(0, TILE - 1)
        ty = rng.randint(0, TILE - 3)
        draw.line(
            [(col * TILE + tx, row * TILE + ty), (col * TILE + tx, row * TILE + ty + 2)],
            fill=DEEP_T,
        )


def draw_trees(draw, col, row, variant=0):
    fill_tile(draw, col, row, TREE_D)
    scatter(draw, col, row, TREE,   density=0.30, seed_offset=variant)
    scatter(draw, col, row, TREE_L, density=0.08, seed_offset=variant + 70)
    rng = random.Random(col * 997 + row * 503 + variant)
    for _ in range(2 + variant % 3):
        cx = rng.randint(3, TILE - 4)
        cy = rng.randint(3, TILE - 4)
        r  = rng.randint(2, 4)
        for ty in range(max(0, cy - r), min(TILE, cy + r + 1)):
            for tx in range(max(0, cx - r), min(TILE, cx + r + 1)):
                if (tx - cx) ** 2 + (ty - cy) ** 2 <= r * r:
                    draw.point((col * TILE + tx, row * TILE + ty), fill=TREE_C)


def draw_path(draw, col, row, style="h"):
    fill_tile(draw, col, row, PATH)
    x, y = col * TILE, row * TILE
    W = TILE
    if style == "h":
        draw.line([(x, y),         (x+W-1, y)],         fill=PATH_E)
        draw.line([(x, y+W-1),     (x+W-1, y+W-1)],     fill=PATH_E)
        draw.line([(x, y+1),       (x+W-1, y+1)],       fill=PATH_D)
        draw.line([(x, y+W-2),     (x+W-1, y+W-2)],     fill=PATH_D)
    elif style == "v":
        draw.line([(x,     y),     (x,     y+W-1)],     fill=PATH_E)
        draw.line([(x+W-1, y),     (x+W-1, y+W-1)],     fill=PATH_E)
        draw.line([(x+1,   y),     (x+1,   y+W-1)],     fill=PATH_D)
        draw.line([(x+W-2, y),     (x+W-2, y+W-1)],     fill=PATH_D)
    elif style == "x":
        for side in ("h", "v"):
            draw_path(draw, col, row, side)
    elif style in ("tl", "tr", "br", "bl"):
        if "t" in style:
            draw.line([(x, y+W-1), (x+W-1, y+W-1)], fill=PATH_E)
        else:
            draw.line([(x, y),     (x+W-1, y)],     fill=PATH_E)
        if "l" in style:
            draw.line([(x+W-1, y), (x+W-1, y+W-1)], fill=PATH_E)
        else:
            draw.line([(x, y),     (x,     y+W-1)], fill=PATH_E)
    elif style.startswith("t_"):
        # T-junction: three open sides, one closed
        closed = style[-1]  # n/s/e/w
        for edge in ("n", "s", "e", "w"):
            if edge == closed:
                continue
            if edge == "n":   draw.line([(x, y),     (x+W-1, y)],     fill=PATH_E)
            elif edge == "s": draw.line([(x, y+W-1), (x+W-1, y+W-1)], fill=PATH_E)
            elif edge == "w": draw.line([(x, y),     (x, y+W-1)],     fill=PATH_E)
            elif edge == "e": draw.line([(x+W-1, y), (x+W-1, y+W-1)], fill=PATH_E)
    else:
        draw.rectangle([x, y, x+W-1, y+W-1], outline=PATH_E)
    # subtle centre crease
    draw.point((x + W // 2, y + W // 2), fill=PATH_D)


def draw_dirt(draw, col, row, variant=0):
    fill_tile(draw, col, row, DIRT)
    scatter(draw, col, row, DIRT_D, density=0.15, seed_offset=variant)
    scatter(draw, col, row, (180, 155, 110), density=0.08, seed_offset=variant + 10)


def draw_rock_ground(draw, col, row, variant=0):
    fill_tile(draw, col, row, ROCK)
    scatter(draw, col, row, ROCK_D, density=0.20, seed_offset=variant)
    scatter(draw, col, row, ROCK_L, density=0.08, seed_offset=variant + 50)
    x, y = col * TILE, row * TILE
    draw.line([(x+2, y+4), (x+8, y+9)],   fill=ROCK_D)
    draw.line([(x+9, y+3), (x+13, y+11)], fill=ROCK_D)


def draw_bridge_h(draw, col, row):
    fill_tile(draw, col, row, (168, 128, 72))
    x, y = col * TILE, row * TILE
    for ty in range(0, TILE, 4):
        draw.line([(x, y+ty), (x+TILE-1, y+ty)], fill=(140, 104, 52))
    draw.line([(x, y),     (x, y+TILE-1)],     fill=(120, 88, 40))
    draw.line([(x+TILE-1, y), (x+TILE-1, y+TILE-1)], fill=(120, 88, 40))


def draw_bridge_v(draw, col, row):
    fill_tile(draw, col, row, (168, 128, 72))
    x, y = col * TILE, row * TILE
    for tx in range(0, TILE, 4):
        draw.line([(x+tx, y), (x+tx, y+TILE-1)], fill=(140, 104, 52))
    draw.line([(x, y),       (x+TILE-1, y)],       fill=(120, 88, 40))
    draw.line([(x, y+TILE-1),(x+TILE-1, y+TILE-1)], fill=(120, 88, 40))


def draw_hazard(draw, col, row, variant=0):
    for ty in range(TILE):
        for tx in range(TILE):
            c = HAZ_Y if ((tx + ty + variant * 2) // 4) % 2 == 0 else HAZ_B
            draw.point((col * TILE + tx, row * TILE + ty), fill=c)


# ── Render a terrain to a standalone 16x16 image ──────────────────────────────

def render_terrain(fn, variant=0):
    """Render a terrain function into an isolated 16x16 RGB tile image."""
    img = Image.new("RGB", (TILE, TILE))
    d   = ImageDraw.Draw(img)
    fn(d, 0, 0, variant)
    return img


# ── Edge / corner composite helpers ───────────────────────────────────────────

def paste_edge(img, col, row, inner_img, outer_img, side):
    """
    Paste inner terrain into (col, row), then overwrite a STRIP-pixel band
    on the given side with the outer terrain.  Gives a clean edge transition.

    side: "N" | "S" | "E" | "W"
    """
    img.paste(inner_img, (col * TILE, row * TILE))
    x, y = col * TILE, row * TILE
    if side == "N":
        region = outer_img.crop((0, 0, TILE, STRIP))
        img.paste(region, (x, y))
    elif side == "S":
        region = outer_img.crop((0, TILE - STRIP, TILE, TILE))
        img.paste(region, (x, y + TILE - STRIP))
    elif side == "W":
        region = outer_img.crop((0, 0, STRIP, TILE))
        img.paste(region, (x, y))
    elif side == "E":
        region = outer_img.crop((TILE - STRIP, 0, TILE, TILE))
        img.paste(region, (x + TILE - STRIP, y))


def paste_corner(img, col, row, inner_img, outer_img, corner):
    """
    Paste inner terrain, then overwrite one quadrant (half×half px) with outer.
    corner: "NW" | "NE" | "SE" | "SW"
    """
    img.paste(inner_img, (col * TILE, row * TILE))
    x, y = col * TILE, row * TILE
    if corner == "NW":
        region = outer_img.crop((0, 0, HALF, HALF))
        img.paste(region, (x, y))
    elif corner == "NE":
        region = outer_img.crop((TILE - HALF, 0, TILE, HALF))
        img.paste(region, (x + HALF, y))
    elif corner == "SE":
        region = outer_img.crop((TILE - HALF, TILE - HALF, TILE, TILE))
        img.paste(region, (x + HALF, y + HALF))
    elif corner == "SW":
        region = outer_img.crop((0, TILE - HALF, HALF, TILE))
        img.paste(region, (x, y + HALF))


def build_terrain_sheet(name, draw_fn, neighbour_a_fn, neighbour_b_fn,
                        extra_row_fn=None, rows=3):
    """
    Build a 16-tile-wide ground sheet for one terrain type.

    Layout per row:
      Row 0: variants 0-3 | edges vs A (N/S/E/W) | corners vs A (NW/NE/SE/SW)
              | inner corners vs A (outer in NW/NE/SE/SW of inner tile = reverse)
      Row 1: edges vs B (N/S/E/W) | corners vs B (NW/NE/SE/SW) | variants 4-7
      Row 2: if extra_row_fn provided, called with (img, draw, row=2); else spare variants
    """
    img  = Image.new("RGB", (COLS * TILE, rows * TILE), ROUG)
    draw = ImageDraw.Draw(img)

    # Pre-render terrain images (variant 0 for transition tiles)
    t_self  = [render_terrain(draw_fn, v)          for v in range(8)]
    t_a     = render_terrain(neighbour_a_fn,   0)
    t_b     = render_terrain(neighbour_b_fn,   0)

    SIDES   = ["N", "S", "E", "W"]
    CORNERS = ["NW", "NE", "SE", "SW"]

    # ── Row 0 ──────────────────────────────────────────────────────────────────
    # Cols 0-3: plain variants
    for v in range(4):
        img.paste(t_self[v], (v * TILE, 0))

    # Cols 4-7: edges, outer = A, inner = self
    for i, side in enumerate(SIDES):
        paste_edge(img, 4 + i, 0, t_self[0], t_a, side)

    # Cols 8-11: corners, outer = A, inner = self
    for i, corner in enumerate(CORNERS):
        paste_corner(img, 8 + i, 0, t_self[0], t_a, corner)

    # Cols 12-15: INNER corners — outer terrain has self in its corner
    # (i.e., self pokes into A from the given corner direction — invert roles)
    for i, corner in enumerate(CORNERS):
        paste_corner(img, 12 + i, 0, t_a, t_self[0], corner)

    # ── Row 1 ──────────────────────────────────────────────────────────────────
    # Cols 0-3: edges vs B
    for i, side in enumerate(SIDES):
        paste_edge(img, i, 1, t_self[0], t_b, side)

    # Cols 4-7: corners vs B
    for i, corner in enumerate(CORNERS):
        paste_corner(img, 4 + i, 1, t_self[0], t_b, corner)

    # Cols 8-11: inner corners vs B
    for i, corner in enumerate(CORNERS):
        paste_corner(img, 8 + i, 1, t_b, t_self[0], corner)

    # Cols 12-15: extra variants
    for v in range(4, 8):
        img.paste(t_self[v], ((12 + v - 4) * TILE, TILE))

    # ── Row 2 ──────────────────────────────────────────────────────────────────
    if extra_row_fn:
        extra_row_fn(img, draw)
    else:
        for v in range(COLS):
            draw_fn(draw, v, 2, variant=v % 8)

    path = os.path.join(OUT_DIR, f"{name}.png")
    img.save(path)
    print(f"  {name}.png  ({img.width}x{img.height})")
    return img


# ── Individual sheet builders ──────────────────────────────────────────────────

def build_fairway():
    def extra(img, draw):
        # Row 2: more fairway/green and fairway/tee combos + spare
        t_self  = render_terrain(draw_fairway, 0)
        t_green = render_terrain(draw_green,   0)
        t_tee   = render_terrain(draw_tee,     0)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, i, 2, t_self, t_green, side)
        for i, corner in enumerate(["NW", "NE", "SE", "SW"]):
            paste_corner(img, 4 + i, 2, t_self, t_green, corner)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, 8 + i, 2, t_self, t_tee, side)
        for v in range(4):
            draw_fairway(draw, 12 + v, 2, variant=v)
    build_terrain_sheet("golf_fairway", draw_fairway, draw_rough, draw_green,
                        extra_row_fn=extra)


def build_rough():
    def extra(img, draw):
        t_self = render_terrain(draw_rough,     0)
        t_deep = render_terrain(draw_deeprough, 0)
        t_tree = render_terrain(draw_trees,     0)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, i, 2, t_self, t_deep, side)
        for i, corner in enumerate(["NW", "NE", "SE", "SW"]):
            paste_corner(img, 4 + i, 2, t_self, t_deep, corner)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, 8 + i, 2, t_self, t_tree, side)
        for i, corner in enumerate(["NW", "NE", "SE", "SW"]):
            paste_corner(img, 12 + i, 2, t_self, t_tree, corner)
    build_terrain_sheet("golf_rough", draw_rough, draw_fairway, draw_deeprough,
                        extra_row_fn=extra)


def build_green():
    def extra(img, draw):
        t_self  = render_terrain(draw_green,   0)
        t_fair  = render_terrain(draw_fairway, 0)
        t_bunker= render_terrain(draw_bunker,  0)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, i, 2, t_self, t_fair, side)
        for i, corner in enumerate(["NW", "NE", "SE", "SW"]):
            paste_corner(img, 4 + i, 2, t_self, t_fair, corner)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, 8 + i, 2, t_self, t_bunker, side)
        for i, corner in enumerate(["NW", "NE", "SE", "SW"]):
            paste_corner(img, 12 + i, 2, t_self, t_bunker, corner)
    build_terrain_sheet("golf_green", draw_green, draw_rough, draw_fairway,
                        extra_row_fn=extra)


def build_tee():
    def extra(img, draw):
        t_self = render_terrain(draw_tee,      0)
        t_fair = render_terrain(draw_fairway,  0)
        t_gree = render_terrain(draw_green,    0)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, i, 2, t_self, t_fair, side)
        for i, corner in enumerate(["NW", "NE", "SE", "SW"]):
            paste_corner(img, 4 + i, 2, t_self, t_fair, corner)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, 8 + i, 2, t_self, t_gree, side)
        for v in range(4):
            draw_tee(draw, 12 + v, 2, variant=v)
    build_terrain_sheet("golf_tee", draw_tee, draw_rough, draw_fairway,
                        extra_row_fn=extra)


def build_bunker():
    def extra(img, draw):
        t_self = render_terrain(draw_bunker,   0)
        t_gree = render_terrain(draw_green,    0)
        t_watr = render_terrain(draw_water,    0)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, i, 2, t_self, t_gree, side)
        for i, corner in enumerate(["NW", "NE", "SE", "SW"]):
            paste_corner(img, 4 + i, 2, t_self, t_gree, corner)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, 8 + i, 2, t_self, t_watr, side)
        for v in range(4):
            draw_bunker(draw, 12 + v, 2, variant=v)
    build_terrain_sheet("golf_bunker", draw_bunker, draw_rough, draw_fairway,
                        extra_row_fn=extra)


def build_water():
    def extra(img, draw):
        t_self = render_terrain(draw_water,    0)
        t_fair = render_terrain(draw_fairway,  0)
        t_gree = render_terrain(draw_green,    0)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, i, 2, t_self, t_fair, side)
        for i, corner in enumerate(["NW", "NE", "SE", "SW"]):
            paste_corner(img, 4 + i, 2, t_self, t_fair, corner)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, 8 + i, 2, t_self, t_gree, side)
        for i, corner in enumerate(["NW", "NE", "SE", "SW"]):
            paste_corner(img, 12 + i, 2, t_self, t_gree, corner)
    build_terrain_sheet("golf_water", draw_water, draw_rough, draw_fairway,
                        extra_row_fn=extra)


def build_deeprough():
    def extra(img, draw):
        t_self = render_terrain(draw_deeprough, 0)
        t_fair = render_terrain(draw_fairway,   0)
        t_tree = render_terrain(draw_trees,     0)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, i, 2, t_self, t_fair, side)
        for i, corner in enumerate(["NW", "NE", "SE", "SW"]):
            paste_corner(img, 4 + i, 2, t_self, t_fair, corner)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, 8 + i, 2, t_self, t_tree, side)
        for i, corner in enumerate(["NW", "NE", "SE", "SW"]):
            paste_corner(img, 12 + i, 2, t_self, t_tree, corner)
    build_terrain_sheet("golf_deeprough", draw_deeprough, draw_rough, draw_trees,
                        extra_row_fn=extra)


def build_trees():
    def extra(img, draw):
        t_self = render_terrain(draw_trees,     0)
        t_deep = render_terrain(draw_deeprough, 0)
        t_fair = render_terrain(draw_fairway,   0)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, i, 2, t_self, t_deep, side)
        for i, corner in enumerate(["NW", "NE", "SE", "SW"]):
            paste_corner(img, 4 + i, 2, t_self, t_deep, corner)
        for i, side in enumerate(["N", "S", "E", "W"]):
            paste_edge(img, 8 + i, 2, t_self, t_fair, side)
        for i, corner in enumerate(["NW", "NE", "SE", "SW"]):
            paste_corner(img, 12 + i, 2, t_self, t_fair, corner)
    build_terrain_sheet("golf_trees", draw_trees, draw_rough, draw_deeprough,
                        extra_row_fn=extra)


def build_path():
    """Cart path: single row of 16 named variants."""
    img  = Image.new("RGB", (COLS * TILE, TILE), PATH)
    draw = ImageDraw.Draw(img)
    styles = ["h", "v", "tl", "tr", "br", "bl",
              "t_s", "t_n", "t_w", "t_e", "x",
              "end", "end", "end", "end", ""]
    for c, style in enumerate(styles):
        draw_path(draw, c, 0, style=style if style else "h")
    path = os.path.join(OUT_DIR, "golf_path.png")
    img.save(path)
    print(f"  golf_path.png  ({img.width}x{img.height})")


def build_surfaces():
    """Bridge planks, dirt and rock ground — 2 rows."""
    img  = Image.new("RGB", (COLS * TILE, 2 * TILE), DIRT)
    draw = ImageDraw.Draw(img)
    # Row 0: bridge H×4, bridge V×4, dirt×4, rock×4
    for c in range(4):  draw_bridge_h(draw, c,     0)
    for c in range(4):  draw_bridge_v(draw, c + 4, 0)
    for c in range(4):  draw_dirt(draw,  c + 8,  0, variant=c)
    for c in range(4):  draw_rock_ground(draw, c + 12, 0, variant=c)
    # Row 1: spare variants
    for c in range(4):  draw_bridge_h(draw, c,     1)
    for c in range(4):  draw_bridge_v(draw, c + 4, 1)
    for c in range(4):  draw_dirt(draw,  c + 8,  1, variant=c + 4)
    for c in range(4):  draw_rock_ground(draw, c + 12, 1, variant=c + 4)
    path = os.path.join(OUT_DIR, "golf_surfaces.png")
    img.save(path)
    print(f"  golf_surfaces.png  ({img.width}x{img.height})")


def build_hazard():
    """Hazard stripes and OOB borders — 2 rows."""
    img  = Image.new("RGB", (COLS * TILE, 2 * TILE), TREE_D)
    draw = ImageDraw.Draw(img)
    # Row 0: hazard stripe×4, dark OOB×4, dark border×4, near-black edge×4
    for c in range(4):  draw_hazard(draw, c,      0, variant=c)
    for c in range(4):
        fill_tile(draw, c + 4, 0, TREE_D)
        scatter(draw, c + 4, 0, TREE, density=0.10, seed_offset=c)
    for c in range(4):
        fill_tile(draw, c + 8, 0, DEEP_D)
        scatter(draw, c + 8, 0, DEEP_T, density=0.15, seed_offset=c)
    for c in range(4):
        fill_tile(draw, c + 12, 0, (12, 28, 12))  # near-black border
    # Row 1: hazard variant 2, transitions
    for c in range(4):  draw_hazard(draw, c,      1, variant=c + 4)
    for c in range(4):
        fill_tile(draw, c + 4, 1, TREE_D)
        scatter(draw, c + 4, 1, TREE_L, density=0.06, seed_offset=c + 20)
    for c in range(4):
        fill_tile(draw, c + 8, 1, DEEP_D)
        scatter(draw, c + 8, 1, ROUG_D, density=0.06, seed_offset=c + 30)
    for c in range(4):
        fill_tile(draw, c + 12, 1, (10, 24, 10))
    path = os.path.join(OUT_DIR, "golf_hazard.png")
    img.save(path)
    print(f"  golf_hazard.png  ({img.width}x{img.height})")


# ── Detail sprite sheet builders (RGBA) ───────────────────────────────────────

def draw_oak(draw, col, row, size=1):
    cx, cy = col * TILE + 7, row * TILE + 6
    draw.rectangle([cx - 1, cy + 3, cx + 1, cy + 7], fill=(100, 70, 36, 255))
    for r, shade in [(6, (30, 90, 30, 200)), (5, (44, 116, 44, 230)),
                     (4, (58, 140, 58, 255)), (3, (74, 158, 74, 255))]:
        for ty in range(-r, r + 1):
            for tx in range(-r, r + 1):
                if tx * tx + ty * ty <= r * r:
                    px_x = cx + tx
                    px_y = cy - 1 + ty
                    if col * TILE <= px_x < (col + 1) * TILE and row * TILE <= px_y < (row + 1) * TILE:
                        draw.point((px_x, px_y), fill=shade)
    draw.point((cx - 1, cy - 4), fill=(100, 175, 100, 200))
    draw.point((cx - 2, cy - 3), fill=(100, 175, 100, 200))


def draw_pine(draw, col, row):
    cx, cy = col * TILE + 7, row * TILE + 3
    draw.rectangle([cx - 1, cy + 9, cx + 1, cy + 12], fill=(110, 78, 40, 255))
    layers = [(cy + 7, 3, (24, 80, 24, 255), (36, 100, 36, 255)),
              (cy + 4, 5, (20, 68, 20, 255), (32,  90, 32, 255)),
              (cy + 1, 6, (16, 58, 16, 255), (28,  78, 28, 255))]
    for base_y, hw, dark, light in layers:
        for tx in range(-hw, hw + 1):
            for ty in range(3):
                px_x = cx + tx
                px_y = base_y + ty
                if col * TILE <= px_x < (col + 1) * TILE and row * TILE <= px_y < (row + 1) * TILE:
                    c = light if abs(tx) <= 1 and ty == 0 else dark
                    draw.point((px_x, px_y), fill=c)


def draw_bush_sprite(draw, col, row, double=False):
    positions = [(-3, 2), (3, 3)] if double else [(0, 2)]
    for ox, oy in positions:
        cx, cy = col * TILE + 7 + ox, row * TILE + 8 + oy
        for r, shade in [(4, (36, 100, 36, 200)), (3, (52, 124, 52, 240)),
                         (2, (68, 148, 68, 255))]:
            for ty in range(-r, r + 1):
                for tx in range(-r, r + 1):
                    if tx * tx + ty * ty <= r * r:
                        px_x = cx + tx
                        px_y = cy + ty
                        if col * TILE <= px_x < (col + 1) * TILE and row * TILE <= px_y < (row + 1) * TILE:
                            draw.point((px_x, px_y), fill=shade)


def draw_flower_cluster(draw, col, row):
    cx, cy = col * TILE + 7, row * TILE + 3
    stems = [(-4, 10, (220, 80, 80)), (-1, 7, (220, 200, 60)),
             (3, 9, (180, 100, 200)), (6, 11, (240, 130, 60))]
    for fx, fy, fc in stems:
        x0, y0 = col * TILE + fx, row * TILE + fy
        draw.line([(x0, y0 + 3), (x0, y0 + 6)], fill=(60, 130, 60, 210))
        for dx, dy in [(0, 0), (-1, 0), (1, 0), (0, -1)]:
            px_x, px_y = x0 + dx, y0 + dy
            if col * TILE <= px_x < (col + 1) * TILE and row * TILE <= px_y < (row + 1) * TILE:
                draw.point((px_x, px_y), fill=fc + (255,))


def draw_grass_tuft(draw, col, row):
    cx, cy = col * TILE + 7, row * TILE + 12
    for gx, gyle in [(-5, 8), (-2, 11), (0, 12), (3, 10), (6, 9)]:
        draw.line([(cx + gx, cy), (cx + gx + 1, cy - gyle)], fill=(58, 128, 58, 220))


def draw_rock_sprite(draw, col, row, size="s"):
    cx, cy = col * TILE + 7, row * TILE + 9
    if size == "s":
        pts = [(cx-2, cy), (cx, cy-3), (cx+3, cy-1), (cx+3, cy+2), (cx, cy+2), (cx-2, cy+1)]
        draw.polygon(pts, fill=(138, 130, 120, 255), outline=(98, 92, 84, 255))
        draw.point((cx - 1, cy - 1), fill=(168, 160, 150, 255))
    elif size == "m":
        pts = [(cx-4, cy), (cx-1, cy-4), (cx+3, cy-4),
               (cx+5, cy-1), (cx+4, cy+2), (cx-1, cy+3), (cx-4, cy+1)]
        draw.polygon(pts, fill=(136, 128, 118, 255), outline=(96, 90, 82, 255))
        draw.point((cx-2, cy-2), fill=(166, 158, 148, 255))
        draw.point((cx,   cy-3), fill=(166, 158, 148, 255))
    elif size == "l":
        pts = [(cx-6, cy+1), (cx-3, cy-5), (cx+2, cy-6),
               (cx+6, cy-3), (cx+6, cy+2), (cx+2, cy+5), (cx-3, cy+5)]
        draw.polygon(pts, fill=(134, 126, 116, 255), outline=(94, 88, 80, 255))
        draw.point((cx-2, cy-3), fill=(164, 156, 146, 255))
        draw.point((cx+1, cy-4), fill=(164, 156, 146, 255))
        draw.line([(cx-1, cy), (cx+3, cy+2)], fill=(104, 98, 90, 255))


def draw_lily(draw, col, row):
    cx, cy = col * TILE + 7, row * TILE + 9
    for r, c in [(4, (28, 116, 56, 200)), (3, (44, 148, 80, 225))]:
        for ty in range(-r, r + 1):
            for tx in range(-r, r + 1):
                if tx * tx + ty * ty <= r * r:
                    px_x, px_y = cx + tx, cy + ty
                    if col * TILE <= px_x < (col + 1) * TILE and row * TILE <= px_y < (row + 1) * TILE:
                        draw.point((px_x, px_y), fill=c)
    # slice out of pad
    draw.point((cx + 3, cy - 1), fill=(0, 0, 0, 0))
    draw.point((cx + 2, cy - 2), fill=(0, 0, 0, 0))
    # flower
    for fx, fy, fc in [(0, -2, (240, 60, 120, 255)), (-1, -3, (220, 40, 100, 255)),
                       (1, -3, (240, 80, 140, 255)), (0, -4, (220, 60, 120, 255))]:
        draw.point((cx + fx, cy + fy), fill=fc)
    draw.point((cx, cy - 3), fill=(255, 220, 50, 255))


def draw_ripple_sprite(draw, col, row):
    import math
    cx, cy = col * TILE + 7, row * TILE + 8
    for r, alpha in [(6, 100), (4, 160), (2, 210)]:
        for step in range(24):
            a   = step / 24 * 2 * math.pi
            px_x = int(cx + r * math.cos(a))
            px_y = int(cy + r * 0.5 * math.sin(a))
            if col * TILE <= px_x < (col + 1) * TILE and row * TILE <= px_y < (row + 1) * TILE:
                draw.point((px_x, px_y), fill=(180, 220, 255, alpha))


def draw_reed_cluster(draw, col, row):
    cx, cy = col * TILE + 8, row * TILE
    for rx, rh in [(1, 10), (4, 13), (7, 9), (10, 12), (13, 11)]:
        x0 = col * TILE + rx
        draw.line([(x0, cy + 14), (x0, cy + 14 - rh)], fill=(80, 140, 80, 230))
        draw.ellipse([x0 - 1, cy + 13 - rh, x0 + 1, cy + 14 - rh],
                     fill=(58, 110, 58, 230))


def draw_flag(draw, col, row, flag_color=(220, 40, 40)):
    x, y = col * TILE, row * TILE
    draw.line([(x+7, y+2), (x+7, y+14)], fill=(220, 210, 190, 255))
    draw.point((x+7, y+14), fill=(160, 150, 130, 255))
    draw.polygon([(x+8, y+2), (x+13, y+5), (x+8, y+8)],
                 fill=flag_color + (255,))
    draw.ellipse([x+3, y+13, x+11, y+15], fill=(0, 0, 0, 70))


def draw_hole_cup(draw, col, row):
    cx, cy = col * TILE + 7, row * TILE + 8
    draw.ellipse([cx-5, cy-2, cx+5, cy+3], fill=(0, 0, 0, 70))
    draw.ellipse([cx-4, cy-4, cx+4, cy+4], fill=(18, 16, 14, 255))
    draw.arc([cx-4, cy-4, cx+4, cy+4], start=200, end=320,
             fill=(140, 130, 120, 255), width=1)


def draw_dist_marker(draw, col, row, color=(220, 40, 40)):
    x, y = col * TILE + 4, row * TILE + 1
    draw.rectangle([x+2, y+5, x+4, y+14], fill=(200, 195, 185, 255))
    draw.ellipse([x, y+1, x+7, y+8], fill=color + (255,))
    draw.ellipse([x+1, y+2, x+6, y+7], fill=(255, 255, 255, 180))


def draw_oob_stake(draw, col, row):
    x, y = col * TILE + 6, row * TILE
    draw.line([(x, y+3), (x, y+15)], fill=(240, 235, 225, 255))
    draw.line([(x+1, y+3), (x+1, y+15)], fill=(230, 225, 215, 255))
    draw.rectangle([x-1, y, x+2, y+4], fill=(220, 40, 40, 255))


def draw_sprinkler(draw, col, row):
    cx, cy = col * TILE + 7, row * TILE + 8
    draw.ellipse([cx-3, cy-3, cx+3, cy+3], fill=(158, 158, 168, 255))
    draw.ellipse([cx-2, cy-2, cx+2, cy+2], fill=(200, 200, 210, 255))
    draw.point((cx, cy), fill=(118, 118, 128, 255))


def draw_shadow_sprite(draw, col, row, size="s"):
    cx, cy = col * TILE + 7, row * TILE + 11
    rx, ry = (4, 2) if size == "s" else (6, 3)
    draw.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], fill=(0, 0, 0, 65))


def build_detail_trees():
    """Oak and pine tree canopy sprites, 2 rows."""
    img  = Image.new("RGBA", (COLS * TILE, 2 * TILE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for c in range(8):
        draw_oak(draw, c, 0)
    for c in range(8, 16):
        draw_pine(draw, c, 0)
    # Row 1: larger oak (paint twice side-by-side for visual variety)
    for c in range(8):
        draw_oak(draw, c, 1)
    for c in range(8, 16):
        draw_pine(draw, c, 1)
    path = os.path.join(OUT_DIR, "golf_detail_trees.png")
    img.save(path)
    print(f"  golf_detail_trees.png  ({img.width}x{img.height})")


def build_detail_plants():
    """Bushes, flowers and grass tufts, 2 rows."""
    img  = Image.new("RGBA", (COLS * TILE, 2 * TILE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Row 0: small bushes, double bushes, flowers, grass tufts
    for c in range(4):  draw_bush_sprite(draw, c,      0, double=False)
    for c in range(4):  draw_bush_sprite(draw, c + 4,  0, double=True)
    for c in range(4):  draw_flower_cluster(draw, c + 8,  0)
    for c in range(4):  draw_grass_tuft(draw, c + 12, 0)
    # Row 1: alternating for variety
    for c in range(4):  draw_bush_sprite(draw, c,      1, double=False)
    for c in range(4):  draw_flower_cluster(draw, c + 4,  1)
    for c in range(4):  draw_grass_tuft(draw, c + 8,  1)
    for c in range(4):  draw_bush_sprite(draw, c + 12, 1, double=True)
    path = os.path.join(OUT_DIR, "golf_detail_plants.png")
    img.save(path)
    print(f"  golf_detail_plants.png  ({img.width}x{img.height})")


def build_detail_rocks():
    """Rock sprites, 1 row: small×4, medium×4, large×4, clusters×4."""
    img  = Image.new("RGBA", (COLS * TILE, TILE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for c in range(4):  draw_rock_sprite(draw, c,      0, "s")
    for c in range(4):  draw_rock_sprite(draw, c + 4,  0, "m")
    for c in range(4):  draw_rock_sprite(draw, c + 8,  0, "l")
    # Clusters: two small rocks per tile
    for c in range(4):
        draw_rock_sprite(draw, c + 12, 0, "s")
        cx, cy = (c + 12) * TILE + 7, 9
        pts = [(cx+3, cy-2), (cx+5, cy-4), (cx+7, cy-2), (cx+7, cy), (cx+5, cy+1)]
        draw.polygon(pts, fill=(136, 128, 118, 255), outline=(96, 90, 82, 255))
    path = os.path.join(OUT_DIR, "golf_detail_rocks.png")
    img.save(path)
    print(f"  golf_detail_rocks.png  ({img.width}x{img.height})")


def build_detail_water():
    """Water feature sprites, 1 row: lily×4, ripple×4, foam×4, reeds×4."""
    img  = Image.new("RGBA", (COLS * TILE, TILE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for c in range(4):  draw_lily(draw, c, 0)
    for c in range(4):  draw_ripple_sprite(draw, c + 4, 0)
    # Foam patches
    rng = random.Random(555)
    for c in range(4):
        for _ in range(10):
            rx = rng.randint(2, 13)
            ry = rng.randint(2, 13)
            draw.ellipse([(c + 8) * TILE + rx - 1, ry - 1,
                          (c + 8) * TILE + rx + 1, ry + 1],
                         fill=(200, 230, 255, 180))
    for c in range(4):  draw_reed_cluster(draw, c + 12, 0)
    path = os.path.join(OUT_DIR, "golf_detail_water.png")
    img.save(path)
    print(f"  golf_detail_water.png  ({img.width}x{img.height})")


def build_detail_markers():
    """Flags, hole cup, yardage and course markers, 2 rows."""
    img  = Image.new("RGBA", (COLS * TILE, 2 * TILE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Row 0: flags (red×4, yellow×4), hole cup×4, distance markers×4
    for c in range(4):  draw_flag(draw, c,      0, flag_color=(220, 40, 40))
    for c in range(4):  draw_flag(draw, c + 4,  0, flag_color=(220, 220, 40))
    for c in range(4):  draw_hole_cup(draw, c + 8, 0)
    for c, col_v in enumerate([(220, 40, 40), (40, 120, 220),
                                (40, 180, 40), (200, 140, 40)]):
        draw_dist_marker(draw, c + 12, 0, color=col_v)
    # Row 1: yardage posts×4, OOB stakes×4, sprinklers×4, shadows×4
    for c, col_v in enumerate([(240, 230, 220), (220, 40, 40),
                                (40, 120, 220), (40, 180, 40)]):
        draw_dist_marker(draw, c, 1, color=col_v)
    for c in range(4):  draw_oob_stake(draw, c + 4,  1)
    for c in range(4):  draw_sprinkler(draw, c + 8,  1)
    for c in range(4):  draw_shadow_sprite(draw, c + 12, 1, size="s")
    path = os.path.join(OUT_DIR, "golf_detail_markers.png")
    img.save(path)
    print(f"  golf_detail_markers.png  ({img.width}x{img.height})")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Ground layer tilesets:")
    build_fairway()
    build_rough()
    build_green()
    build_tee()
    build_bunker()
    build_water()
    build_deeprough()
    build_trees()
    build_path()
    build_surfaces()
    build_hazard()

    print("\nDetail layer tilesets (RGBA):")
    build_detail_trees()
    build_detail_plants()
    build_detail_rocks()
    build_detail_water()
    build_detail_markers()

    print("\nDone. All files saved to assets/tilemaps/")
    print()
    print("Ground files (opaque - use on Ground layer):")
    print("  golf_fairway.png    golf_rough.png      golf_green.png")
    print("  golf_tee.png        golf_bunker.png     golf_water.png")
    print("  golf_deeprough.png  golf_trees.png      golf_path.png")
    print("  golf_surfaces.png   golf_hazard.png")
    print()
    print("Detail files (RGBA transparent - use on Detail layer):")
    print("  golf_detail_trees.png   golf_detail_plants.png")
    print("  golf_detail_rocks.png   golf_detail_water.png")
    print("  golf_detail_markers.png")
    print()
    print("Each ground file layout (16 cols x 3 rows):")
    print("  Row 0 cols  0- 3: plain variants")
    print("  Row 0 cols  4- 7: edge vs primary neighbour (N/S/E/W)")
    print("  Row 0 cols  8-11: corner vs primary neighbour (NW/NE/SE/SW)")
    print("  Row 0 cols 12-15: inner corner vs primary neighbour")
    print("  Row 1 cols  0- 3: edge vs secondary neighbour (N/S/E/W)")
    print("  Row 1 cols  4- 7: corner vs secondary neighbour (NW/NE/SE/SW)")
    print("  Row 1 cols  8-11: inner corner vs secondary neighbour")
    print("  Row 1 cols 12-15: extra variants")
    print("  Row 2: additional transitions (terrain-specific)")
