"""
save_system.py — JSON save/load for the player's career.

Save files live in  saves/<player_name>.json  (auto-created).
"""

import json
import os
import re

from src.career.player import Player

SAVE_DIR    = "saves"
SAVE_FORMAT = 1


def _safe_filename(name: str) -> str:
    """Convert a player name to a safe filename (strip non-alphanumeric)."""
    safe = re.sub(r"[^\w\s-]", "", name).strip()
    safe = re.sub(r"\s+", "_", safe)
    return safe or "player"


def save_path_for(player_name: str) -> str:
    return os.path.join(SAVE_DIR, f"{_safe_filename(player_name)}.json")


def save_game(player: Player, tournament=None) -> str:
    """Serialise the player (and optional active tournament) to JSON."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    path = save_path_for(player.name)
    data = {
        "save_format": SAVE_FORMAT,
        "player":      player.to_dict(),
        "tournament":  tournament.to_dict() if tournament is not None else None,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def load_game(path: str):
    """Load a save file; returns (Player, tournament_dict_or_None)."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    player = Player.from_dict(data["player"])
    return player, data.get("tournament")


def list_saves() -> list[str]:
    """Return all .json paths in SAVE_DIR, newest first."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    paths = [
        os.path.join(SAVE_DIR, f)
        for f in os.listdir(SAVE_DIR)
        if f.endswith(".json")
    ]
    paths.sort(key=os.path.getmtime, reverse=True)
    return paths


def get_save_preview(path: str) -> dict:
    """Return a lightweight summary dict for displaying on the load screen."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        p = data.get("player", {})
        log = p.get("career_log", [])
        return {
            "name":          p.get("name", "Unknown"),
            "nationality":   p.get("nationality", ""),
            "tour_level":    p.get("tour_level", 1),
            "events_played": p.get("events_played", 0),
            "money":         p.get("money", 0),
            "last_round":    log[-1] if log else None,
            "path":          path,
        }
    except Exception:
        return {"name": os.path.basename(path), "path": path}
