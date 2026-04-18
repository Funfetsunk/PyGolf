# Editor Upgrade — Three-Layer Course System

## Context

The editor currently implements a **two-layer** model (from `CourseEditorPlan.md` Phase E2):

| Current Layer | Purpose |
|---|---|
| Visual layer | Which tile from which tileset to draw |
| Attribute layer | Terrain type (Fairway, Rough, Bunker, etc.) for game logic |

This plan upgrades the system to **three layers**, splitting the visual layer into a **ground layer** (solid, full coverage) and a new **detail layer** (transparent overlaid sprites — trees, buildings, fences). The attribute layer becomes the **logic layer** (renamed for clarity, unchanged in meaning).

---

## The Three Layers

### Layer 1 — Ground (Visual, Opaque)

- Every tile is filled with exactly one ground tile
- Sources: existing opaque tilesets — `Hills.png`, `Tilled_Dirt.png`, `Water.png`
- Drawn first (bottom of the rendering stack)
- Equivalent to the current visual layer — no data format change needed here
- Represents the base surface: fairway grass, sand, water, rough, tee, green

### Layer 2 — Detail (Visual, Transparent)

- Each tile may be empty, or hold one detail sprite
- Sources: **new RGBA PNG tilesets** where backgrounds are transparent (alpha = 0)
- Drawn second, on top of the ground layer, with per-pixel alpha blending
- When a tree tile is placed, the trunk and canopy pixels are opaque; the surrounding pixels are transparent so the ground shows through
- Represents overlaid world objects: trees, tree clusters, buildings, fences, rocks, signage, flowers

### Layer 3 — Logic (Gameplay Attribute)

- Each tile holds a terrain code: `F` Fairway, `R` Rough, `D` Deep Rough, `B` Bunker, `W` Water, `T` Trees, `G` Green, `X` Tee
- Invisible in the final game render — used only by shot physics and AI
- Shown in the editor as a coloured semi-transparent overlay (same as current attribute mode)
- Completely independent of what the ground or detail layers show

**Critical point**: the three layers are independent. A tile can show lush fairway grass (ground), have no detail, but be coded `T` Trees (logic) if there were trees there in the past and the rough terrain penalty is intended. Or it can show a detailed tree sprite (detail) over rough ground (ground) while the logic layer says `R` Rough because the tree is decorative only. The designer has full control.

---

## Data Format Changes

### Current schema (v2)

```json
{
  "visual":      [["Hills:4:5", ...], ...],
  "attributes":  [["F", "R", ...], ...]
}
```

### New schema (v3)

```json
{
  "version": 3,
  "tilesets": [
    { "id": "Hills",       "path": "assets/tilemaps/Hills.png",       "transparent": false },
    { "id": "Tilled_Dirt", "path": "assets/tilemaps/Tilled_Dirt.png", "transparent": false },
    { "id": "Water",       "path": "assets/tilemaps/Water.png",       "transparent": false },
    { "id": "Details",     "path": "assets/tilemaps/Details.png",     "transparent": true  }
  ],
  "holes": [
    {
      "number": 1,
      "par": 4,
      "yardage": 310,
      "stroke_index": 7,
      "tee": [23, 33],
      "pin": [23, 3],
      "grid_cols": 48,
      "grid_rows": 36,
      "ground":  [["Hills:4:5", "Hills:4:5", ...], ...],
      "detail":  [["", "", "Details:2:0", ...], ...],
      "logic":   [["F", "F", "T", ...], ...]
    }
  ]
}
```

**Key points:**
- `ground` replaces `visual` — same format, same tile reference strings (`"SheetID:col:row"`)
- `detail` is a new parallel 2D array — empty string `""` means no detail on that tile
- `logic` replaces `attributes` — same terrain codes as before
- `tilesets` entry gains a `transparent` boolean — tells the loader to preserve alpha when loading
- All three arrays are always the same dimensions (`grid_cols × grid_rows`)

### Backward compatibility

Old v2 files (with `visual` + `attributes`) are automatically migrated on load:
- `visual` → becomes `ground`
- `detail` → initialised as all empty strings
- `attributes` → becomes `logic`

The loader writes v3 on any save, so files are upgraded once and stay current.

---

## Detail Tileset Requirements

### What makes a valid detail tileset

Detail tilesets must be **RGBA PNG files** (32-bit with alpha channel). The background of each tile must be transparent (alpha = 0). The foreground pixels (the actual object) can be any opacity.

