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
    # ── Tour 3 — Development Tour (12 events) ────────────────────────────
    3: [
        _e(1,  "proam",        "proam",       opener=True),
        _e(2,  "regular",      "stroke"),
        _e(3,  "stableford",   "stableford"),
        _e(4,  "regular",      "stroke"),
        _e(5,  "matchplay",    "match"),
        _e(6,  "regular",      "stroke"),
        _e(7,  "regular",      "stroke"),
        _e(8,  "skins",        "skins"),
        _e(9,  "regular",      "stroke"),
        _e(10, "stableford",   "stableford"),
        _e(11, "regular",      "stroke"),
        _e(12, "championship", "stroke",      finale=True),
    ],
    # ── Tour 4 — Continental Tour (14 events) ────────────────────────────
    4: [
        _e(1,  "proam",        "proam",       opener=True),
        _e(2,  "regular",      "stroke"),
        _e(3,  "stableford",   "stableford"),
        _e(4,  "regular",      "stroke"),
        _e(5,  "matchplay",    "match"),
        _e(6,  "regular",      "stroke"),
        _e(7,  "regular",      "stroke"),
        _e(8,  "skins",        "skins"),
        _e(9,  "regular",      "stroke"),
        _e(10, "stableford",   "stableford"),
        _e(11, "regular",      "stroke"),
        _e(12, "regular",      "stroke"),
        _e(13, "regular",      "stroke"),
        _e(14, "championship", "stroke",      finale=True),
    ],
    # ── Tour 5 — World Tour (16 events) ──────────────────────────────────
    5: [
        _e(1,  "proam",        "proam",       opener=True),
        _e(2,  "regular",      "stroke"),
        _e(3,  "stableford",   "stableford"),
        _e(4,  "regular",      "stroke"),
        _e(5,  "matchplay",    "match"),
        _e(6,  "regular",      "stroke"),
        _e(7,  "regular",      "stroke"),
        _e(8,  "skins",        "skins"),
        _e(9,  "regular",      "stroke"),
        _e(10, "stableford",   "stableford"),
        _e(11, "matchplay",    "match"),
        _e(12, "regular",      "stroke"),
        _e(13, "regular",      "stroke"),
        _e(14, "skins",        "skins"),
        _e(15, "regular",      "stroke"),
        _e(16, "championship", "stroke",      finale=True),
    ],
}


def _build_tour6_schedule() -> list[dict]:
    """Tour 6 — The Grand Tour (18 events). Majors at 4, 9, 14, 18."""
    events = []
    for n in range(1, 19):
        major_id = GRAND_TOUR_MAJOR_SCHEDULE.get(n)
        if major_id:
            events.append(_e(n, "major", "stroke",
                             finale=(n == 18), major=True, mid=major_id))
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
