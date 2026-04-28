"""
narrative_handler.py — applies the effect of a narrative event choice.

All mutations go through apply_effect() so they stay in one place.
Temporary stat modifiers are stored in player.temp_stat_modifiers and
consumed at the start of each GolfRoundState (reset to {} there).
"""

from __future__ import annotations
import random


def apply_effect(player, effect_key: str) -> str:
    """Mutate *player* according to *effect_key*.

    Returns a short confirmation string suitable for a flash message.
    """
    fn = _EFFECTS.get(effect_key)
    if fn is None:
        return ""
    return fn(player) or ""


# ── Effect implementations ────────────────────────────────────────────────────

def _none(player):
    return ""


def _accept_best_available_sponsor(player):
    if player.active_sponsor is not None:
        return "Already have a sponsor."
    from src.career.sponsorship import get_available_sponsors
    deals = get_available_sponsors(player.tour_level, player.reputation)
    if not deals:
        return "No sponsor deals available right now."
    best = max(deals, key=lambda d: d["season_bonus"])
    player.accept_sponsor(best)
    return f"Signed with {best['name']}! +${best['signing_fee']:,} signing fee."


def _reputation_boost(player):
    player.gain_reputation(5)
    return "Reputation +5"


def _fitness_temp_minus_5(player):
    player.temp_stat_modifiers["fitness"] = (
        player.temp_stat_modifiers.get("fitness", 0) - 5)
    return "Fitness -5 for this event."


def _skip_event(player):
    # Advance events_this_season by 1 to simulate skipping the next event.
    from src.career.tournament import EVENTS_PER_SEASON
    total = EVENTS_PER_SEASON.get(player.tour_level, 8)
    if player.events_this_season < total - 1:
        player.events_this_season += 1
    return "Rested — next event skipped."


def _earn_200_reputation(player):
    player.earn_money(200)
    player.gain_reputation(5)
    return "+$200 and Reputation +5"


def _mental_temp_plus_2(player):
    player.temp_stat_modifiers["mental"] = (
        player.temp_stat_modifiers.get("mental", 0) + 2)
    return "Mental +2 for this event."


def _reputation_5(player):
    player.gain_reputation(5)
    return "Reputation +5"


def _equip_prototype_driver(player):
    max_dist = random.randint(245, 285)
    accuracy = round(random.uniform(0.62, 0.74), 2)
    player.prototype_club = {
        "name":                "Prototype Driver",
        "max_distance_yards":  max_dist,
        "accuracy":            accuracy,
        "can_shape":           True,
        "is_prototype":        True,
        "prototype_uses":      0,
    }
    goal = getattr(player, "prototype_uses_goal", 5)
    return (f"Prototype Driver: {max_dist} yds, {accuracy:.0%} acc. "
            f"Use it {goal}x and finish top 10 to unlock Accuracy +1 permanently!")


def _set_slump_objective(player):
    player.slump_objective = {"type": "win", "target": 2, "progress": 0}
    return "Season objective set: win the next 2 events."


_EFFECTS = {
    "none":                          _none,
    "accept_best_available_sponsor": _accept_best_available_sponsor,
    "reputation_boost":              _reputation_boost,
    "fitness_temp_minus_5":          _fitness_temp_minus_5,
    "skip_event":                    _skip_event,
    "earn_200_reputation":           _earn_200_reputation,
    "mental_temp_plus_2":            _mental_temp_plus_2,
    "reputation_5":                  _reputation_5,
    "equip_prototype_driver":        _equip_prototype_driver,
    "set_slump_objective":           _set_slump_objective,
}
