"""
HUD — the right-hand info panel drawn during a golf round.

Displays:
  • Hole number, par, and yardage
  • Stroke count and score vs par
  • Current terrain (lie)
  • Active club with prev/next cycle buttons
  • Power bar (fills while player drags)
  • Shot shape selector (Draw / Straight / Fade)
  • Mini-map of the hole with ball and pin markers
"""

import math

import pygame

from src.golf.shot import ShotState, ShotShape, MAX_DRAG_PIXELS
from src.utils.math_utils import clamp

# ── Colour palette ────────────────────────────────────────────────────────────
C_BG         = ( 22,  28,  22)
C_PANEL_TOP  = ( 32,  40,  32)
C_BORDER     = ( 75, 105,  75)
C_DIVIDER    = ( 50,  70,  50)
C_WHITE      = (255, 255, 255)
C_OFF_WHITE  = (220, 225, 215)
C_LIGHT_GRAY = (165, 168, 160)
C_DARK_GRAY  = ( 48,  52,  48)
C_GREEN      = ( 55, 185,  55)
C_RED        = (215,  50,  50)
C_GOLD       = (215, 175,  50)
C_BLUE       = ( 60, 120, 215)

PANEL_WIDTH  = 320


class HUD:
    """Right-side information and control panel."""

    def __init__(self, screen_width, screen_height):
        self.screen_width  = screen_width
        self.screen_height = screen_height
        self.panel_x       = screen_width - PANEL_WIDTH
        self.panel_rect    = pygame.Rect(self.panel_x, 0, PANEL_WIDTH, screen_height)

        self.font_large  = pygame.font.SysFont("arial", 28, bold=True)
        self.font_medium = pygame.font.SysFont("arial", 19)
        self.font_small  = pygame.font.SysFont("arial", 15)

        self._build_buttons()

    def _build_buttons(self):
        px = self.panel_x

        # Club navigation arrows
        self.btn_prev_club = pygame.Rect(px + 10,  260, 34, 28)
        self.btn_next_club = pygame.Rect(px + 276, 260, 34, 28)

        # Shot shape buttons
        btn_y = 390
        btn_w = 84
        btn_h = 34
        gap   = 5
        self.shape_buttons = {
            ShotShape.DRAW:     pygame.Rect(px + 10,                  btn_y, btn_w, btn_h),
            ShotShape.STRAIGHT: pygame.Rect(px + 10 +  btn_w + gap,   btn_y, btn_w, btn_h),
            ShotShape.FADE:     pygame.Rect(px + 10 + (btn_w + gap)*2, btn_y, btn_w, btn_h),
        }

        # Mini-map area
        self.minimap_rect = pygame.Rect(px + 10, 460, PANEL_WIDTH - 20, 190)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface, hole, strokes, club, shot_ctrl, terrain_name,
             renderer=None, ball_world_pos=None):
        """
        Draw the complete HUD panel.

        renderer        : CourseRenderer — used to draw the mini-map (optional)
        ball_world_pos  : (x, y) in world pixels — ball position for mini-map
        """
        # ── Background ────────────────────────────────────────────────────────
        pygame.draw.rect(surface, C_BG, self.panel_rect)

        # Gradient header stripe
        header = pygame.Rect(self.panel_x, 0, PANEL_WIDTH, 72)
        pygame.draw.rect(surface, C_PANEL_TOP, header)
        pygame.draw.line(surface, C_BORDER,
                         (self.panel_x, 0), (self.panel_x, self.screen_height), 2)

        x  = self.panel_x + 14   # left content margin
        rw = PANEL_WIDTH - 28    # usable row width

        # ── Hole header ───────────────────────────────────────────────────────
        self._text(surface, f"Hole {hole.number}", self.font_large, C_WHITE, x, 14)
        par_txt = f"Par {hole.par}   •   {hole.yardage} yds"
        self._text(surface, par_txt, self.font_small, C_LIGHT_GRAY, x, 48)

        self._divider(surface, 72)

        # ── Strokes ───────────────────────────────────────────────────────────
        y = 82
        self._text(surface, "Strokes", self.font_small, C_LIGHT_GRAY, x, y)

        num_surf = self.font_large.render(str(strokes), True, C_WHITE)
        surface.blit(num_surf, (x, y + 18))

        if strokes > 0:
            diff = strokes - hole.par
            diff_str   = (str(diff) if diff < 0
                          else "E" if diff == 0
                          else f"+{diff}")
            diff_color = C_GREEN if diff < 0 else C_WHITE if diff == 0 else C_RED
            self._text(surface, diff_str, self.font_medium, diff_color,
                       x + num_surf.get_width() + 10, y + 22)

        self._divider(surface, 140)

        # ── Lie ───────────────────────────────────────────────────────────────
        y = 150
        self._text(surface, "Lie",         self.font_small,  C_LIGHT_GRAY, x,      y)
        self._text(surface, terrain_name,  self.font_medium, C_OFF_WHITE,  x + 32, y - 1)

        self._divider(surface, 178)

        # ── Club ──────────────────────────────────────────────────────────────
        y = 188
        self._text(surface, "Club", self.font_small, C_LIGHT_GRAY, x, y)

        # Prev / Next arrows
        self._draw_button(surface, self.btn_prev_club, "<", C_DARK_GRAY, C_OFF_WHITE)
        self._draw_button(surface, self.btn_next_club, ">", C_DARK_GRAY, C_OFF_WHITE)

        # Club name centred between arrows
        club_cx = (self.btn_prev_club.right + self.btn_next_club.left) // 2
        club_s  = self.font_medium.render(club.name, True, C_GOLD)
        surface.blit(club_s, (club_cx - club_s.get_width() // 2,
                               self.btn_prev_club.y + 5))

        # Max distance below
        dist_s = self.font_small.render(f"Max {club.max_distance_yards} yds",
                                         True, C_LIGHT_GRAY)
        surface.blit(dist_s, (club_cx - dist_s.get_width() // 2, 295))

        self._divider(surface, 318)

        # ── Power bar ─────────────────────────────────────────────────────────
        y = 326
        self._text(surface, "Power", self.font_small, C_LIGHT_GRAY, x, y)

        power    = shot_ctrl.get_power()
        bar_rect = pygame.Rect(x, y + 18, rw, 20)

        pygame.draw.rect(surface, C_DARK_GRAY, bar_rect, border_radius=4)
        if power > 0:
            fc = (C_GREEN if power < 0.65 else C_GOLD if power < 0.88 else C_RED)
            pygame.draw.rect(surface, fc,
                             pygame.Rect(x, y + 18, int(rw * power), 20),
                             border_radius=4)
        pygame.draw.rect(surface, C_DIVIDER, bar_rect, 1, border_radius=4)

        pct = self.font_small.render(f"{int(power * 100)}%", True, C_WHITE)
        surface.blit(pct, (x + rw // 2 - pct.get_width() // 2, y + 20))

        self._divider(surface, 368)

        # ── Shot shape ────────────────────────────────────────────────────────
        y = 376
        self._text(surface, "Shot Shape", self.font_small, C_LIGHT_GRAY, x, y)

        accents = {ShotShape.DRAW: C_BLUE, ShotShape.STRAIGHT: C_GREEN, ShotShape.FADE: C_RED}
        for shape, rect in self.shape_buttons.items():
            accent   = accents[shape]
            active   = shot_ctrl.shot_shape == shape
            bg       = accent if active else C_DARK_GRAY
            pygame.draw.rect(surface, bg,     rect, border_radius=5)
            pygame.draw.rect(surface, accent, rect, 2, border_radius=5)
            lbl = self.font_small.render(shape.value, True, C_WHITE)
            surface.blit(lbl, lbl.get_rect(center=rect.center))

        self._divider(surface, 434)

        # ── Mini-map ──────────────────────────────────────────────────────────
        y = 440
        self._text(surface, "Course Map", self.font_small, C_LIGHT_GRAY, x, y)

        if renderer is not None and ball_world_pos is not None:
            renderer.draw_minimap(surface, self.minimap_rect, ball_world_pos)
        else:
            # Placeholder if renderer not provided
            pygame.draw.rect(surface, C_DARK_GRAY, self.minimap_rect, border_radius=3)
            pygame.draw.rect(surface, C_DIVIDER,   self.minimap_rect, 1, border_radius=3)

        self._divider(surface, self.minimap_rect.bottom + 8)

        # ── Controls (compact) ────────────────────────────────────────────────
        y = self.minimap_rect.bottom + 16
        for line in ("Click near ball  •  Drag to aim",
                     "Release to shoot  •  Scroll = club"):
            self._text(surface, line, self.font_small, (110, 115, 108), x, y)
            y += 20

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_click(self, pos, shot_ctrl, clubs, current_index):
        for shape, rect in self.shape_buttons.items():
            if rect.collidepoint(pos):
                shot_ctrl.shot_shape = shape
                return current_index
        if self.btn_prev_club.collidepoint(pos):
            return (current_index - 1) % len(clubs)
        if self.btn_next_club.collidepoint(pos):
            return (current_index + 1) % len(clubs)
        return current_index

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _text(self, surface, text, font, color, x, y):
        surface.blit(font.render(text, True, color), (x, y))

    def _divider(self, surface, y):
        pygame.draw.line(surface, C_DIVIDER,
                         (self.panel_x + 10, y),
                         (self.panel_x + PANEL_WIDTH - 10, y))

    def _draw_button(self, surface, rect, label, bg, text_color):
        pygame.draw.rect(surface, bg,        rect, border_radius=4)
        pygame.draw.rect(surface, C_BORDER,  rect, 1, border_radius=4)
        lbl = self.font_medium.render(label, True, text_color)
        surface.blit(lbl, lbl.get_rect(center=rect.center))
