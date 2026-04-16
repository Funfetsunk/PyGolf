"""
auto_derive.py — maps visual tile references to terrain attributes.

When auto-derive is enabled, painting a visual tile also sets the attribute
for that tile automatically.  The designer can then manually override any
cell where the auto-derive guess is wrong.

Priority order
──────────────
1. Exact (sheet_id, col, row) → Terrain  (specific tile overrides sheet default)
2. Sheet-level fallback → Terrain         (any tile from that sheet)
3. None                                    (unknown sheet — no auto-derive)
"""

from src.golf.terrain import Terrain

# ── Exact-tile mappings ───────────────────────────────────────────────────────
# Source: logical reverse of _TILE_SPEC in src/utils/tileset.py.
# Where multiple terrains share the same source tile (GREEN/TEE/FAIRWAY all
# use Hills 4,5), we pick the most common field-use as the default.
_EXACT: dict[tuple[str, int, int], Terrain] = {
    ("Hills", 4, 5): Terrain.FAIRWAY,   # standard fairway tile
    ("Hills", 3, 5): Terrain.ROUGH,     # standard rough tile
}

# ── Sheet-level fallbacks ─────────────────────────────────────────────────────
# Any tile from a sheet that isn't in _EXACT gets this terrain.
_SHEET: dict[str, Terrain] = {
    "Hills":              Terrain.ROUGH,     # unlisted Hills tiles → rough
    "Tilled_Dirt":        Terrain.BUNKER,
    "Tilled_Dirt_v2":     Terrain.BUNKER,
    "Tilled_Dirt_Wide":   Terrain.BUNKER,
    "Water":              Terrain.WATER,
}


def derive(tileset_id: str, src_col: int, src_row: int) -> Terrain | None:
    """
    Return the auto-derived Terrain for a visual tile, or None if unknown.

    tileset_id : the tileset ID string (usually the filename stem, e.g. "Hills")
    src_col    : column of the source tile in the sheet
    src_row    : row of the source tile in the sheet
    """
    exact = _EXACT.get((tileset_id, src_col, src_row))
    if exact is not None:
        return exact

    # Sheet-level match (case-insensitive, ignores spaces vs underscores)
    norm_id = tileset_id.lower().replace(" ", "_")
    for stem, terrain in _SHEET.items():
        if stem.lower().replace(" ", "_") == norm_id:
            return terrain

    return None
