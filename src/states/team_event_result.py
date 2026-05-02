"""
TeamEventResultState — shown after each day of the International Team Event.

Phase "after_day1"
  Shown when the foursomes round completes.  Summarises Day 1, then simulates
  Day 2 singles automatically and shows the overall team result.

This state finalises the session, awards wins to the player, then routes back
to CareerHubState.
"""

import pygame

from src.ui        import fonts
from src.constants import SCREEN_W, SCREEN_H

C_BG      = ( 10,  15,  30)
C_PANEL   = ( 18,  28,  50)
C_BORDER  = ( 60,  90, 160)
C_WHITE   = (255, 255, 255)
C_GRAY    = (155, 158, 175)
C_GOLD    = (215, 175,  50)
C_GREEN   = ( 55, 185,  55)
C_RED     = (215,  50,  50)
C_BLUE    = ( 80, 130, 220)
C_BTN     = ( 28,  55, 120)
C_BTN_HOV = ( 50,  90, 180)


class TeamEventResultState:
    """Shows Day 1 foursomes result, simulates Day 2, then shows the winner."""

    def __init__(self, game, course, foursomes_scores: list | None):
        self.game   = game
        self.player = game.player
        session     = game.current_tournament

        # ── Finalise foursomes if we have scores (played, not skipped) ────────
        if foursomes_scores is not None and session is not None:
            session.finalize_foursomes(foursomes_scores)

        # ── Simulate Day 2 singles ─────────────────────────────────────────────
        if session is not None and session.singles_result is None:
            session.simulate_singles(self.player.tour_level)

        # ── Apply result to player ─────────────────────────────────────────────
        if session is not None and session.home_won:
            self.player.team_event_wins = getattr(self.player, "team_event_wins", 0) + 1
            prize = _prize_for_tour(self.player.tour_level)
            self.player.earn_money(prize)
            self.player.gain_reputation(8)
            self._prize = prize
            self._won   = True
        else:
            self._prize = _consolation_for_tour(self.player.tour_level)
            self.player.earn_money(self._prize)
            self._won = False

        # ── Autosave ──────────────────────────────────────────────────────────
        try:
            from src.utils.save_system import save_game
            save_game(self.player, None)
        except Exception as e:
            print(f"Team event autosave failed: {e}")

        # Clear tournament
        self.game.current_tournament = None

        # ── Fonts / UI ────────────────────────────────────────────────────────
        self.font_huge  = fonts.heading(52)
        self.font_title = fonts.heading(30)
        self.font_hdr   = fonts.heading(18)
        self.font_med   = fonts.body(17)
        self.font_small = fonts.body(14)

        bw, bh = 280, 50
        self._btn = pygame.Rect(SCREEN_W // 2 - bw // 2, SCREEN_H - 80, bw, bh)
        self._hover = False

        self._session_snap = session   # keep reference for display

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hover = self._btn.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn.collidepoint(event.pos):
                self._go_hub()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self._go_hub()

    def _go_hub(self):
        from src.states.career_hub import CareerHubState
        self.game.change_state(CareerHubState(self.game))

    def update(self, dt): pass

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(C_BG)
        cx = SCREEN_W // 2
        s  = self._session_snap

        # ── Header ────────────────────────────────────────────────────────────
        ty = 22
        title_col = C_GOLD if self._won else C_WHITE
        title_txt = "Victory!" if self._won else "Defeat"
        th = self.font_huge.render(title_txt, True, title_col)
        surface.blit(th, (cx - th.get_width() // 2, ty)); ty += 60

        sub = self.font_hdr.render("International Team Event — Final Result", True, C_GRAY)
        surface.blit(sub, (cx - sub.get_width() // 2, ty)); ty += 36

        # ── Day 1 result ──────────────────────────────────────────────────────
        _box(surface, pygame.Rect(cx - 540, ty, 520, 130))
        d1h = self.font_hdr.render("Day 1 — Foursomes", True, C_GOLD)
        surface.blit(d1h, (cx - 525, ty + 8))
        if s is not None:
            _row(surface, self.font_med,
                 f"Your team score:  {s.foursomes_player_score if s.foursomes_player_score else '—'}",
                 C_WHITE, cx - 525, ty + 36)
            _row(surface, self.font_med,
                 f"Opponents score:  {s.foursomes_opp_score}",
                 C_WHITE, cx - 525, ty + 60)
            r1 = s.foursomes_result or "—"
            col = C_GREEN if r1 == "win" else (C_RED if r1 == "loss" else C_GOLD)
            _row(surface, self.font_med,
                 f"Result:  {r1.upper()}   →  "
                 f"{'Home +1' if r1 == 'win' else ('Away +1' if r1 == 'loss' else 'Half point each')}",
                 col, cx - 525, ty + 88)

        # ── Day 2 result ──────────────────────────────────────────────────────
        _box(surface, pygame.Rect(cx + 20, ty, 520, 130))
        d2h = self.font_hdr.render("Day 2 — Singles (simulated)", True, C_GOLD)
        surface.blit(d2h, (cx + 35, ty + 8))
        if s is not None:
            opp = s.singles_opponent
            _row(surface, self.font_med,
                 f"Your match:  {self.player.name}  vs  {opp}",
                 C_WHITE, cx + 35, ty + 36)
            sr = s.singles_result or "—"
            sc = C_GREEN if sr == "win" else C_RED
            _row(surface, self.font_med,
                 f"Result:  {sr.upper()}   →  "
                 f"{'Home +1' if sr == 'win' else 'Away +1'}",
                 sc, cx + 35, ty + 60)

        ty += 150

        # ── Overall score ─────────────────────────────────────────────────────
        _box(surface, pygame.Rect(cx - 260, ty, 520, 110))
        oh = self.font_hdr.render("Final Team Score", True, C_GOLD)
        surface.blit(oh, (cx - oh.get_width() // 2, ty + 8))
        if s is not None:
            score_txt = (f"Home  {s.team_points_home:.0f}  —  "
                         f"{s.team_points_away:.0f}  Away")
            sc_col    = C_GREEN if self._won else C_RED
            scl = self.font_title.render(score_txt, True, sc_col)
            surface.blit(scl, (cx - scl.get_width() // 2, ty + 40))
            win_lbl = "HOME WIN!" if self._won else "AWAY WIN"
            wls = self.font_hdr.render(win_lbl, True, sc_col)
            surface.blit(wls, (cx - wls.get_width() // 2, ty + 82))

        ty += 130

        # ── Rewards ───────────────────────────────────────────────────────────
        rl = self.font_med.render(
            f"Prize money: ${self._prize:,}   "
            f"{'  Reputation +8' if self._won else ''}",
            True, C_GOLD if self._won else C_GRAY)
        surface.blit(rl, (cx - rl.get_width() // 2, ty)); ty += 26

        wins = getattr(self.player, "team_event_wins", 0)
        if wins > 0:
            wl = self.font_small.render(
                f"Career team event wins: {wins}", True, C_GOLD)
            surface.blit(wl, (cx - wl.get_width() // 2, ty))

        # ── Button ────────────────────────────────────────────────────────────
        bg = C_BTN_HOV if self._hover else C_BTN
        pygame.draw.rect(surface, bg,    self._btn, border_radius=9)
        pygame.draw.rect(surface, C_BLUE, self._btn, 2, border_radius=9)
        bl = self.font_hdr.render("Return to Career Hub", True, C_WHITE)
        surface.blit(bl, bl.get_rect(center=self._btn.center))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _prize_for_tour(tour_level: int) -> int:
    prizes = {1: 1000, 2: 3000, 3: 6000, 4: 12000, 5: 25000, 6: 50000}
    return prizes.get(tour_level, 5000)


def _consolation_for_tour(tour_level: int) -> int:
    return _prize_for_tour(tour_level) // 4


def _box(surface, r: pygame.Rect):
    pygame.draw.rect(surface, C_PANEL,  r, border_radius=8)
    pygame.draw.rect(surface, C_BORDER, r, 1, border_radius=8)


def _row(surface, font, text: str, color, x: int, y: int):
    s = font.render(text, True, color)
    surface.blit(s, (x, y))
