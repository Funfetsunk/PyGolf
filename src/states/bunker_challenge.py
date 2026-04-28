"""
BunkerChallengeState — 3 bunker escape attempts.
Ball starts in sand; must land within target radius of 24px.
Reward: ≥2 successes → Short Game+1 (once per season).
"""

import math

import pygame

from src.states.practice_base import (
    PracticeBase,
    VIEWPORT_W, VIEWPORT_H, TILE_SZ, PX_PER_YARD,
    C_GOLD, C_GREEN, C_GRAY, C_WHITE,
)
from src.golf.terrain import Terrain

MINIGAME_ID    = "bunker_challenge"
TOTAL_ATTEMPTS = 3

TEE_X      = VIEWPORT_W // 2
TEE_Y      = 450   # in the bunker

TARGET_X   = VIEWPORT_W // 2
TARGET_Y   = 355   # green target
TARGET_R   = 24    # px — must land within this


class BunkerChallengeState(PracticeBase):
    MINIGAME_ID = MINIGAME_ID
    TITLE       = "Bunker Escape"

    def _build_layout(self):
        self._tee_x = float(TEE_X)
        self._tee_y = float(TEE_Y)
        self._attempts_remaining = TOTAL_ATTEMPTS
        self._passes = 0

    def _draw_course(self, surface):
        # Sky
        pygame.draw.rect(surface, (80, 140, 200),
                         pygame.Rect(0, 0, VIEWPORT_W, 220))
        # Green section (top)
        pygame.draw.rect(surface, (50, 170, 60),
                         pygame.Rect(0, 220, VIEWPORT_W, 180))
        # Bunker (sandy area, bottom)
        pygame.draw.rect(surface, (210, 190, 120),
                         pygame.Rect(0, 380, VIEWPORT_W, VIEWPORT_H - 380))
        # Bunker lip
        pygame.draw.rect(surface, (160, 140, 80),
                         pygame.Rect(0, 378, VIEWPORT_W, 6))
        # Target circle on the green
        pygame.draw.circle(surface, (255, 60, 60),
                           (TARGET_X, TARGET_Y), TARGET_R, 3)
        pygame.draw.circle(surface, (255, 200, 0),
                           (TARGET_X, TARGET_Y), 6)
        # Tee marker in bunker
        pygame.draw.circle(surface, (240, 220, 160),
                           (TEE_X, TEE_Y), 6, 1)
        fnt = self.font_small
        ts = fnt.render("TARGET", True, (255, 200, 50))
        surface.blit(ts, (TARGET_X - ts.get_width() // 2, TARGET_Y - TARGET_R - 16))

    def _get_club(self):
        return self._make_effective_club("Sand Wedge")

    def _get_terrain(self):
        return Terrain.BUNKER

    def _on_shot_resolved(self, holed: bool):
        bx, by = self.ball.x, self.ball.y
        d = math.sqrt((bx - TARGET_X)**2 + (by - TARGET_Y)**2)
        success = (d <= TARGET_R)
        if success:
            self._passes += 1
            self._score += 1
        shot_n = TOTAL_ATTEMPTS - self._attempts_remaining + 1
        self._result_msg = (
            f"{'Hit target!' if success else 'Missed target'}  "
            f"({shot_n}/{TOTAL_ATTEMPTS})")

    def _on_complete(self):
        p = self.game.player
        if p is None:
            return
        msg_parts = []
        if self._passes >= 2 and self._can_give_perm_stat(MINIGAME_ID):
            p.stats["short_game"] = min(80, p.stats["short_game"] + 1)
            self._mark_perm_stat_given(MINIGAME_ID)
            msg_parts.append("Short Game+1!")
        self._complete_msg = (
            f"Done! {self._passes}/{TOTAL_ATTEMPTS} escaped  " +
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
        s = fnt.render(f"Successes: {self._passes}/{TOTAL_ATTEMPTS}", True, C_WHITE)
        surface.blit(s, (px, py)); py += 16
        s2 = fnt.render("Need 2+ for Short Game+1", True, C_GRAY)
        surface.blit(s2, (px, py))


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
