"""
PuttingGreenState — 10 putts at a single pin.
Pre-generated positions: 3 short (8y), 4 medium (18-22y), 3 long (32-40y).
Holed = 3 pts; within 2 yards = 1 pt; else = 0 pts.

Rewards:
  ≥20 pts → temp_event_buffs["putting"] = 3  ("Hot Putter" — lasts until round end)
  ≥25 pts → Putting+1 (once per season)
"""

import math
import random

import pygame

from src.states.practice_base import (
    PracticeBase,
    VIEWPORT_W, VIEWPORT_H, TILE_SZ, PX_PER_YARD,
    C_GOLD, C_GREEN, C_GRAY, C_WHITE,
)
from src.golf.terrain import Terrain

MINIGAME_ID = "putting_green"
TOTAL_PUTTS = 10

# Pin world pos — middle of the green
PIN_X = VIEWPORT_W // 2
PIN_Y = 300

# 2 yards in pixels
_TWO_YARDS_PX = 2.0 * PX_PER_YARD


def _gen_positions(seed):
    rng = random.Random(seed)
    positions = []
    # 3 short (8y ± 1y)
    for i in range(3):
        angle = rng.uniform(0, 2 * math.pi)
        dist  = rng.uniform(7, 9) * PX_PER_YARD
        positions.append((PIN_X + math.cos(angle) * dist,
                          PIN_Y + math.sin(angle) * dist))
    # 4 medium (18-22y)
    for i in range(4):
        angle = rng.uniform(0, 2 * math.pi)
        dist  = rng.uniform(18, 22) * PX_PER_YARD
        positions.append((PIN_X + math.cos(angle) * dist,
                          PIN_Y + math.sin(angle) * dist))
    # 3 long (32-40y)
    for i in range(3):
        angle = rng.uniform(0, 2 * math.pi)
        dist  = rng.uniform(32, 40) * PX_PER_YARD
        positions.append((PIN_X + math.cos(angle) * dist,
                          PIN_Y + math.sin(angle) * dist))
    return positions


class PuttingGreenState(PracticeBase):
    MINIGAME_ID = MINIGAME_ID
    TITLE       = "Putting Green"

    def _build_layout(self):
        self._attempts_remaining = TOTAL_PUTTS
        self._attempt_num = 0
        seed = id(self.game.player) & 0xFFFF if self.game.player else 42
        self._positions = _gen_positions(seed)
        self._set_tee_for_attempt()
        self._putt_results: list[int] = []

    def _set_tee_for_attempt(self):
        if self._attempt_num < len(self._positions):
            self._tee_x, self._tee_y = self._positions[self._attempt_num]
        else:
            self._tee_x, self._tee_y = float(PIN_X + 30), float(PIN_Y + 30)

    def _pin_world_pos(self):
        return (float(PIN_X), float(PIN_Y))

    def _draw_course(self, surface):
        # Entire viewport is green
        surface.fill((40, 160, 60))
        # Lighter circle for the green
        pygame.draw.circle(surface, (60, 190, 70),
                           (PIN_X, PIN_Y), 220)
        # Pin hole
        pygame.draw.circle(surface, (20, 20, 20), (PIN_X, PIN_Y), 6)
        # Flag
        pygame.draw.line(surface, (200, 200, 200),
                         (PIN_X, PIN_Y - 6), (PIN_X, PIN_Y - 36), 2)
        pygame.draw.polygon(surface, (220, 60, 60), [
            (PIN_X, PIN_Y - 36), (PIN_X + 18, PIN_Y - 28), (PIN_X, PIN_Y - 20)])
        # Fringe marker ring
        pygame.draw.circle(surface, (50, 140, 50), (PIN_X, PIN_Y), 220, 2)
        # Ball position indicator
        tx, ty = int(self._tee_x), int(self._tee_y)
        pygame.draw.circle(surface, (200, 200, 200), (tx, ty), 4, 1)

    def _get_club(self):
        return self._make_effective_club("Putter")

    def _get_terrain(self):
        return Terrain.GREEN

    def _on_shot_resolved(self, holed: bool):
        if holed:
            pts = 3
        else:
            d = math.sqrt((self.ball.x - PIN_X)**2 + (self.ball.y - PIN_Y)**2)
            pts = 1 if d <= _TWO_YARDS_PX else 0
        self._score += pts
        self._putt_results.append(pts)
        shot_n = TOTAL_PUTTS - self._attempts_remaining + 1
        if holed:
            self._result_msg = f"Holed! +3 pts  (Putt {shot_n}/{TOTAL_PUTTS})"
        elif pts == 1:
            self._result_msg = f"Close! +1 pt  (Putt {shot_n}/{TOTAL_PUTTS})"
        else:
            self._result_msg = f"Miss  (Putt {shot_n}/{TOTAL_PUTTS})"

    def _next_attempt(self):
        self._shot_done = False
        self._attempt_num += 1
        if self._attempts_remaining <= 0:
            self._complete = True
            self._on_complete()
        else:
            self._set_tee_for_attempt()
            self.ball.place(self._tee_x, self._tee_y)
            from src.golf.shot import ShotState
            self.shot_ctrl.state = ShotState.IDLE

    def _on_complete(self):
        p = self.game.player
        if p is None:
            return
        msg_parts = []
        if self._score >= 20:
            p.temp_event_buffs = getattr(p, "temp_event_buffs", {})
            p.temp_event_buffs["putting"] = 3
            msg_parts.append("Hot Putter! +3 Putting for next round")
        if self._score >= 25 and self._can_give_perm_stat(MINIGAME_ID):
            p.stats["putting"] = min(80, p.stats["putting"] + 1)
            self._mark_perm_stat_given(MINIGAME_ID)
            msg_parts.append("Putting+1!")
        self._complete_msg = (
            f"Green done! Score: {self._score}  " +
            ("  ".join(msg_parts) if msg_parts else ""))
        p.practice_cooldowns[MINIGAME_ID] = 1

    def _draw_panel_extra(self, surface, px, py):
        if self._complete and hasattr(self, "_complete_msg"):
            fnt = self.font_small
            for line in _wrap(self._complete_msg, fnt, 280):
                s = fnt.render(line, True, C_GOLD)
                surface.blit(s, (px, py)); py += 16
            return
        fnt = self.font_small
        s = fnt.render("Scoring: Hole=3  ≤2y=1", True, C_GRAY)
        surface.blit(s, (px, py)); py += 16
        for i, pts in enumerate(self._putt_results[-6:]):
            col = C_GOLD if pts == 3 else C_GREEN if pts == 1 else C_GRAY
            label = "●" if pts > 0 else "○"
            s = fnt.render(f"  Putt {i+1}: {label} {pts}pt", True, col)
            surface.blit(s, (px, py)); py += 14


def _wrap(text, font, max_w):
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
