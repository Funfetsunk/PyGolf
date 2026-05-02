"""
Ball — tracks position, flight animation, and hole-detection.

Flight path
-----------
The ball travels from its start position toward the landing point.
Three overlaid effects shape the visible path:

  Base path  — straight lerp along the aimed direction.
  Shape curve — draw/fade lateral offset applied quadratically (starts
                straight, curves more toward the end, like real ball flight).
  Wind drift  — lateral/along drift applied linearly (builds up evenly
                throughout the flight).

A vertical arc is added so the ball appears to travel through the air.
A shadow at ground level shows where the ball will land.

After landing the ball enters a ROLLING state: it continues in the shot
direction, decelerating under friction, before coming to rest.  The roll
distance is passed in from golf_round.py and is terrain-dependent.
"""

import math
from enum import Enum, auto

import pygame

from src.utils.math_utils import clamp

BASE_FLIGHT_DURATION = 1.1
HOLE_CAPTURE_RADIUS  = 5     # direct landing/roll capture (~1.6 yards)
HOLE_ROLL_RADIUS     = 9     # mid-flight "rolling over hole" capture (last 25% of flight)
BALL_RADIUS          = 5
ARC_HEIGHT           = 35
SINK_DURATION        = 0.45
ROLL_DECEL           = 180.0  # px / s²  — ground friction deceleration


class BallState(Enum):
    AT_REST = auto()
    FLYING  = auto()
    ROLLING = auto()
    SINKING = auto()
    IN_HOLE = auto()


