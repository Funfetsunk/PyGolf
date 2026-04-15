"""
GolfRoundState — Phase 1 core: one playable golf hole from tee to cup.

Flow
────
1. Ball starts on the tee.
2. Player uses click-drag to aim and hit.
3. Each valid shot increments the stroke counter.
4. Landing in water adds a penalty stroke and drops the ball.
5. Reaching the pin ends the hole; a completion screen shows the score.
6. Player can press any key / click to restart and play again.

Layout
──────
  Left 960 px  : course viewport
  Right 320 px : HUD panel (handled by src/ui/hud.py)
"""

import math

import pygame

from src.golf.ball     import Ball, BallState
from src.golf.shot     import ShotController, ShotState
from src.golf.terrain  import Terrain, TERRAIN_PROPS
from src.golf.club     import STARTER_BAG
from src.course.hole   import make_hole_1
from src.course.renderer import CourseRenderer
from src.ui.hud        import HUD
from src.utils.math_utils import clamp

# ── Layout constants ──────────────────────────────────────────────────────────
VIEWPORT_W = 960
VIEWPORT_H = 720
SCREEN_W   = 1280
SCREEN_H   = 720

# ── Colours ───────────────────────────────────────────────────────────────────
C_WHITE      = (255, 255, 255)
C_BLACK      = (  0,   0,   0)
C_GREEN      = ( 60, 185,  60)
C_RED        = (220,  55,  55)
C_YELLOW     = (255, 220,   0)
C_DARK_BG    = (  0,   0,   0, 160)   # semi-transparent overlay


