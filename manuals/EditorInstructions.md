# Golf Course Editor — User Manual

> **Version:** Phase E3  
> **Entry point:** `python editor.py` (run from the project root)  
> **Purpose:** Developer tool for building golf courses. Players never see this — run `main.py` to play the game.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Window Layout](#2-window-layout)
3. [Toolbar](#3-toolbar)
4. [Tileset Panel (Left)](#4-tileset-panel-left)
5. [Attribute Panel (Left)](#5-attribute-panel-left)
6. [Course Canvas (Centre)](#6-course-canvas-centre)
7. [Hole Panel (Right)](#7-hole-panel-right)
8. [Status Bar](#8-status-bar)
9. [Working with Holes](#9-working-with-holes)
10. [Saving and Opening Courses](#10-saving-and-opening-courses)
11. [Validation](#11-validation)
12. [Terrain Reference](#12-terrain-reference)
13. [Complete Controls Reference](#13-complete-controls-reference)
14. [Workflow: Building a Hole from Scratch](#14-workflow-building-a-hole-from-scratch)

---

## 1. Getting Started

### Prerequisites

```
pip install pygame pygame_gui
```

### Launching the editor

From the project root folder:

```
python editor.py
```

A 1440 × 900 window opens. The editor starts with a blank single-hole course ready to paint.

---

## 2. Window Layout

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  TOOLBAR  [New] [Open] [Save] [Import PNG]  [Grid] [Zoom-] [Zoom+]  [V] [A] [B] │
├──────────────┬─────────────────────────────────────────────────┬─────────────────┤
│              │                                                 │                 │
│   TILESET    │                                                 │   HOLE INFO     │
│   PALETTE    │              COURSE CANVAS                      │                 │
│  (left 240)  │              (centre 980)                       │  (right 220)    │
│              │                                                 │                 │
│   Tile grid  │   Pan, zoom, paint, flood-fill, eyedropper      │  ◀ Hole N/M ▶  │
│   Click tile │                                                 │  Par / Yds / SI │
│   to select  │                                                 │  Set Tee/Pin    │
│              │                                                 │                 │
├──────────────┤                                                 ├─────────────────┤
│  ATTRIBUTE   │                                                 │  COURSE INFO    │
│  BRUSH       │                                                 │                 │
│              │                                                 │  Name / Tour    │
│  Terrain     │                                                 │  Hole grid      │
│  type rows   │                                                 │  + Hole / -Hole │
│              │                                                 │                 │
│  Auto-derive │                                                 │                 │
├──────────────┴─────────────────────────────────────────────────┴─────────────────┤
│  STATUS BAR  (col,row) | terrain | tile ref | attr brush | zoom | view | hole    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

| Region | Position | Purpose |
|---|---|---|
| Toolbar | Top, full width | File operations, canvas display settings |
| Tileset Panel | Left, upper half | Select which tile to paint with |
| Attribute Panel | Left, lower half | Select which gameplay attribute to paint |
| Course Canvas | Centre | The tile-painting work area |
| Hole Panel | Right | Hole and course metadata |
| Status Bar | Bottom, full width | Live tile info and editor state |

---

## 3. Toolbar

The toolbar runs across the top of the window.

### File Buttons

| Button | Action |
|---|---|
| **New** | Discard the current course and start a blank one-hole course. Tilesets are unloaded. |
| **Open** | Opens a native file picker. Select any `.json` course file from `data/courses/`. |
| **Save** | Save the current course to JSON. If the file has not been saved before, a Save As dialog appears. Validation runs first — see [Section 11](#11-validation). |

### Tileset Button

| Button | Action |
|---|---|
| **Import PNG** | Opens a file picker (starting in `assets/tilemaps/`). Select a tileset PNG to load it into the palette. Multiple tilesets can be loaded in one session. |

### Canvas Display Buttons

| Button | Action |
|---|---|
| **Grid** | Toggle the tile grid lines on or off. |
| **Zoom −** | Zoom the canvas out one step. |
| **Zoom +** | Zoom the canvas in one step. |

### View Mode Buttons

These three buttons control what is drawn on the canvas. A blue underline shows the active mode.

| Button | Mode | What you see |
|---|---|---|
| **V** | Visual | Only the painted tileset graphics. Empty tiles are dark grey. |
| **A** | Attributes | Solid colour blocks showing terrain types only. No pixel art. |
| **B** | Both | Tileset graphics with a semi-transparent colour overlay showing terrain attributes. **This is the default and recommended mode.** |

> **Tip:** Use **A** mode to check that attributes are correctly set everywhere before saving. Use **V** mode to review the artwork without the attribute tint.

---

## 4. Tileset Panel (Left)

The tileset palette occupies the upper 480 pixels of the left panel.

### Loading a Tileset

Click **Import PNG** in the toolbar (or use the **Import PNG** button). A file picker opens starting in `assets/tilemaps/`. Select a `.png` file. The sheet loads immediately and becomes the active palette.

Every tileset PNG is a grid of 16 × 16 pixel source tiles.

### Browsing the Palette

- The panel shows all tiles from the active sheet, scaled up to 20 × 20 for visibility.
- **Scroll wheel** inside the panel scrolls up and down through the tile grid.
- **Hover** over any tile to see a subtle white highlight.

### Selecting a Tile (Active Brush)

**Left-click** any tile in the palette. That tile becomes the active visual brush — shown with a blue outline in the palette. Any subsequent left-click on the canvas paints this tile.

### Switching Between Multiple Tilesets

If more than one tileset has been imported, **< / >** navigation buttons appear below the sheet name in the panel header.

- **<** — switch to the previous tileset
- **>** — switch to the next tileset

The sheet name and a counter (e.g. `2/3`) are shown in the header.

---

## 5. Attribute Panel (Left)

The attribute panel occupies the lower portion of the left panel. It controls the **gameplay layer** — what the game engine uses for shot physics, not what the course looks like.

### Terrain Types

Click any row to set it as the active attribute brush.

| Terrain | Code | Colour | Game effect |
|---|---|---|---|
| **Tee Box** | X | Light green | Starting position for the hole |
| **Fairway** | F | Medium green | Full distance, good accuracy |
| **Rough** | R | Dark green | Reduced distance and accuracy |
| **Deep Rough** | D | Dark green (darker) | Heavy distance and accuracy penalty |
| **Bunker** | B | Sand yellow | Significant distance penalty |
| **Water** | W | Blue | Hazard — penalty stroke |
| **Trees** | T | Forest green | Ball blocked or deflected |
| **Green** | G | Bright green | Putting surface, pin location |

The selected terrain shows a blue bar on the left edge of its row and a brighter label.

### Painting Attributes

Hold **A** while left-clicking (or dragging) on the canvas to paint the active attribute onto tiles. The visual appearance of the tile is not changed — only the gameplay attribute.

### Auto-Derive Toggle

At the bottom of the attribute panel is the **Auto-derive** button.

- **ON** (green): When you paint a visual tile onto the canvas, the editor automatically sets the attribute for that tile based on which tileset it came from. For example, any tile from `Tilled_Dirt.png` is automatically marked as **Bunker**. Any tile from `Water.png` becomes **Water**.
- **OFF** (dark red): Visual tiles are painted without touching the attribute layer. You set all attributes manually.

Auto-derive uses a built-in mapping table. You can always override any individual tile by painting an attribute on top with **A + click**.

**Known auto-derive mappings:**

| Tileset | Auto attribute |
|---|---|
| `Hills.png` tile (4,5) | Fairway |
| `Hills.png` tile (3,5) | Rough |
| Any other Hills tile | Rough |
| `Tilled_Dirt.png` | Bunker |
| `Tilled_Dirt_v2.png` | Bunker |
| `Tilled_Dirt_Wide.png` | Bunker |
| `Water.png` | Water |

---

## 6. Course Canvas (Centre)

The canvas is the main tile-painting area. It represents a 2D top-down view of the current hole's tile grid. The default grid size is 48 columns × 36 rows.

### Navigating the Canvas

#### Zooming

| Method | Action |
|---|---|
| **Scroll wheel up** | Zoom in (towards cursor position) |
| **Scroll wheel down** | Zoom out (towards cursor position) |
| **Zoom +** toolbar button | Zoom in (towards canvas centre) |
| **Zoom −** toolbar button | Zoom out (towards canvas centre) |

Zoom levels: 0.5×, 1×, 1.5×, 2×, 3×, 4×, 6×, 8×. The zoom pivots around the cursor position when using the scroll wheel, so what you are looking at stays centred.

#### Panning

| Method | Action |
|---|---|
| **Middle-mouse-button drag** | Pan in any direction |
| **Space + left-click drag** | Pan in any direction |

The grey outline rectangle shows the boundary of the full tile grid. You can pan slightly outside the boundary.

#### Grid Lines

Toggle with the **Grid** button. Grid lines are only drawn when the zoom level is 0.75× or above — at very small zoom they would be invisible anyway.

### Painting Tiles

#### Visual Layer (what the hole looks like)

1. Select a tile in the Tileset Panel.
2. **Left-click** (or hold and drag) on the canvas.
3. The selected tile is painted at every cell you drag through.
4. If Auto-derive is ON, the attribute for that cell is set automatically.

#### Attribute Layer (how the engine treats the tile)

1. Select a terrain type in the Attribute Panel.
2. Hold **A** and **left-click** (or hold and drag) on the canvas.
3. The attribute is written to those cells without changing the visual tile.

> **Note:** You can paint attributes onto empty (unvisualised) cells. This is useful if you want to set gameplay regions before adding the artwork.

### Flood Fill

**F + left-click** on any canvas tile flood-fills the connected region of tiles that share the same value as the clicked tile.

- Without **A** held: fills the **visual layer** with the active tile brush.
- With **A** held: fills the **attribute layer** with the active terrain brush.

The fill is bounded by edges of the grid and stops when it encounters a tile with a different value.

> **Example:** Paint all fairway grass with F + click on the fairway region to flood-fill the attribute layer without touching the visuals.

### Eyedropper (Pick-up)

**Right-click** on any canvas tile to sample it and set it as the active brush.

- Without **A** held: samples the **visual tile** — the next left-click will paint that same tile.
- With **A** held: samples the **attribute** at that cell — sets it as the active attribute brush.

### Tee and Pin Markers

After using the **Set Tee** or **Set Pin** buttons (see [Section 7](#7-hole-panel-right)), the editor enters placement mode. The next left-click on the canvas places the marker:

- **Tee marker**: small green square with a **T** label.
- **Pin marker**: small red square with a **P** label.

Markers are drawn on top of the tile artwork at any zoom level. They are stored as tile grid coordinates, not pixel positions.

The status bar shows `[PLACE TEE]` or `[PLACE PIN]` while placement mode is active.

---

## 7. Hole Panel (Right)

The right panel is split into two sections: **Hole Info** (top) and **Course Info** (bottom).

### Hole Info

#### Navigating Holes

| Control | Action |
|---|---|
| **◀** button | Go to the previous hole |
| **▶** button | Go to the next hole |
| **Hole grid** (see Course Info) | Click any hole number to jump directly to it |

When you navigate away from a hole, the current canvas state (visuals, attributes, tee, pin, par, yds, SI) is automatically saved into the course data. Nothing is lost.

The label between the navigation buttons shows the current hole and total count: e.g. **Hole 3 / 9**.

#### Hole Metadata Fields

These three fields store information about the current hole. Edit them by clicking into the field and typing.

| Field | Description |
|---|---|
| **Par** | The par for this hole. Valid range: 3–6. |
| **Yds** | The hole length in yards from tee to pin. |
| **SI** | Stroke Index — a number from 1 to 18 indicating the difficulty ranking of the hole within the course (1 = hardest, 18 = easiest). |

Changes are saved when you navigate to another hole or save the course.

#### Setting the Tee Position

1. Click **Set Tee**. The button gets a green border and the status bar shows `[PLACE TEE]`.
2. Click anywhere on the canvas. A green **T** marker appears at that tile.
3. The editor leaves placement mode automatically.

The tee tile should ideally be on a **Tee Box** (X) attribute tile. The validator will warn you if it is not.

#### Setting the Pin Position

1. Click **Set Pin**. The button gets a red border and the status bar shows `[PLACE PIN]`.
2. Click anywhere on the canvas. A red **P** marker appears at that tile.
3. The editor leaves placement mode automatically.

The pin tile should ideally be on a **Green** (G) attribute tile. The validator will warn you if it is not.

> **Tip:** Place the tee marker first, then navigate to where the green should be, paint a green attribute region, then place the pin marker inside that region.

---

### Course Info

#### Course Name

A text field showing the name of the course. Click and edit it to rename the course. The name is used in the saved JSON file.

#### Tour

A dropdown menu for assigning the course to a tour level. The six options are:

| Tour | Description |
|---|---|
| `amateur` | Local amateur events |
| `challenger` | Semi-professional level 1 |
| `development` | Semi-professional level 2 |
| `continental` | Professional level 1 |
| `world` | Professional level 2 |
| `grand` | The top-level tour (equivalent to the PGA) |

When you save the course, the file is placed in the matching subfolder inside `data/courses/`.

#### Holes Grid

The 18-slot grid at the bottom of the Course Info section shows all holes in the course. 

- **Filled** slots (darker grey) exist as actual holes.
- **Active** hole (blue) is the one currently displayed on the canvas.
- **Empty** slots (near-black) are available slots not yet created.
- **Click any filled slot** to jump directly to that hole.

#### Adding and Deleting Holes

| Button | Action |
|---|---|
| **+ Hole** | Adds a new blank hole at the end of the course and switches to it. Maximum 18 holes. |
| **− Hole** | Deletes the current hole. The previous hole becomes active. Cannot delete if only one hole remains. |

---

## 8. Status Bar

The status bar at the bottom of the screen provides real-time information. Items are separated by vertical bars (`|`).

| Item | Meaning |
|---|---|
| `(col, row)  TerrainName` | Grid coordinates of the tile under the cursor, and its current attribute terrain name. |
| `Tile:SheetName(col,row)` | The active visual tile brush — which sheet and which tile within it. |
| `Attr:TERRAIN_NAME` | The active attribute brush. |
| `2.0×` | Current zoom level. |
| `BOTH` / `VISUAL` / `ATTRIBUTES` | Current view mode. |
| `H3/9` | Current hole number / total holes. |
| `[PLACE TEE]` / `[PLACE PIN]` | Shown when the canvas is waiting for a placement click. |
| `filename.json *` | The file the course is saved to. The `*` suffix indicates unsaved changes. |
| Green message (right side) | Timed status message (saved, load errors, warnings, etc.). |

---

## 9. Working with Holes

### Switching Holes

Use **◀ / ▶** in the Hole Panel or click any hole number in the grid. The current hole's state is automatically flushed before the new one loads. Nothing is lost.

### Adding a Hole

Click **+ Hole** in the Course Info section. A blank 48 × 36 rough grid is created, the canvas clears, and you are taken to the new hole. The new hole's number defaults to `n+1` and stroke index defaults to its position.

### Deleting a Hole

Click **− Hole**. The current hole is removed and you are taken to the nearest remaining hole. This cannot be undone — save first if you are unsure.

### Renumbering and Stroke Index

Hole numbers do not automatically renumber when holes are deleted or reordered. Use the SI (Stroke Index) field to define playing difficulty within the round. The validator will warn if all 18 stroke indices are not unique when the course has a full 18 holes.

---

## 10. Saving and Opening Courses

### Saving

Click **Save** in the toolbar.

- If the course has never been saved, a **Save As** dialog opens, starting in `data/courses/<tour>/`.
- If the course was previously saved or opened from a file, it saves to the same path without prompting.
- Validation runs automatically on every save. See [Section 11](#11-validation).
- The `*` dirty indicator in the status bar disappears after a successful save.

**What gets saved:**
- All holes (visual grids, attribute grids, tee/pin positions, par, yds, SI)
- Course name and tour
- The list of tilesets used (as relative paths from the project root)
- Format version number

The course is saved as a human-readable JSON file in `data/courses/<tour>/`.

### Opening

Click **Open** in the toolbar. A file picker opens at `data/courses/`. Navigate to any `.json` course file and select it.

On load:
- All tilesets referenced in the file are automatically re-loaded from their paths in `assets/tilemaps/`. A warning appears in the status bar if any tileset file is missing.
- Hole 1 is displayed on the canvas.
- The Hole Panel is populated with hole 1's metadata.
- The Course Info fields are populated with the course name and tour.

### Starting Fresh

Click **New** to discard the current course entirely and start with a single blank hole. Any unsaved changes are lost — there is no confirmation prompt.

---

## 11. Validation

Validation runs automatically every time you click **Save**. It checks the following:

### Errors (block saving)

These must be fixed before the course can be saved:

| Check | What it means |
|---|---|
| Every hole must have a tee position | Click **Set Tee** and place a marker on each hole. |
| Every hole must have a pin position | Click **Set Pin** and place a marker on each hole. |
| Course must have at least one hole | Cannot save a course with no holes. |

When errors are found, the save is cancelled and the count is shown in the status bar. Details are printed to the console.

### Warnings (allow saving)

These do not block saving but indicate things that should probably be fixed:

| Check | What it means |
|---|---|
| Tee not on a Tee Box tile | The tee marker is not on an `X` attribute tile. |
| Pin not on a Green tile | The pin marker is not on a `G` attribute tile. |
| Unusual par value | Par is outside the 3–6 range. |
| Yardage not set | The yardage field is 0. |
| Stroke index out of range | Stroke index is outside 1–18. |
| Duplicate stroke indices | For 18-hole courses, all SI values should be unique (1–18). |

When warnings are found, the course saves but a count is shown in the status bar and details are printed to the console.

> **Best practice:** Check the console output for full validation messages before considering a course complete.

---

## 12. Terrain Reference

This table lists every terrain attribute in the editor, its keyboard shortcut code (used in the saved JSON), its colour in Attribute view, and its effect on gameplay.

| Terrain | Code | Attribute view colour | Gameplay notes |
|---|---|---|---|
| **Tee Box** | `X` | Light green | Place the tee marker here. Shot starts from this tile. |
| **Fairway** | `F` | Medium green | Standard distance, good accuracy. The ideal landing zone. |
| **Rough** | `R` | Dark green | Moderate distance and accuracy penalty. |
| **Deep Rough** | `D` | Very dark green | Heavy distance and accuracy penalty. Off-course areas. |
| **Bunker** | `B` | Sand / tan | Significant distance penalty. Club selection affected. |
| **Water** | `W` | Blue | Hazard. Ball lost — penalty stroke applied. |
| **Trees** | `T` | Forest green | Ball may be blocked or deflected. Cannot play normally. |
| **Green** | `G` | Bright green | The putting surface. Place the pin marker here. |

---

## 13. Complete Controls Reference

### Toolbar Buttons

| Button | Function |
|---|---|
| New | Start a new blank course |
| Open | Open a `.json` course file |
| Save | Save the course (runs validation first) |
| Import PNG | Load a tileset from `assets/tilemaps/` |
| Grid | Toggle grid lines |
| Zoom − | Zoom out one step |
| Zoom + | Zoom in one step |
| V | Visual-only view mode |
| A | Attribute-only view mode |
| B | Both layers view mode (default) |

### Canvas Mouse Controls

| Input | Action |
|---|---|
| **Left-click / drag** | Paint active visual tile |
| **A + left-click / drag** | Paint active attribute |
| **F + left-click** | Flood fill visual layer from this tile |
| **A + F + left-click** | Flood fill attribute layer from this tile |
| **Right-click** | Eyedropper — sample visual tile |
| **A + right-click** | Eyedropper — sample attribute |
| **Middle-click drag** | Pan canvas |
| **Space + left-click drag** | Pan canvas |
| **Scroll wheel** | Zoom in / out towards cursor |

### Tileset Panel Controls

| Input | Action |
|---|---|
| **Left-click on a tile** | Select as active visual brush |
| **Scroll wheel** | Scroll the tile grid up / down |
| **< button** | Switch to previous tileset |
| **> button** | Switch to next tileset |

### Hole Panel Controls

| Control | Action |
|---|---|
| **◀ button** | Go to previous hole |
| **▶ button** | Go to next hole |
| **Par / Yds / SI fields** | Edit hole metadata (click and type) |
| **Set Tee button** | Arm tee placement — next canvas click sets tee |
| **Set Pin button** | Arm pin placement — next canvas click sets pin |
| **Hole number in grid** | Jump to that hole |
| **+ Hole** | Add a new blank hole |
| **− Hole** | Delete the current hole |
| **Name field** | Edit the course name |
| **Tour dropdown** | Assign the course to a tour |

---

## 14. Workflow: Building a Hole from Scratch

This walkthrough covers the full process for one hole.

### Step 1: Import Tilesets

1. Click **Import PNG** in the toolbar.
2. Navigate to `assets/tilemaps/` and import `Hills.png` for terrain.
3. Repeat for `Tilled_Dirt.png` (bunkers) and `Water.png` if needed.
4. Each import adds the sheet to the palette; use **< / >** in the panel to switch between them.

### Step 2: Paint the Fairway

1. Select the `Hills.png` sheet in the palette.
2. Find the fairway tile (column 4, row 5 in the sheet — a mid-green grass tile).
3. Click it in the palette to select it as the active brush.
4. Make sure **Auto-derive** is **ON** and the view mode is **B** (both layers).
5. Left-click and drag on the canvas to paint the fairway corridor. The attribute layer fills in automatically as `Fairway (F)`.

### Step 3: Paint the Rough

1. Select the rough tile from `Hills.png` (column 3, row 5).
2. Paint the rough on either side of the fairway.
3. The attribute layer auto-derives as `Rough (R)`.

> **Tip:** Use **F + left-click** on one rough cell to flood-fill the entire rough region in one click, rather than dragging. Make sure to flood-fill the attribute layer too with **A + F + left-click**.

### Step 4: Add a Bunker

1. Switch to the `Tilled_Dirt.png` sheet using **>** in the palette.
2. Select any tile from the sheet.
3. Paint the bunker shape on the canvas. The attribute auto-derives as `Bunker (B)`.

### Step 5: Mark the Green

1. Switch back to `Hills.png`.
2. Select a bright-green tile or use the existing fairway tile for the putting surface.
3. Paint the green area (usually near the top of the hole grid for a top-to-bottom layout).
4. Now paint the **attribute layer**: select **Green** in the Attribute Panel, hold **A**, and paint over the green area (or flood-fill with **A + F + click**).

### Step 6: Mark the Tee Box

1. Paint a small area (2–4 tiles) at the starting position with the fairway tile.
2. Select **Tee Box** in the Attribute Panel.
3. Hold **A** and paint the tee box attribute over those tiles.

### Step 7: Place the Tee and Pin Markers

1. In the Hole Panel (right), click **Set Tee**.
2. Click on the tee box area of the canvas. The green **T** marker appears.
3. Click **Set Pin**.
4. Click on the centre of the green. The red **P** marker appears.

### Step 8: Set Hole Metadata

In the Hole Panel:

1. Set **Par** to the correct value (e.g. 4).
2. Set **Yds** to the approximate hole length.
3. Set **SI** (Stroke Index) — the difficulty rank within the course round.

### Step 9: Check in Attribute View

1. Press **A** (or click the **A** button) to switch to Attribute view.
2. Scan the whole hole — every tile should have a colour. Dark grey / black means an unattributed tile — those default to Rough.
3. Confirm the tee area shows light green (Tee Box), the fairway shows medium green, the green shows bright green.
4. Press **B** to return to combined view.

### Step 10: Save

1. Click **Save**.
2. Validation runs. If errors appear in the status bar, check the console, fix them, and save again.
3. If warnings appear, decide whether to fix them or proceed.
4. On success, navigate to `data/courses/<tour>/` to confirm the `.json` file was created.

---

*End of Golf Course Editor User Manual — Phase E3*
