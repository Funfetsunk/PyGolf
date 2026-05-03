"""
CttpCompetitionState — Closest to the Pin Competition (Phase 8, Task 8.2).

3 attempts with PW or 9-Iron at a 120-yard pin. Track best (closest) distance.
5 AI opponents have pre-simulated distances from the pin based on tour level.
Win if player's best distance <= the closest opponent.

Chains to PuttingChallengeState on completion.
"""

import math
import random

import pygame

from src.states.practice_base import (
    PracticeBase,
    VIEWPORT_W, VIEWPORT_H, PX_PER_YARD,
    C_GOLD, C_GREEN, C_GRAY, C_WHITE, C_BTN, C_BTN_H, C_BORDER,
)
from src.golf.terrain import Terrain

TOTAL_ATTEMPTS = 3
NUM_OPPONENTS  = 5

TEE_X = VIEWPORT_W // 2
TEE_Y = VIEWPORT_H - 80

PIN_X = VIEWPORT_W // 2
PIN_Y = int(TEE_Y - 120 * PX_PER_YARD)

_CLUBS = ["Pitching Wedge", "9-Iron"]

# Opponent distances (yards from pin) by tour level — lower = better opponents
_OPP_RANGES = {
    1: (7.0, 28.0),
    2: (5.5, 20.0),
    3: (4.0, 16.0),
    4: (2.8, 11.5),
    5: (1.5, 7.5),
    6: (0.6, 4.5),
}


def _sim_opponents(tour_level: int, seed: int) -> list[float]:
    rng = random.Random(seed)
    lo, hi = _OPP_RANGES.get(tour_level, (7.0, 28.0))
    return sorted([round(rng.uniform(lo, hi), 1) for _ in range(NUM_OPPONENTS)])


