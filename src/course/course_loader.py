"""
course_loader.py — load JSON courses produced by the editor into Course/Hole objects.

Usage
─────
    from src.course.course_loader import load_course
    course = load_course("data/courses/amateur/greenfields.json")

The returned Course contains Hole objects with optional visual_grid and tilesets
attributes that CourseRenderer will use when present, falling back to the
attribute-based procedural renderer for any unvisualised tiles.
"""

import json
import os
import pygame

from src.course.course import Course
from src.course.hole   import Hole

# Must match tools/editor/canvas.py SOURCE_TILE so tile extraction aligns
_SOURCE_TILE = 32


def load_course(path: str) -> Course:
    """
    Load a JSON course file and return a fully populated Course object.

    Tileset PNGs referenced in the file are loaded automatically.
    Missing tileset files are silently skipped — the renderer falls back
    to procedural textures for those tiles.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    course_meta = data.get("course", {})
    name = course_meta.get("name", "Unnamed Course")

    project_root = _find_project_root(path)
    tilesets = _load_tilesets(data.get("tilesets", []), project_root)

    holes = [_build_hole(h, tilesets) for h in data.get("holes", [])]
    return Course(name=name, holes=holes)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_hole(h: dict, tilesets: dict) -> Hole:
    """Convert a JSON hole dict into a Hole object."""
    rows = h.get("grid_rows", 60)
    cols = h.get("grid_cols", 80)

    # Attribute grid → list[str] (one string per row, each char is a terrain code)
    raw_attrs = h.get("attributes")
    if raw_attrs and len(raw_attrs) == rows:
        grid = ["".join(str(c) for c in row[:cols]) for row in raw_attrs]
    else:
        grid = ["R" * cols for _ in range(rows)]

    tee = tuple(h["tee"]) if h.get("tee") else (cols // 2, rows - 3)
    pin = tuple(h["pin"]) if h.get("pin") else (cols // 2, 3)

    raw_visual = h.get("visual")
    visual_grid = _decode_visual(raw_visual) if raw_visual else None

    return Hole(
        number      = h.get("number", 1),
        par         = h.get("par", 4),
        yardage     = h.get("yardage", 0),
        tee_pos     = tee,
        pin_pos     = pin,
        grid        = grid,
        visual_grid = visual_grid,
        tilesets    = tilesets if visual_grid else None,
    )


def _decode_visual(json_grid: list) -> list:
    """Decode JSON visual grid (None | "id:col:row" strings) to (id,col,row) tuples."""
    result = []
    for row in json_grid:
        vis_row = []
        for cell in row:
            if cell is None:
                vis_row.append(None)
            elif isinstance(cell, str):
                parts = cell.split(":")
                vis_row.append(
                    (parts[0], int(parts[1]), int(parts[2]))
                    if len(parts) == 3 else None
                )
            else:
                vis_row.append(None)
        result.append(vis_row)
    return result


def _load_tilesets(specs: list, project_root: str) -> dict:
    """Load each tileset PNG and return {id: Surface}. Silently skips missing files."""
    sheets: dict[str, pygame.Surface] = {}
    if not pygame.get_init():
        return sheets
    for spec in specs:
        tid   = spec.get("id", "")
        tpath = spec.get("path", "")
        abs_path = (
            os.path.normpath(os.path.join(project_root, tpath))
            if not os.path.isabs(tpath) else tpath
        )
        if os.path.exists(abs_path):
            try:
                sheets[tid] = pygame.image.load(abs_path).convert_alpha()
            except Exception:
                pass
    return sheets


def _find_project_root(json_path: str) -> str:
    """Walk up from the JSON file until we find a directory containing main.py."""
    d = os.path.dirname(os.path.abspath(json_path))
    for _ in range(10):
        if os.path.exists(os.path.join(d, "main.py")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return os.getcwd()
