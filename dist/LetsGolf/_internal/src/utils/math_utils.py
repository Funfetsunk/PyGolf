"""
Math utility helpers — vector maths, interpolation, coordinate conversions.
"""

import math


def distance(p1, p2):
    """Euclidean distance between two (x, y) points."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.sqrt(dx * dx + dy * dy)


def normalize(dx, dy):
    """
    Return a unit vector in the direction (dx, dy).
    Returns (0.0, 0.0) if the vector has zero length.
    """
    mag = math.sqrt(dx * dx + dy * dy)
    if mag == 0:
        return 0.0, 0.0
    return dx / mag, dy / mag


def lerp(a, b, t):
    """Linear interpolation: returns a value between a and b at position t (0..1)."""
    return a + (b - a) * t


def lerp_point(p1, p2, t):
    """Linearly interpolate between two (x, y) points."""
    return (lerp(p1[0], p2[0], t), lerp(p1[1], p2[1], t))


def clamp(value, min_val, max_val):
    """Constrain value to the range [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def pixels_to_tile(px, py, tile_size):
    """Convert pixel coordinates to tile column/row indices."""
    return int(px // tile_size), int(py // tile_size)


def tile_to_pixels_center(col, row, tile_size):
    """Return the pixel coordinates of the centre of a tile."""
    return (col * tile_size + tile_size // 2,
            row * tile_size + tile_size // 2)
