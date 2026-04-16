# Course Editor — Development Plan

---

## 1. Overview

The course editor is a standalone development tool for creating and editing golf courses for the game. It lets you paint terrain visually using imported tilemap PNGs, assign gameplay attributes (water, bunker, green, etc.) to regions, set hole metadata (par, yardage, tee and pin positions), and export finished courses directly into the game's data pipeline.

The editor is not a game feature — players never see it. It is a developer tool, used only during course production.

---

## 2. Same Repo or Separate Repo?

**Decision: Same repository, separate entry point.**

### Why not a separate repo?

A separate repository creates a permanent synchronisation problem. Every time the game's terrain types, data formats, or asset folder layout changes, the editor repo must also be updated. There is no shared ground truth. Assets would need to be duplicated or managed across two locations. This is a maintenance burden that grows over time, especially as the game gains six tours and dozens of courses.

### Why the same repo works well

| Concern | How it is handled |
|---|---|
| Shared terrain definitions | Editor imports `src.golf.terrain` directly — one source of truth |
| Shared asset folder | `assets/tilemaps/` is used by both editor and game — no copying |
| Shared course format | One JSON schema, one loader, used everywhere |
| Player access | Players never run `editor.py` — it is a dev-only entry point |
| Distribution | When packaging the game for players, exclude `tools/` — one line in a build script |

This is standard practice in game development. Unity, Godot, and every major engine keep their level editors in the same project.

### Folder structure

```
Golf/
├── main.py              ← game entry point (players run this)
├── editor.py            ← editor entry point (developers run this)
├── tools/
│   └── editor/
│       ├── __init__.py
│       ├── editor_app.py        # top-level editor loop
│       ├── canvas.py            # tile painting viewport
│       ├── tileset_panel.py     # tileset palette (left panel)
│       ├── attribute_panel.py   # terrain attribute picker (right panel)
│       ├── hole_panel.py        # hole metadata (par, yardage, tee, pin)
│       ├── course_panel.py      # course-level info and hole list
│       └── dialogs.py           # file open/save wrappers
├── assets/
│   └── tilemaps/        ← shared — same files in editor and game
├── data/
│   └── courses/         ← NEW: JSON course files output by the editor
│       ├── amateur/
│       ├── challenger/
│       ├── development/
│       ├── continental/
│       ├── world/
│       └── grand/
└── src/
    ├── golf/terrain.py  ← shared terrain definitions
    └── course/
        ├── hole.py          ← shared
        ├── course.py        ← shared
        └── course_loader.py ← NEW: loads JSON courses (used by game)
```

---

## 3. Technology Stack

The editor uses the same base technology as the game — **Python + Pygame** — so no new language or runtime is needed. Two additions are required:

| Package | Purpose | Install |
|---|---|---|
| `pygame` | Canvas rendering (already installed) | — |
| `pygame_gui` | UI panels, buttons, sliders, input fields | `pip install pygame_gui` |
| `tkinter` | File open/save dialogs | stdlib — no install needed |

`pygame_gui` gives proper windowed UI components (panels, dropdown menus, text inputs, scrollable lists) on top of a Pygame surface. It follows the same rendering loop as the game, so there is no context switching. `tkinter` is only used for its `filedialog` module — one function call to open a native OS file picker.

**Why not a full GUI framework (PyQt, wxPython)?**
A full GUI framework would provide more polished UI widgets, but introduces a second major dependency and a second rendering paradigm. The course canvas (where tiles are painted) would need to be embedded as a widget — complex and fragile. Staying in Pygame keeps the canvas first-class and the rendering consistent with how courses actually look in the game.

---

## 4. Two-Layer Course Model

This is the most important architectural decision. The current game uses a single terrain attribute layer (each tile is a `Terrain` enum value) and the renderer automatically picks the right tileset tile. The editor introduces a second, separate layer.

### Layer 1 — Visual layer (what it looks like)
Each tile stores a reference to a specific tile in a specific tileset PNG: `("Hills", col, row)`. This controls the pixel art appearance of the course. The game renderer uses this layer when it exists to draw tiles exactly as the designer laid them out.

