"""
attribute_panel.py — terrain attribute brush selector.

Sits in the lower portion of the left panel.  Shows a row per terrain type
with a colour swatch and name.  Click a row to select that terrain as the
active attribute brush.  Includes an Auto-derive toggle button.

Public interface
────────────────
  draw(surface)
  handle_event(event) → bool
  selected     : Terrain enum — the active attribute brush
  auto_derive  : bool — whether painting a visual tile also sets attribute
"""

import pygame
from src.golf.terrain import Terrain, TERRAIN_PROPS

# Ordered list of terrain types shown in the panel
TERRAIN_ORDER = [
    Terrain.TEE,
    Terrain.FAIRWAY,
    Terrain.ROUGH,
    Terrain.DEEP_ROUGH,
    Terrain.BUNKER,
    Terrain.WATER,
    Terrain.TREES,
    Terrain.GREEN,
]

ROW_H    = 34      # height of each terrain row
HEADER_H = 28      # height of the panel header
SWATCH   = 18      # colour swatch size
MARGIN   = 8       # left/right margin
BTN_H    = 30      # auto-derive button height
BTN_GAP  = 6       # gap above button


class AttributePanel:
    """Terrain attribute brush selector panel."""

    def __init__(self, rect: pygame.Rect):
        self.rect        = rect
        self.selected    = Terrain.ROUGH    # default attribute brush
        self.auto_derive = True             # auto-set attribute when painting visual

        self._auto_btn_rect = pygame.Rect(0, 0, 0, 0)
        self._font   = pygame.font.SysFont("monospace", 12)
        self._font_h = pygame.font.SysFont("monospace", 11, bold=True)

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event) -> bool:
        """Returns True if the event was consumed."""
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        if not self.rect.collidepoint(event.pos):
            return False

        # Auto-derive button
        if self._auto_btn_rect.collidepoint(event.pos):
            self.auto_derive = not self.auto_derive
            return True

        # Terrain row
        terrain = self._pos_to_terrain(event.pos)
        if terrain is not None:
            self.selected = terrain
            return True

        return False

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        old_clip = surface.get_clip()
        surface.set_clip(self.rect)

        # Panel background
        pygame.draw.rect(surface, (40, 40, 40), self.rect)

        # Top separator line
        pygame.draw.line(surface, (70, 70, 70),
                         (self.rect.x, self.rect.y),
                         (self.rect.right, self.rect.y))
        # Right border
        pygame.draw.line(surface, (70, 70, 70),
                         (self.rect.right - 1, self.rect.top),
                         (self.rect.right - 1, self.rect.bottom))

        # Header
        hdr = self._font_h.render("ATTRIBUTE BRUSH", True, (160, 160, 160))
        surface.blit(hdr, (self.rect.x + MARGIN,
                           self.rect.y + (HEADER_H - hdr.get_height()) // 2))

        # Terrain rows
        y = self.rect.y + HEADER_H
        for terrain in TERRAIN_ORDER:
            self._draw_row(surface, terrain, y)
            y += ROW_H

        # Auto-derive button
        btn_y = y + BTN_GAP
        btn_rect = pygame.Rect(self.rect.x + MARGIN, btn_y,
                               self.rect.width - MARGIN * 2, BTN_H)
        self._auto_btn_rect = btn_rect

        btn_col = (45, 115, 70) if self.auto_derive else (90, 50, 50)
        pygame.draw.rect(surface, btn_col, btn_rect, border_radius=3)
        pygame.draw.rect(surface, (80, 80, 80), btn_rect, 1, border_radius=3)

        lbl = "Auto-derive  ON" if self.auto_derive else "Auto-derive  OFF"
        t   = self._font.render(lbl, True, (210, 210, 210))
        surface.blit(t, (btn_rect.x + (btn_rect.width - t.get_width()) // 2,
                         btn_rect.y + (btn_rect.height - t.get_height()) // 2))

        surface.set_clip(old_clip)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _draw_row(self, surface: pygame.Surface, terrain: Terrain, y: int):
        props    = TERRAIN_PROPS[terrain]
        color    = props["color"]
        name     = props["name"]
        selected = (terrain == self.selected)
        rx, rw   = self.rect.x, self.rect.width

        # Row highlight
        if selected:
            pygame.draw.rect(surface, (50, 70, 95), (rx, y, rw, ROW_H))

        # Selection indicator — 3-px blue bar on left edge
        if selected:
            pygame.draw.rect(surface, (80, 160, 255), (rx, y, 3, ROW_H))

        # Colour swatch
        sw_x = rx + MARGIN
        sw_y = y + (ROW_H - SWATCH) // 2
        pygame.draw.rect(surface, color, (sw_x, sw_y, SWATCH, SWATCH))
        pygame.draw.rect(surface, (110, 110, 110), (sw_x, sw_y, SWATCH, SWATCH), 1)

        # Name text
        fg  = (230, 230, 230) if selected else (155, 155, 155)
        txt = self._font.render(name, True, fg)
        surface.blit(txt, (sw_x + SWATCH + 7,
                           y + (ROW_H - txt.get_height()) // 2))

        # Row separator
        pygame.draw.line(surface, (55, 55, 55),
                         (rx, y + ROW_H - 1), (rx + rw, y + ROW_H - 1))

    def _pos_to_terrain(self, pos) -> Terrain | None:
        y = self.rect.y + HEADER_H
        for terrain in TERRAIN_ORDER:
            if pygame.Rect(self.rect.x, y, self.rect.width, ROW_H).collidepoint(pos):
                return terrain
            y += ROW_H
        return None
