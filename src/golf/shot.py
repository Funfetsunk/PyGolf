"""
Shot controller — manages the click-drag input system for taking shots.

How it works
------------
1. Player LEFT-CLICKS near the ball → enters AIMING state.
2. Player DRAGS the mouse away from click point → the direction of drag
   becomes the shot direction; drag distance sets power (capped at MAX_DRAG).
3. Player RELEASES the mouse button → shot fires, returns the world-pixel
   landing position.

Shot shaping
------------
DRAW curves the ball slightly to the left (relative to shot direction).
FADE curves it right. Straight goes true.
"""

import math
import random
from enum import Enum, auto

from src.golf.terrain import Terrain, TERRAIN_PROPS
from src.utils.math_utils import normalize, clamp

# How far (px) the player must drag to reach 100% power.
MAX_DRAG_PIXELS = 130

# Click must be within this many screen pixels of the ball to start aiming.
AIM_CLICK_RADIUS = 35

# How much lateral curve is applied as a fraction of total shot distance.
SHAPE_CURVE_FRACTION = 0.10


class ShotShape(Enum):
    DRAW     = "Draw"
    STRAIGHT = "Straight"
    FADE     = "Fade"


class ShotState(Enum):
    IDLE      = auto()   # No shot in progress, waiting for click
    AIMING    = auto()   # Player is dragging to set direction and power
    EXECUTING = auto()   # Ball is currently flying


class ShotController:
    """Manages all shot input and calculates the landing position."""

    def __init__(self):
        self.state       = ShotState.IDLE
        self.shot_shape  = ShotShape.STRAIGHT

        # Mouse positions in screen coordinates
        self._drag_start   = None
        self._drag_current = None

    # ── Mouse event handlers ───────────────────────────────────────────────────

    def handle_mousedown(self, screen_pos, ball_screen_pos):
        """
        Called on left mouse button press.
        Only starts aiming if the click is close enough to the ball.
        """
        if self.state != ShotState.IDLE:
            return

        bx, by = ball_screen_pos
        mx, my = screen_pos
        if math.sqrt((mx - bx) ** 2 + (my - by) ** 2) <= AIM_CLICK_RADIUS:
            self.state         = ShotState.AIMING
            self._drag_start   = screen_pos
            self._drag_current = screen_pos

    def handle_mousemove(self, screen_pos):
        """Called on every mouse-move event."""
        if self.state == ShotState.AIMING:
            self._drag_current = screen_pos

    def handle_mouseup(self, screen_pos, ball_world_pos, club, current_terrain, tile_size):
        """
        Called on left mouse button release.
        Calculates the landing position and returns it as (world_x, world_y),
        or None if the drag was too small / invalid.
        """
        if self.state != ShotState.AIMING:
            return None

        self._drag_current = screen_pos

        dx = self._drag_current[0] - self._drag_start[0]
        dy = self._drag_current[1] - self._drag_start[1]
        drag_dist = math.sqrt(dx * dx + dy * dy)

        # Ignore tiny drags (accidental clicks)
        if drag_dist < 6:
            self.state = ShotState.IDLE
            return None

        # Power fraction 0..1 based on drag distance
        power = clamp(drag_dist / MAX_DRAG_PIXELS, 0.0, 1.0)

        # Normalised shot direction (same direction as drag)
        dir_x, dir_y = normalize(dx, dy)

        # Fetch terrain modifiers for where the ball currently sits
        props    = TERRAIN_PROPS[current_terrain]
        dist_mod = props['dist_mod']
        acc_mod  = props['acc_mod']

        # Can't hit from water (handled as a penalty elsewhere)
        if current_terrain == Terrain.WATER:
            self.state = ShotState.IDLE
            return None

        # Convert club distance (yards) to world pixels
        # Scale: 10 yards per tile, tile_size pixels per tile
        yards_per_pixel = 10.0 / tile_size
        max_dist_px = (club.max_distance_yards / 10.0) * tile_size

        # Apply power and terrain penalty
        shot_dist_px = power * max_dist_px * dist_mod

        # Shot shaping: lateral offset perpendicular to the shot direction
        # Perpendicular clockwise = (dir_y, -dir_x), counter-clockwise = (-dir_y, dir_x)
        perp_x = -dir_y   # perpendicular left
        perp_y =  dir_x
        shape_offset_px = 0.0
        if self.shot_shape == ShotShape.DRAW and club.can_shape:
            shape_offset_px = -shot_dist_px * SHAPE_CURVE_FRACTION   # left curve
        elif self.shot_shape == ShotShape.FADE and club.can_shape:
            shape_offset_px =  shot_dist_px * SHAPE_CURVE_FRACTION   # right curve

        # Random scatter based on club accuracy and terrain accuracy penalty
        effective_accuracy = club.accuracy * acc_mod
        scatter_range = (1.0 - effective_accuracy) * shot_dist_px * 0.18
        scatter = random.uniform(-scatter_range, scatter_range)

        # Final landing position in world coordinates
        bx, by = ball_world_pos
        target_x = bx + dir_x * shot_dist_px + perp_x * (shape_offset_px + scatter)
        target_y = by + dir_y * shot_dist_px + perp_y * (shape_offset_px + scatter)

        self.state = ShotState.EXECUTING
        return (target_x, target_y)

    def on_ball_landed(self):
        """Call this when the ball finishes its flight animation."""
        self.state = ShotState.IDLE

    def cancel(self):
        """Cancel an in-progress aim (e.g. right-click)."""
        self.state         = ShotState.IDLE
        self._drag_start   = None
        self._drag_current = None

    # ── Query helpers ──────────────────────────────────────────────────────────

    def get_power(self):
        """Current power fraction 0..1. Only meaningful during AIMING."""
        if self.state != ShotState.AIMING or not self._drag_current:
            return 0.0
        dx = self._drag_current[0] - self._drag_start[0]
        dy = self._drag_current[1] - self._drag_start[1]
        return clamp(math.sqrt(dx * dx + dy * dy) / MAX_DRAG_PIXELS, 0.0, 1.0)

    def get_aim_line(self, ball_screen_pos):
        """
        Return ((start_x, start_y), (end_x, end_y), power) for drawing
        the aim arrow, or None if not currently aiming.
        The line originates at the ball and points in the shot direction.
        """
        if self.state != ShotState.AIMING or not self._drag_current:
            return None

        bx, by = ball_screen_pos
        dx = self._drag_current[0] - self._drag_start[0]
        dy = self._drag_current[1] - self._drag_start[1]
        drag_dist = math.sqrt(dx * dx + dy * dy)

        if drag_dist == 0:
            return None

        power  = clamp(drag_dist / MAX_DRAG_PIXELS, 0.0, 1.0)
        ndx, ndy = dx / drag_dist, dy / drag_dist

        # Arrow length scales slightly with power so player gets visual feedback
        line_len = 60 + power * 50
        end_x = bx + ndx * line_len
        end_y = by + ndy * line_len

        return ((bx, by), (end_x, end_y), power)