### Layer 2 — Attribute layer (how the game engine treats it)
Each tile stores a `Terrain` enum value: `FAIRWAY`, `ROUGH`, `BUNKER`, `WATER`, `TREES`, `GREEN`, `TEE`. This controls shot physics — distance modifiers, accuracy penalties, hazard rules. This is the layer the game logic reads.

### Why two layers?

Without two layers, every tile looks exactly like its terrain type. Every bunker looks identical. Every fairway looks the same. Two layers allow:
- Visual variety: a fairway with different grass patterns in different areas
- Artistic control: place exactly the tiles you want, not whatever the auto-renderer picks
- Realism: rough at the edge of a bunker can transition gradually visually, while still being either ROUGH or BUNKER for gameplay

### Linking layers

In the editor, the attribute layer can be painted independently OR it can be **auto-derived** from the visual layer via a configurable mapping:

```
Hills.png tile (4,5) → auto-attribute: FAIRWAY
Hills.png tile (3,5) → auto-attribute: ROUGH
Tilled_Dirt.png any tile → auto-attribute: BUNKER
Water.png any tile → auto-attribute: WATER
```

The designer can override any auto-derived attribute. This means you can paint quickly using just the visual layer (attributes follow automatically) and then manually adjust specific tiles.

---

## 5. Course Data Format

Courses are stored as **JSON files** in `data/courses/<tour>/`. This is the single format used by both the editor (saves) and the game (loads).

```json
{
  "version": 2,
  "course": {
    "name": "Greenfields Golf Club",
    "tour": "amateur",
    "par": 72
  },
  "tilesets": [
    { "id": "Hills",       "path": "assets/tilemaps/Hills.png" },
    { "id": "Tilled_Dirt", "path": "assets/tilemaps/Tilled_Dirt.png" },
    { "id": "Water",       "path": "assets/tilemaps/Water.png" }
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
      "visual": [
        ["Hills:4:5", "Hills:4:5", "Hills:0:0", ...],
        ...
      ],
      "attributes": [
        ["F", "F", "T", ...],
        ...
      ]
    }
  ]
}
```

**Key points:**
- `visual` and `attributes` are parallel 2D arrays — same dimensions
- Tileset references use `"SheetID:col:row"` strings — human-readable and portable
- Attribute codes match the existing game: `F`=Fairway, `R`=Rough, `D`=Deep Rough, `B`=Bunker, `W`=Water, `T`=Trees, `G`=Green, `X`=Tee
- Paths to tilesets are relative to the project root — work on any machine
- `version` field allows format migration if the schema changes later

### Game integration

A new `src/course/course_loader.py` reads these JSON files and returns `Course` objects exactly like the current `make_greenfields_course()` factory functions do. The game's state machine does not need to change.

```python
from src.course.course_loader import load_course
course = load_course("data/courses/amateur/greenfields.json")
```

The existing Python-based courses (`courses_data.py`) continue to work unchanged during the transition. New courses go through the JSON pipeline immediately.

---

