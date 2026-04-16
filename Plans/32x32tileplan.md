# 32×32 Tile Upgrade Plan

## 1. Overview

This plan covers three related changes:

1. **Tile size** — source PNG tiles change from 16×16 to 32×32 pixels, displayed natively at 32px per tile (no scaling).
2. **Bigger courses** — the default hole grid grows from 48×36 to 80×60 tiles so that every hole is larger than the screen and the camera must scroll to follow the ball.
3. **Remove grid lines** — the faint 1-pixel grid visible in the game is eliminated.

The camera/scrolling system already exists in `golf_round.py` — it just has nothing to scroll today because the world is exactly the same size as the viewport. Changing the tile size and grid dimensions will activate it automatically with no structural rewrites.

---

## 2. Yardage Per Tile — The Maths

The game uses a fixed constant: **1 tile = 10 yards.** This stays the same after the upgrade. Only the pixel representation of that tile changes.

### Current numbers

| | Value |
|---|---|
| Source tile | 16 × 16 px |
| Display tile | 20 × 20 px (scaled up) |
| Grid | 48 cols × 36 rows |
| World size (pixels) | 960 × 720 |
| Viewport | 960 × 720 |
| World size (yards) | 480 × 360 yards |
| Yards per pixel | 10 ÷ 20 = **0.5 yds/px** |

The world exactly matches the viewport, so the camera never moves.

### New numbers

| | Value |
|---|---|
| Source tile | 32 × 32 px |
| Display tile | 32 × 32 px (no scaling — 1 : 1) |
| Default grid | 80 cols × 60 rows |
| World size (pixels) | 2560 × 1920 |
| Viewport | 960 × 720 (unchanged) |
| World size (yards) | 800 × 600 yards |
| Yards per pixel | 10 ÷ 32 = **0.3125 yds/px** |

The world is now **2.67× wider** and **2.67× taller** than the viewport. The camera must scroll to keep up with the ball.

### What the player sees at any moment

With a 960 × 720 viewport and 32 px/tile:

- **Horizontal:** 960 ÷ 32 = **30 tiles = 300 yards** visible at once
- **Vertical:** 720 ÷ 32 = **22.5 tiles ≈ 225 yards** visible at once

This gives a good close-up view of the immediate play area while the rest of the hole scrolls into view as the ball advances.

### Per-par recommended grid sizes

| Par | Typical length | Recommended grid | World (yards) |
|---|---|---|---|
| Par 3 | 100–250 yds | 64 × 36 tiles | 640 × 360 yds |
| Par 4 | 250–450 yds | 80 × 54 tiles | 800 × 540 yds |
| Par 5 | 450–600 yds | 80 × 72 tiles | 800 × 720 yds |
| Default (editor) | — | **80 × 60 tiles** | 800 × 600 yds |

The course editor already stores `grid_cols` and `grid_rows` per hole, so each hole can have its own grid size.

---

## 3. Why No Scaling

At 16×16 source tiles the game scaled up to 20 px to give the tiles a softer, slightly larger look. At 32×32 source the tiles are already large enough to be displayed at exactly 32 px without any scaling. This means:

- **Crisper pixel art** — no interpolation artifacts
- **Simpler code** — the `pygame.transform.scale` call in `TilesetManager` still works, but because source and target are the same size it is effectively a copy
- **Editor and game agree** — both use `TILE_SIZE = 32` so what the editor shows is exactly what the player sees

---

## 4. Files to Change

### 4.1 `src/utils/tileset.py`

| Change | From | To |
|---|---|---|
| `SOURCE_TILE` constant | `16` | `32` |
| `load()` default `tile_size` parameter | `20` | `32` |

The extraction logic (`pygame.Rect(col * SOURCE_TILE, ...)`) reads tiles from the sheet at the new 32-pixel pitch. The scale call in `_extract` stays but becomes a no-op since source and destination are equal.

---

### 4.2 `src/course/renderer.py`

