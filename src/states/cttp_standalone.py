"""
CttpStandaloneState — Closest to the Pin, 1 shot at a 120-yard pin.
Tracks personal best distance; earn $100 for a new PB.
Club toggle: PW (110y) or 9-Iron (135y).
"""

import math

import pygame

from src.states.practice_base import (
    PracticeBase,
    VIEWPORT_W, VIEWPORT_H, TILE_SZ, PX_PER_YARD,
    C_GOLD, C_GREEN, C_GRAY, C_WHITE, C_BTN, C_BTN_H, C_BORDER,
)
from src.golf.terrain import Terrain

MINIGAME_ID = "cttp_standalone"

TEE_X = VIEWPORT_W // 2
TEE_Y = VIEWPORT_H - 80

# 120 yards away
PIN_X = VIEWPORT_W // 2
PIN_Y = int(TEE_Y - 120 * PX_PER_YARD)   # 580 - 192 = 388

_CLUBS = ["Pitching Wedge", "9-Iron"]


class CttpStandaloneState(PracticeBase):
    MINIGAME_ID = MINIGAME_ID
    TITLE       = "Closest to Pin"

    def _build_layout(self):
        self._tee_x = float(TEE_X)
        self._tee_y = float(TEE_Y)
        self._attempts_remaining = 1
        self._club_idx = 0   # 0=PW, 1=9-Iron
        self._dist_yards: float | None = None
        # Club selection buttons (in panel area — we position them in draw)
        self._club_btns: list[tuple[str, pygame.Rect]] = []
        bx = 970   # PANEL_X + 10
        for i, name in enumerate(_CLUBS):
            self._club_btns.append((name, pygame.Rect(bx, 120 + i * 34, 280, 26)))

    def _pin_world_pos(self):
        return (float(PIN_X), float(PIN_Y))

    def _draw_course(self, surface):
        # Sky
        pygame.draw.rect(surface, (80, 140, 200),
                         pygame.Rect(0, 0, VIEWPORT_W, PIN_Y - 30))
        # Fairway
        pygame.draw.rect(surface, (60, 170, 60),
                         pygame.Rect(0, PIN_Y - 30, VIEWPORT_W, VIEWPORT_H - (PIN_Y - 30)))
        # Pin hole
        pygame.draw.circle(surface, (20, 20, 20), (PIN_X, PIN_Y), 6)
        # Flag
        pygame.draw.line(surface, (220, 220, 220),
                         (PIN_X, PIN_Y - 6), (PIN_X, PIN_Y - 40), 2)
        pygame.draw.polygon(surface, (220, 50, 50), [
            (PIN_X, PIN_Y - 40), (PIN_X + 20, PIN_Y - 31), (PIN_X, PIN_Y - 22)])
        # Distance rings
        for r_yds in (5, 10, 20):
            r_px = int(r_yds * PX_PER_YARD)
            pygame.draw.circle(surface, (100, 220, 100), (PIN_X, PIN_Y), r_px, 1)
        # Tee box
        pygame.draw.rect(surface, (255, 255, 200),
                         pygame.Rect(TEE_X - 12, TEE_Y - 4, 24, 6), border_radius=2)
        # 120y label
        fnt = self.font_small
        ls = fnt.render("120 yards", True, (200, 230, 200))
        surface.blit(ls, (PIN_X + 14, PIN_Y - 8))

    def _get_club(self):
        return self._make_effective_club(_CLUBS[self._club_idx])

    def _get_terrain(self):
        return Terrain.FAIRWAY

    def _on_shot_resolved(self, holed: bool):
        bx, by = self.ball.x, self.ball.y
        d_px = math.sqrt((bx - PIN_X)**2 + (by - PIN_Y)**2)
        d_y  = d_px / PX_PER_YARD
        self._dist_yards = d_y

        p = self.game.player
        if p is None:
            self._result_msg = f"{'Holed!' if holed else f'{d_y:.1f} yards'}"
            return

        if holed:
            self._result_msg = "Holed out!"
            d_y = 0.0
        else:
            self._result_msg = f"{d_y:.1f} yards from pin"

        prev_best = getattr(p, "cttp_best_yards", None)
        is_pb = (prev_best is None or d_y < prev_best)
        if is_pb:
            p.cttp_best_yards = d_y
            p.earn_money(100)
            self._result_msg += "  ★ Personal Best! +$100"

    def _on_complete(self):
        p = self.game.player
        if p is not None:
            p.practice_cooldowns[MINIGAME_ID] = 1

    # ── Override handle_event to capture club-toggle clicks ──────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, (name, r) in enumerate(self._club_btns):
                if r.collidepoint(event.pos) and not self._complete and not self._shot_done:
                    self._club_idx = i
                    return
        super().handle_event(event)

    # ── Panel content ─────────────────────────────────────────────────────────

    def _draw_panel_extra(self, surface, px, py):
        fnt = self.font_small

        # Club selector
        cs = fnt.render("Club:", True, C_GRAY)
        surface.blit(cs, (px, py)); py += 16
        for i, (name, r) in enumerate(self._club_btns):
            active = (i == self._club_idx)
            bg = C_BTN_H if active else C_BTN
            pygame.draw.rect(surface, bg, r, border_radius=4)
            pygame.draw.rect(surface, C_BORDER, r, 1, border_radius=4)
            ls = fnt.render(name + ("  ✓" if active else ""), True, C_WHITE)
            surface.blit(ls, ls.get_rect(center=r.center))
        py = self._club_btns[-1][1].bottom + 12

        # Personal best
        p = self.game.player
        best = getattr(p, "cttp_best_yards", None) if p else None
        pb_str = f"{best:.1f}y" if best is not None else "—"
        ps = fnt.render(f"Personal Best: {pb_str}", True, C_GOLD)
        surface.blit(ps, (px, py)); py += 18

        if self._dist_yards is not None:
            ds = fnt.render(f"This shot: {self._dist_yards:.1f}y", True, C_WHITE)
            surface.blit(ds, (px, py))
