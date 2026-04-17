"""
RoundSummaryState — shown at the end of an 18-hole round.

Displays:
  • Full 18-hole scorecard
  • Total score vs par with score name
  • "Play Again" button (restarts a fresh round on the same course)
"""

import pygame

from src.ui.scorecard import Scorecard

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG      = ( 10,  16,  10)
C_PANEL   = ( 20,  30,  20)
C_BORDER  = ( 65,  95,  65)
C_WHITE   = (255, 255, 255)
C_GRAY    = (165, 168, 160)
C_GREEN   = ( 55, 185,  55)
C_RED     = (215,  50,  50)
C_YELLOW  = (215, 175,  50)
C_GOLD    = (210, 170,  30)
C_BTN     = ( 35, 100,  35)
C_BTN_HOV = ( 55, 145,  55)

SCREEN_W = 1280
SCREEN_H = 720

# Colour-coded score descriptions for full-round totals
_ROUND_DESCRIPTIONS = [
    (-20,  "Phenomenal Round!",       (180, 220,  80)),
    (-10,  "Exceptional Round!",      ( 55, 185,  55)),
    ( -5,  "Excellent Round!",        ( 55, 185,  55)),
    ( -1,  "Great Round!",            ( 55, 185,  55)),
    (  0,  "Round of Par",            (210, 210, 210)),
    (  4,  "Decent Round",            (200, 200, 160)),
    (  9,  "Room for Improvement",    (200, 160, 100)),
    (  18, "Tough Day Out There",     (215,  80,  80)),
    (999,  "Keep Practising!",        (180,  50,  50)),
]


def _round_description(total_diff):
    """Return (text, colour) based on how far over/under par the round was."""
    for threshold, text, color in _ROUND_DESCRIPTIONS:
        if total_diff <= threshold:
            return text, color
    return "Keep Practising!", (180, 50, 50)