| Change | Detail |
|---|---|
| `TILE_SIZE = 20` | Change to `32` |
| `self._tileset.load(assets_dir, tile_size=TILE_SIZE)` | Picks up the new constant automatically |
| **Remove the TEE border draw** | Line ~164: `pygame.draw.rect(result, (200, 230, 200), (0, 0, tile_size, tile_size), 1)` — delete this line entirely. It draws a 1-px white box around every tee tile, which is the main source of visible grid lines. |
| Procedural stripe widths | `_stripe(..., width=4)` looks fine at 20 px but will show narrow tile-boundary seams at 32 px. Increase to `width=8` for fairway/tee/green stripe functions so the stripe pattern is proportionally correct. |

The `_build_course_surface`, `draw`, `world_to_screen`, `world_size` methods all use `self.tile_size` and need no changes — they scale automatically.

---

### 4.3 `src/data/courses_data.py`

The existing 18-hole Greenfields course is defined in tile coordinates against a 48×36 grid. These coordinates will look wrong (too small, in the wrong corners) on the new 80×60 grid.

**Two options:**

- **Option A (quick):** Keep the old courses running on the old 48×36 grid for now by leaving the `_COLS = 48` / `_ROWS = 36` constants unchanged. Old courses will display in the top-left corner of the new world — playable but not ideal.
- **Option B (recommended):** Redesign the 18 holes using the course editor at 80×60 (or per-par sizes from the table above) and export them as JSON files into `data/courses/amateur/`. Once the game's JSON course loader (Phase E4) is in place, the Python courses can be retired.

Update the module docstring to reflect the new tile size regardless.

---

### 4.4 `src/course/hole.py`

| Change | Detail |
|---|---|
| Comment on line 12 | Update `tile_size pixels per tile is set in the renderer (default 20 px)` → `32 px` |
| `make_sample_hole()` | Change `rows, cols = 36, 48` → `rows, cols = 60, 80` |
| Comment on line 64–65 | Update world-size comment from `960 × 720` to `2560 × 1920` |

---

### 4.5 `src/golf/shot.py`

No code change required. The formula on line ~118:

```python
yards_per_pixel = 10.0 / tile_size
```

reads `tile_size` from the renderer at runtime, so it automatically recalculates to `10 / 32 = 0.3125` with the new tile size. Shot distances in yards remain meaningful and unchanged.

---

### 4.6 `src/states/golf_round.py`

The camera follow system already exists and is already called every frame. Currently it has nothing to do because:

```python
max(0, world_w - VIEWPORT_W)  # = max(0, 960 - 960) = 0  → camera never moves
```

After the change:

```python
max(0, 2560 - 960)  # = 1600  → camera can move up to 1600 px horizontally
max(0, 1920 - 720)  # = 1200  → camera can move up to 1200 px vertically
```

**No code changes needed.** The existing `_follow_camera` and `_clamp_camera` methods activate automatically.

The `VIEWPORT_W = 960` and `VIEWPORT_H = 720` constants stay the same — the viewport does not change, only the world behind it does.

---

### 4.7 `tools/editor/canvas.py`

| Change | From | To |
|---|---|---|
| `SOURCE_TILE` | `16` | `32` |
| `BASE_TILE` | `20` | `32` |

The default zoom index stays at 1 (1.0×). At 1× zoom with 32 px tiles, the editor canvas will show the world in the same proportion as the game. A full 80×60 grid at 1× takes 2560×1920 px — larger than the canvas area, so the designer will use zoom-out to get an overview and zoom-in to paint detail. This is correct behaviour.

---

### 4.8 `tools/editor/tileset_panel.py`

| Change | From | To |
|---|---|---|
| `SOURCE_TILE` | `16` | `32` |
| `DISPLAY_TILE` | `20` | `32` |

Tiles in the palette will display at 32×32, which is larger and easier to click. The tile grid layout recalculates automatically.

---

### 4.9 `tools/editor/dialogs.py`

