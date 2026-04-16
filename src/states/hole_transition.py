"""
HoleTransitionState — shown between holes.

Displays:
  • The scorecard so far (all completed holes)
  • Hole just completed: score name (birdie / par / bogey etc.)
  • "Next Hole" button to continue
"""

import pygame

from src.ui.scorecard import Scorecard

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG      = ( 12,  20,  12)
C_PANEL   = ( 20,  30,  20)
C_BORDER  = ( 65,  95,  65)
C_WHITE   = (255, 255, 255)
C_GRAY    = (165, 168, 160)
C_GREEN   = ( 55, 185,  55)
C_RED     = (215,  50,  50)
C_YELLOW  = (215, 175,  50)
C_BTN     = ( 40, 120,  40)
C_BTN_HOV = ( 60, 160,  60)

SCREEN_W = 1280
SCREEN_H = 720


class HoleTransitionState:
    """Between-hole screen with running scorecard and 'Next Hole' button."""

    def __init__(self, game, course, completed_hole_index, scores):
        """
        Parameters
        ----------
        game                 : Game
        course               : Course
        completed_hole_index : int — 0-based index of the hole just completed
        scores               : list[int] — strokes for holes 0..completed_hole_index
        """
        self.game                 = game
        self.course               = course
        self.completed_hole_index = completed_hole_index
        self.scores               = scores   # length = completed_hole_index + 1

        self.scorecard = Scorecard(course)

        self.font_title  = pygame.font.SysFont("arial", 36, bold=True)
        self.font_large  = pygame.font.SysFont("arial", 28, bold=True)
        self.font_medium = pygame.font.SysFont("arial", 20)
        self.font_small  = pygame.font.SysFont("arial", 16)

        # Button
        btn_w, btn_h = 260, 50
        self.btn_next = pygame.Rect(
            SCREEN_W // 2 - btn_w // 2,
            SCREEN_H - 80,
            btn_w, btn_h)
        self._btn_hover = False

        # Scorecard rect (centred, most of the screen)
        sc_w = min(1100, SCREEN_W - 60)
        sc_h = 200
        self.sc_rect = pygame.Rect(
            (SCREEN_W - sc_w) // 2,
            240,
            sc_w, sc_h)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _score_label(self, strokes, par):
        if strokes == 1:
            return "Hole in One!", C_YELLOW
        diff = strokes - par
        labels = {
            -3: ("Albatross!", C_YELLOW),
            -2: ("Eagle!",     C_GREEN),
            -1: ("Birdie!",    C_GREEN),
             0: ("Par",        C_WHITE),
             1: ("Bogey",      C_RED),
             2: ("Double Bogey", C_RED),
        }
        return labels.get(diff, (f"+{diff}" if diff > 0 else str(diff), C_RED))

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_next.collidepoint(event.pos):
                self._go_next()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_n):
                self._go_next()
        elif event.type == pygame.MOUSEMOTION:
            self._btn_hover = self.btn_next.collidepoint(event.pos)

    def _go_next(self):
        from src.states.golf_round import GolfRoundState
        next_index = self.completed_hole_index + 1
        self.game.change_state(
            GolfRoundState(self.game, self.course, next_index, self.scores))

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        pass   # static screen — nothing to animate yet

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(C_BG)

        cx = SCREEN_W // 2

        # ── Title ─────────────────────────────────────────────────────────────
        hole_num = self.completed_hole_index + 1
        title = self.font_title.render(
            f"Hole {hole_num} Complete", True, C_WHITE)
        surface.blit(title, (cx - title.get_width() // 2, 28))

        # ── Score badge ───────────────────────────────────────────────────────
        strokes = self.scores[self.completed_hole_index]
        par     = self.course.get_hole(self.completed_hole_index).par
        label, lcolor = self._score_label(strokes, par)

        badge = self.font_large.render(label, True, lcolor)
        surface.blit(badge, (cx - badge.get_width() // 2, 80))

        detail = self.font_medium.render(
            f"{strokes} strokes  •  Par {par}", True, C_GRAY)
        surface.blit(detail, (cx - detail.get_width() // 2, 120))

        # ── Running total ─────────────────────────────────────────────────────
        total_strokes = sum(self.scores)
        total_par     = self.course.total_par_through(len(self.scores))
        diff          = total_strokes - total_par
        diff_str      = ("E" if diff == 0
                         else f"+{diff}" if diff > 0
                         else str(diff))
        diff_color    = (C_GREEN if diff < 0
                         else C_RED if diff > 0
                         else C_WHITE)

        running = self.font_medium.render(
            f"Round total after {len(self.scores)} holes:  "
            f"{total_strokes}  ({diff_str})", True, diff_color)
        surface.blit(running, (cx - running.get_width() // 2, 158))

        # ── Scorecard ─────────────────────────────────────────────────────────
        sc_title = self.font_small.render("SCORECARD", True, C_GRAY)
        surface.blit(sc_title,
                     (self.sc_rect.x, self.sc_rect.y - sc_title.get_height() - 4))

        self.scorecard.draw(surface, self.sc_rect, self.scores)

        # ── Divider ───────────────────────────────────────────────────────────
        div_y = self.sc_rect.bottom + 16
        pygame.draw.line(surface, C_BORDER,
                         (60, div_y), (SCREEN_W - 60, div_y))

        # ── Next Hole button ──────────────────────────────────────────────────
        next_hole_num = self.completed_hole_index + 2   # 1-based
        btn_color = C_BTN_HOV if self._btn_hover else C_BTN
        pygame.draw.rect(surface, btn_color, self.btn_next, border_radius=8)
        pygame.draw.rect(surface, C_GREEN,   self.btn_next, 2, border_radius=8)

        btn_lbl = self.font_medium.render(
            f"Next: Hole {next_hole_num}  (Enter / N)", True, C_WHITE)
        surface.blit(btn_lbl, btn_lbl.get_rect(center=self.btn_next.center))

        # ── Remaining holes hint ──────────────────────────────────────────────
        remaining = 18 - len(self.scores)
        hint = self.font_small.render(
            f"{remaining} hole{'s' if remaining != 1 else ''} remaining", True, C_GRAY)
        surface.blit(hint, (cx - hint.get_width() // 2, self.btn_next.bottom + 8))
