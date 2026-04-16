"""
Ball — tracks position, flight animation, and hole-detection.

Flight is animated over a fixed duration using smooth interpolation.
A visual arc is added so the ball appears to travel through the air.
A shadow drawn at ground level shows where the ball will land.
"""

import math
from enum import Enum, auto

import pygame

from src.utils.math_utils import lerp_point, clamp

# How long the ball spends in the air (seconds).
# Longer clubs feel weightier with a slightly longer duration.
BASE_FLIGHT_DURATION = 1.1

# How close (in world pixels) the ball must land to the pin to count as holed.
HOLE_CAPTURE_RADIUS = 14

# Visual radius of the ball in pixels.
BALL_RADIUS = 5

# Maximum height of the flight arc in pixels (at the midpoint of the trajectory).
ARC_HEIGHT = 35

# How long the ball takes to shrink into the cup.
SINK_DURATION = 0.45


class BallState(Enum):
    AT_REST  = auto()   # Sitting still, waiting for player input
    FLYING   = auto()   # Mid-air, being animated toward landing spot
    SINKING  = auto()   # Shrinking into the cup
    IN_HOLE  = auto()   # Fully holed — round is complete


class Ball:
    """
    The golf ball.

    World coordinates are in pixels (matching the course tile map).
    """

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.state = BallState.AT_REST

        # Flight animation bookkeeping
        self._start_x = x
        self._start_y = y
        self._target_x = x
        self._target_y = y
        self._flight_timer    = 0.0
        self._flight_duration = BASE_FLIGHT_DURATION
        self._is_putt         = False

        # Sink animation bookkeeping
        self._sink_timer = 0.0
        self._pin_x      = 0.0
        self._pin_y      = 0.0

    # ── Public interface ───────────────────────────────────────────────────────

    @property
    def pos(self):
        """Current world position as (x, y) tuple."""
        return (self.x, self.y)

    def is_moving(self):
        return self.state == BallState.FLYING

    def hit(self, target_x, target_y, flight_duration=BASE_FLIGHT_DURATION,
            is_putt=False):
        """
        Launch the ball toward (target_x, target_y).
        is_putt=True suppresses the air arc so the ball rolls along the ground.
        """
        self._start_x = self.x
        self._start_y = self.y
        self._target_x = float(target_x)
        self._target_y = float(target_y)
        self._flight_timer    = 0.0
        self._flight_duration = flight_duration
        self._is_putt         = is_putt
        self.state = BallState.FLYING

    def place(self, x, y):
        """Teleport the ball to (x, y) without animation (used for drops/penalties)."""
        self.x = float(x)
        self.y = float(y)
        self.state = BallState.AT_REST

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt, pin_world_pos):
        """
        Advance the ball's animation.
        pin_world_pos: (x, y) world-pixel position of the hole.
        """
        if self.state == BallState.SINKING:
            self._sink_timer += dt
            # Glide toward pin centre as it sinks
            t = clamp(self._sink_timer / SINK_DURATION, 0.0, 1.0)
            self.x = self.x + (self._pin_x - self.x) * t * 0.15
            self.y = self.y + (self._pin_y - self.y) * t * 0.15
            if self._sink_timer >= SINK_DURATION:
                self.state = BallState.IN_HOLE
            return

        if self.state != BallState.FLYING:
            return

        self._flight_timer += dt
        t = clamp(self._flight_timer / self._flight_duration, 0.0, 1.0)

        # Ease-out so the ball decelerates as it lands (feels more natural)
        t_smooth = 1.0 - (1.0 - t) ** 2

        pos = lerp_point(
            (self._start_x, self._start_y),
            (self._target_x, self._target_y),
            t_smooth,
        )
        self.x, self.y = pos

        # Landing check
        if self._flight_timer >= self._flight_duration:
            self.x = self._target_x
            self.y = self._target_y
            self.state = BallState.AT_REST

            # Check if close enough to the pin to begin sinking
            px, py = pin_world_pos
            dist = math.sqrt((self.x - px) ** 2 + (self.y - py) ** 2)
            if dist <= HOLE_CAPTURE_RADIUS:
                self.state    = BallState.SINKING
                self._sink_timer = 0.0
                self._pin_x   = px
                self._pin_y   = py

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface, camera_x, camera_y):
        """
        Draw the ball on screen.
        camera_x/y: the top-left world position currently visible (scroll offset).
        """
        if self.state == BallState.IN_HOLE:
            return  # Ball has fully dropped — nothing to draw

        # Sinking: shrink the ball into the cup over SINK_DURATION
        if self.state == BallState.SINKING:
            t = clamp(self._sink_timer / SINK_DURATION, 0.0, 1.0)
            r = max(1, int(BALL_RADIUS * (1.0 - t)))
            sx = int(self.x - camera_x)
            sy = int(self.y - camera_y)
            pygame.draw.circle(surface, (245, 245, 245), (sx, sy), r)
            pygame.draw.circle(surface, (160, 160, 160), (sx, sy), r, 1)
            return

        arc_offset = self._get_arc_offset()

        # Ground-level shadow — stays at the true world position (no arc offset).
        # The shadow grows and blurs slightly as the ball rises.
        shadow_sx = int(self.x - camera_x)
        shadow_sy = int(self.y - camera_y)
        # Scale shadow with height: higher arc = wider, more transparent shadow
        rise = abs(arc_offset)                      # 0 at rest, peak during flight
        shadow_alpha = max(30, 120 - rise * 2)
        shadow_rx    = BALL_RADIUS + rise // 6
        shadow_ry    = max(2, BALL_RADIUS // 2 - rise // 12)

        shadow_surf = pygame.Surface((shadow_rx * 4, shadow_ry * 4), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf,
                            (0, 0, 0, shadow_alpha),
                            shadow_surf.get_rect())
        surface.blit(shadow_surf,
                     (shadow_sx - shadow_rx * 2 + shadow_rx // 4,
                      shadow_sy - shadow_ry))

        # ── Ball sphere ───────────────────────────────────────────────────────
        bsx = int(self.x - camera_x)
        bsy = int(self.y - camera_y) + arc_offset
        r   = BALL_RADIUS

        # Base white fill
        pygame.draw.circle(surface, (245, 245, 245), (bsx, bsy), r)

        # Subtle grey shading on the lower-right (gives a 3-D sphere impression)
        shade_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(shade_surf, (0, 0, 0, 45),
                           (r + 1 + 1, r + 1 + 1), r)
        surface.blit(shade_surf, (bsx - r + 1, bsy - r + 1))

        # Bright specular highlight (top-left)
        hl_x = bsx - r // 3
        hl_y = bsy - r // 3
        pygame.draw.circle(surface, (255, 255, 255), (hl_x, hl_y), max(1, r // 3))

        # Crisp dark outline
        pygame.draw.circle(surface, (160, 160, 160), (bsx, bsy), r, 1)

    def _get_arc_offset(self):
        """
        Vertical pixel offset for the flight arc (negative = upward on screen).
        Putts return 0 — the ball stays on the ground and rolls.
        """
        if self.state != BallState.FLYING or self._is_putt:
            return 0
        t = clamp(self._flight_timer / self._flight_duration, 0.0, 1.0)
        # 4*t*(1-t) gives a parabola that starts and ends at 0, peaks at 1 when t=0.5
        return -int(ARC_HEIGHT * 4 * t * (1.0 - t))
