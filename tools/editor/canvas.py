"""
canvas.py — zoomable, pannable two-layer course painting canvas.

Layers
──────
  visual_grid[row][col]    : (tileset_id, src_col, src_row) | None
  attribute_grid[row][col] : Terrain char value ('F', 'R', 'B', …)

View modes
──────────
  'visual'     — draw visual tiles only
  'attributes' — draw solid attribute-colour blocks only
  'both'       — visual tiles with a semi-transparent attribute overlay

Controls
────────
  Left-click / drag          → paint active visual brush
  A + left-click / drag      → paint active attribute brush
  F + left-click             → flood fill (A held = attribute layer)
  Right-click                → eyedropper (samples visual or attribute)
  Middle-click / Space+drag  → pan
  Scroll wheel               → zoom
"""

import pygame
from collections import deque

from src.golf.terrain import Terrain, TERRAIN_PROPS, CHAR_TO_TERRAIN
from tools.editor.auto_derive import derive as _auto_derive

SOURCE_TILE = 32
BASE_TILE   = 32

ZOOM_LEVELS       = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]
DEFAULT_ZOOM_INDEX = 1   # 1.0×

# Opacity of the attribute overlay in 'both' mode (0–255)
OVERLAY_ALPHA = 110


class CourseCanvas:
    """
    Renders and handles interaction for the two-layer tile-painting canvas.

    Coordinate systems
    ──────────────────
    World  : 0 → cols*BASE_TILE  /  0 → rows*BASE_TILE  (pixels)
    Camera : (self._ox, self._oy) = world point at canvas top-left
    Screen : rect.x + (world_x - _ox) * zoom
    """

    def __init__(self, rect: pygame.Rect, rows: int = 36, cols: int = 48):
        self.rect = rect
        self.rows = rows
        self.cols = cols

        self._zoom_index = DEFAULT_ZOOM_INDEX
        self._ox = 0.0
        self._oy = 0.0

        # ── Two-layer grids ───────────────────────────────────────────────────
        self.visual_grid    = [[None] * cols for _ in range(rows)]
        self.attribute_grid = [["R"]  * cols for _ in range(rows)]

        # ── Active brushes ────────────────────────────────────────────────────
        self.active_brush     = None            # (id, sc, sr) visual tile
        self.active_attribute = Terrain.ROUGH   # attribute brush

        # ── Display options ───────────────────────────────────────────────────
        self.show_grid         = True
        self.view_mode         = "both"         # 'visual' | 'attributes' | 'both'
        self.auto_derive_enabled = True

        # ── Caches ────────────────────────────────────────────────────────────
        self._tile_cache: dict    = {}          # (id,sc,sr,px) → Surface
        self._overlay_surf        = None        # single-tile SRCALPHA surface

        # ── Tee / Pin positions ───────────────────────────────────────────────
        self.tee_pos: tuple[int, int] | None = None
        self.pin_pos: tuple[int, int] | None = None
        self._set_mode: str | None = None   # 'tee' | 'pin' | None
        self._marker_font: pygame.font.Font | None = None

        # ── Interaction state ─────────────────────────────────────────────────
        self.hovered_tile          = None       # (col, row) or None
        self._painting             = False
        self._painting_attribute   = False      # True when A is held during paint
        self._panning              = False
        self._pan_start_mouse      = (0, 0)
        self._pan_start_offset     = (0.0, 0.0)

        self._center_on_world()

    # ── Public helpers ────────────────────────────────────────────────────────

    @property
    def zoom(self) -> float:
        return ZOOM_LEVELS[self._zoom_index]

    def zoom_in(self):
        if self._zoom_index < len(ZOOM_LEVELS) - 1:
            self._zoom_at_screen_centre(self._zoom_index + 1)

    def zoom_out(self):
        if self._zoom_index > 0:
            self._zoom_at_screen_centre(self._zoom_index - 1)

    @property
    def set_mode(self) -> str | None:
        return self._set_mode

    def enter_set_mode(self, mode: str) -> None:
        """Arm tee ('tee') or pin ('pin') placement — next canvas click places it."""
        self._set_mode = mode

    def clear_set_mode(self) -> None:
        self._set_mode = None

    def reset(self, rows: int = 36, cols: int = 48):
        """Clear both grids and reset zoom/pan."""
        self.rows = rows
        self.cols = cols
        self.visual_grid    = [[None] * cols for _ in range(rows)]
        self.attribute_grid = [["R"]  * cols for _ in range(rows)]
        self.tee_pos        = None
        self.pin_pos        = None
        self._set_mode      = None
        self._tile_cache.clear()
        self._overlay_surf = None
        self._zoom_index   = DEFAULT_ZOOM_INDEX
        self._center_on_world()

    def load_grids(self, visual_grid, attribute_grid=None):
        """Load both layers from deserialized data."""
        self.rows        = len(visual_grid)
        self.cols        = len(visual_grid[0]) if visual_grid else 0
        self.visual_grid = visual_grid

        if attribute_grid and len(attribute_grid) == self.rows:
            # Validate each cell character
            valid = set(CHAR_TO_TERRAIN.keys())
            self.attribute_grid = [
                [c if c in valid else "R" for c in row]
                for row in attribute_grid
            ]
        else:
            self.attribute_grid = [["R"] * self.cols for _ in range(self.rows)]

        self._tile_cache.clear()
        self._overlay_surf = None

    # Keep backward-compatible alias used by editor_app from Phase E1
    def load_visual_grid(self, visual_grid):
        self.load_grids(visual_grid)

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event, tilesets) -> bool:
        """Process a pygame event. Returns True if consumed."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not self.rect.collidepoint(event.pos):
                return False

            keys = pygame.key.get_pressed()

            if event.button == 4:
                self._zoom_at_cursor(self._zoom_index + 1, event.pos)
                return True
            if event.button == 5:
                self._zoom_at_cursor(self._zoom_index - 1, event.pos)
                return True
            if event.button == 2 or (event.button == 1 and keys[pygame.K_SPACE]):
                self._panning          = True
                self._pan_start_mouse  = event.pos
                self._pan_start_offset = (self._ox, self._oy)
                return True
            if event.button == 1:
                # Tee / pin placement mode — consume click without painting
                if self._set_mode:
                    tile = self._screen_to_tile(event.pos)
                    if tile:
                        if self._set_mode == "tee":
                            self.tee_pos = tile
                        else:
                            self.pin_pos = tile
                        self._set_mode = None
                    return True
                if keys[pygame.K_f]:
                    # Flood fill — attribute layer when A held, else visual
                    tile = self._screen_to_tile(event.pos)
                    if tile:
                        self._flood_fill(tile[0], tile[1],
                                         use_attribute=keys[pygame.K_a])
                else:
                    self._painting           = True
                    self._painting_attribute = keys[pygame.K_a]
                    self._paint_at(event.pos)
                return True
            if event.button == 3:
                self._eyedrop_at(event.pos)
                return True

        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.hovered_tile = self._screen_to_tile(event.pos)
            else:
                self.hovered_tile = None

            if self._panning:
                dx = event.pos[0] - self._pan_start_mouse[0]
                dy = event.pos[1] - self._pan_start_mouse[1]
                z  = self.zoom
                self._ox = self._pan_start_offset[0] - dx / z
                self._oy = self._pan_start_offset[1] - dy / z
                self._clamp_offset()
                return True
            if self._painting and self.rect.collidepoint(event.pos):
                self._paint_at(event.pos)
                return True

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button in (1, 2):
                self._painting = False
                self._panning  = False

        return False

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, tilesets: dict):
        old_clip = surface.get_clip()
        surface.set_clip(self.rect)

        pygame.draw.rect(surface, (22, 22, 22), self.rect)

        z          = self.zoom
        display_px = max(1, int(BASE_TILE * z))

        # Ensure the overlay surface matches current display_px
        if self.view_mode == "both":
            if (self._overlay_surf is None or
                    self._overlay_surf.get_width() != display_px):
                self._overlay_surf = pygame.Surface(
                    (display_px, display_px), pygame.SRCALPHA)

        # Visible tile range
        col_min = max(0, int(self._ox // BASE_TILE))
        col_max = min(self.cols,
                      int((self._ox + self.rect.width  / z) // BASE_TILE) + 2)
        row_min = max(0, int(self._oy // BASE_TILE))
        row_max = min(self.rows,
                      int((self._oy + self.rect.height / z) // BASE_TILE) + 2)

        for row in range(row_min, row_max):
            for col in range(col_min, col_max):
                sx = self.rect.x + int((col * BASE_TILE - self._ox) * z)
                sy = self.rect.y + int((row * BASE_TILE - self._oy) * z)

                cell       = self.visual_grid[row][col]
                attr_char  = self.attribute_grid[row][col]
                attr_terr  = CHAR_TO_TERRAIN.get(attr_char, Terrain.ROUGH)
                attr_color = TERRAIN_PROPS[attr_terr]["color"]

                if self.view_mode == "visual":
                    self._draw_visual_tile(surface, cell, sx, sy,
                                           display_px, tilesets)

                elif self.view_mode == "attributes":
                    pygame.draw.rect(surface, attr_color,
                                     (sx, sy, display_px, display_px))

                else:  # 'both'
                    self._draw_visual_tile(surface, cell, sx, sy,
                                           display_px, tilesets)
                    self._overlay_surf.fill((*attr_color, OVERLAY_ALPHA))
                    surface.blit(self._overlay_surf, (sx, sy))

        # World boundary outline
        bx = self.rect.x + int(-self._ox * z)
        by = self.rect.y + int(-self._oy * z)
        bw = int(self.cols * BASE_TILE * z)
        bh = int(self.rows * BASE_TILE * z)
        pygame.draw.rect(surface, (70, 70, 70), (bx, by, bw, bh), 1)

        # Grid lines
        if self.show_grid and z >= 0.75:
            self._draw_grid(surface, z, col_min, col_max, row_min, row_max)

        # Hover highlight
        if self.hovered_tile is not None:
            hc, hr = self.hovered_tile
            hx = self.rect.x + int((hc * BASE_TILE - self._ox) * z)
            hy = self.rect.y + int((hr * BASE_TILE - self._oy) * z)
            hl = pygame.Surface((display_px, display_px), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 50))
            surface.blit(hl, (hx, hy))

        # Tee / pin position markers
        if self.tee_pos is not None:
            tc, tr = self.tee_pos
            if 0 <= tc < self.cols and 0 <= tr < self.rows:
                sx = self.rect.x + int((tc * BASE_TILE - self._ox) * z)
                sy = self.rect.y + int((tr * BASE_TILE - self._oy) * z)
                self._draw_marker(surface, sx, sy, display_px,
                                  (30, 190, 30), "T")

        if self.pin_pos is not None:
            pc, pr = self.pin_pos
            if 0 <= pc < self.cols and 0 <= pr < self.rows:
                sx = self.rect.x + int((pc * BASE_TILE - self._ox) * z)
                sy = self.rect.y + int((pr * BASE_TILE - self._oy) * z)
                self._draw_marker(surface, sx, sy, display_px,
                                  (210, 40, 40), "P")

        surface.set_clip(old_clip)

    # ── Internal draw helpers ─────────────────────────────────────────────────

    def _draw_visual_tile(self, surface, cell, sx, sy, display_px, tilesets):
        if cell is not None:
            tile_surf = self._get_tile(cell, display_px, tilesets)
            if tile_surf is not None:
                surface.blit(tile_surf, (sx, sy))
            else:
                # Missing tileset → magenta error block
                pygame.draw.rect(surface, (160, 40, 160),
                                 (sx, sy, display_px, display_px))
        else:
            pygame.draw.rect(surface, (35, 35, 35),
                             (sx, sy, display_px, display_px))

    def _draw_marker(self, surface, sx, sy, display_px, color, label):
        """Overlay a small coloured square + letter at (sx, sy) for tee/pin."""
        size = max(4, min(display_px, 16))
        mx   = sx + (display_px - size) // 2
        my   = sy + (display_px - size) // 2
        pygame.draw.rect(surface, color, (mx, my, size, size))
        pygame.draw.rect(surface, (0, 0, 0), (mx, my, size, size), 1)
        if size >= 10:
            if self._marker_font is None:
                self._marker_font = pygame.font.SysFont("monospace", 10, bold=True)
            ts = self._marker_font.render(label, True, (0, 0, 0))
            surface.blit(ts, (
                mx + (size - ts.get_width())  // 2,
                my + (size - ts.get_height()) // 2,
            ))

    def _draw_grid(self, surface, z, col_min, col_max, row_min, row_max):
        color = (55, 55, 55)
        for col in range(col_min, col_max + 1):
            x = self.rect.x + int((col * BASE_TILE - self._ox) * z)
            pygame.draw.line(surface, color, (x, self.rect.top), (x, self.rect.bottom))
        for row in range(row_min, row_max + 1):
            y = self.rect.y + int((row * BASE_TILE - self._oy) * z)
            pygame.draw.line(surface, color, (self.rect.left, y), (self.rect.right, y))

    # ── Tile cache ────────────────────────────────────────────────────────────

    def _get_tile(self, cell, display_px, tilesets) -> pygame.Surface | None:
        tid, sc, sr = cell
        key = (tid, sc, sr, display_px)
        if key not in self._tile_cache:
            sheet = tilesets.get(tid)
            if sheet is None:
                return None
            src = pygame.Rect(sc * SOURCE_TILE, sr * SOURCE_TILE,
                              SOURCE_TILE, SOURCE_TILE)
            if src.right > sheet.get_width() or src.bottom > sheet.get_height():
                return None
            raw    = sheet.subsurface(src)
            scaled = pygame.transform.scale(raw, (display_px, display_px))
            self._tile_cache[key] = scaled.convert()
        return self._tile_cache[key]

    # ── Coordinate helpers ────────────────────────────────────────────────────

    def _screen_to_tile(self, pos) -> tuple[int, int] | None:
        z   = self.zoom
        wx  = (pos[0] - self.rect.x) / z + self._ox
        wy  = (pos[1] - self.rect.y) / z + self._oy
        col = int(wx // BASE_TILE)
        row = int(wy // BASE_TILE)
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return (col, row)
        return None

    # ── Painting ──────────────────────────────────────────────────────────────

    def _paint_at(self, pos):
        tile = self._screen_to_tile(pos)
        if tile is None:
            return
        col, row = tile

        if self._painting_attribute:
            self.attribute_grid[row][col] = self.active_attribute.value
        else:
            if self.active_brush is not None:
                self.visual_grid[row][col] = self.active_brush
                # Auto-derive attribute from the tile just painted
                if self.auto_derive_enabled:
                    tid, sc, sr = self.active_brush
                    terrain = _auto_derive(tid, sc, sr)
                    if terrain is not None:
                        self.attribute_grid[row][col] = terrain.value

    def _eyedrop_at(self, pos):
        """Sample the tile (or attribute) under pos and set as active brush."""
        tile = self._screen_to_tile(pos)
        if tile is None:
            return
        col, row = tile
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            char = self.attribute_grid[row][col]
            terrain = CHAR_TO_TERRAIN.get(char)
            if terrain:
                self.active_attribute = terrain
        else:
            self.active_brush = self.visual_grid[row][col]

    def _flood_fill(self, col: int, row: int, use_attribute: bool):
        """
        BFS flood fill starting at (col, row).

        use_attribute=True  → fills attribute_grid with active_attribute
        use_attribute=False → fills visual_grid  with active_brush
        """
        if use_attribute:
            grid      = self.attribute_grid
            target    = grid[row][col]
            fill_val  = self.active_attribute.value
        else:
            grid      = self.visual_grid
            target    = grid[row][col]
            fill_val  = self.active_brush

        if fill_val is None or fill_val == target:
            return

        queue   = deque([(col, row)])
        visited = set()

        while queue:
            c, r = queue.popleft()
            if (c, r) in visited:
                continue
            if not (0 <= c < self.cols and 0 <= r < self.rows):
                continue
            if grid[r][c] != target:
                continue
            visited.add((c, r))
            grid[r][c] = fill_val
            for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nc, nr = c + dc, r + dr
                if (nc, nr) not in visited:
                    queue.append((nc, nr))

    # ── Zoom helpers ──────────────────────────────────────────────────────────

    def _zoom_at_screen_centre(self, new_index: int):
        cx = self.rect.x + self.rect.width  // 2
        cy = self.rect.y + self.rect.height // 2
        self._zoom_at_cursor(new_index, (cx, cy))

    def _zoom_at_cursor(self, new_index: int, cursor_pos):
        new_index = max(0, min(len(ZOOM_LEVELS) - 1, new_index))
        if new_index == self._zoom_index:
            return
        old_z = self.zoom
        wx    = (cursor_pos[0] - self.rect.x) / old_z + self._ox
        wy    = (cursor_pos[1] - self.rect.y) / old_z + self._oy
        self._zoom_index = new_index
        new_z = self.zoom
        self._ox = wx - (cursor_pos[0] - self.rect.x) / new_z
        self._oy = wy - (cursor_pos[1] - self.rect.y) / new_z
        self._clamp_offset()

    def _clamp_offset(self):
        z         = self.zoom
        world_w   = self.cols * BASE_TILE
        world_h   = self.rows * BASE_TILE
        visible_w = self.rect.width  / z
        visible_h = self.rect.height / z
        self._ox  = max(-visible_w * 0.9, min(world_w - visible_w * 0.1, self._ox))
        self._oy  = max(-visible_h * 0.9, min(world_h - visible_h * 0.1, self._oy))

    def _center_on_world(self):
        z         = self.zoom
        world_w   = self.cols * BASE_TILE
        world_h   = self.rows * BASE_TILE
        visible_w = self.rect.width  / z
        visible_h = self.rect.height / z
        self._ox  = (world_w - visible_w) / 2.0
        self._oy  = (world_h - visible_h) / 2.0
