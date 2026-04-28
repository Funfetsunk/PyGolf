"""
PracticeBase — shared base class for all practice minigame states.

Each minigame is a self-contained screen with:
  • A 960-wide left viewport (world coords = screen coords, camera fixed at 0,0)
  • A 320-wide right panel showing score, instructions, and a Back button
  • ShotController click-drag input (same as GolfRoundState)
  • Ball physics via Ball (no wind, no roll)
  • Procedural course drawing (no CourseRenderer)

Subclasses override:
  _build_layout()        — place tee/pin/targets; called in __init__
  _draw_course(surface)  — paint the viewport background
  _on_shot_resolved(holed: bool)  — scoring logic after each ball comes to rest
  _on_complete()         — called when all attempts are exhausted
  _get_club()            — return the Club to use for this minigame
  _pin_world_pos()       — override to make the ball sinkable (return (cx, cy))

Non-virtual helpers available to subclasses:
  _make_effective_club(club_name) — player-stat-scaled club copy
  _can_give_perm_stat(mid)        — True if not given this season
  _mark_perm_stat_given(mid)      — record season number to prevent double-reward
  self._tee_x, self._tee_y        — set in _build_layout
  self._attempts_remaining        — decrement externally or via _handle_ball_resolved
  self._score                     — accumulate in _on_shot_resolved
  self._shot_done                 — set True when shot resolves; cleared by _next_attempt
"""

import math

import pygame

from src.golf.ball   import Ball, BallState
from src.golf.shot   import ShotController, ShotState
from src.golf.terrain import Terrain
from src.ui           import fonts
from src.constants    import SCREEN_W, SCREEN_H
from src.utils.math_utils import clamp

VIEWPORT_W  = 960
VIEWPORT_H  = 720
PANEL_X     = VIEWPORT_W
PANEL_W     = SCREEN_W - VIEWPORT_W   # 320
TILE_SZ     = 16
PX_PER_YARD = 1.6     # 1 tile = 10 yards = 16 px  →  1.6 px/yard

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG     = ( 10,  16,  10)
C_PANEL  = ( 18,  28,  18)
C_BORDER = ( 55,  90,  55)
C_WHITE  = (255, 255, 255)
C_GRAY   = (130, 138, 120)
C_GREEN  = ( 55, 185,  55)
C_GOLD   = (210, 170,  30)
C_BTN    = ( 28,  75,  28)
C_BTN_H  = ( 50, 120,  50)
C_BTN_DIS= ( 60,  52,  42)
C_RED    = (200,  50,  50)


