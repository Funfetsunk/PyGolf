"""
CourseRenderer — draws the tile-based course map with textured terrain.

Each terrain type gets a procedurally-generated texture:
  Fairway / Green / Tee  →  mowed stripe pattern
  Rough / Deep Rough     →  noisy base + grass blades
  Bunker                 →  sandy grain + ripple lines
  Water                  →  blue base + ripple highlights
  Trees                  →  dark background + top-down canopy circles

All randomness is seeded per tile so textures are deterministic but varied.

Public interface
────────────────
  draw(surface, camera_x, camera_y, viewport_rect)
  draw_minimap(surface, dest_rect, ball_world_pos)
  get_pin_world_pos() / get_tee_world_pos() / world_size()
"""

import random
import pygame

from src.golf.terrain import Terrain, TERRAIN_PROPS

TILE_SIZE = 20


# ─────────────────────────────────────────────────────────────────────────────
# Tile texture generators
# ─────────────────────────────────────────────────────────────────────────────

def _make_tile(terrain, tile_size, seed):
    """Return a pygame.Surface with a textured fill for the given terrain."""
    ts  = tile_size
    rng = random.Random(seed)
    surf = pygame.Surface((ts, ts))

    if terrain == Terrain.FAIRWAY:
        _stripe(surf, ts, light=(82, 162, 78), dark=(68, 140, 64), width=4)

    elif terrain == Terrain.TEE:
        _stripe(surf, ts, light=(118, 215, 108), dark=(100, 192, 90), width=4)
        # White edge marker
        pygame.draw.rect(surf, (185, 240, 180), (0, 0, ts, ts), 1)

    elif terrain == Terrain.GREEN:
        # Finer stripes — putting surface feels smoother
        _stripe(surf, ts, light=(130, 232, 118), dark=(112, 208, 100), width=5)

    elif terrain == Terrain.ROUGH:
        _noisy_fill(surf, ts, rng, base=(44, 112, 42), spread=18)
        _grass_blades(surf, ts, rng, color=(62, 138, 58), count=5)

    elif terrain == Terrain.DEEP_ROUGH:
        _noisy_fill(surf, ts, rng, base=(26, 78, 26), spread=12)
        _grass_blades(surf, ts, rng, color=(38, 100, 36), count=9)

    elif terrain == Terrain.BUNKER:
        _bunker(surf, ts, rng)

    elif terrain == Terrain.WATER:
        _water(surf, ts, rng)

    elif terrain == Terrain.TREES:
        _trees(surf, ts, rng)

    else:
        surf.fill(TERRAIN_PROPS[terrain]['color'])

    return surf


# ── Texture helpers ───────────────────────────────────────────────────────────

