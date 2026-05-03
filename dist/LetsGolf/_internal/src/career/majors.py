"""
majors.py — The 4 Major championship definitions.

Majors are held during the Grand Tour (Level 6) season at fixed event
positions.  They are 2-round events with elevated prize funds and award
double world ranking points.
"""

MAJORS: dict[str, dict] = {
    "green_jacket": {
        "name":        "The Green Jacket Invitational",
        "short_name":  "Green Jacket",
        "course_name": "The Augusta Classic",
        "prize_fund":  5_000_000,
    },
    "heritage_open": {
        "name":        "The Heritage Open",
        "short_name":  "Heritage Open",
        "course_name": "Heritage Links",
        "prize_fund":  4_500_000,
    },
    "royal_championship": {
        "name":        "The Royal Championship",
        "short_name":  "Royal Championship",
        "course_name": "Royal Open Links",
        "prize_fund":  4_500_000,
    },
    "grand_classic": {
        "name":        "The Grand Classic",
        "short_name":  "Grand Classic",
        "course_name": "Grand Classic GC",
        "prize_fund":  5_000_000,
    },
}

MAJOR_ORDER = ["green_jacket", "heritage_open", "royal_championship", "grand_classic"]

# Grand Tour season event-number (1-based) → major_id
# Season has 22 events; skills events precede each major; majors at 4, 10, 16, 22
GRAND_TOUR_MAJOR_SCHEDULE: dict[int, str] = {
    4:  "green_jacket",
    10: "heritage_open",
    16: "royal_championship",
    22: "grand_classic",
}


def is_major_event(tour_level: int, event_number: int) -> str | None:
    """Return major_id if this event is a major, else None."""
    if tour_level != 6:
        return None
    return GRAND_TOUR_MAJOR_SCHEDULE.get(event_number)


def get_major_course(major_id: str):
    """Return a Course object for the given major."""
    from src.data.courses_library import (
        make_augusta_classic, make_heritage_links,
        make_royal_open_links, make_grand_classic_gc,
    )
    _MAP = {
        "green_jacket":       make_augusta_classic,
        "heritage_open":      make_heritage_links,
        "royal_championship": make_royal_open_links,
        "grand_classic":      make_grand_classic_gc,
    }
    fn = _MAP.get(major_id)
    return fn() if fn else None