class CttpCompetitionState(PracticeBase):
    MINIGAME_ID = "cttp_competition"
    TITLE       = "Closest to Pin"

    def __init__(self, game):
        super().__init__(game)
        session    = game.current_tournament
        tour_level = getattr(session, "tour_level", 1)
        seed       = (id(session) + 1) & 0xFFFF
        self._opp_distances = _sim_opponents(tour_level, seed)

    def _build_layout(self):
        self._tee_x              = float(TEE_X)
        self._tee_y              = float(TEE_Y)
        self._attempts_remaining = TOTAL_ATTEMPTS
        self._club_idx           = 0
        self._best_dist: float | None = None
        self._last_dist: float | None = None
        self._complete_msg       = ""
        self._opp_distances: list[float] = []
        # Club selection buttons in the panel
        bx = 970
        self._club_btns: list[tuple[str, pygame.Rect]] = [
            (name, pygame.Rect(bx, 120 + i * 34, 280, 26))
            for i, name in enumerate(_CLUBS)
        ]

    def _pin_world_pos(self):
        return (float(PIN_X), float(PIN_Y))

    def _draw_course(self, surface):
        # Sky
        pygame.draw.rect(surface, (80, 140, 200),
                         pygame.Rect(0, 0, VIEWPORT_W, PIN_Y - 30))
        # Fairway
        pygame.draw.rect(surface, (60, 170, 60),
                         pygame.Rect(0, PIN_Y - 30, VIEWPORT_W, VIEWPORT_H - (PIN_Y - 30)))
        # Green circle
        pygame.draw.circle(surface, (55, 190, 65), (PIN_X, PIN_Y), 70)
        pygame.draw.circle(surface, (45, 155, 55), (PIN_X, PIN_Y), 70, 2)
        # Distance rings (5, 10, 20 yards)
        for r_y in (5, 10, 20):
            r_px = int(r_y * PX_PER_YARD)
            pygame.draw.circle(surface, (100, 220, 100), (PIN_X, PIN_Y), r_px, 1)
        # Pin
        pygame.draw.circle(surface, (15, 15, 15), (PIN_X, PIN_Y), 6)
        pygame.draw.line(surface, (210, 210, 210),
                         (PIN_X, PIN_Y - 6), (PIN_X, PIN_Y - 42), 2)
        pygame.draw.polygon(surface, (220, 50, 50), [
            (PIN_X, PIN_Y - 42), (PIN_X + 22, PIN_Y - 32), (PIN_X, PIN_Y - 22)])
        # Best distance marker
        if self._best_dist is not None:
            r_px = int(self._best_dist * PX_PER_YARD)
            pygame.draw.circle(surface, C_GOLD, (PIN_X, PIN_Y), max(1, r_px), 2)
        # Tee box
        pygame.draw.rect(surface, (255, 255, 200),
                         pygame.Rect(TEE_X - 12, TEE_Y - 4, 24, 6), border_radius=2)
        fnt = self.font_small
        ls  = fnt.render("120 yards", True, (200, 230, 200))
        surface.blit(ls, (PIN_X + 14, PIN_Y - 8))

    def _get_club(self):
        return self._make_effective_club(_CLUBS[self._club_idx])

    def _get_terrain(self):
        return Terrain.FAIRWAY

    def _on_shot_resolved(self, holed: bool):
        bx, by  = self.ball.x, self.ball.y
        d_px    = math.sqrt((bx - PIN_X) ** 2 + (by - PIN_Y) ** 2)
        d_yards = 0.0 if holed else d_px / PX_PER_YARD
        shots   = TOTAL_ATTEMPTS - self._attempts_remaining + 1

        self._last_dist = d_yards
        if self._best_dist is None or d_yards < self._best_dist:
            self._best_dist = d_yards

        if holed:
            self._result_msg = f"Holed out!  (Shot {shots}/{TOTAL_ATTEMPTS})"
        else:
            self._result_msg = f"{d_yards:.1f}y from pin  (Shot {shots}/{TOTAL_ATTEMPTS})"

    def _on_complete(self):
        best     = self._best_dist if self._best_dist is not None else 9999.0
        opp_best = self._opp_distances[0] if self._opp_distances else 9999.0
        won      = best <= opp_best

        session = self.game.current_tournament
        if hasattr(session, "record"):
            session.record("cttp", {"dist_yards": best, "won": won})

        if won:
            self._complete_msg = f"You won! {best:.1f}y beats {opp_best:.1f}y"
        else:
            self._complete_msg = f"Runner-up — your best: {best:.1f}y  top: {opp_best:.1f}y"

    def _on_continue(self):
        from src.states.putting_challenge_state import PuttingChallengeState
        self.game.change_state(PuttingChallengeState(self.game))

    # ── Club toggle ───────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, (_, r) in enumerate(self._club_btns):
                if r.collidepoint(event.pos) and not self._complete and not self._shot_done:
                    self._club_idx = i
                    return
        super().handle_event(event)

    # ── Panel ─────────────────────────────────────────────────────────────────

    def _draw_panel_extra(self, surface, px, py):
        fnt = self.font_small

        if self._complete and self._complete_msg:
            for line in _wrap(self._complete_msg, fnt, 280):
                s = fnt.render(line, True, C_GOLD)
                surface.blit(s, (px, py)); py += 16
            py += 8
            s = fnt.render("Next: Putting Challenge  >", True, C_GREEN)
            surface.blit(s, (px, py))
            return

        # Club selector
        cs = fnt.render("Club:", True, C_GOLD)
        surface.blit(cs, (px, py)); py += 16
        for i, (name, r) in enumerate(self._club_btns):
            active = (i == self._club_idx)
            bg     = C_BTN_H if active else C_BTN
            pygame.draw.rect(surface, bg, r, border_radius=4)
            pygame.draw.rect(surface, C_BORDER, r, 1, border_radius=4)
            ls = fnt.render(name + ("  ✓" if active else ""), True, C_WHITE)
            surface.blit(ls, ls.get_rect(center=r.center))
        py = self._club_btns[-1][1].bottom + 10

        # Best this session
        best_s = "--" if self._best_dist is None else f"{self._best_dist:.1f}y"
        bs = fnt.render(f"Best: {best_s}", True, C_GOLD)
        surface.blit(bs, (px, py)); py += 18

        if self._last_dist is not None:
            ls2 = fnt.render(f"Last: {self._last_dist:.1f}y", True, C_WHITE)
            surface.blit(ls2, (px, py)); py += 18

        py += 6
        hdr = fnt.render("Opponents:", True, C_GRAY)
        surface.blit(hdr, (px, py)); py += 15
        best_now = self._best_dist if self._best_dist is not None else 9999.0
        for i, d in enumerate(self._opp_distances):
            beat = best_now <= d
            col  = C_GREEN if beat else C_WHITE
            s    = fnt.render(f"  {i+1}. {d:.1f}y", True, col)
            surface.blit(s, (px, py)); py += 14


def _wrap(text: str, font, max_w: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines
