"""
Club definitions — each club has a maximum distance, accuracy rating,
and whether it can be shaped (draw/fade).

Phase 1 uses a basic starter bag. Future phases will expand this with
purchasable club sets.
"""


class Club:
    """
    Represents a single golf club.

    Attributes
    ----------
    name              : display name shown in the HUD
    max_distance_yards: how far the ball travels at 100% power on a clean lie
    accuracy          : 0.0–1.0; higher means tighter shot dispersion
    can_shape         : whether draw/fade shaping can be applied
    """

    def __init__(self, name, max_distance_yards, accuracy, can_shape=True):
        self.name = name
        self.max_distance_yards = max_distance_yards
        self.accuracy = accuracy
        self.can_shape = can_shape

    def __repr__(self):
        return f"Club({self.name}, {self.max_distance_yards}yds, acc={self.accuracy})"


# ── Starter bag ───────────────────────────────────────────────────────────────
# Ordered from longest to shortest (as you'd see in a real bag).
# Index 0 = Driver is selected first.
STARTER_BAG = [
    Club("Driver",          250, accuracy=0.68, can_shape=True),
    Club("3-Wood",          220, accuracy=0.72, can_shape=True),
    Club("5-Iron",          175, accuracy=0.78, can_shape=True),
    Club("7-Iron",          155, accuracy=0.82, can_shape=True),
    Club("9-Iron",          135, accuracy=0.86, can_shape=True),
    Club("Pitching Wedge",  110, accuracy=0.90, can_shape=False),
    Club("Sand Wedge",       90, accuracy=0.86, can_shape=False),
    Club("Putter",           55, accuracy=0.96, can_shape=False),
]