class RoundSummaryState:
    """End-of-round screen with full scorecard."""

    def __init__(self, game, course, scores):
        """
        Parameters
        ----------
        game   : Game
        course : Course
        scores : list[int] — 18 stroke totals (one per hole)
        """
        self.game   = game
        self.course = course
        self.scores = scores    # must be length 18

        self.scorecard = Scorecard(course)

        # Log and save if a player profile exists
        if game.player is not None:
            game.player.log_round(course.name, sum(scores), course.par)
            try:
                from src.utils.save_system import save_game
                save_game(game.player)
            except Exception as e:
                print(f"Auto-save failed: {e}")

        self.font_title  = pygame.font.SysFont("arial", 42, bold=True)
        self.font_large  = pygame.font.SysFont("arial", 30, bold=True)
        self.font_medium = pygame.font.SysFont("arial", 20)
        self.font_small  = pygame.font.SysFont("arial", 15)

        # Scorecard area
        sc_w = min(1140, SCREEN_W - 40)
        sc_h = 215
        self.sc_rect = pygame.Rect(
            (SCREEN_W - sc_w) // 2,
            230,
            sc_w, sc_h)

        # Play Again / Return to Menu buttons
        btn_w, btn_h = 260, 52
        gap = 20
        total = btn_w * 2 + gap
        bx = SCREEN_W // 2 - total // 2
        by = SCREEN_H - 76
        self.btn_play_again = pygame.Rect(bx + btn_w + gap, by, btn_w, btn_h)
        self.btn_menu       = pygame.Rect(bx,               by, btn_w, btn_h)
        self._hover_play    = False
        self._hover_menu    = False

    # ── Computed stats ────────────────────────────────────────────────────────

    @property
    def _total_strokes(self):
        return sum(self.scores)

    @property
    def _total_diff(self):
        return self._total_strokes - self.course.par

    @property
    def _front_strokes(self):
        return sum(self.scores[:9])

    @property
    def _back_strokes(self):
        return sum(self.scores[9:])

    def _best_hole(self):
        """Return (hole_index, diff) for the best hole relative to par."""
        best_diff = 999
        best_idx  = 0
        for i, s in enumerate(self.scores):
            d = s - self.course.get_hole(i).par
            if d < best_diff:
                best_diff = d
                best_idx  = i
        return best_idx, best_diff

    def _worst_hole(self):
        """Return (hole_index, diff) for the worst hole relative to par."""
        worst_diff = -999
        worst_idx  = 0
        for i, s in enumerate(self.scores):
            d = s - self.course.get_hole(i).par
            if d > worst_diff:
                worst_diff = d
                worst_idx  = i
        return worst_idx, worst_diff

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_play_again.collidepoint(event.pos):
                self._play_again()
            elif self.btn_menu.collidepoint(event.pos):
                self._return_to_menu()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                self._play_again()
            elif event.key == pygame.K_ESCAPE:
                self._return_to_menu()
        elif event.type == pygame.MOUSEMOTION:
            self._hover_play = self.btn_play_again.collidepoint(event.pos)
            self._hover_menu = self.btn_menu.collidepoint(event.pos)

    def _play_again(self):
        from src.states.golf_round import GolfRoundState
        self.game.change_state(GolfRoundState(self.game, self.course, 0, []))

    def _return_to_menu(self):
        from src.states.main_menu import MainMenuState
        self.game.change_state(MainMenuState(self.game))

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        pass

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(C_BG)

        cx = SCREEN_W // 2
        total_diff = self._total_diff
        diff_str   = ("E" if total_diff == 0
                      else f"+{total_diff}" if total_diff > 0
                      else str(total_diff))

        # ── Title ─────────────────────────────────────────────────────────────
        title = self.font_title.render("Round Complete", True, C_WHITE)
        surface.blit(title, (cx - title.get_width() // 2, 18))

        # ── Course name ───────────────────────────────────────────────────────
        course_lbl = self.font_medium.render(
            self.course.name, True, C_GRAY)
        surface.blit(course_lbl, (cx - course_lbl.get_width() // 2, 70))

        # ── Total score ───────────────────────────────────────────────────────
        score_color = (C_GREEN if total_diff < 0
                       else C_RED if total_diff > 0
                       else C_WHITE)
        score_txt = self.font_large.render(
            f"{self._total_strokes}  ({diff_str})  •  Par {self.course.par}",
            True, score_color)
        surface.blit(score_txt, (cx - score_txt.get_width() // 2, 100))

        # ── Round description ─────────────────────────────────────────────────
        desc, desc_color = _round_description(total_diff)
        desc_surf = self.font_medium.render(desc, True, desc_color)
        surface.blit(desc_surf, (cx - desc_surf.get_width() // 2, 142))

        # ── Front / Back split ────────────────────────────────────────────────
        fp  = self.course.front_par
        bp  = self.course.back_par
        fd  = self._front_strokes - fp
        bd  = self._back_strokes  - bp
        fds = "E" if fd == 0 else (f"+{fd}" if fd > 0 else str(fd))
        bds = "E" if bd == 0 else (f"+{bd}" if bd > 0 else str(bd))
        split_txt = (f"Front: {self._front_strokes} ({fds})   "
                     f"Back: {self._back_strokes} ({bds})")
        split_surf = self.font_small.render(split_txt, True, C_GRAY)
        surface.blit(split_surf, (cx - split_surf.get_width() // 2, 178))

        # ── Scorecard ─────────────────────────────────────────────────────────
        sc_title = self.font_small.render("SCORECARD", True, C_GRAY)
        surface.blit(sc_title,
                     (self.sc_rect.x, self.sc_rect.y - sc_title.get_height() - 4))

        self.scorecard.draw(surface, self.sc_rect, self.scores)

        # ── Best / worst hole ─────────────────────────────────────────────────
        best_i,  best_d  = self._best_hole()
        worst_i, worst_d = self._worst_hole()

        def diff_label(d):
            labels = {-3: "Albatross", -2: "Eagle", -1: "Birdie",
                       0: "Par", 1: "Bogey", 2: "Double Bogey"}
            return labels.get(d, f"+{d}" if d > 0 else str(d))

        stats_y = self.sc_rect.bottom + 12
        best_txt  = (f"Best hole: #{best_i + 1}  —  "
                     f"{diff_label(best_d)}")
        worst_txt = (f"Toughest hole: #{worst_i + 1}  —  "
                     f"{diff_label(worst_d)}")
        best_s  = self.font_small.render(best_txt,  True, C_GREEN)
        worst_s = self.font_small.render(worst_txt, True, C_RED)

        gap = 40
        total_w = best_s.get_width() + gap + worst_s.get_width()
        bx = cx - total_w // 2
        surface.blit(best_s,  (bx, stats_y))
        surface.blit(worst_s, (bx + best_s.get_width() + gap, stats_y))

        # ── Divider ───────────────────────────────────────────────────────────
        div_y = stats_y + 24
        pygame.draw.line(surface, C_BORDER,
                         (60, div_y), (SCREEN_W - 60, div_y))

        # ── Buttons ───────────────────────────────────────────────────────────
        # Return to Menu
        menu_bg = (55, 30, 30) if self._hover_menu else (38, 20, 20)
        pygame.draw.rect(surface, menu_bg,  self.btn_menu, border_radius=8)
        pygame.draw.rect(surface, C_RED,    self.btn_menu, 2, border_radius=8)
        ml = self.font_medium.render("Main Menu  (Esc)", True, C_WHITE)
        surface.blit(ml, ml.get_rect(center=self.btn_menu.center))

        # Play Again
        play_bg = C_BTN_HOV if self._hover_play else C_BTN
        pygame.draw.rect(surface, play_bg,  self.btn_play_again, border_radius=8)
        pygame.draw.rect(surface, C_GREEN,  self.btn_play_again, 2, border_radius=8)
        pl = self.font_medium.render("Play Again  (Enter)", True, C_WHITE)
        surface.blit(pl, pl.get_rect(center=self.btn_play_again.center))