```
╔══════╦══════╦══════╗
║ Tree ║ Fence║ Rock ║   ← each 32×32 tile
║  🌲  ║ ||||  ║  🪨  ║   ← opaque pixels
║  (α) ║  (α) ║  (α) ║   ← transparent background
╚══════╩══════╩══════╝
```

### Suggested initial detail tiles (Details.png)

A starter `Details.png` tileset should contain at minimum:

| Row 0 | Trees: single pine, single oak, small bush, large bush, dead tree |
| Row 1 | Clusters: 2-tree group, 3-tree group, dense canopy patch |
| Row 2 | Structures: fence segment H, fence segment V, fence corner, low wall, gate |
| Row 3 | Rocks & props: small rock, large rock, boulder, flower patch, tall grass |
| Row 4 | Buildings: small shed, score hut, cart path marker, distance marker |

Detail tiles can span multiple grid tiles (e.g. a large tree can be two tiles wide). In the editor, multi-tile stamps are supported by rubber-band selecting a region of the detail palette.

### Rendering rule

When the game draws a tile with a detail entry, it blits the detail surface using `pygame.BLEND_ALPHA_SDL2` or `pygame.Surface.set_alpha()`, which correctly blends the transparent pixels with whatever the ground layer drew first.

---

## Game Renderer Changes (`src/course/renderer.py`)

### Current render order

```
1. Draw all tiles using the visual layer (one blit per tile)
2. Blit baked surface to screen
```

### New render order

```
1. Bake ground layer → ground_surface  (opaque, SDL default)
2. Bake detail layer → detail_surface  (SRCALPHA, transparent background)
3. Composite: ground_surface → detail_surface blitted on top with alpha
4. Cache the composited result (only re-bake when course loads)
5. Each frame: blit composited_surface to screen using camera offset
6. Draw animated elements (flag wave) on top — unchanged
```

### Baking strategy

The ground and detail surfaces are baked once at course load (same as the current single bake). The detail surface is created with `pygame.SRCALPHA` so transparency is preserved. The two are composited into a single cached surface — no per-frame overhead, same draw performance as today.

If a detail tile is modified at runtime (not currently needed), the bake is simply called again.

### `TilesetManager` changes

The existing `TilesetManager` singleton must be told whether a tileset uses transparency:

```python
TilesetManager.instance().load("Details", "assets/tilemaps/Details.png", transparent=True)
```

When `transparent=True`, the sheet is loaded with `pygame.image.load(...).convert_alpha()` instead of `.convert()`. All tile extractions from that sheet preserve the alpha channel.

---

## Course Loader Changes (`src/course/course_loader.py`)

The loader already reads the JSON into `Hole` objects. Changes needed:

1. Detect v2 vs v3 by checking for `"ground"` key (v3) or `"visual"` key (v2)
2. For v2: map `visual → ground`, create empty `detail` grid, rename `attributes → logic`
3. Store all three grids on the `Hole` object:
   - `hole.ground_layer: list[list[str]]`
   - `hole.detail_layer: list[list[str]]`
   - `hole.logic_layer: list[list[str]]`
4. Pass `transparent=True` when registering detail tilesets with `TilesetManager`

### `Hole` class changes (`src/course/hole.py`)

Add storage for the new layers. The existing `grid` attribute (used by `get_terrain_at_pixel()`) maps to `logic_layer`. No game logic changes — just an internal rename.

---

## Editor UI Changes (`tools/editor/editor_app.py`)

### Layer control bar

Add a **layer control bar** directly above the canvas (below the toolbar). It contains:

```
[ Ground ▼ ]  [ Detail ▼ ]  [ Logic ▼ ]   👁 G  👁 D  👁 L
```

- Three buttons to set the **active layer** (the one currently being painted)
- Three eye-icon toggles to show/hide each layer in the viewport
- The active layer button is highlighted; others are dimmed
- Keyboard shortcut: `1` = active Ground, `2` = active Detail, `3` = active Logic

### Tileset palette behaviour per layer

| Active Layer | Palette shows | Paint tool writes to |
|---|---|---|
| Ground | Opaque tilesets (Hills, Tilled_Dirt, Water, custom) | `ground` array |
| Detail | Transparent tilesets (Details, custom RGBA) | `detail` array |
| Logic | Terrain code buttons (Fairway, Rough, etc.) | `logic` array |

