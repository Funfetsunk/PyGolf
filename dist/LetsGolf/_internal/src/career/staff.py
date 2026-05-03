"""
staff.py — staff member definitions for the career progression system.

Staff unlock at Tour Level 4 (Continental Tour).  Each hire costs a one-time
fee and a per-event salary deducted after every tournament.

Caddie variants are mutually exclusive — only one caddie may be hired at a time.
Each caddie has a personality that drives pre-shot tip text in GolfRoundState.
"""

# staff_id → config dict
STAFF_TYPES: dict[str, dict] = {
    "coach": {
        "label":       "Golf Coach",
        "description": "Improves accuracy and overall ball-striking.",
        "hire_cost":   15_000,
        "salary":      500,
        "min_tour":    4,
        "bonuses":     {"accuracy": 3},
    },
    "caddie_budget": {
        "label":       "Budget Caddie",
        "description": "Solid reads at a reasonable price.",
        "hire_cost":   4_000,
        "salary":      150,
        "min_tour":    4,
        "bonuses":     {"short_game": 1, "putting": 1},
        "personality": "blunt",
    },
    "caddie": {
        "label":       "Tour Caddie",
        "description": "Reads greens and courses; improves short game and putting.",
        "hire_cost":   8_000,
        "salary":      300,
        "min_tour":    4,
        "bonuses":     {"short_game": 2, "putting": 2},
        "personality": "tactical",
    },
    "caddie_elite": {
        "label":       "Elite Caddie",
        "description": "World-class course management; maximises confidence.",
        "hire_cost":   15_000,
        "salary":      500,
        "min_tour":    4,
        "bonuses":     {"short_game": 3, "putting": 3},
        "personality": "optimistic",
    },
    "psychologist": {
        "label":       "Sports Psychologist",
        "description": "Keeps you composed under pressure; improves mental game.",
        "hire_cost":   12_000,
        "salary":      400,
        "min_tour":    4,
        "bonuses":     {"mental": 3},
    },
    "trainer": {
        "label":       "Fitness Trainer",
        "description": "Peak physical condition; boosts power and fitness.",
        "hire_cost":   10_000,
        "salary":      350,
        "min_tour":    4,
        "bonuses":     {"fitness": 3, "power": 2},
    },
}

# Caddie variants are mutually exclusive — firing any existing caddie on hire.
CADDIE_IDS: frozenset[str] = frozenset({"caddie_budget", "caddie", "caddie_elite"})

STAFF_ORDER = ["coach", "caddie_budget", "caddie", "caddie_elite",
               "psychologist", "trainer"]


def get_total_salary(hired: list[str]) -> int:
    """Return total per-event salary for a list of staff IDs."""
    return sum(STAFF_TYPES[sid]["salary"] for sid in hired if sid in STAFF_TYPES)
