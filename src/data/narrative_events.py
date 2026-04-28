"""
narrative_events.py — one-time story events and season arcs.

NARRATIVE_EVENTS: list of dicts, each with a trigger lambda (player → bool),
title, body text, and two choices (label + effect key).  The effect keys are
handled by NarrativeHandler.apply_effect().

SEASON_ARCS: keyed by (tour_level, relative_season_on_that_tour).  A generic
fallback covers any key that isn't explicitly listed.
"""

import random

# ── One-time career events ────────────────────────────────────────────────────

NARRATIVE_EVENTS = [
    {
        "id": "first_sponsor_offer",
        "trigger": lambda p: (p.career_wins >= 1
                              and p.active_sponsor is None
                              and p.tour_level >= 2),
        "title": "Sponsor Interest",
        "body": (
            "A mid-tier equipment brand has noticed your results.\n"
            "They want to offer you a deal."
        ),
        "choice_a": {"label": "Sign the deal",       "effect": "accept_best_available_sponsor"},
        "choice_b": {"label": "Hold out for better", "effect": "reputation_boost"},
    },
    {
        "id": "back_injury",
        "trigger": lambda p: (p.events_played >= 10
                              and random.random() < 0.15),
        "title": "Practice Injury",
        "body": (
            "You tweaked your back in practice.\n"
            "Play through it or take a rest week?"
        ),
        "choice_a": {"label": "Play through (Fitness -5 this event)", "effect": "fitness_temp_minus_5"},
        "choice_b": {"label": "Rest (skip next event)",               "effect": "skip_event"},
    },
    {
        "id": "mentor_request",
        "trigger": lambda p: (p.tour_level >= 3
                              and p.career_wins >= 2),
        "title": "Young Golfer",
        "body": "A junior golfer asks to shadow you for the week.",
        "choice_a": {"label": "Mentor them ($200 + reputation boost)", "effect": "earn_200_reputation"},
        "choice_b": {"label": "Decline",                               "effect": "none"},
    },
    {
        "id": "rival_press",
        "trigger": lambda p: (p.rival_name is not None
                              and p.tour_level >= 2),
        "title": "Media Question",
        "body": "A reporter asks about your rivalry. How do you respond?",
        "choice_a": {"label": "Respond confidently (Mental +2 this event)", "effect": "mental_temp_plus_2"},
        "choice_b": {"label": "Stay humble (Reputation +5)",                "effect": "reputation_5"},
    },
    {
        "id": "prototype_club",
        "trigger": lambda p: (p.tour_level >= 3
                              and p.club_set_name in (
                                  "semi-pro", "pro", "tour", "tour_elite")),
        "title": "Prototype Driver",
        "body": (
            "An equipment rep wants you to test an unreleased driver.\n"
            "Stats unknown until you use it."
        ),
        "choice_a": {"label": "Try it (randomised driver stats)",   "effect": "equip_prototype_driver"},
        "choice_b": {"label": "Stick with your current bag",        "effect": "none"},
    },
    {
        "id": "slump_motivator",
        "trigger": lambda p: (len(p.career_log) >= 3
                              and all(r["diff"] > 3 for r in p.career_log[-3:])),
        "title": "Media Write-Off",
        "body": (
            "The press is questioning your form.\n"
            "Three events over +3. Respond on the course."
        ),
        "choice_a": {"label": "Acknowledge (season objective: win next 2)", "effect": "set_slump_objective"},
        "choice_b": {"label": "Ignore it",                                  "effect": "none"},
    },
    {
        "id": "charity_proam_invite",
        "trigger": lambda p: p.reputation >= 40,
        "title": "Charity Pro-Am Invite",
        "body": (
            "You've been invited to a charity pro-am alongside Hall of Fame legends.\n"
            "Play alongside history."
        ),
        "choice_a": {"label": "Accept (Reputation +5)", "effect": "reputation_5"},
        "choice_b": {"label": "Decline",                "effect": "none"},
    },
]


# ── Season arcs ───────────────────────────────────────────────────────────────

SEASON_ARCS: dict[tuple, dict] = {
    (1, 1): {
        "title":        "The Rookie Year",
        "objective":    "Finish top 3 in season standings",
        "metric":       "season_position",
        "target":       3,
        "reward_money": 500,
    },
    (1, 2): {
        "title":        "The Sophomore Test",
        "objective":    "Win one event",
        "metric":       "season_wins",
        "target":       1,
        "reward_money": 750,
    },
    (2, 1): {
        "title":        "The Breakthrough",
        "objective":    "Win the Match Play Championship",
        "metric":       "matchplay_win",
        "target":       1,
        "reward_money": 1_000,
    },
    (2, 2): {
        "title":        "Challenger Dominant",
        "objective":    "Win 2 events this season",
        "metric":       "season_wins",
        "target":       2,
        "reward_money": 1_500,
    },
    (3, 1): {
        "title":        "Development Tour Rising Star",
        "objective":    "Finish top 5 in season standings",
        "metric":       "season_position",
        "target":       5,
        "reward_money": 2_000,
    },
    (4, 1): {
        "title":        "Going Continental",
        "objective":    "Win one event on the Continental Tour",
        "metric":       "season_wins",
        "target":       1,
        "reward_money": 5_000,
    },
    (5, 1): {
        "title":        "World Stage Debut",
        "objective":    "Finish inside the top 50 world ranking",
        "metric":       "world_rank",
        "target":       50,
        "reward_money": 10_000,
    },
    (6, 1): {
        "title":        "Grand Tour Contender",
        "objective":    "Win a Major championship",
        "metric":       "major_win",
        "target":       1,
        "reward_money": 25_000,
    },
    # TODO: arcs are only defined for season 1 of tours 3-6 and seasons 1-2 of
    # tours 1-2. Every other combination falls to _GENERIC_ARC ("Make Your Mark
    # — win 2 events"), which means long-stay players on tours 3-6 see the same
    # arc for years. Add per-tour season-2+ arcs when tour progression content
    # is fleshed out.
}

_GENERIC_ARC = {
    "title":        "Make Your Mark",
    "objective":    "Win 2 events this season",
    "metric":       "season_wins",
    "target":       2,
    "reward_money": 1_000,
}


def get_arc_id(tour_level: int, season: int) -> str | None:
    """Return the arc id string for (tour_level, season), or None for generic."""
    key = (tour_level, season)
    if key in SEASON_ARCS:
        return f"{tour_level}_{season}"
    return "generic"


def get_arc(arc_id: str | None) -> dict | None:
    """Return the arc dict for an arc_id, or the generic arc."""
    if arc_id is None:
        return None
    if arc_id == "generic":
        return _GENERIC_ARC
    try:
        parts = arc_id.split("_")
        key = (int(parts[0]), int(parts[1]))
        return SEASON_ARCS.get(key, _GENERIC_ARC)
    except Exception:
        return _GENERIC_ARC


def check_arc_complete(player, arc: dict) -> bool:
    """Return True if the player has met the arc objective."""
    metric = arc.get("metric", "")
    target = arc.get("target", 1)
    if metric == "season_wins":
        return player.career_wins >= target
    if metric == "season_position":
        # Not directly measurable here — handled in tour_standings
        return False
    if metric == "world_rank":
        return player.world_rank <= target
    if metric == "matchplay_win":
        return player.career_wins >= target
    if metric == "major_win":
        return len(player.majors_won) >= target
    return False