| Change | From | To |
|---|---|---|
| `make_empty_hole` default `cols` | `48` | `80` |
| `make_empty_hole` default `rows` | `36` | `60` |
| `make_empty_course` default `cols` | `48` | `80` |
| `make_empty_course` default `rows` | `36` | `60` |

New holes created in the editor will default to the 80×60 grid. Existing saved JSON files that specify `grid_cols` and `grid_rows` in each hole continue to work because the loader reads those values directly rather than using defaults.

---

## 5. Removing Grid Lines

Grid lines in the game come from two sources. Both are eliminated.

### Source 1 — Explicit TEE border (fix: delete one line)

In `renderer.py`, after each tee tile is built, a 1-pixel white rectangle is drawn around it:

```python
pygame.draw.rect(result, (200, 230, 200), (0, 0, tile_size, tile_size), 1)
```

This creates a visible white grid within the tee box area. **Delete this line.** The tee area is already visually distinguishable by its lighter colour; the border is not needed.

### Source 2 — Stripe seams in procedural tiles (fix: widen stripes)

The fairway, tee, and green procedural fallback textures use 4-pixel-wide vertical stripes (`width=4`). At 20 px tiles these stripes divide cleanly. At 32 px they create a visible seam at each tile boundary because the stripe phase resets at the start of each tile.

Fix: increase the stripe width from `4` to `8` in `_make_procedural_tile`. The longer stripes will align less obviously at tile borders and the seam will be barely visible.

The permanent solution — which eliminates both sources entirely — is to use proper 32×32 tileset PNG files where the grass, sand, and water textures are designed to tile seamlessly. When a tileset is loaded, the renderer uses those textures instead of the procedural fallback, and no seams exist at all.

> **Tileset art specification:** Each tile in a tileset PNG must be exactly 32 × 32 pixels, aligned to a strict grid with no padding between tiles. The texture within each tile should tile seamlessly with neighbouring tiles of the same terrain type. Different terrain types (e.g. fairway next to rough) can have visible edges — this is intentional and handled by `_draw_border_shadows`.

---

## 6. Summary of All Constants Changed

| File | Constant | Old | New |
|---|---|---|---|
| `src/utils/tileset.py` | `SOURCE_TILE` | `16` | `32` |
| `src/utils/tileset.py` | `tile_size` default | `20` | `32` |
| `src/course/renderer.py` | `TILE_SIZE` | `20` | `32` |
| `src/course/hole.py` | `make_sample_hole` cols/rows | `48, 36` | `80, 60` |
| `tools/editor/canvas.py` | `SOURCE_TILE` | `16` | `32` |
| `tools/editor/canvas.py` | `BASE_TILE` | `20` | `32` |
| `tools/editor/tileset_panel.py` | `SOURCE_TILE` | `16` | `32` |
| `tools/editor/tileset_panel.py` | `DISPLAY_TILE` | `20` | `32` |
| `tools/editor/dialogs.py` | `make_empty_hole` cols/rows | `48, 36` | `80, 60` |
| `tools/editor/dialogs.py` | `make_empty_course` cols/rows | `48, 36` | `80, 60` |

**No changes required in:**
- `src/states/golf_round.py` — camera system activates automatically
- `src/golf/shot.py` — yardage formula is already dynamic
- Any UI or HUD file — viewport dimensions are unchanged

---

## 7. Implementation Order

1. Change `SOURCE_TILE` and `TILE_SIZE` constants in `tileset.py` and `renderer.py`
2. Delete the TEE border line and widen procedural stripes in `renderer.py`
3. Update editor constants (`canvas.py`, `tileset_panel.py`, `dialogs.py`)
4. Update `hole.py` defaults and comments
5. Run the game — camera scrolling will be live; verify with the existing Greenfields course (it will appear small in the world — that is expected until courses are redesigned)
6. Run the editor — import a 32×32 tileset and build a test hole at 80×60 to confirm everything looks correct
7. Redesign courses using the editor (Phase E4 work — once JSON course loading is implemented, retire the old Python-defined courses)