## 6. Editor UI Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TOOLBAR: [New] [Open] [Save] [Export] | [Undo] [Redo] | [Grid] [Zoom] │
├────────────────┬────────────────────────────────────────┬───────────────┤
│  TILESET       │                                        │  HOLE INFO    │
│  PALETTE       │          COURSE CANVAS                 │               │
│                │                                        │  Hole:  [1▾]  │
│  [Import PNG]  │   (paint tiles here, zoom, pan)        │  Par:   [4  ] │
│                │                                        │  Yds:   [310 ]│
│  [Sheet view]  │   ← tile grid with visual layer        │  SI:    [7   ]│
│  Click tile    │      and attribute overlay toggle      │               │
│  to select     │                                        │  [Set Tee]    │
│                │                                        │  [Set Pin]    │
│                │                                        │               │
├────────────────┤                                        ├───────────────┤
│  ATTRIBUTE     │                                        │  COURSE INFO  │
│  BRUSH         │                                        │               │
│                │                                        │  Name: [    ] │
│  ○ Fairway     │                                        │  Tour: [    ] │
│  ○ Rough       │                                        │  Par:  72     │
│  ○ Deep Rough  │                                        │               │
│  ○ Bunker      │                                        │  Holes:       │
│  ○ Water       │                                        │  1 2 3 4 5    │
│  ○ Trees       │                                        │  6 7 8 9 ...  │
│  ○ Green       │                                        │               │
│  ○ Tee Box     │                                        │  [Add Hole]   │
│                │                                        │  [Del Hole]   │
│  [Auto-derive] │                                        │               │
└────────────────┴────────────────────────────────────────┴───────────────┘
│  STATUS BAR: Tile (12, 8) | Terrain: FAIRWAY | Zoom: 2x | Greenfields H1│
└─────────────────────────────────────────────────────────────────────────┘
```

### Panels

**Tileset Palette (left)**
- Import any PNG tileset with `[Import PNG]`
- Tile grid display — click to select a tile as the active paint brush
- Multiple imported sheets are selectable via a dropdown
- Hovering a tile shows its pixel coordinates (sheet:col:row)

**Course Canvas (centre)**
- Zoomable (1x–8x) and pannable (middle mouse drag or spacebar+drag)
- Left-click paints the active brush (visual tile or attribute)
- Right-click samples the tile under the cursor (eyedropper)
- Shift+drag for rectangle fill
- Toggle overlay: `[V]` visual only, `[A]` attributes highlighted (colour-coded), `[B]` both
- Grid lines toggle
- Tee and pin positions shown as markers (click `[Set Tee]` / `[Set Pin]` then click canvas)

**Hole Info (top right)**
- Hole selector (1–18)
- Par, yardage, stroke index text inputs
- Set Tee and Set Pin click-mode buttons

**Course Info (bottom right)**
- Course name, tour assignment
- Holes list with quick-navigate
- Add/delete holes

**Toolbar**
- New, Open, Save (JSON), Export (also triggers game-ready output)
- Undo/Redo (up to 50 operations)
- Grid toggle, zoom level

---

## 7. Core Features

### Painting

| Tool | Shortcut | Behaviour |
|---|---|---|
| Tile brush | Left-click | Paint visual tile at cursor |
| Attribute brush | A + left-click | Paint terrain attribute at cursor |
| Flood fill | F + left-click | Fill connected region with active brush |
| Rectangle fill | Shift + drag | Fill rectangle with active brush |
| Eyedropper | Right-click | Pick tile/attribute under cursor |
| Erase | E + left-click | Reset tile to default (rough / no visual) |

### Tileset management

- Import any number of PNG tilesets
- Each tileset is registered in the course JSON and referenced by ID
- Tilesets used in a course are validated on save — missing files are flagged
- Auto-derive attributes toggle: when on, painting a visual tile from a known sheet (Hills, Tilled_Dirt, Water) also sets the matching attribute automatically using the same mapping the game renderer uses

### Hole management

- Add / remove holes (1–18)
- Copy a hole to another slot
- Resize the grid per-hole (default 48×36)
- Preview button renders the hole exactly as the game would display it

### Validation

On save and export, the editor checks:
- Every hole has a valid tee and pin position
- Tee is on a TEE attribute tile, pin is on a GREEN attribute tile
- No holes reference missing tileset files
- Par, yardage, stroke index are all set
- Warnings (not errors) for: very large grids, no bunkers or water, no rough border

---

## 8. Multi-Tour Support

Courses are organised by tour from day one. The JSON `"tour"` field and folder structure handle this:

```
data/courses/
├── amateur/
│   └── greenfields.json
├── challenger/
│   ├── lakeside.json
│   └── riverside.json
├── development/
├── continental/
├── world/
└── grand/
    ├── the_open.json
    ├── masters_classic.json
    ├── national_championship.json
    └── heritage_cup.json
