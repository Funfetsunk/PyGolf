"""
LongDriveState — Long Drive Competition (Phase 8, Task 8.1).

3 attempts with Driver. Track longest carry that stays inside the fairway OOB lines.
5 AI opponents have pre-simulated distances based on tour level.
Win if player's best carry >= the top opponent distance.

Chains to CttpCompetitionState on completion.
"""

import math
import random

import pygame

from src.states.practice_base import (
    PracticeBase,
    VIEWPORT_W, VIEWPORT_H, PX_PER_YARD,
    C_GOLD, C_GREEN, C_GRAY, C_WHITE, C_RED,
)
from src.golf.terrain import Terrain

TOTAL_ATTEMPTS = 3
NUM_OPPONENTS  = 5

FAIR_CENTER = VIEWPORT_W // 2
FAIR_HALF_W = 96    # ±96px ≈ ±60 yards; OOB outside this
FAIR_LEFT   = FAIR_CENTER - FAIR_HALF_W
FAIR_RIGHT  = FAIR_CENTER + FAIR_HALF_W

TEE_X = FAIR_CENTER
TEE_Y = 645

# Opponent carry ranges (yards) by tour level
_OPP_RANGES = {
    1: (185, 235),
    2: (205, 252),
    3: (222, 268),
    4: (240, 280),
    5: (262, 302),
    6: (285, 325),
}

_MARKERS = [150, 200, 250, 300, 350]


def _sim_opponents(tour_level: int, seed: int) -> list[float]:
    rng = random.Random(seed)
    lo, hi = _OPP_RANGES.get(tour_level, (185, 265))
    return sorted([round(rng.uniform(lo, hi), 1) for _ in range(NUM_OPPONENTS)], reverse=True)


class LongDriveState(PracticeBase):
    MINIGAME_ID = "long_drive"
    TITLE       = "Long Drive"

    def __init__(self, game):
        super().__init__(game)
        session    = game.current_tournament
        tour_level = getattr(session, "tour_level", 1)
        seed       = id(session) & 0xFFFF
        self._opp_distances = _sim_opponents(tour_level, seed)

    def _build_layout(self):
        self._tee_x           = float(TEE_X)
        self._tee_y           = float(TEE_Y)
        self._attempts_remaining = TOTAL_ATTEMPTS
        self._best_carry      = 0.0
        self._last_carry: float | None = None
        self._oob             = False
        self._complete_msg    = ""
        self._opp_distances: list[float] = []

    def _draw_course(self, surface):
        # Sky
        pygame.draw.rect(surface, (80, 140, 200),
                         pygame.Rect(0, 0, VIEWPORT_W, TEE_Y - 360))
        # Rough
        pygame.draw.rect(surface, (30, 100, 30),
                         pygame.Rect(0, TEE_Y - 360, VIEWPORT_W, VIEWPORT_H))
        # Fairway
        pygame.draw.rect(surface, (60, 180, 60),
                         pygame.Rect(FAIR_LEFT, 0, FAIR_HALF_W * 2, VIEWPORT_H))
        # OOB dashed lines
        for x in (FAIR_LEFT, FAIR_RIGHT):
            for y in range(0, VIEWPORT_H, 24):
                pygame.draw.line(surface, (230, 220, 50), (x, y), (x, min(y + 12, VIEWPORT_H)), 2)
        # Distance markers
        fnt = self.font_small
        for yards in _MARKERS:
            py = int(TEE_Y - yards * PX_PER_YARD)
            if 0 <= py < VIEWPORT_H:
                pygame.draw.line(surface, (90, 180, 90),
                                 (FAIR_LEFT, py), (FAIR_RIGHT, py), 1)
                ls = fnt.render(f"{yards}y", True, (170, 230, 170))
                surface.blit(ls, (FAIR_RIGHT + 5, py - 7))
        # Tee box
        pygame.draw.rect(surface, (255, 255, 200),
                         pygame.Rect(TEE_X - 14, TEE_Y - 4, 28, 8), border_radius=2)
        # Best-carry indicator line
        if self._best_carry > 0:
            by = int(TEE_Y - self._best_carry * PX_PER_YARD)
            if 0 <= by < VIEWPORT_H:
                pygame.draw.line(surface, C_GOLD,
                                 (FAIR_LEFT, by), (FAIR_RIGHT, by), 2)

    def _get_club(self):
        return self._make_effective_club("Driver")

    def _get_terrain(self):
        return Terrain.FAIRWAY

    def _on_shot_resolved(self, holed: bool):
        bx, by      = self.ball.x, self.ball.y
        in_bounds   = FAIR_LEFT <= bx <= FAIR_RIGHT
        carry_px    = TEE_Y - by
        carry_yards = max(0.0, carry_px / PX_PER_YARD)
        shots_done  = TOTAL_ATTEMPTS - self._attempts_remaining + 1

        if in_bounds and carry_yards > 0:
            self._oob        = False
            self._last_carry = carry_yards
            if carry_yards > self._best_carry:
                self._best_carry = carry_yards
            self._result_msg = f"{carry_yards:.0f} yards  (Shot {shots_done}/{TOTAL_ATTEMPTS})"
        else:
            self._oob        = True
            self._last_carry = 0.0
            self._result_msg = f"Out of bounds!  (Shot {shots_done}/{TOTAL_ATTEMPTS})"

    def _on_complete(self):
        best     = self._best_carry
        opp_best = self._opp_distances[0] if self._opp_distances else 0.0
        won      = best >= opp_best

        session = self.game.current_tournament
        if hasattr(session, "record"):
            session.record("long_drive", {"dist_yards": best, "won": won})

        if won:
            self._complete_msg = f"You won! {best:.0f}y beats {opp_best:.0f}y"
        else:
            self._complete_msg = f"Runner-up — your best: {best:.0f}y  top: {opp_best:.0f}y"

    def _on_continue(self):
        from src.states.cttp_competition import CttpCompetitionState
        self.game.change_state(CttpCompetitionState(self.game))

    def _draw_panel_extra(self, surface, px, py):
        fnt = self.font_small

        if self._complete and self._complete_msg:
            for line in _wrap(self._complete_msg, fnt, 280):
                s = fnt.render(line, True, C_GOLD)
                surface.blit(s, (px, py)); py += 16
            py += 8
            s = fnt.render("Next: Closest to Pin  >", True, C_GREEN)
            surface.blit(s, (px, py))
            return

        bc = fnt.render(f"Best: {self._best_carry:.0f}y", True, C_GOLD)
        surface.blit(bc, (px, py)); py += 18

        if self._last_carry is not None:
            col = C_RED if self._oob else C_WHITE
            lbl = "OOB" if self._oob else f"{self._last_carry:.0f}y"
            ls  = fnt.render(f"Last: {lbl}", True, col)
            surface.blit(ls, (px, py)); py += 18

        py += 6
        hdr = fnt.render("Opponents:", True, C_GRAY)
        surface.blit(hdr, (px, py)); py += 15
        for i, d in enumerate(self._opp_distances):
            beat = self._best_carry >= d
            col  = C_GREEN if beat else C_WHITE
            s    = fnt.render(f"  {i+1}. {d:.0f}y", True, col)
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
