"""
TilesetManager — loads tileset PNGs from assets/tilemaps/ and extracts
individual tiles for use in the course renderer.

All 32x32 source tiles are used at native size (32 px) with no scaling.

Usage
─────
    from src.utils.tileset import TilesetManager
    mgr = TilesetManager()
    surf = mgr.get(terrain)   # returns a 32x32 pygame.Surface
"""

import os
import pygame
from src.golf.terrain import Terrain

# Source tile size in the PNG sheets
SOURCE_TILE = 32

# Map: terrain → (sheet_filename_stem, col, row, brightness_delta)
# brightness_delta: positive = lighten (BLEND_ADD), negative = darken (BLEND_SUB)
_TILE_SPEC = {
    # Terrain            sheet           col  row  delta
    Terrain.FAIRWAY:    ("Hills",          4,  5,  0),
    Terrain.ROUGH:      ("Hills",          3,  5,  0),   # naturally darker green
    Terrain.DEEP_ROUGH: ("Hills",          3,  5, -42),  # same tile, darkened
    Terrain.BUNKER:     ("Tilled_Dirt",    1,  5,  0),
    Terrain.WATER:      ("Water",          1,  0,  0),
    Terrain.GREEN:      ("Hills",          4,  5, +30),  # brightened for putting green
    Terrain.TEE:        ("Hills",          4,  5, +12),  # slightly lighter than fairway
    # TREES uses a procedural tile — handled by CourseRenderer directly
}


class TilesetManager:
    """Loads tileset sheets once and caches scaled terrain tiles."""

    _instance = None   # singleton so sheets are only loaded once

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._sheets: dict[str, pygame.Surface] = {}
        self._tiles:  dict[Terrain, pygame.Surface] = {}
        self._ready = False

    def load(self, assets_dir: str, tile_size: int = 32):
        """
        Load all sheets and pre-extract terrain tiles.

        assets_dir : path to the directory containing the tileset PNGs
        tile_size  : target tile size in pixels (default 32, matches TILE_SIZE)
        """
        sheets_needed = {"Hills", "Tilled_Dirt", "Water"}
        for stem in sheets_needed:
            path = os.path.join(assets_dir, f"{stem}.png")
            if not os.path.exists(path):
                # Also try with a space (e.g. "Tilled Dirt.png")
                alt = os.path.join(assets_dir, f"{stem.replace('_', ' ')}.png")
                if os.path.exists(alt):
                    path = alt
            if os.path.exists(path):
                self._sheets[stem] = pygame.image.load(path).convert_alpha()

        for terrain, (stem, col, row, delta) in _TILE_SPEC.items():
            if stem not in self._sheets:
                continue
            surf = self._extract(stem, col, row, tile_size)
            if surf is not None:
                self._apply_brightness(surf, delta)
                self._tiles[terrain] = surf

        self._ready = True

    # ── Tile access ───────────────────────────────────────────────────────────

    def get(self, terrain: Terrain) -> pygame.Surface | None:
        """Return the pre-built tile for this terrain, or None if unavailable."""
        return self._tiles.get(terrain)

    def is_ready(self) -> bool:
        return self._ready and bool(self._tiles)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _extract(self, stem: str, col: int, row: int,
                 tile_size: int) -> pygame.Surface | None:
        sheet = self._sheets.get(stem)
        if sheet is None:
            return None

        src_rect = pygame.Rect(col * SOURCE_TILE, row * SOURCE_TILE,
                               SOURCE_TILE, SOURCE_TILE)
        if (src_rect.right  > sheet.get_width() or
                src_rect.bottom > sheet.get_height()):
            return None

        raw = pygame.Surface((SOURCE_TILE, SOURCE_TILE), pygame.SRCALPHA)
        raw.blit(sheet, (0, 0), area=src_rect)

        # Scale to display tile size — nearest-neighbour keeps pixel art crisp
        scaled = pygame.transform.scale(raw, (tile_size, tile_size))
        return scaled.convert()   # drop alpha channel — tiles are all solid

    @staticmethod
    def _apply_brightness(surf: pygame.Surface, delta: int):
        """Lighten (delta > 0) or darken (delta < 0) the tile in-place."""
        if delta == 0:
            return
        v = abs(delta)
        colour = (v, v, v)
        flag = pygame.BLEND_RGB_ADD if delta > 0 else pygame.BLEND_RGB_SUB
        surf.fill(colour, special_flags=flag)
