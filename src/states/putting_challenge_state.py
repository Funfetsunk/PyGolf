"""
PuttingChallengeState — Putting Challenge Competition (Phase 8, Task 8.3).

3 putts at increasing distances: 12y, 25y, 40y (one attempt each).
Score = sum of final distances from pin (0 if holed). Lowest total wins.
5 AI opponents have pre-simulated scores based on tour level.
Win if player's total score <= the best (lowest) opponent score.

Finalises the SkillsSession and returns to CareerHubState on completion.
"""

import math
import random

import pygame

from src.states.practice_base import (
    PracticeBase,
    VIEWPORT_W, VIEWPORT_H, PX_PER_YARD,
    C_GOLD, C_GREEN, C_GRAY, C_WHITE,
)
from src.golf.terrain import Terrain
from src.golf.shot import ShotState

NUM_OPPONENTS = 5

PIN_X = VIEWPORT_W // 2
PIN_Y = 310

# Fixed putt distances (yards) and starting angles (degrees from below)
_PUTTS = [
    (12, 270),   # short:  below pin
    (25, 225),   # medium: lower-left
    (40, 315),   # long:   lower-right
]

# Opponent total distance-from-pin scores by tour level — lower = better
_OPP_RANGES = {
    1: (15.0, 55.0),
    2: (10.0, 40.0),
    3: (7.0,  28.0),
    4: (4.0,  18.0),
    5: (1.5,  10.0),
    6: (0.0,   5.0),
}

_TWO_YARDS_PX = 2.0 * PX_PER_YARD


def _sim_opponents(tour_level: int, seed: int) -> list[float]:
    rng = random.Random(seed)
    lo, hi = _OPP_RANGES.get(tour_level, (15.0, 55.0))
    return sorted([round(rng.uniform(lo, hi), 1) for _ in range(NUM_OPPONENTS)])


def _tee_pos(dist_yards: float, angle_deg: float) -> tuple[float, float]:
    rad = math.radians(angle_deg)
    d   = dist_yards * PX_PER_YARD
    return (PIN_X + math.cos(rad) * d, PIN_Y + math.sin(rad) * d)


