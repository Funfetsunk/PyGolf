"""
Club definitions — starter bag plus five upgrade tiers.

Each set improves distance and accuracy.  Players buy sets via the Career Hub.
"""


class Club:
    def __init__(self, name, max_distance_yards, accuracy, can_shape=True,
                 is_prototype=False, prototype_uses=0):
        self.name = name
        self.max_distance_yards = max_distance_yards
        self.accuracy = accuracy
        self.can_shape = can_shape
        self.is_prototype = is_prototype
        self.prototype_uses = prototype_uses

    def __repr__(self):
        return f"Club({self.name}, {self.max_distance_yards}yds, acc={self.accuracy:.2f})"


# ── Bag definitions ───────────────────────────────────────────────────────────
# Each entry: (name, dist, base_acc, can_shape)
_BAGS_RAW = {
    "starter": [
        ("Driver",         250, 0.56, True),
        ("3-Wood",         220, 0.60, True),
        ("5-Iron",         175, 0.66, True),
        ("7-Iron",         155, 0.70, True),
        ("9-Iron",         135, 0.74, True),
        ("Pitching Wedge", 110, 0.80, False),
        ("Sand Wedge",      90, 0.74, False),
        ("Putter",          55, 0.92, False),
    ],
    "mid_range": [
        ("Driver",         265, 0.59, True),
        ("3-Wood",         235, 0.63, True),
        ("5-Iron",         185, 0.69, True),
        ("7-Iron",         165, 0.73, True),
        ("9-Iron",         145, 0.77, True),
        ("Pitching Wedge", 120, 0.83, False),
        ("Sand Wedge",     100, 0.77, False),
        ("Putter",          55, 0.92, False),
    ],
    "pro": [
        ("Driver",         278, 0.62, True),
        ("3-Wood",         248, 0.66, True),
        ("5-Iron",         196, 0.72, True),
        ("7-Iron",         175, 0.76, True),
        ("9-Iron",         154, 0.80, True),
        ("Pitching Wedge", 129, 0.86, False),
        ("Sand Wedge",     109, 0.80, False),
        ("Putter",          55, 0.92, False),
    ],
    "tournament": [
        ("Driver",         288, 0.65, True),
        ("3-Wood",         258, 0.69, True),
        ("5-Iron",         204, 0.75, True),
        ("7-Iron",         182, 0.79, True),
        ("9-Iron",         161, 0.83, True),
        ("Pitching Wedge", 136, 0.89, False),
        ("Sand Wedge",     116, 0.83, False),
        ("Putter",          55, 0.93, False),
    ],
    "elite": [
        ("Driver",         298, 0.68, True),
        ("3-Wood",         268, 0.72, True),
        ("5-Iron",         212, 0.78, True),
        ("7-Iron",         189, 0.82, True),
        ("9-Iron",         168, 0.86, True),
        ("Pitching Wedge", 143, 0.91, False),
        ("Sand Wedge",     123, 0.86, False),
        ("Putter",          55, 0.94, False),
    ],
    "professional": [
        ("Driver",         308, 0.71, True),
        ("3-Wood",         278, 0.75, True),
        ("5-Iron",         220, 0.81, True),
        ("7-Iron",         196, 0.85, True),
        ("9-Iron",         175, 0.89, True),
        ("Pitching Wedge", 150, 0.93, False),
        ("Sand Wedge",     130, 0.89, False),
        ("Putter",          55, 0.95, False),
    ],
}

STARTER_BAG = [Club(n, d, a, s) for n, d, a, s in _BAGS_RAW["starter"]]

# ── Set metadata ──────────────────────────────────────────────────────────────
CLUB_SET_ORDER = [
    "starter", "mid_range", "pro", "tournament", "elite", "professional"
]

CLUB_SETS = {
    "starter":      {"label": "Starter Set",        "cost": 0,        "min_tour": 1},
    "mid_range":    {"label": "Mid-Range Set",       "cost": 2_000,    "min_tour": 2},
    "pro":          {"label": "Pro Set",             "cost": 8_000,    "min_tour": 3},
    "tournament":   {"label": "Tournament Set",      "cost": 25_000,   "min_tour": 4},
    "elite":        {"label": "Elite Set",           "cost": 80_000,   "min_tour": 5},
    "professional": {"label": "Professional Set",    "cost": 200_000,  "min_tour": 6},
}


def get_club_bag(set_name: str) -> list:
    """Return a list of Club objects for the given set name."""
    raw = _BAGS_RAW.get(set_name, _BAGS_RAW["starter"])
    return [Club(n, d, a, s) for n, d, a, s in raw]
