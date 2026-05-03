"""
Season schedule templates — one entry per event slot per tour level.

Each entry dict:
  event_number : 1-based position in the season
  event_type   : "regular" | "proam" | "stableford" | "skins" | "matchplay"
                 | "championship" | "major"
  format       : Tournament format string matching FORMAT_* constants
  is_opener    : True for event 1 of the season
  is_finale    : True for the season-closing championship / Grand Classic
  is_major     : True only on Tour 6 major slots
  major_id     : major_id string for Tour 6 major slots, else None
"""

from src.career.majors import GRAND_TOUR_MAJOR_SCHEDULE


def _e(n, typ, fmt, opener=False, finale=False, major=False, mid=None):
    return {
        "event_number": n,
        "event_type":   typ,
        "format":       fmt,
        "is_opener":    opener,
        "is_finale":    finale,
        "is_major":     major,
        "major_id":     mid,
    }


SCHEDULE_TEMPLATES: dict[int, list[dict]] = {
    # ── Tour 1 — Amateur Circuit (8 events) ──────────────────────────────
    1: [
        _e(1,  "proam",        "proam",       opener=True),
        _e(2,  "regular",      "stroke"),
        _e(3,  "stableford",   "stableford"),
        _e(4,  "regular",      "stroke"),
        _e(5,  "regular",      "stroke"),
        _e(6,  "regular",      "stroke"),
        _e(7,  "regular",      "stroke"),
        _e(8,  "championship", "stroke",      finale=True),
    ],
    # ── Tour 2 — Challenger Tour (10 events) ─────────────────────────────
    2: [
        _e(1,  "proam",        "proam",       opener=True),
        _e(2,  "regular",      "stroke"),
        _e(3,  "stableford",   "stableford"),
        _e(4,  "regular",      "stroke"),
        _e(5,  "matchplay",    "match"),
        _e(6,  "regular",      "stroke"),
        _e(7,  "regular",      "stroke"),
        _e(8,  "skins",        "skins"),
        _e(9,  "regular",      "stroke"),
        _e(10, "championship", "stroke",      finale=True),
    ],
    # ── Tour 3 — Development Tour (13 events) ────────────────────────────
    3: [
        _e(1,  "proam",        "proam",       opener=True),
        _e(2,  "regular",      "stroke"),
        _e(3,  "stableford",   "stableford"),
        _e(4,  "regular",      "stroke"),
        _e(5,  "matchplay",    "match"),
        _e(6,  "regular",      "stroke"),
        _e(7,  "skills",       "skills"),
        _e(8,  "regular",      "stroke"),
        _e(9,  "skins",        "skins"),
        _e(10, "regular",      "stroke"),
        _e(11, "stableford",   "stableford"),
        _e(12, "regular",      "stroke"),
        _e(13, "championship", "stroke",      finale=True),
    ],
    # ── Tour 4 — Continental Tour (15 events) ────────────────────────────
    4: [
        _e(1,  "proam",        "proam",       opener=True),
        _e(2,  "regular",      "stroke"),
        _e(3,  "stableford",   "stableford"),
        _e(4,  "regular",      "stroke"),
        _e(5,  "matchplay",    "match"),
        _e(6,  "regular",      "stroke"),
        _e(7,  "regular",      "stroke"),
        _e(8,  "skills",       "skills"),
        _e(9,  "skins",        "skins"),
        _e(10, "regular",      "stroke"),
        _e(11, "stableford",   "stableford"),
        _e(12, "regular",      "stroke"),
        _e(13, "matchplay",    "match"),
        _e(14, "regular",      "stroke"),
        _e(15, "championship", "stroke",      finale=True),
    ],
    # ── Tour 5 — World Tour (17 events) ──────────────────────────────────
    5: [
        _e(1,  "proam",        "proam",       opener=True),
        _e(2,  "regular",      "stroke"),
        _e(3,  "stableford",   "stableford"),
        _e(4,  "regular",      "stroke"),
        _e(5,  "matchplay",    "match"),
        _e(6,  "regular",      "stroke"),
        _e(7,  "regular",      "stroke"),
        _e(8,  "skins",        "skins"),
        _e(9,  "skills",       "skills"),
        _e(10, "regular",      "stroke"),
        _e(11, "stableford",   "stableford"),
        _e(12, "matchplay",    "match"),
        _e(13, "regular",      "stroke"),
        _e(14, "regular",      "stroke"),
        _e(15, "skins",        "skins"),
        _e(16, "regular",      "stroke"),
        _e(17, "championship", "stroke",      finale=True),
    ],
}


def _build_tour6_schedule() -> list[dict]:
    """Tour 6 — The Grand Tour (22 events). Skills then Major at slots 3-4, 9-10, 15-16, 21-22."""
    # majors at event numbers 4, 10, 16, 22; skills events at 3, 9, 15, 21
    _T6_MAJORS  = {4: "green_jacket", 10: "heritage_open",
                   16: "royal_championship", 22: "grand_classic"}
    _T6_SKILLS  = {3, 9, 15, 21}
    events = []
    for n in range(1, 23):
        mid = _T6_MAJORS.get(n)
        if mid:
            events.append(_e(n, "major", "stroke",
                             finale=(n == 22), major=True, mid=mid))
        elif n in _T6_SKILLS:
            events.append(_e(n, "skills", "skills"))
        elif n == 1:
            events.append(_e(1, "proam", "proam", opener=True))
        else:
            events.append(_e(n, "regular", "stroke"))
    return events


SCHEDULE_TEMPLATES[6] = _build_tour6_schedule()


def generate_season_schedule(tour_level: int, season: int) -> list[dict]:
    """Return a fresh copy of the event list for this tour level."""
    import copy
    template = SCHEDULE_TEMPLATES.get(tour_level)
    if not template:
        total = {1: 8, 2: 10, 3: 12, 4: 14, 5: 16, 6: 18}.get(tour_level, 8)
        return [_e(n, "regular", "stroke") for n in range(1, total + 1)]
    return copy.deepcopy(template)
