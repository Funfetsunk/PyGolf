"""
tour.py — static tour configuration helpers.
"""

from src.career.tournament import (
    EVENTS_PER_SEASON, PROMOTION_THRESHOLD, PRIZE_FUNDS, TOUR_DISPLAY_NAMES
)

TOUR_IDS = ["amateur", "challenger", "development", "continental", "world", "grand"]

# level (1-6) → tour_id
_LEVEL_TO_ID = {i + 1: tid for i, tid in enumerate(TOUR_IDS)}
_ID_TO_LEVEL = {tid: i + 1 for i, tid in enumerate(TOUR_IDS)}


def get_tour_id(level: int) -> str:
    return _LEVEL_TO_ID.get(level, "amateur")


def get_tour_level(tour_id: str) -> int:
    return _ID_TO_LEVEL.get(tour_id, 1)


def get_config(level: int) -> dict:
    """Return a config dict for a tour level."""
    tour_id = get_tour_id(level)
    return {
        "level":       level,
        "tour_id":     tour_id,
        "name":        TOUR_DISPLAY_NAMES.get(level, "Tour"),
        "events":      EVENTS_PER_SEASON.get(level, 8),
        "promotion":   PROMOTION_THRESHOLD.get(level),
        "prize_fund":  PRIZE_FUNDS.get(level, 0),
    }
