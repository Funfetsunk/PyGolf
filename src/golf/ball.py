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
"""

import math
from enum import Enum, auto

import pygame

from src.utils.math_utils import clamp

BASE_FLIGHT_DURATION = 1.1
HOLE_CAPTURE_RADIUS  = 14
BALL_RADIUS          = 5
ARC_HEIGHT           = 35
SINK_DURATION        = 0.45


class BallState(Enum):
    AT_REST = auto()
    FLYING  = auto()
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
        # Straight aim point (no shape, no wind) — used as the base flight path
        self._aim_x    = x
        self._aim_y    = y
        # Shape offset at landing (applied quadratically during flight)
        self._shape_x  = 0.0
        self._shape_y  = 0.0
        # Wind offset at landing (applied linearly during flight)
        self._wind_x   = 0.0
        self._wind_y   = 0.0

        self._flight_timer    = 0.0
        self._flight_duration = BASE_FLIGHT_DURATION
        self._is_putt         = False

        self._sink_timer = 0.0
        self._pin_x      = 0.0
        self._pin_y      = 0.0

    @property
    def pos(self):
        return (self.x, self.y)

    def is_moving(self):
        return self.state == BallState.FLYING

    def hit(self, target_x, target_y, is_putt=False,
            aim_x=None, aim_y=None,
            shape_x=0.0, shape_y=0.0,
            wind_x=0.0, wind_y=0.0):
        """
        Launch the ball toward (target_x, target_y).

        aim_x/y   : straight aim point with no shaping and no wind — used as
                    the base interpolation path so the ball starts straight.
        shape_x/y : shape displacement vector (applied quadratically during
                    flight — ball starts straight then curves).
        wind_x/y  : wind displacement vector (applied linearly — steady drift).
        is_putt   : suppresses the vertical arc so the ball rolls on the ground.

        If aim_x/y are omitted the ball travels in a straight line to target.
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
        self.state = BallState.FLYING

    def place(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.state = BallState.AT_REST

    def update(self, dt, pin_world_pos):
        if self.state == BallState.SINKING:
            self._sink_timer += dt
            t = clamp(self._sink_timer / SINK_DURATION, 0.0, 1.0)
            self.x += (self._pin_x - self.x) * t * 0.15
            self.y += (self._pin_y - self.y) * t * 0.15
            if self._sink_timer >= SINK_DURATION:
                self.state = BallState.IN_HOLE
            return

        if self.state != BallState.FLYING:
            return

        self._flight_timer += dt
        t = clamp(self._flight_timer / self._flight_duration, 0.0, 1.0)

        # Ease-out so the ball decelerates as it lands
        t_smooth = 1.0 - (1.0 - t) ** 2

        # Base path: straight lerp along the aimed direction
        base_x = self._start_x + t_smooth * (self._aim_x - self._start_x)
        base_y = self._start_y + t_smooth * (self._aim_y - self._start_y)

        # Shape curve: quadratic — starts near zero, full offset at landing
        shape_t = t_smooth ** 2
        # Wind drift: linear — builds up evenly throughout the flight
        wind_t  = t_smooth

        self.x = base_x + self._shape_x * shape_t + self._wind_x * wind_t
        self.y = base_y + self._shape_y * shape_t + self._wind_y * wind_t

        if self._flight_timer >= self._flight_duration:
            self.x = self._target_x
            self.y = self._target_y
            self.state = BallState.AT_REST

            px, py = pin_world_pos
            if math.sqrt((self.x - px) ** 2 + (self.y - py) ** 2) <= HOLE_CAPTURE_RADIUS:
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

        # Ground-level shadow
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

    def _get_arc_offset(self):
        if self.state != BallState.FLYING or self._is_putt:
            return 0
        t = clamp(self._flight_timer / self._flight_duration, 0.0, 1.0)
        return -int(ARC_HEIGHT * 4 * t * (1.0 - t))
