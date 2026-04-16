"""
dialogs.py — file open/save wrappers and course JSON helpers.

File dialogs use tkinter.filedialog for native OS pickers.
Course helpers handle the JSON format defined in CourseEditorPlan.md.
"""

import json
import os

import tkinter as tk
from tkinter import filedialog


# ── File dialogs ──────────────────────────────────────────────────────────────

def ask_open_png(initial_dir="assets/tilemaps"):
    """Open a native file picker for PNG tilesets. Returns path or None."""
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
    """Open a native file picker for course JSON files. Returns path or None."""
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
    """Open a native save-as dialog for course JSON files. Returns path or None."""
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

def make_empty_course(rows=36, cols=48):
    """Return a fresh course data dict with one blank hole."""
    return {
        "version": 2,
        "course": {
            "name": "Untitled",
            "tour": "development",
            "par": 72,
        },
        "tilesets": [],
        "holes": [
            {
                "number": 1,
                "par": 4,
                "yardage": 0,
                "stroke_index": 1,
                "tee": [cols // 2, rows - 3],
                "pin": [cols // 2, 3],
                "grid_cols": cols,
                "grid_rows": rows,
                "visual": [[None] * cols for _ in range(rows)],
                "attributes": [["R"] * cols for _ in range(rows)],
            }
        ],
    }


def save_course(course_data, path, visual_grid, attribute_grid, tileset_registry):
    """
    Write the course to a JSON file.

    course_data     : the course dict (mutated in-place before writing)
    path            : destination file path
    visual_grid     : list[list[(id,col,row)|None]] from the canvas
    attribute_grid  : list[list[str]] of terrain char codes ('R','F',…)
    tileset_registry: dict {id: filepath} of all loaded tilesets
    """
    # Update hole 0 visual and attribute layers
    if course_data["holes"]:
        course_data["holes"][0]["visual"]     = _visual_to_json(visual_grid)
        course_data["holes"][0]["attributes"] = attribute_grid
        course_data["holes"][0]["grid_rows"]  = len(visual_grid)
        course_data["holes"][0]["grid_cols"]  = len(visual_grid[0]) if visual_grid else 0

    # Rebuild tilesets list from those actually referenced in the visual grid
    used_ids = set()
    for row in visual_grid:
        for cell in row:
            if cell is not None:
                used_ids.add(cell[0])

    course_data["tilesets"] = [
        {"id": tid, "path": tileset_registry[tid]}
        for tid in used_ids
        if tid in tileset_registry
    ]

    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(course_data, f, indent=2)


def load_course(path):
    """
    Load a course JSON file.

    Returns (course_data, visual_grid, attribute_grid, tileset_specs) where:
      course_data    : the parsed dict
      visual_grid    : list[list[(id,col,row)|None]]
      attribute_grid : list[list[str]] of terrain char codes, or None
      tileset_specs  : list of {"id": ..., "path": ...} entries
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows, cols = 36, 48
    if data.get("holes"):
        hole = data["holes"][0]
        rows = hole.get("grid_rows", 36)
        cols = hole.get("grid_cols", 48)

    # Visual grid
    visual_grid = None
    if data.get("holes"):
        raw = data["holes"][0].get("visual")
        if raw:
            visual_grid = _json_to_visual(raw)
    if visual_grid is None:
        visual_grid = [[None] * cols for _ in range(rows)]

    # Attribute grid
    attribute_grid = None
    if data.get("holes"):
        raw_attr = data["holes"][0].get("attributes")
        if raw_attr and len(raw_attr) == rows:
            attribute_grid = raw_attr

    return data, visual_grid, attribute_grid, data.get("tilesets", [])


# ── Internal encoding helpers ─────────────────────────────────────────────────

def _visual_to_json(visual_grid):
    """Convert visual_grid (None or (id,col,row)) to JSON-serialisable lists."""
    result = []
    for row in visual_grid:
        json_row = []
        for cell in row:
            if cell is None:
                json_row.append(None)
            else:
                tid, sc, sr = cell
                json_row.append(f"{tid}:{sc}:{sr}")
        result.append(json_row)
    return result


def _json_to_visual(json_grid):
    """Decode JSON grid back to (id,col,row) tuples."""
    result = []
    for row in json_grid:
        vis_row = []
        for cell in row:
            if cell is None:
                vis_row.append(None)
            else:
                parts = cell.split(":")
                if len(parts) == 3:
                    vis_row.append((parts[0], int(parts[1]), int(parts[2])))
                else:
                    vis_row.append(None)
        result.append(vis_row)
    return result