When Detail is the active layer, only RGBA/transparent tilesets appear in the palette dropdown. The editor warns if you try to add a non-transparent tileset as a detail source.

An **Erase tool** (keyboard `E`) clears the active layer's tile to empty:
- Ground: resets to the default background tile
- Detail: sets to `""` (no detail)
- Logic: resets to `R` (Rough) as a safe default

### Canvas viewport compositing

The editor viewport always renders all visible layers in order:

```
Ground layer tiles    (always visible unless hidden)
      ↓
Detail layer tiles    (alpha-composited on top; transparent areas show ground)
      ↓
Logic overlay         (semi-transparent coloured overlay, shown when Logic is active or toggled on)
      ↓
Tee/Pin markers
      ↓
Grid lines (optional)
```

The logic overlay uses the same colour-coded system as the current attribute overlay:
- Green = Fairway/Tee/Green
- Yellow = Rough/Deep Rough
- Tan = Bunker
- Blue = Water
- Dark green = Trees

### Eyedropper (right-click) per layer

Right-clicking samples from the **active layer**:
- Ground active → picks up the ground tile under cursor
- Detail active → picks up the detail tile under cursor (or clears selection if empty)
- Logic active → selects the matching terrain code button

### Detail palette — multi-tile stamp

In the detail palette, click-drag to select a **rectangular region** of the detail tileset. Painting then stamps the entire selected region as a block. This allows large trees or buildings that span 2×2 or 3×2 tiles to be placed as a single operation.

### Auto-derive in three layers

The existing auto-derive system (visual tile → attribute) is updated to:
- Ground tile from a known tileset (Hills, Tilled_Dirt, Water) → auto-sets Logic layer
- Detail tile placed → optionally auto-sets Logic to `T` Trees (configurable toggle: "Tree detail → Trees logic")

Auto-derive can be turned off per-tile with a right-click override.

---

## New Keyboard Shortcuts

| Key | Action |
|---|---|
| `1` | Set Ground as active layer |
| `2` | Set Detail as active layer |
| `3` | Set Logic as active layer |
| `Shift+1` | Toggle Ground layer visibility |
| `Shift+2` | Toggle Detail layer visibility |
| `Shift+3` | Toggle Logic layer visibility |
| `E` | Erase active layer at cursor |
| `Ctrl+D` | Duplicate active layer selection |

All existing shortcuts remain unchanged.

---

## New File: `assets/tilemaps/Details.png`

A new transparent-background tileset must be created (or sourced) before the detail layer is usable. This can be done:

**Option A — Pixel art from scratch**: Use Aseprite, LibreSprite, or similar. Draw tree/object sprites on a transparent canvas. Export as RGBA PNG.

**Option B — Adapt existing sprites**: The current procedural `_trees()` renderer in `renderer.py` draws dark canopy circles. These can be rasterised to a PNG for a quick starting tileset.

**Option C — Free tileset assets**: Open-licence top-down RPG/strategy tilesets often include trees and objects usable as detail tiles (check itch.io for CC0/CC-BY assets).

The plan is not blocked waiting for the final art — the code can be built and tested with placeholder single-colour RGBA tiles immediately.

---

## Implementation Phases

### Phase EU1 — Data Layer (backend only, no visible change)

**Goal:** All three layers exist in the data model and round-trip through save/load.

- [ ] Update `Hole` class to store `ground_layer`, `detail_layer`, `logic_layer`
- [ ] Update `course_loader.py`: read v3 format; auto-migrate v2 files on load
- [ ] Update `dialogs.py` (editor): write v3 format on save
- [ ] Add `transparent` flag to `TilesetManager.load()`
- [ ] Update `renderer.py`: read `ground_layer` for baking (detail layer render is a stub for now)

**Test:** Save a course, reload it, confirm no data is lost. Game still runs unchanged.

---

### Phase EU2 — Detail Render Pipeline

**Goal:** Detail tiles blit with transparency over the ground layer in the game.

- [ ] `renderer.py`: create `detail_surface` with `pygame.SRCALPHA` during bake
- [ ] Iterate `detail_layer`, blit each non-empty tile from its RGBA tileset onto `detail_surface`
- [ ] Composite: blit `detail_surface` onto `ground_surface` after ground bake completes
- [ ] `TilesetManager`: support `.convert_alpha()` path for transparent sheets
- [ ] Create placeholder `Details.png` (8×4 grid of RGBA placeholder tiles with visible test patterns)
- [ ] Manual test: place detail tiles in a test course JSON; confirm transparency works in game