class Ball:
    """The golf ball."""

    def __init__(self, x, y):
        self.x     = float(x)
        self.y     = float(y)
        self.state = BallState.AT_REST

        self._start_x  = x
        self._start_y  = y
        self._target_x = x
        self._target_y = y
        self._aim_x    = x
        self._aim_y    = y
        self._shape_x  = 0.0
        self._shape_y  = 0.0
        self._wind_x   = 0.0
        self._wind_y   = 0.0

        self._flight_timer    = 0.0
        self._flight_duration = BASE_FLIGHT_DURATION
        self._is_putt         = False
        self._roll_dist_px    = 0.0

        # Rolling state
        self._roll_dir_x = 0.0
        self._roll_dir_y = 0.0
        self._roll_speed = 0.0   # px/s, decreases to zero under ROLL_DECEL

        self._sink_timer = 0.0
        self._pin_x      = 0.0
        self._pin_y      = 0.0

        self._spin_angle = 0.0   # for rolling animation

        # Firmness modifier — scales roll distance (set per-hole from tournament).
        # >1.0 = firmer ground = more roll; <1.0 = softer = less roll.
        self.roll_mod: float = 1.0

    @property
    def pos(self):
        return (self.x, self.y)

    def is_moving(self):
        return self.state in (BallState.FLYING, BallState.ROLLING)

    def hit(self, target_x, target_y, is_putt=False,
            aim_x=None, aim_y=None,
            shape_x=0.0, shape_y=0.0,
            wind_x=0.0, wind_y=0.0,
            roll_dist_px=0.0):
        """
        Launch the ball toward (target_x, target_y).

        aim_x/y      : straight aim point (no shaping, no wind).
        shape_x/y    : perpendicular curve offset (quadratic during flight).
        wind_x/y     : wind drift (linear during flight).
        roll_dist_px : how far the ball rolls after landing (0 = stop immediately).
        is_putt      : suppresses arc and post-landing roll.
        """
        self._start_x = self.x
        self._start_y = self.y
        self._target_x = float(target_x)
        self._target_y = float(target_y)
        self._aim_x   = float(aim_x) if aim_x is not None else float(target_x)
        self._aim_y   = float(aim_y) if aim_y is not None else float(target_y)
        self._shape_x = float(shape_x)
        self._shape_y = float(shape_y)
        self._wind_x  = float(wind_x)
        self._wind_y  = float(wind_y)

        self._flight_timer    = 0.0
        self._flight_duration = BASE_FLIGHT_DURATION
        self._is_putt         = is_putt
        self._roll_dist_px    = 0.0 if is_putt else float(roll_dist_px)
        self.state = BallState.FLYING

    def place(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.state = BallState.AT_REST

    def stop_roll(self):
        """Immediately kill the roll and come to rest (e.g. ball enters a bunker)."""
        self._roll_speed = 0.0
        self.state = BallState.AT_REST

    def update(self, dt, pin_world_pos):
        # ── Sinking ───────────────────────────────────────────────────────────
        if self.state == BallState.SINKING:
            self._sink_timer += dt
            t = clamp(self._sink_timer / SINK_DURATION, 0.0, 1.0)
            self.x += (self._pin_x - self.x) * t * 0.15
            self.y += (self._pin_y - self.y) * t * 0.15
            if self._sink_timer >= SINK_DURATION:
                self.state = BallState.IN_HOLE
            return

        # ── Rolling ───────────────────────────────────────────────────────────
        if self.state == BallState.ROLLING:
            self._roll_speed = max(0.0, self._roll_speed - ROLL_DECEL * dt)
            if self._roll_speed <= 0.0:
                self.state = BallState.AT_REST
                self._spin_angle = 0.0
                return

            self.x += self._roll_dir_x * self._roll_speed * dt
            self.y += self._roll_dir_y * self._roll_speed * dt
            self._spin_angle += self._roll_speed * dt * 0.12

            px, py = pin_world_pos
            if math.sqrt((self.x - px) ** 2 + (self.y - py) ** 2) <= HOLE_CAPTURE_RADIUS:
                self.state       = BallState.SINKING
                self._sink_timer = 0.0
                self._pin_x      = px
                self._pin_y      = py
            return

        if self.state != BallState.FLYING:
            return

        # ── Flying ────────────────────────────────────────────────────────────
        self._flight_timer += dt
        t = clamp(self._flight_timer / self._flight_duration, 0.0, 1.0)

        # Ease-out so the ball decelerates as it approaches the target
        t_smooth = 1.0 - (1.0 - t) ** 2

        base_x = self._start_x + t_smooth * (self._aim_x - self._start_x)
        base_y = self._start_y + t_smooth * (self._aim_y - self._start_y)

        shape_t = t_smooth ** 2   # quadratic: straight early, curving near end
        wind_t  = t_smooth        # linear: steady drift throughout

        self.x = base_x + self._shape_x * shape_t + self._wind_x * wind_t
        self.y = base_y + self._shape_y * shape_t + self._wind_y * wind_t

        px, py = pin_world_pos
        dist_to_pin = math.sqrt((self.x - px) ** 2 + (self.y - py) ** 2)

        # "Rolling over the hole" — ball nearly at ground level passes over hole.
        # Gate on arc height so airborne balls above the hole aren't captured.
        arc_height = ARC_HEIGHT * 4 * t * (1.0 - t)
        if arc_height <= BALL_RADIUS and dist_to_pin <= HOLE_ROLL_RADIUS:
            self.x = px
            self.y = py
            self.state       = BallState.SINKING
            self._sink_timer = 0.0
            self._pin_x      = px
            self._pin_y      = py
            return

        if self._flight_timer >= self._flight_duration:
            self.x = self._target_x
            self.y = self._target_y

            # Start rolling if terrain allows, otherwise stop
            dx = self._target_x - self._start_x
            dy = self._target_y - self._start_y
            mag = math.sqrt(dx * dx + dy * dy)

            if self._roll_dist_px > 0.0 and mag > 0.0:
                self._roll_dir_x = dx / mag
                self._roll_dir_y = dy / mag
                # v₀ chosen so the ball decelerates to rest over exactly roll_dist_px
                self._roll_speed = math.sqrt(2.0 * ROLL_DECEL * self._roll_dist_px)
                self.state = BallState.ROLLING
            else:
                self.state = BallState.AT_REST
                dist_landed = math.sqrt((self.x - px) ** 2 + (self.y - py) ** 2)
                if dist_landed <= HOLE_CAPTURE_RADIUS:
                    self.state       = BallState.SINKING
                    self._sink_timer = 0.0
                    self._pin_x      = px
                    self._pin_y      = py

    def draw(self, surface, camera_x, camera_y):
        if self.state == BallState.IN_HOLE:
            return

        if self.state == BallState.SINKING:
            t = clamp(self._sink_timer / SINK_DURATION, 0.0, 1.0)
            r  = max(1, int(BALL_RADIUS * (1.0 - t)))
            sx = int(self.x - camera_x)
            sy = int(self.y - camera_y)
            pygame.draw.circle(surface, (245, 245, 245), (sx, sy), r)
            pygame.draw.circle(surface, (160, 160, 160), (sx, sy), r, 1)
            return

        arc_offset = self._get_arc_offset()

        # Ground-level shadow (shrinks and fades as ball rises)
        shadow_sx = int(self.x - camera_x)
        shadow_sy = int(self.y - camera_y)
        rise         = abs(arc_offset)
        shadow_alpha = max(30, 120 - rise * 2)
        shadow_rx    = BALL_RADIUS + rise // 6
        shadow_ry    = max(2, BALL_RADIUS // 2 - rise // 12)

        shadow_surf = pygame.Surface((shadow_rx * 4, shadow_ry * 4), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, shadow_alpha), shadow_surf.get_rect())
        surface.blit(shadow_surf,
                     (shadow_sx - shadow_rx * 2 + shadow_rx // 4, shadow_sy - shadow_ry))

        bsx = int(self.x - camera_x)
        bsy = int(self.y - camera_y) + arc_offset
        r   = BALL_RADIUS

        pygame.draw.circle(surface, (245, 245, 245), (bsx, bsy), r)

        shade_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(shade_surf, (0, 0, 0, 45), (r + 2, r + 2), r)
        surface.blit(shade_surf, (bsx - r + 1, bsy - r + 1))

        hl_x = bsx - r // 3
        hl_y = bsy - r // 3
        pygame.draw.circle(surface, (255, 255, 255), (hl_x, hl_y), max(1, r // 3))
        pygame.draw.circle(surface, (160, 160, 160), (bsx, bsy), r, 1)

        # Spinning dimple when rolling
        if self.state == BallState.ROLLING:
            spin_r = max(1, r - 2)
            dx = int(math.cos(self._spin_angle) * spin_r)
            dy = int(math.sin(self._spin_angle) * spin_r)
            pygame.draw.circle(surface, (110, 110, 110), (bsx + dx, bsy + dy), 1)

    def _get_arc_offset(self):
        if self.state not in (BallState.FLYING,) or self._is_putt:
            return 0
        t = clamp(self._flight_timer / self._flight_duration, 0.0, 1.0)
        return -int(ARC_HEIGHT * 4 * t * (1.0 - t))