def _stripe(surf, ts, light, dark, width):
    """Alternating vertical stripes — simulates a mowed lawn."""
    for x in range(ts):
        color = light if (x // width) % 2 == 0 else dark
        for y in range(ts):
            surf.set_at((x, y), color)


def _noisy_fill(surf, ts, rng, base, spread):
    """Fill with per-pixel brightness noise around a base colour."""
    for y in range(ts):
        for x in range(ts):
            v = rng.randint(-spread, spread)
            c = tuple(max(0, min(255, base[i] + v)) for i in range(3))
            surf.set_at((x, y), c)


def _grass_blades(surf, ts, rng, color, count):
    """Small vertical strokes that look like tufts of grass."""
    for _ in range(count):
        bx = rng.randint(1, ts - 2)
        by = rng.randint(3, ts - 1)
        h  = rng.randint(2, 4)
        lean = rng.randint(-1, 1)
        pygame.draw.line(surf, color, (bx, by), (bx + lean, by - h), 1)


def _bunker(surf, ts, rng):
    """Sandy texture with grain noise and faint ripple lines."""
    base = (212, 197, 146)
    for y in range(ts):
        for x in range(ts):
            v = rng.randint(-24, 24)
            c = tuple(max(150, min(245, base[i] + v)) for i in range(3))
            surf.set_at((x, y), c)
    # Faint ripples
    for ry in range(4, ts, 5):
        pygame.draw.line(surf, (192, 176, 124), (1, ry),     (ts - 2, ry),     1)
        pygame.draw.line(surf, (228, 214, 162), (1, ry + 1), (ts - 2, ry + 1), 1)
    # Subtle dark border for depth
    pygame.draw.rect(surf, (178, 162, 112), (0, 0, ts, ts), 1)


def _water(surf, ts, rng):
    """Blue water with horizontal ripple highlights and sparkle pixels."""
    base = (45, 100, 195)
    surf.fill(base)
    # Alternating lighter/darker horizontal bands → ripple illusion
    for ry in range(0, ts, 4):
        pygame.draw.line(surf, (70, 130, 218), (0, ry),     (ts, ry),     1)
        pygame.draw.line(surf, (30,  82, 168), (0, ry + 2), (ts, ry + 2), 1)
    # Sparkle glints
    for _ in range(3):
        sx = rng.randint(2, ts - 3)
        sy = rng.randint(2, ts - 3)
        surf.set_at((sx, sy),         (210, 232, 255))
        surf.set_at((sx + 1, sy),     (170, 205, 248))
        surf.set_at((sx,     sy + 1), (170, 205, 248))


def _trees(surf, ts, rng):
    """Dark floor + 1–2 top-down tree canopies per tile."""
    surf.fill((10, 44, 10))
    n = rng.randint(1, 2)
    for _ in range(n):
        cx = rng.randint(ts // 4, 3 * ts // 4)
        cy = rng.randint(ts // 4, 3 * ts // 4)
        r  = rng.randint(5, 8)
        pygame.draw.circle(surf, (16,  60, 16), (cx, cy), r)          # outer shadow
        pygame.draw.circle(surf, (26,  84, 22), (cx, cy), max(1, r-2))# mid
        pygame.draw.circle(surf, (44, 112, 38), (cx-1, cy-2), max(1, r-4))  # highlight


# ─────────────────────────────────────────────────────────────────────────────
# Renderer class
# ─────────────────────────────────────────────────────────────────────────────

class CourseRenderer:
    """Pre-renders and draws the course tile map."""

    def __init__(self, hole):
        self.hole      = hole
        self.tile_size = TILE_SIZE

        self._course_surface = None
        self._build_course_surface()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_course_surface(self):
        """Render every tile to an off-screen surface (done once at startup)."""
        width  = self.hole.cols * self.tile_size
        height = self.hole.rows * self.tile_size
        self._course_surface = pygame.Surface((width, height))

        ts = self.tile_size
        for row in range(self.hole.rows):
            for col in range(self.hole.cols):
                terrain = self.hole.get_terrain_at(col, row)
                # Use a unique seed per tile for natural variation
                seed = col * 10007 + row * 37 + hash(terrain.value)
                tile = _make_tile(terrain, ts, seed)
                self._course_surface.blit(tile, (col * ts, row * ts))

        # Draw terrain-edge shadows for visual depth (bunker / water borders)
        self._draw_border_shadows()

        # Overlay markers
        self._draw_pin()
        self._draw_tee_marker()

    def _draw_border_shadows(self):
        """
        Draw a 1-pixel dark edge on the inside of bunker and water tiles
        wherever they border a different terrain type.
        """
        ts        = self.tile_size
        shadow    = (0, 0, 0)
        neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for row in range(self.hole.rows):
            for col in range(self.hole.cols):
                terrain = self.hole.get_terrain_at(col, row)
                if terrain not in (Terrain.BUNKER, Terrain.WATER):
                    continue

                tx, ty = col * ts, row * ts
                for dr, dc in neighbors:
                    nbr = self.hole.get_terrain_at(col + dc, row + dr)
                    if nbr == terrain:
                        continue
                    # Draw a 1-px line on the edge that faces the neighbor
                    if dr == -1:   # top edge
                        pygame.draw.line(self._course_surface, shadow,
                                         (tx, ty), (tx + ts - 1, ty))
                    elif dr == 1:  # bottom edge
                        pygame.draw.line(self._course_surface, shadow,
                                         (tx, ty + ts - 1), (tx + ts - 1, ty + ts - 1))
                    elif dc == -1: # left edge
                        pygame.draw.line(self._course_surface, shadow,
                                         (tx, ty), (tx, ty + ts - 1))
                    elif dc == 1:  # right edge
                        pygame.draw.line(self._course_surface, shadow,
                                         (tx + ts - 1, ty), (tx + ts - 1, ty + ts - 1))

    def _draw_pin(self):
        """Draw the hole cup, flag stick, and triangular flag."""
        col, row = self.hole.pin_pos
        cx = col * self.tile_size + self.tile_size // 2
        cy = row * self.tile_size + self.tile_size // 2

        # Hole cup: black circle with white rim
        pygame.draw.circle(self._course_surface, (255, 255, 255), (cx, cy), 7)
        pygame.draw.circle(self._course_surface, (0,   0,   0),   (cx, cy), 6)

        # Flag stick
        pygame.draw.line(self._course_surface, (220, 220, 220),
                         (cx, cy - 2), (cx, cy - 22), 2)

        # Flag — red triangle
        pygame.draw.polygon(self._course_surface, (210, 35, 35), [
            (cx,      cy - 22),
            (cx + 13, cy - 17),
            (cx,      cy - 11),
        ])
        pygame.draw.polygon(self._course_surface, (240, 60, 60), [
            (cx,      cy - 22),
            (cx + 11, cy - 17),
            (cx,      cy - 12),
        ], 1)

    def _draw_tee_marker(self):
        """Draw small white tee-marker dots either side of the tee position."""
        col, row = self.hole.tee_pos
        cx = col * self.tile_size + self.tile_size // 2
        cy = row * self.tile_size + self.tile_size // 2
        for ox in (-8, 8):
            pygame.draw.circle(self._course_surface, (255, 255, 255), (cx + ox, cy), 3)
            pygame.draw.circle(self._course_surface, (140, 180, 140), (cx + ox, cy), 3, 1)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface, camera_x, camera_y, viewport_rect):
        """
        Blit the visible portion of the course onto surface.

        camera_x/y    : top-left world position currently shown
        viewport_rect : pygame.Rect of the area on screen to draw into
        """
        source_area = pygame.Rect(
            int(camera_x), int(camera_y),
            viewport_rect.width, viewport_rect.height,
        )
        surface.blit(self._course_surface,
                     (viewport_rect.x, viewport_rect.y),
                     area=source_area)

    def draw_minimap(self, surface, dest_rect, ball_world_pos):
        """
        Draw a scaled-down overview of the entire hole into dest_rect.
        Shows terrain colours, the pin, and the ball's current position.

        dest_rect      : pygame.Rect where the minimap should appear on screen
        ball_world_pos : (x, y) in world pixels
        """
        ts   = self.tile_size
        cols = self.hole.cols
        rows = self.hole.rows

        # Scale to fit dest_rect while keeping aspect ratio
        scale = min(dest_rect.width  / (cols * ts),
                    dest_rect.height / (rows * ts))
        map_w = int(cols * ts * scale)
        map_h = int(rows * ts * scale)

        mini = pygame.Surface((map_w, map_h))

        # Draw terrain tiles at minimap scale
        mtw = max(1, int(ts * scale))
        mth = max(1, int(ts * scale))
        for row in range(rows):
            for col in range(cols):
                terrain = self.hole.get_terrain_at(col, row)
                color   = TERRAIN_PROPS[terrain]['color']
                mx = int(col * ts * scale)
                my = int(row * ts * scale)
                pygame.draw.rect(mini, color, (mx, my, mtw, mth))

        # Pin marker
        pc, pr     = self.hole.pin_pos
        pin_mx     = int((pc * ts + ts // 2) * scale)
        pin_my     = int((pr * ts + ts // 2) * scale)
        pygame.draw.circle(mini, (0,   0,   0),   (pin_mx, pin_my), 4)
        pygame.draw.circle(mini, (255, 255, 255), (pin_mx, pin_my), 3)
        pygame.draw.circle(mini, (210,  35,  35), (pin_mx, pin_my), 2)

        # Ball marker
        bx, by  = ball_world_pos
        ball_mx = int(bx * scale)
        ball_my = int(by * scale)
        ball_mx = max(2, min(map_w - 3, ball_mx))
        ball_my = max(2, min(map_h - 3, ball_my))
        pygame.draw.circle(mini, (0,   0,   0),   (ball_mx, ball_my), 4)
        pygame.draw.circle(mini, (255, 255, 255), (ball_mx, ball_my), 3)

        # Blit centred within dest_rect
        ox = dest_rect.x + (dest_rect.width  - map_w) // 2
        oy = dest_rect.y + (dest_rect.height - map_h) // 2
        surface.blit(mini, (ox, oy))

        # Border frame
        pygame.draw.rect(surface, (90, 120, 90),
                         pygame.Rect(ox - 1, oy - 1, map_w + 2, map_h + 2), 1)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def world_to_screen(self, world_x, world_y, camera_x, camera_y,
                        viewport_x=0, viewport_y=0):
        return (int(world_x - camera_x + viewport_x),
                int(world_y - camera_y + viewport_y))

    def get_pin_world_pos(self):
        col, row = self.hole.pin_pos
        return (col * self.tile_size + self.tile_size // 2,
                row * self.tile_size + self.tile_size // 2)

    def get_tee_world_pos(self):
        col, row = self.hole.tee_pos
        return (col * self.tile_size + self.tile_size // 2,
                row * self.tile_size + self.tile_size // 2)

    def world_size(self):
        return (self.hole.cols * self.tile_size,
                self.hole.rows * self.tile_size)
