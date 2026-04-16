"""
dialogs.py — file open/save wrappers and course JSON helpers (Phase E3).

Multi-hole model
────────────────
  _course["holes"][i]["visual"]  is stored in memory as Python tuples
  (None or (id, col, row)).  On disk it is encoded to "id:col:row" strings.
  flush_hole_to_course / load_hole_from_course translate between the two
  in-memory representations (canvas ↔ course dict).  save_course encodes
  to strings before writing JSON; load_course decodes strings back to tuples.
"""

import copy
import json
import os

import tkinter as tk
from tkinter import filedialog


# ── File dialogs ──────────────────────────────────────────────────────────────

def ask_open_png(initial_dir="assets/tilemaps"):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        parent=root,
        initialdir=initial_dir,
        title="Import Tileset PNG",
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
    )
    root.destroy()
    return path or None


def ask_open_file(initial_dir="data/courses"):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        parent=root,
        initialdir=initial_dir,
        title="Open Course",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
    )
    root.destroy()
    return path or None


def ask_save_file(initial_dir="data/courses"):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.asksaveasfilename(
        parent=root,
        initialdir=initial_dir,
        title="Save Course",
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
    )
    root.destroy()
    return path or None


# ── Course data helpers ───────────────────────────────────────────────────────

def make_empty_hole(cols: int = 48, rows: int = 36, number: int = 1) -> dict:
    """Return a blank hole dict with Python-format visual grid (None values)."""
    return {
        "number":       number,
        "par":          4,
        "yardage":      0,
        "stroke_index": number,
        "tee":          [cols // 2, rows - 3],
        "pin":          [cols // 2, 3],
        "grid_cols":    cols,
        "grid_rows":    rows,
        "visual":       [[None] * cols for _ in range(rows)],
        "attributes":   [["R"]  * cols for _ in range(rows)],
    }


def make_empty_course(rows: int = 36, cols: int = 48) -> dict:
    """Return a fresh course dict with one blank hole."""
    return {
        "version": 2,
        "course": {
            "name": "Untitled",
            "tour": "development",
            "par":  72,
        },
        "tilesets": [],
        "holes": [make_empty_hole(cols, rows, 1)],
    }


def flush_hole_to_course(course_data: dict, hole_index: int,
                          visual_grid, attribute_grid,
                          tee_pos, pin_pos,
                          par: int, yds: int, si: int) -> None:
    """
    Write canvas state into course_data["holes"][hole_index].

    visual_grid    : list[list[(id,col,row)|None]]  (Python tuples)
    attribute_grid : list[list[str]]
    tee_pos / pin_pos : (col, row) | None
    """
    holes = course_data["holes"]
    rows  = len(visual_grid)
    cols  = len(visual_grid[0]) if visual_grid else 0

    # Ensure the slot exists
    while len(holes) <= hole_index:
        holes.append(make_empty_hole(cols, rows, len(holes) + 1))

    h = holes[hole_index]
    h["visual"]       = visual_grid
    h["attributes"]   = attribute_grid
    h["tee"]          = list(tee_pos) if tee_pos else h.get("tee", [cols // 2, rows - 3])
    h["pin"]          = list(pin_pos) if pin_pos else h.get("pin", [cols // 2, 3])
    h["par"]          = par
    h["yardage"]      = yds
    h["stroke_index"] = si
    h["grid_rows"]    = rows
    h["grid_cols"]    = cols


def load_hole_from_course(course_data: dict, hole_index: int):
    """
    Extract hole canvas state from course_data.

    Returns (visual_grid, attr_grid, tee_pos, pin_pos, cols, rows).
    visual_grid cells are Python tuples (None or (id, col, row)).
    """
    holes = course_data.get("holes", [])
    if hole_index >= len(holes):
        rows, cols = 36, 48
        return (
            [[None] * cols for _ in range(rows)],
            [["R"]  * cols for _ in range(rows)],
            None, None, cols, rows,
        )

    h    = holes[hole_index]
    rows = h.get("grid_rows", 36)
    cols = h.get("grid_cols", 48)

    visual = h.get("visual") or [[None] * cols for _ in range(rows)]
    attrs  = h.get("attributes") or [["R"] * cols for _ in range(rows)]

    tee = tuple(h["tee"]) if h.get("tee") else None
    pin = tuple(h["pin"]) if h.get("pin") else None

    return visual, attrs, tee, pin, cols, rows


def save_course(course_data: dict, path: str, tileset_registry: dict) -> None:
    """
    Encode all holes to string format and write JSON to disk.

    tileset_registry : dict {id: filepath} of all loaded tilesets
    All holes in course_data must have already been flushed via
    flush_hole_to_course before calling this.
    """
    data = copy.deepcopy(course_data)

    # Encode visual grids to "id:col:row" string format
    for hole in data["holes"]:
        hole["visual"] = _visual_to_json(hole.get("visual") or [])

    # Rebuild tilesets from tiles actually referenced across all holes
    used_ids: set[str] = set()
    for hole in data["holes"]:
        for row in hole.get("visual", []):
            for cell in row:
                if isinstance(cell, str):
                    used_ids.add(cell.split(":")[0])

    data["tilesets"] = [
        {"id": tid, "path": tileset_registry[tid]}
        for tid in sorted(used_ids)
        if tid in tileset_registry
    ]

    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_course(path: str):
    """
    Load a course JSON file.

    Returns (course_data, tileset_specs) where course_data["holes"][i]["visual"]
    is already decoded to Python tuples (None or (id, col, row)).
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Decode all hole visual grids from strings to tuples
    for hole in data.get("holes", []):
        raw = hole.get("visual")
        if raw:
            hole["visual"] = _json_to_visual(raw)
        else:
            rows = hole.get("grid_rows", 36)
            cols = hole.get("grid_cols", 48)
            hole["visual"] = [[None] * cols for _ in range(rows)]

    return data, data.get("tilesets", [])


def validate_course(course_data: dict) -> list[tuple[str, str]]:
    """
    Validate course_data.  Returns a list of (level, message) tuples where
    level is 'error' or 'warning'.  Errors block saving; warnings do not.
    """
    issues: list[tuple[str, str]] = []
    holes = course_data.get("holes", [])

    if not holes:
        issues.append(("error", "Course has no holes."))
        return issues

    for i, hole in enumerate(holes):
        n = hole.get("number", i + 1)

        # Tee / pin presence
        if not hole.get("tee"):
            issues.append(("error", f"Hole {n}: tee position not set."))
        if not hole.get("pin"):
            issues.append(("error", f"Hole {n}: pin position not set."))

        # Tee should sit on a TEE attribute tile
        tee = hole.get("tee")
        if tee:
            tc, tr = tee
            attrs = hole.get("attributes", [])
            if (attrs and 0 <= tr < len(attrs)
                    and 0 <= tc < len(attrs[tr])
                    and attrs[tr][tc] != "X"):
                issues.append(("warning",
                                f"Hole {n}: tee marker is not on a Tee Box tile."))

        # Pin should sit on a GREEN tile
        pin = hole.get("pin")
        if pin:
            pc, pr = pin
            attrs = hole.get("attributes", [])
            if (attrs and 0 <= pr < len(attrs)
                    and 0 <= pc < len(attrs[pr])
                    and attrs[pr][pc] != "G"):
                issues.append(("warning",
                                f"Hole {n}: pin marker is not on a Green tile."))

        par = hole.get("par", 0)
        if not (3 <= par <= 6):
            issues.append(("warning", f"Hole {n}: unusual par value ({par})."))

        yds = hole.get("yardage", 0)
        if yds <= 0:
            issues.append(("warning", f"Hole {n}: yardage not set."))

        si = hole.get("stroke_index", 0)
        if not (1 <= si <= 18):
            issues.append(("warning",
                            f"Hole {n}: stroke index out of range ({si})."))

    # Duplicate stroke indices across the full round
    if len(holes) == 18:
        si_vals = [h.get("stroke_index") for h in holes]
        if len(set(si_vals)) != 18:
            issues.append(("warning",
                            "Stroke indices are not all unique across 18 holes."))

    return issues


# ── Internal encoding helpers ─────────────────────────────────────────────────

def _visual_to_json(visual_grid) -> list:
    """Convert visual_grid (None | (id,col,row) tuples) to JSON-serialisable form."""
    result = []
    for row in visual_grid:
        json_row = []
        for cell in row:
            if cell is None:
                json_row.append(None)
            elif isinstance(cell, (tuple, list)):
                tid, sc, sr = cell
                json_row.append(f"{tid}:{sc}:{sr}")
            else:
                json_row.append(cell)   # already a string (shouldn't happen)
        result.append(json_row)
    return result


def _json_to_visual(json_grid) -> list:
    """Decode JSON grid (None | "id:col:row" strings) back to tuples."""
    result = []
    for row in json_grid:
        vis_row = []
        for cell in row:
            if cell is None:
                vis_row.append(None)
            elif isinstance(cell, str):
                parts = cell.split(":")
                vis_row.append((parts[0], int(parts[1]), int(parts[2]))
                               if len(parts) == 3 else None)
            else:
                vis_row.append(None)
        result.append(vis_row)
    return result