```

The editor's `[Open]` dialog defaults to `data/courses/` and shows the tour subfolders. The Course Info panel has a Tour dropdown matching the six tour levels. Saving a file automatically places it in the correct subfolder.

The game's tour data (`src/data/tours_data.py`) references courses by filename. When a course is edited and re-saved, the game picks up changes automatically — no manual wiring needed.

---

## 9. Asset Pipeline

### Rule: assets live in one place

All tileset PNGs live in `assets/tilemaps/`. The editor reads from there. The game reads from there. There is no copying, no syncing, no separate asset folder.

### Adding a new tileset

1. Drop the PNG into `assets/tilemaps/`
2. Open the editor, click `[Import PNG]` and select the file
3. The editor registers it — it is now available for painting
4. Courses that use it reference it by relative path `assets/tilemaps/filename.png`
5. The game's `TilesetManager` will load it automatically when the course is loaded (since it uses the same path)

### What the editor exports

On `[Export]`, the editor:
1. Validates the course (see above)
2. Writes the JSON file to `data/courses/<tour>/coursename.json`
3. Writes a human-readable summary to stdout (hole count, par, tour)

The game's `course_loader.py` reads these files. No compilation, no build step — edit, save, run game.

---

## 10. Development Phases

### Phase E1 — Foundations
- `editor.py` entry point, Pygame window, `pygame_gui` layout
- Canvas with pan and zoom
- Tileset palette: load PNG, display tile grid, select tile
- Left-click paint on canvas (visual layer only)
- Grid toggle, zoom controls
- Save and load JSON (visual layer only, no attributes yet)

**Deliverable:** Open a tileset, paint tiles onto a blank grid, save and reopen.

---

### Phase E2 — Attribute Layer
- Attribute brush panel (Fairway, Rough, Bunker, Water, Trees, Green, Tee)
- Attribute overlay rendering (colour-coded semi-transparent layer)
- Auto-derive attributes from known tileset mappings
- Toggle: visual / attributes / both
- Flood fill tool

**Deliverable:** Full two-layer editing. Paint visuals and gameplay attributes independently.

---

### Phase E3 — Hole Metadata & Validation
- Hole info panel (par, yardage, stroke index)
- Set Tee and Set Pin click-mode
- Multi-hole support (add, remove, navigate, copy)
- Course info panel (name, tour)
- Validation on save with warning/error display

**Deliverable:** A complete 18-hole course can be built and validated from scratch.

---

### Phase E4 — Game Integration
- `src/course/course_loader.py` — load JSON courses into `Course`/`Hole` objects
- Game renderer updated to use visual layer from JSON when present
- `tours_data.py` updated to reference JSON courses
- In-editor preview (renders hole using the game's actual renderer)
- Export button with validation

**Deliverable:** Courses built in the editor can be played in the game.

---

### Phase E5 — Polish & Productivity
- Undo/Redo (50 operations)
- Rectangle fill (Shift+drag)
- Eyedropper (right-click)
- Keyboard shortcuts for all common operations
- Recent files list
- Minimap of full course in editor

**Deliverable:** Editor is fast and comfortable to use for building full 18-hole courses.

---

## 11. What Is Not In Scope

- The editor is never visible to the player — no in-game course creator
- No real-time multiplayer or cloud sync for course files
- No procedural generation tools (courses are hand-crafted)
- No animated tiles or particle effects in the editor
- The editor does not simulate shot physics or AI scoring

---

## 12. Summary of Key Decisions

| Decision | Choice | Reason |
|---|---|---|
| Same or separate repo | **Same repo** | Shared assets, shared data format, no sync problem |
| Entry point | **`editor.py`** at root | Clear separation, easy to exclude from player builds |
| Technology | **Python + Pygame + pygame_gui** | Consistent with game, one extra dependency |
| File dialogs | **tkinter.filedialog** | Standard library, native OS dialogs, no install |
| Course format | **JSON in `data/courses/`** | Human-readable, git-friendly, no compile step |
| Asset location | **`assets/tilemaps/`** shared | Single source of truth, no duplication |
| Layers | **Visual + Attribute** | Visual variety without sacrificing gameplay accuracy |
| Multi-tour | **Subfolders from day one** | No migration needed when more tours are added |