**Test:** A course with detail layer entries renders correctly. Ground shows through transparent detail pixels.

---

### Phase EU3 — Editor Layer Switcher

**Goal:** The editor UI can switch between three layers and paint each independently.

- [ ] Add layer control bar to `editor_app.py` (above canvas)
- [ ] Wire `1/2/3` shortcuts to active layer selection
- [ ] Wire `Shift+1/2/3` to layer visibility toggles
- [ ] Tileset palette dropdown: filter to opaque tilesets when Ground is active; filter to transparent tilesets when Detail is active; hide tileset, show terrain buttons when Logic is active
- [ ] Canvas paint tool writes to the correct layer array based on active layer
- [ ] Canvas viewport composites all three layers each frame in correct order
- [ ] Eyedropper reads from active layer
- [ ] Erase tool (`E`) clears active layer at cursor

**Test:** Paint on all three layers independently in the editor; save and confirm all three arrays are correct in the JSON.

---

### Phase EU4 — Detail Palette Polish

**Goal:** Detail painting is comfortable for building real courses.

- [ ] Multi-tile stamp: click-drag in detail palette to select a region; paint stamps the whole region
- [ ] Detail layer preview: semi-transparent dim overlay when Ground is active (so detail is always visible but not dominant)
- [ ] Erase mode for detail (`E` while Detail active): single tile or shift+drag to erase rectangle
- [ ] Auto-derive: option to auto-set Logic to `T` Trees when a detail tree tile is placed
- [ ] Import RGBA PNG into editor and register as a detail tileset source

**Test:** Build a test hole using all three layers; play it in the game; confirm visual quality and logic layer accuracy.

---

### Phase EU5 — Validation & Migration

**Goal:** Existing courses and saved files all work correctly with no manual intervention.

- [ ] Auto-migration: any v2 file opened in the editor is silently upgraded to v3 on save
- [ ] Validation: warn if any detail tile references a non-RGBA tileset
- [ ] Validation: warn if any detail tile is placed outside the course boundary
- [ ] Update all existing Python-built courses (`courses_library.py`) to export their visual/logic data in a form compatible with the new renderer (ground layer from existing tileset lookups; detail layer empty)
- [ ] Update `course_loader.py` to handle Python-built courses that set only two layers

**Test:** Load every existing course; confirm no visual regressions; confirm game logic unchanged.

---

## Summary of Changes by File

| File | Change |
|---|---|
| `src/course/hole.py` | Add `ground_layer`, `detail_layer`, `logic_layer` attributes |
| `src/course/course_loader.py` | Read v3 format; v2 auto-migration |
| `src/course/renderer.py` | Three-layer bake: ground (opaque) + detail (SRCALPHA) composite |
| `src/utils/tileset.py` | `transparent` flag on load; `.convert_alpha()` path |
| `tools/editor/editor_app.py` | Layer control bar; `1/2/3` shortcuts; layer visibility toggles |
| `tools/editor/canvas.py` | Paint/erase/eyedropper reads and writes correct layer |
| `tools/editor/tileset_panel.py` | Filter palette by layer type; multi-tile stamp for detail |
| `tools/editor/dialogs.py` | Write v3 JSON; v2→v3 migration on load |
| `assets/tilemaps/Details.png` | New RGBA detail tileset (to be created) |

**Files that do NOT change:**
- `src/golf/terrain.py` — terrain codes unchanged
- `src/golf/shot.py`, `ball.py` — no change
- `src/states/golf_round.py` — no change
- All career, player, tournament, tour files — no change

---

## Open Questions

1. **Multi-tile detail objects** — do trees/buildings span multiple tiles as a single stamp, or is each tile placed individually? Recommendation: support both. Single-tile placement for small details; multi-tile stamp for larger objects.

2. **Detail layer Z-ordering** — currently all detail tiles render at the same Z level. If a building is placed, should it occlude the player/ball when the ball passes "behind" it? Deferred — implement flat rendering first, add Z-layers as a future phase if needed.

3. **Detail collision** — should detail tiles add any gameplay effect independently of the logic layer, or is the logic layer always the authority? Recommendation: logic layer is always the authority. Detail is purely cosmetic.

4. **Animated detail tiles** — waving flag is already animated outside the bake. Could detail tiles animate (rustling trees, flowing water surface)? Deferred — out of scope for this plan.