class TargetZone:
    """Circular scoring zone drawn on the course."""
    def __init__(self, cx, cy, outer_r, inner_r,
                 outer_pts, inner_pts, label=""):
        self.cx       = cx
        self.cy       = cy
        self.outer_r  = outer_r
        self.inner_r  = inner_r
        self.outer_pts = outer_pts
        self.inner_pts = inner_pts
        self.label    = label

    def score_for(self, bx, by):
        d = math.sqrt((bx - self.cx) ** 2 + (by - self.cy) ** 2)
        if self.inner_r > 0 and d <= self.inner_r:
            return self.inner_pts
        if d <= self.outer_r:
            return self.outer_pts
        return 0

    def draw(self, surface):
        cx, cy = int(self.cx), int(self.cy)
        pygame.draw.circle(surface, (200, 200, 50),   (cx, cy), int(self.outer_r), 2)
        if self.inner_r > 0:
            pygame.draw.circle(surface, (255, 60, 60),  (cx, cy), int(self.inner_r), 2)
        if self.label:
            fnt = fonts.body(11)
            ls  = fnt.render(self.label, True, (220, 220, 100))
            surface.blit(ls, (cx - ls.get_width() // 2, cy - int(self.outer_r) - 14))


class PracticeBase:
    """Abstract base for practice minigame states."""

    MINIGAME_ID = "practice_base"
    TITLE       = "Practice"

    def __init__(self, game):
        self.game   = game
        self.player = game.player

        self.font_title = fonts.heading(26)
        self.font_hdr   = fonts.body(15, bold=True)
        self.font_med   = fonts.body(14)
        self.font_small = fonts.body(12)

        self._tee_x: float = VIEWPORT_W / 2
        self._tee_y: float = VIEWPORT_H * 0.8
        self._attempts_remaining: int = 1
        self._score:  int  = 0
        self._shot_done: bool = False
        self._complete: bool  = False
        self._result_msg: str = ""
        self._hov = None

        # Back button (in panel) and Continue button (shown when complete)
        self._btn_back     = pygame.Rect(PANEL_X + 10, SCREEN_H - 46, PANEL_W - 20, 34)
        self._btn_continue = pygame.Rect(PANEL_X + 10, SCREEN_H - 84, PANEL_W - 20, 34)

        self._build_layout()

        self.ball      = Ball(self._tee_x, self._tee_y)
        self.shot_ctrl = ShotController()

    # ── Virtual interface ─────────────────────────────────────────────────────

    def _build_layout(self):
        """Set tee pos, targets, attempt count, etc."""

    def _draw_course(self, surface):
        """Paint the 960-wide left viewport."""
        surface.fill((30, 100, 30), pygame.Rect(0, 0, VIEWPORT_W, VIEWPORT_H))

    def _on_shot_resolved(self, holed: bool):
        """Called when the ball comes to rest. Update self._score and self._result_msg."""

    def _on_complete(self):
        """Called when all attempts are used up. Award stats/money etc."""

    def _get_club(self):
        """Return the Club object to use for all shots."""
        return self._make_effective_club("Pitching Wedge")

    def _pin_world_pos(self):
        """Return (wx, wy) of the pin — ball sinks when it reaches this point.
        Default is off-screen (no sinking). Override for putting/cttp."""
        return (-2000.0, -2000.0)

    def _get_terrain(self) -> Terrain:
        """Terrain at the ball — affects distance/accuracy modifiers."""
        return Terrain.FAIRWAY

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_effective_club(self, club_name: str):
        from src.golf.club import Club, get_club_bag, STARTER_BAG
        player = self.game.player
        bag    = list(player.clubs) if player else list(STARTER_BAG)
        club   = next((c for c in bag if c.name == club_name), None)
        if club is None:
            club = next((c for c in STARTER_BAG if c.name == club_name), None)
        if club is None or player is None:
            return club

        tmp = dict(getattr(player, "temp_stat_modifiers", {}))
        for k, v in getattr(player, "temp_event_buffs", {}).items():
            tmp[k] = tmp.get(k, 0) + v

        def eff(key):
            return (player.stats.get(key, 50)
                    + player.staff_stat_bonus(key)
                    + tmp.get(key, 0))

        power_mult = 1.0 + (eff("power") - 50) / 200.0
        if club.name == "Putter":
            acc_bonus = (eff("putting") - 50) / 500.0
        elif club.name in ("Pitching Wedge", "Sand Wedge"):
            acc_bonus = (eff("short_game") - 50) / 500.0
        else:
            acc_bonus = (eff("accuracy") - 50) / 500.0

        new_dist = club.max_distance_yards * power_mult
        new_acc  = min(0.99, club.accuracy + acc_bonus)
        return Club(club.name, new_dist, new_acc, club.can_shape)

    def _can_give_perm_stat(self, mid: str) -> bool:
        p = self.game.player
        if p is None:
            return False
        return p.practice_stat_seasons.get(mid, -1) != p.season

    def _mark_perm_stat_given(self, mid: str) -> None:
        p = self.game.player
        if p is not None:
            p.practice_stat_seasons[mid] = p.season

    def _ball_screen_pos(self):
        return (int(self.ball.x), int(self.ball.y))

    # ── Internal shot resolution ───────────────────────────────────────────────

    def _handle_ball_resolved(self, holed: bool):
        self._on_shot_resolved(holed)
        self._attempts_remaining -= 1
        self._shot_done = True

    def _next_attempt(self):
        """After player acknowledges result, set up for the next shot or finish."""
        self._shot_done = False
        if self._attempts_remaining <= 0:
            self._complete = True
            self._on_complete()
        else:
            self.ball.place(self._tee_x, self._tee_y)
            self.shot_ctrl.state = ShotState.IDLE

    def _reset_ball(self):
        self.ball.place(self._tee_x, self._tee_y)
        self.shot_ctrl.state = ShotState.IDLE

    def _on_continue(self):
        """Called when the player clicks Continue after completion. Override to chain states."""
        self._go_back()

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            if self._complete and self._btn_continue.collidepoint(pos):
                self._hov = "continue"
            elif self._btn_back.collidepoint(pos):
                self._hov = "back"
            else:
                self._hov = None
            self.shot_ctrl.handle_mousemove(pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._complete and self._btn_continue.collidepoint(event.pos):
                self._on_continue()
                return
            if self._btn_back.collidepoint(event.pos):
                self._go_back()
                return

            if self._complete or self._shot_done:
                if self._shot_done:
                    self._next_attempt()
                return

            # Shot input
            if self.shot_ctrl.state == ShotState.IDLE:
                self.shot_ctrl.handle_mousedown(
                    event.pos, self._ball_screen_pos())

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.shot_ctrl.state == ShotState.AIMING:
                club    = self._get_club()
                terrain = self._get_terrain()
                result  = self.shot_ctrl.handle_mouseup(
                    event.pos,
                    (self.ball.x, self.ball.y),
                    club, terrain, TILE_SZ)
                if result is not None:
                    self.ball.hit(
                        result.target_x, result.target_y,
                        is_putt=(club.name == "Putter"),
                        aim_x=result.aim_x, aim_y=result.aim_y,
                        shape_x=result.shape_x, shape_y=result.shape_y,
                        roll_dist_px=0.0)

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        if self._complete or self._shot_done:
            return

        pin = self._pin_world_pos()
        self.ball.update(dt, pin)

        if self.shot_ctrl.state == ShotState.EXECUTING:
            if self.ball.state in (BallState.AT_REST, BallState.IN_HOLE):
                self.shot_ctrl.on_ball_landed()
                holed = (self.ball.state == BallState.IN_HOLE)
                self._handle_ball_resolved(holed)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        # Viewport
        vp = surface.subsurface(pygame.Rect(0, 0, VIEWPORT_W, VIEWPORT_H))
        self._draw_course(vp)
        self.ball.draw(vp, 0, 0)

        # Aim line
        aim = self.shot_ctrl.get_aim_line(self._ball_screen_pos())
        if aim:
            (sx, sy), (ex, ey), power = aim
            pygame.draw.line(vp, (255, 220, 0), (sx, sy), (ex, ey), 2)
            pw_s = self.font_small.render(f"{int(power*100)}%", True, (255, 220, 0))
            vp.blit(pw_s, (int(ex) + 4, int(ey) - 8))

        # Result overlay
        if self._shot_done and self._result_msg:
            txt = self.font_hdr.render(self._result_msg, True, C_GOLD)
            vp.blit(txt, (VIEWPORT_W // 2 - txt.get_width() // 2, VIEWPORT_H // 2 - 20))
            cont = self.font_small.render("Click to continue", True, C_GRAY)
            vp.blit(cont, (VIEWPORT_W // 2 - cont.get_width() // 2, VIEWPORT_H // 2 + 10))

        # Panel
        panel = pygame.Rect(PANEL_X, 0, PANEL_W, SCREEN_H)
        pygame.draw.rect(surface, C_PANEL, panel)
        pygame.draw.rect(surface, C_BORDER, panel, 1)
        self._draw_panel(surface)

    def _draw_panel(self, surface):
        px = PANEL_X + 10
        py = 14

        title = self.font_title.render(self.TITLE, True, C_WHITE)
        surface.blit(title, (PANEL_X + (PANEL_W - title.get_width()) // 2, py))
        py += title.get_height() + 8

        # Score
        score_s = self.font_hdr.render(f"Score: {self._score}", True, C_GOLD)
        surface.blit(score_s, (px, py)); py += 22

        # Attempts remaining
        att_s = self.font_med.render(
            f"Shots left: {self._attempts_remaining}", True, C_WHITE)
        surface.blit(att_s, (px, py)); py += 20

        # Completion message
        if self._complete:
            done_s = self.font_hdr.render("Complete!", True, C_GREEN)
            surface.blit(done_s, (px, py)); py += 24

        py += 10
        self._draw_panel_extra(surface, px, py)

        # Continue button (when complete) + Back button
        if self._complete:
            cbg = C_BTN_H if self._hov == "continue" else C_BTN
            pygame.draw.rect(surface, cbg, self._btn_continue, border_radius=4)
            pygame.draw.rect(surface, C_GREEN, self._btn_continue, 1, border_radius=4)
            cl = self.font_med.render("Continue  >", True, C_WHITE)
            surface.blit(cl, cl.get_rect(center=self._btn_continue.center))

        bg = C_BTN_H if self._hov == "back" else C_BTN
        pygame.draw.rect(surface, bg, self._btn_back, border_radius=4)
        pygame.draw.rect(surface, C_BORDER, self._btn_back, 1, border_radius=4)
        bl = self.font_med.render("< Back to Hub", True, C_WHITE)
        surface.blit(bl, bl.get_rect(center=self._btn_back.center))

    def _draw_panel_extra(self, surface, px, py):
        """Override to add minigame-specific panel content."""

    def _go_back(self):
        from src.states.career_hub import CareerHubState
        self.game.change_state(CareerHubState(self.game))