class GolfRoundState:
    """Phase 1: single hole golf round."""

    def __init__(self, game):
        self.game = game

        # ── Build hole and renderer ───────────────────────────────────────────
        self.hole     = make_hole_1()
        self.renderer = CourseRenderer(self.hole)
        self.tile_sz  = self.renderer.tile_size

        # ── Camera (scroll offset in world pixels) ────────────────────────────
        # For Phase 1 the hole is 960×720 px — it fits the viewport exactly,
        # so camera stays at (0, 0). The system is in place for larger holes.
        self.cam_x = 0.0
        self.cam_y = 0.0

        # ── Golf objects ──────────────────────────────────────────────────────
        tee_wx, tee_wy = self.renderer.get_tee_world_pos()
        self.ball    = Ball(tee_wx, tee_wy)
        self.clubs   = list(STARTER_BAG)           # copy so we can expand later
        self.club_idx = 0                           # driver selected by default
        self.strokes  = 0

        self.shot_ctrl = ShotController()

        # ── UI ────────────────────────────────────────────────────────────────
        self.hud = HUD(SCREEN_W, SCREEN_H)

        # Fonts
        self.font_big = pygame.font.SysFont("arial", 40, bold=True)
        self.font_med = pygame.font.SysFont("arial", 22)

        # ── State flags ───────────────────────────────────────────────────────
        self.hole_complete    = False
        self.complete_timer   = 0.0          # seconds since hole finished

        self.message          = ""
        self.message_timer    = 0.0

        # ── Last ball position before each shot (for water drop) ──────────────
        self._last_safe_x = tee_wx
        self._last_safe_y = tee_wy

        # Auto-select putter if starting on green (shouldn't happen on hole 1)
        self._auto_select_club()

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def current_club(self):
        return self.clubs[self.club_idx]

    def _ball_screen_pos(self):
        """Ball position in screen (viewport) coordinates."""
        return (int(self.ball.x - self.cam_x),
                int(self.ball.y - self.cam_y))

    def _pin_world_pos(self):
        return self.renderer.get_pin_world_pos()

    def _pin_screen_pos(self):
        px, py = self._pin_world_pos()
        return (int(px - self.cam_x), int(py - self.cam_y))

    def _ball_terrain(self):
        return self.hole.get_terrain_at_pixel(self.ball.x, self.ball.y, self.tile_sz)

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event):
        # Any input after hole complete restarts the hole
        if self.hole_complete:
            if (self.complete_timer > 1.2 and
                    event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN)):
                self._restart()
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._on_left_click(event.pos)
            elif event.button == 3:
                # Right-click cancels current aim
                self.shot_ctrl.cancel()

        elif event.type == pygame.MOUSEMOTION:
            self.shot_ctrl.handle_mousemove(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self._on_left_release(event.pos)

        elif event.type == pygame.MOUSEWHEEL:
            # Scroll through clubs (skip putter unless on green)
            direction = -1 if event.y > 0 else 1
            self._cycle_club(direction)

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_UP):
                self._cycle_club(-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                self._cycle_club(1)

    def _on_left_click(self, pos):
        """Handle a left mouse-button press."""
        # Clicks on the HUD panel go to the HUD handler
        if pos[0] >= VIEWPORT_W:
            self.club_idx = self.hud.handle_click(
                pos, self.shot_ctrl, self.clubs, self.club_idx)
            return

        # Course viewport click — start aiming if ball is at rest
        if self.ball.state == BallState.AT_REST:
            self.shot_ctrl.handle_mousedown(pos, self._ball_screen_pos())

    def _on_left_release(self, pos):
        """Handle a left mouse-button release — fires the shot if aiming."""
        if pos[0] >= VIEWPORT_W:
            return
        if self.ball.state != BallState.AT_REST:
            return

        terrain = self._ball_terrain()
        result  = self.shot_ctrl.handle_mouseup(
            pos,
            self.ball.pos,
            self.current_club,
            terrain,
            self.tile_sz,
        )

        if result is None:
            return

        target_x, target_y = result

        # Clamp landing position to course world bounds
        world_w, world_h = self.renderer.world_size()
        target_x = clamp(target_x, 0, world_w - 1)
        target_y = clamp(target_y, 0, world_h - 1)

        # Record current position as last safe spot (before water check)
        self._last_safe_x = self.ball.x
        self._last_safe_y = self.ball.y

        self.strokes += 1
        is_putt = (self.current_club.name == "Putter")
        self.ball.hit(target_x, target_y, is_putt=is_putt)

    def _cycle_club(self, direction):
        """Move to next/previous club in the bag."""
        self.club_idx = (self.club_idx + direction) % len(self.clubs)

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        if self.hole_complete:
            self.complete_timer += dt
            return

        # Update ball physics / animation
        self.ball.update(dt, self._pin_world_pos())

        # React when ball has just landed
        if (self.shot_ctrl.state == ShotState.EXECUTING
                and self.ball.state == BallState.AT_REST):
            self._on_ball_landed()

        # Check for hole-out
        if self.ball.state == BallState.IN_HOLE:
            self.hole_complete  = True
            self.complete_timer = 0.0

        # Smooth camera follow (ball is at centre of viewport)
        if self.ball.state == BallState.FLYING:
            self._follow_camera(dt)

        # Count down on-screen message
        if self.message_timer > 0:
            self.message_timer -= dt

    def _on_ball_landed(self):
        """Called once when the ball finishes moving."""
        self.shot_ctrl.on_ball_landed()
        terrain = self._ball_terrain()

        # Water hazard: penalty stroke + drop near last safe position
        if terrain == Terrain.WATER:
            self.strokes += 1
            self._show_message("Water hazard! +1 penalty stroke", 2.8)
            # Drop ball a short distance back from water on the last safe spot
            drop_x = (self.ball.x + self._last_safe_x) / 2
            drop_y = (self.ball.y + self._last_safe_y) / 2
            self.ball.place(drop_x, drop_y)

        self._auto_select_club()

    def _auto_select_club(self):
        """
        Pick the most appropriate club after a shot lands.

        - On the green: always switch to the putter.
        - Everywhere else: find the club whose effective max distance
          (club max * terrain distance modifier) is closest to the
          remaining distance to the pin. The putter is excluded from
          this search so it is never suggested off the green.
        """
        terrain = self._ball_terrain()

        # ── Green: putter only ────────────────────────────────────────────────
        if terrain == Terrain.GREEN:
            for i, c in enumerate(self.clubs):
                if c.name == "Putter":
                    self.club_idx = i
                    return

        # ── Bunker: sand wedge always ─────────────────────────────────────────
        if terrain == Terrain.BUNKER:
            for i, c in enumerate(self.clubs):
                if c.name == "Sand Wedge":
                    self.club_idx = i
                    return

        # ── Off green: closest-distance club ─────────────────────────────────
        pin_wx, pin_wy = self._pin_world_pos()
        dist_px = math.sqrt((self.ball.x - pin_wx) ** 2 +
                            (self.ball.y - pin_wy) ** 2)
        dist_yards = dist_px / self.tile_sz * 10

        # How far each club actually sends the ball from this lie
        dist_mod = TERRAIN_PROPS[terrain]['dist_mod']

        best_idx  = 0
        best_diff = float('inf')

        for i, club in enumerate(self.clubs):
            if club.name == "Putter":
                continue                         # never suggest putter off-green

            effective_max = club.max_distance_yards * dist_mod
            diff = abs(effective_max - dist_yards)

            if diff < best_diff:
                best_diff = diff
                best_idx  = i

        self.club_idx = best_idx

    def _follow_camera(self, dt):
        """Smoothly pan the camera to keep the ball roughly centred."""
        target_cx = self.ball.x - VIEWPORT_W / 2
        target_cy = self.ball.y - VIEWPORT_H / 2
        speed = 4.0 * dt
        self.cam_x += (target_cx - self.cam_x) * speed
        self.cam_y += (target_cy - self.cam_y) * speed
        self._clamp_camera()

    def _clamp_camera(self):
        """Keep camera within the course world bounds."""
        world_w, world_h = self.renderer.world_size()
        self.cam_x = clamp(self.cam_x, 0, max(0, world_w - VIEWPORT_W))
        self.cam_y = clamp(self.cam_y, 0, max(0, world_h - VIEWPORT_H))

    def _show_message(self, text, duration):
        self.message       = text
        self.message_timer = duration

    def _restart(self):
        """Restart the current hole."""
        self.__init__(self.game)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        viewport = pygame.Rect(0, 0, VIEWPORT_W, VIEWPORT_H)

        # ── Course tiles ──────────────────────────────────────────────────────
        surface.fill((20, 80, 20))   # fallback background (trees/OOB colour)
        self.renderer.draw(surface, int(self.cam_x), int(self.cam_y), viewport)

        # ── Aim arrow ────────────────────────────────────────────────────────
        aim = self.shot_ctrl.get_aim_line(self._ball_screen_pos())
        if aim:
            self._draw_aim_arrow(surface, *aim)

        # ── Ball ─────────────────────────────────────────────────────────────
        self.ball.draw(surface, int(self.cam_x), int(self.cam_y))

        # ── Off-screen pin indicator ─────────────────────────────────────────
        self._draw_pin_indicator(surface)

        # ── Distance to pin label ────────────────────────────────────────────
        if self.ball.state == BallState.AT_REST and not self.hole_complete:
            self._draw_distance_to_pin(surface)

        # ── HUD panel ────────────────────────────────────────────────────────
        terrain_name = TERRAIN_PROPS[self._ball_terrain()]['name']
        self.hud.draw(surface, self.hole, self.strokes,
                      self.current_club, self.shot_ctrl, terrain_name,
                      renderer=self.renderer, ball_world_pos=self.ball.pos)

        # ── Floating message ─────────────────────────────────────────────────
        if self.message and self.message_timer > 0:
            self._draw_message(surface)

        # ── Hole complete overlay ─────────────────────────────────────────────
        if self.hole_complete:
            self._draw_complete_overlay(surface)

    def _draw_aim_arrow(self, surface, start, end, power):
        """Draw a coloured arrow from the ball in the shot direction."""
        # Colour shifts green → yellow → red as power increases
        r = int(min(255, power * 2 * 255))
        g = int(min(255, (1.0 - power) * 2 * 255))
        color = (r, g, 0)

        sx, sy = int(start[0]), int(start[1])
        ex, ey = int(end[0]),   int(end[1])

        pygame.draw.line(surface, color, (sx, sy), (ex, ey), 3)

        # Arrowhead triangle
        dx, dy = ex - sx, ey - sy
        mag = math.sqrt(dx * dx + dy * dy)
        if mag > 0:
            ndx, ndy = dx / mag, dy / mag
            size = 12
            tip   = (ex, ey)
            left  = (int(ex - ndx * size + ndy * 5),
                     int(ey - ndy * size - ndx * 5))
            right = (int(ex - ndx * size - ndy * 5),
                     int(ey - ndy * size + ndx * 5))
            pygame.draw.polygon(surface, color, [tip, left, right])

    def _draw_pin_indicator(self, surface):
        """
        Draw a compass-style arrow at the edge of the viewport pointing toward
        the pin whenever the pin is off-screen.
        """
        psx, psy = self._pin_screen_pos()
        if 20 <= psx <= VIEWPORT_W - 20 and 20 <= psy <= VIEWPORT_H - 20:
            return   # Pin is visible — no indicator needed

        cx, cy = VIEWPORT_W // 2, VIEWPORT_H // 2
        angle  = math.atan2(psy - cy, psx - cx)
        margin = 38

        # Project onto the viewport edge
        ind_x = int(cx + math.cos(angle) * (VIEWPORT_W // 2 - margin))
        ind_y = int(cy + math.sin(angle) * (VIEWPORT_H // 2 - margin))
        ind_x = clamp(ind_x, margin, VIEWPORT_W - margin)
        ind_y = clamp(ind_y, margin, VIEWPORT_H - margin)

        pygame.draw.circle(surface, C_YELLOW, (ind_x, ind_y), 14, 2)

        # Distance label
        pin_wx, pin_wy = self._pin_world_pos()
        dist_yd = int(math.sqrt((self.ball.x - pin_wx) ** 2 +
                                (self.ball.y - pin_wy) ** 2)
                      / self.tile_sz * 10)
        lbl = self.font_med.render(f"{dist_yd}y", True, C_YELLOW)
        surface.blit(lbl, (ind_x - lbl.get_width() // 2, ind_y + 16))

    def _draw_distance_to_pin(self, surface):
        """Draw a small distance label near the ball."""
        pin_wx, pin_wy = self._pin_world_pos()
        dist_yd = int(math.sqrt((self.ball.x - pin_wx) ** 2 +
                                (self.ball.y - pin_wy) ** 2)
                      / self.tile_sz * 10)

        bsx, bsy = self._ball_screen_pos()
        lbl = self.font_med.render(f"{dist_yd} yds to pin", True, C_YELLOW)
        lx  = clamp(bsx - lbl.get_width() // 2, 4, VIEWPORT_W - lbl.get_width() - 4)
        ly  = clamp(bsy - 26, 4, VIEWPORT_H - 20)
        surface.blit(lbl, (lx, ly))

    def _draw_message(self, surface):
        """Draw a centred floating notification message."""
        lbl = self.font_med.render(self.message, True, (255, 230, 80))
        x   = (VIEWPORT_W - lbl.get_width())  // 2
        surface.blit(lbl, (x, 28))

    def _draw_complete_overlay(self, surface):
        """Semi-transparent overlay shown when the hole is complete."""
        # Dim the course
        overlay = pygame.Surface((VIEWPORT_W, VIEWPORT_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        surface.blit(overlay, (0, 0))

        cx = VIEWPORT_W // 2

        # Score name
        diff = self.strokes - self.hole.par
        score_labels = {
            -3: ("Albatross!",    C_GREEN),
            -2: ("Eagle!",        C_GREEN),
            -1: ("Birdie!",       C_GREEN),
             0: ("Par",           C_WHITE),
             1: ("Bogey",         C_RED),
             2: ("Double Bogey",  C_RED),
        }
        label, color = score_labels.get(diff, (f"+{diff}" if diff > 0 else str(diff), C_RED))

        self._blit_centred(surface, "Hole Complete!",
                           self.font_big, C_WHITE, cx, 220)
        self._blit_centred(surface, label,
                           self.font_big, color,  cx, 278)
        self._blit_centred(surface,
                           f"{self.strokes} strokes   (Par {self.hole.par})",
                           self.font_med, (190, 190, 190), cx, 340)

        if self.complete_timer > 1.2:
            self._blit_centred(surface,
                               "Click or press any key to play again",
                               self.font_med, (155, 155, 155), cx, 400)

    def _blit_centred(self, surface, text, font, color, cx, y):
        surf = font.render(text, True, color)
        surface.blit(surf, (cx - surf.get_width() // 2, y))
