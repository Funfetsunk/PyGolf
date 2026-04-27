"""
sponsorship.py — sponsor deal definitions and progress helpers.

One sponsor contract may be active at a time.  The signing fee is paid
immediately on acceptance; the season bonus is paid as soon as the
performance target is met (the contract then clears so the player can sign
another).  Any contract still active at season reset expires without
payout.
"""

# Target types:  "top10" | "top5" | "win" | "played"
SPONSORS: list[dict] = [
    {
        "id":              "hydromax",
        "name":            "HydroMax Sports",
        "signing_fee":      2_000,
        "season_bonus":     8_000,
        "target":          {"type": "top10", "count": 3},
        "min_tour":        2,
        "min_reputation":  0,
        "description":     "Finish top 10 in 3 events this season.",
    },
    {
        "id":              "iron_grip",
        "name":            "Iron Grip Gloves",
        "signing_fee":      1_500,
        "season_bonus":     6_000,
        "target":          {"type": "played", "count": 6},
        "min_tour":        1,
        "min_reputation":  0,
        "description":     "Play at least 6 events this season.",
    },
    {
        "id":              "eagle_apparel",
        "name":            "Eagle Apparel",
        "signing_fee":      5_000,
        "season_bonus":    20_000,
        "target":          {"type": "top5", "count": 3},
        "min_tour":        3,
        "min_reputation":  0,
        "description":     "Finish top 5 in 3 events this season.",
    },
    {
        "id":              "apex_drivers",
        "name":            "Apex Drivers Co.",
        "signing_fee":      8_000,
        "season_bonus":    40_000,
        "target":          {"type": "win", "count": 1},
        "min_tour":        3,
        "min_reputation":  20,
        "description":     "Win at least 1 event this season.",
    },
    {
        "id":              "prestige_watches",
        "name":            "Prestige Watches",
        "signing_fee":     15_000,
        "season_bonus":    80_000,
        "target":          {"type": "top5", "count": 5},
        "min_tour":        5,
        "min_reputation":  50,
        "description":     "Finish top 5 in 5 events this season.",
    },
    {
        "id":              "summit_energy",
        "name":            "Summit Energy",
        "signing_fee":     25_000,
        "season_bonus":   150_000,
        "target":          {"type": "win", "count": 2},
        "min_tour":        5,
        "min_reputation":  50,
        "description":     "Win 2 or more events this season.",
    },
]


def get_available_sponsors(tour_level: int, reputation: int = 0) -> list[dict]:
    """Return sponsors available for the given tour level and reputation."""
    return [s for s in SPONSORS
            if s["min_tour"] <= tour_level
            and s.get("min_reputation", 0) <= reputation]


def is_target_met(contract: dict, progress: dict) -> bool:
    """Check whether the season target in a contract has been achieved."""
    target = contract["target"]
    return progress.get(target["type"], 0) >= target["count"]


def progress_label(contract: dict, progress: dict) -> str:
    """Human-readable progress string, e.g. '2 / 3 top-10 finishes'."""
    target = contract["target"]
    t_type = target["type"]
    count  = target["count"]
    done   = progress.get(t_type, 0)
    labels = {
        "top10":  "top-10 finish",
        "top5":   "top-5 finish",
        "win":    "win",
        "played": "event played",
    }
    noun = labels.get(t_type, t_type)
    if count > 1:
        noun += "es" if noun.endswith("finish") else "s"
    return f"{done} / {count} {noun}"
