"""
DrivingRangeState — 8 shots at 5 distance targets (150-250y).
Rewards Power (and optionally Accuracy) stat permanently (once per season).
"""

import math

import pygame

from src.states.practice_base import (
    PracticeBase, TargetZone,
    VIEWPORT_W, VIEWPORT_H, TILE_SZ, PX_PER_YARD,
    C_GOLD, C_GREEN, C_GRAY, C_WHITE,
)
from src.golf.terrain import Terrain

MINIGAME_ID   = "driving_range"
TOTAL_SHOTS   = 8

# (distance_yards, lateral_offset_px) for each of the 5 range bays
_TARGET_SPECS = [
    (150, -15),
    (175, +18),
    (200,  -8),
    (225, +20),
    (250, -12),
]

# Ring radii in pixels
_BULL_R  = 10   # bullseye  → 5 pts
_INNER_R = 24   # inner ring → 3 pts
_OUTER_R = 48   # outer ring → 1 pt

TEE_X = VIEWPORT_W // 2
TEE_Y = VIEWPORT_H - 80


class DrivingRangeState(PracticeBase):
    MINIGAME_ID = MINIGAME_ID
    TITLE       = "Driving Range"

    def _build_layout(self):
        self._tee_x = TEE_X
        self._tee_y = TEE_Y
        self._attempts_remaining = TOTAL_SHOTS
        self._targets: list[TargetZone] = []
        for dist_y, lat_x in _TARGET_SPECS:
            dy = dist_y * PX_PER_YARD
            cx = TEE_X + lat_x
            cy = TEE_Y - dy
            self._targets.append(
                TargetZone(cx, cy, _OUTER_R, _BULL_R, 1, 5,
                           label=f"{dist_y}y"))
        self._shot_results: list[tuple[int, int]] = []  # (pts, dist)

    def _draw_course(self, surface):
        # Sky
        sky_r = pygame.Rect(0, 0, VIEWPORT_W, 120)
        pygame.draw.rect(surface, (80, 140, 200), sky_r)
        # Grass
        pygame.draw.rect(surface, (40, 130, 40),
                         pygame.Rect(0, 120, VIEWPORT_W, VIEWPORT_H - 120))
        # Target circles
        for t in self._targets:
            t.draw(surface)
        # Tee marker
        pygame.draw.rect(surface, (255, 255, 200),
                         pygame.Rect(TEE_X - 8, TEE_Y - 4, 16, 6), border_radius=2)
        # Distance lines
        fnt = self.font_small
        for t in self._targets:
            pygame.draw.line(surface, (100, 200, 100),
                             (0, int(t.cy)), (VIEWPORT_W, int(t.cy)), 1)

    def _get_club(self):
        return self._make_effective_club("Driver")

    def _get_terrain(self):
        return Terrain.FAIRWAY

    def _on_shot_resolved(self, holed: bool):
        bx, by = self.ball.x, self.ball.y
        best_pts = 0
        best_dist = 9999.0
        for t in self._targets:
            pts = t.score_for(bx, by)
            if pts > best_pts:
                best_pts = pts
                best_dist = math.sqrt((bx - t.cx)**2 + (by - t.cy)**2)
        self._score += best_pts
        self._shot_results.append((best_pts, int(best_dist)))
        shots_done = TOTAL_SHOTS - self._attempts_remaining + 1
        if best_pts == 5:
            self._result_msg = f"Bullseye! +5 pts  (Shot {shots_done}/{TOTAL_SHOTS})"
        elif best_pts > 0:
            self._result_msg = f"+{best_pts} pts  (Shot {shots_done}/{TOTAL_SHOTS})"
        else:
            self._result_msg = f"Miss  (Shot {shots_done}/{TOTAL_SHOTS})"

    def _on_complete(self):
        p = self.game.player
        if p is None:
            return
        msg_parts = []
        if self._score >= 35:
            if self._can_give_perm_stat(MINIGAME_ID + "_power"):
                p.stats["power"]    = min(80, p.stats["power"]    + 1)
                p.stats["accuracy"] = min(80, p.stats["accuracy"] + 1)
                self._mark_perm_stat_given(MINIGAME_ID + "_power")
                msg_parts.append("Power+1, Accuracy+1!")
        elif self._score >= 30:
            if self._can_give_perm_stat(MINIGAME_ID + "_power"):
                p.stats["power"] = min(80, p.stats["power"] + 2)
                self._mark_perm_stat_given(MINIGAME_ID + "_power")
                msg_parts.append("Power+2!")
        elif self._score >= 20:
            if self._can_give_perm_stat(MINIGAME_ID + "_power"):
                p.stats["power"] = min(80, p.stats["power"] + 1)
                self._mark_perm_stat_given(MINIGAME_ID + "_power")
                msg_parts.append("Power+1!")
        self._complete_msg = (
            f"Range done! Score: {self._score}  " +
            ("  ".join(msg_parts) if msg_parts else "(stat already improved this season)"))
        p.practice_cooldowns[MINIGAME_ID] = 1

    def _draw_panel_extra(self, surface, px, py):
        if self._complete and hasattr(self, "_complete_msg"):
            fnt = self.font_small
            for word_chunk in _wrap(self._complete_msg, fnt, 280):
                s = fnt.render(word_chunk, True, C_GOLD)
                surface.blit(s, (px, py)); py += 16
            return
        # Shot history
        fnt = self.font_small
        s = fnt.render("Last shots:", True, C_GRAY)
        surface.blit(s, (px, py)); py += 16
        for pts, dist in self._shot_results[-6:]:
            col = C_GOLD if pts >= 3 else C_WHITE if pts > 0 else C_GRAY
            s = fnt.render(f"  {pts}pts  ({dist}px off)", True, col)
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