class PuttingChallengeState(PracticeBase):
    MINIGAME_ID = "putting_challenge"
    TITLE       = "Putting Challenge"

    def __init__(self, game):
        super().__init__(game)
        session    = game.current_tournament
        tour_level = getattr(session, "tour_level", 1)
        seed       = (id(session) + 2) & 0xFFFF
        self._opp_scores = _sim_opponents(tour_level, seed)

    def _build_layout(self):
        self._attempts_remaining = len(_PUTTS)
        self._attempt_num        = 0
        self._putt_scores:  list[float] = []
        self._total_score:  float       = 0.0
        self._complete_msg: str         = ""
        self._opp_scores:   list[float] = []
        self._set_tee_for_attempt()

    def _set_tee_for_attempt(self):
        if self._attempt_num < len(_PUTTS):
            dist, angle = _PUTTS[self._attempt_num]
            tx, ty = _tee_pos(dist, angle)
        else:
            tx, ty = float(PIN_X + 40), float(PIN_Y + 40)
        self._tee_x = tx
        self._tee_y = ty

    def _pin_world_pos(self):
        return (float(PIN_X), float(PIN_Y))

    def _draw_course(self, surface):
        surface.fill((40, 160, 60))
        pygame.draw.circle(surface, (58, 192, 72), (PIN_X, PIN_Y), 240)
        pygame.draw.circle(surface, (48, 148, 56), (PIN_X, PIN_Y), 240, 2)
        # Distance rings
        for dist_y, _ in _PUTTS:
            r_px = int(dist_y * PX_PER_YARD)
            pygame.draw.circle(surface, (80, 160, 80), (PIN_X, PIN_Y), r_px, 1)
        # Pin
        pygame.draw.circle(surface, (15, 15, 15), (PIN_X, PIN_Y), 6)
        pygame.draw.line(surface, (200, 200, 200),
                         (PIN_X, PIN_Y - 6), (PIN_X, PIN_Y - 38), 2)
        pygame.draw.polygon(surface, (220, 55, 55), [
            (PIN_X, PIN_Y - 38), (PIN_X + 20, PIN_Y - 29), (PIN_X, PIN_Y - 20)])
        # Tee position indicators (all future positions)
        fnt = self.font_small
        for i, (dist_y, angle) in enumerate(_PUTTS):
            tx, ty = _tee_pos(dist_y, angle)
            col = C_GOLD if i == self._attempt_num else (100, 130, 100)
            pygame.draw.circle(surface, col, (int(tx), int(ty)), 4, 1)
            lbl = fnt.render(f"{dist_y}y", True, col)
            surface.blit(lbl, (int(tx) + 6, int(ty) - 7))

    def _get_club(self):
        return self._make_effective_club("Putter")

    def _get_terrain(self):
        return Terrain.GREEN

    def _on_shot_resolved(self, holed: bool):
        if holed:
            dist_yards = 0.0
        else:
            d_px       = math.sqrt((self.ball.x - PIN_X) ** 2 + (self.ball.y - PIN_Y) ** 2)
            dist_yards = d_px / PX_PER_YARD

        self._total_score += dist_yards
        self._putt_scores.append(dist_yards)
        putt_n = self._attempt_num + 1

        if holed:
            self._result_msg = f"Holed! +0  (Putt {putt_n}/3)"
        else:
            self._result_msg = f"{dist_yards:.1f}y away  (Putt {putt_n}/3)"

    def _next_attempt(self):
        self._shot_done   = False
        self._attempt_num += 1
        if self._attempts_remaining <= 0:
            self._complete = True
            self._on_complete()
        else:
            self._set_tee_for_attempt()
            self.ball.place(self._tee_x, self._tee_y)
            self.shot_ctrl.state = ShotState.IDLE

    def _on_complete(self):
        total    = self._total_score
        opp_best = self._opp_scores[0] if self._opp_scores else 9999.0
        won      = total <= opp_best

        session = self.game.current_tournament
        if hasattr(session, "record"):
            session.record("putting", {"score": total, "opp_best": opp_best, "won": won})

        # Finalise the whole skills session and apply all rewards
        summary = {}
        if hasattr(session, "finalise"):
            summary = session.finalise(self.game.player)

        wins = summary.get("wins", 0)
        prize = summary.get("prize", 0)
        if won:
            self._complete_msg = (
                f"You won! {total:.1f}y beats {opp_best:.1f}y  |  "
                f"Session: {wins}/3 wins, ${prize:,} earned"
            )
        else:
            self._complete_msg = (
                f"Runner-up — {total:.1f}y vs {opp_best:.1f}y  |  "
                f"Session: {wins}/3 wins, ${prize:,} earned"
            )

    def _on_continue(self):
        from src.states.career_hub import CareerHubState
        self.game.current_tournament = None
        self.game.change_state(CareerHubState(self.game))

    # ── Panel ─────────────────────────────────────────────────────────────────

    def _draw_panel_extra(self, surface, px, py):
        fnt = self.font_small

        if self._complete and self._complete_msg:
            for line in _wrap(self._complete_msg, fnt, 280):
                s = fnt.render(line, True, C_GOLD)
                surface.blit(s, (px, py)); py += 16
            return

        # Current total score
        ts = fnt.render(f"Total dist: {self._total_score:.1f}y", True, C_GOLD)
        surface.blit(ts, (px, py)); py += 18

        py += 4
        s = fnt.render("Scoring: 0 if holed", True, C_GRAY)
        surface.blit(s, (px, py)); py += 14
        s = fnt.render("lowest total wins", True, C_GRAY)
        surface.blit(s, (px, py)); py += 18

        # Per-putt results
        labels = ["12y", "25y", "40y"]
        for i, score in enumerate(self._putt_scores):
            col = C_GREEN if score == 0.0 else C_WHITE
            lbl = "Holed!" if score == 0.0 else f"{score:.1f}y"
            s = fnt.render(f"  Putt {i+1} ({labels[i]}): {lbl}", True, col)
            surface.blit(s, (px, py)); py += 14

        py += 6
        hdr = fnt.render("Opponents:", True, C_GRAY)
        surface.blit(hdr, (px, py)); py += 15
        for i, d in enumerate(self._opp_scores):
            beat = self._total_score <= d
            col  = C_GREEN if beat else C_WHITE
            s    = fnt.render(f"  {i+1}. {d:.1f}y total", True, col)
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
