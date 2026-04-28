"""
SkillsSession — lightweight container for an active skills competition event.

Stored as game.current_tournament during skills events so the three comp
states (LongDrive → CttP → PuttingChallenge) can share accumulated results.

Skills events give:
  • prize_per_win  × number of comps won (cash)
  • gain_reputation(5) per win
  • temp_stat_modifiers buff for each won comp (clears on next round start)
  • small season-standing points (participation + performance)
  • achievements: skills_long_drive / skills_cttp (if applicable)
"""

# Prize awarded per individual competition won, by tour level
SKILL_PRIZES: dict[int, int] = {
    1: 200, 2: 500, 3: 1_000, 4: 2_000, 5: 4_000, 6: 8_000,
}

# Season-standing points awarded after the skills event, by wins (0-3)
_SEASON_PTS: dict[int, int] = {0: 5, 1: 15, 2: 25, 3: 40}


class SkillsSession:
    """Container stored as game.current_tournament for a skills event."""

    # ── Compatibility stubs so code that checks game.current_tournament works ──
    event_type  = "skills"
    is_major    = False
    is_qschool  = False
    format      = "skills"
    is_opener   = False
    is_finale   = False

    def __init__(self, name: str, tour_level: int,
                 event_number: int, total_events: int):
        self.name         = name
        self.tour_level   = tour_level
        self.event_number = event_number
        self.total_events = total_events
        self.prize_per_win = SKILL_PRIZES.get(tour_level, 500)
        self.skills_result: dict = {
            "long_drive": None,   # {"dist_yards": float, "won": bool}
            "cttp":       None,   # {"dist_yards": float, "won": bool}
            "putting":    None,   # {"score": int, "opp_best": int, "won": bool}
            "total_wins": 0,
        }

    def record(self, key: str, result: dict) -> None:
        """Store one competition result and accumulate total wins."""
        self.skills_result[key] = result
        if result.get("won", False):
            self.skills_result["total_wins"] += 1

    def is_complete(self) -> bool:
        return self.skills_result["putting"] is not None

    def finalise(self, player) -> dict:
        """Apply all rewards to the player. Returns summary dict."""
        wins = self.skills_result["total_wins"]

        # Cash
        total_prize = self.prize_per_win * wins
        player.earn_money(total_prize)
        player.total_earnings += total_prize

        # Season-standing points (skills count as played event)
        pts = _SEASON_PTS.get(wins, 5)
        player.season_points += pts

        # Reputation
        if wins > 0:
            player.gain_reputation(wins * 5)

        # Temp stat buffs for won comps (cleared at start of next round)
        if self.skills_result.get("long_drive", {}) and \
                self.skills_result["long_drive"].get("won"):
            player.temp_stat_modifiers["power"] = (
                player.temp_stat_modifiers.get("power", 0) + 2)

        if self.skills_result.get("cttp", {}) and \
                self.skills_result["cttp"].get("won"):
            player.temp_stat_modifiers["short_game"] = (
                player.temp_stat_modifiers.get("short_game", 0) + 2)

        if self.skills_result.get("putting", {}) and \
                self.skills_result["putting"].get("won"):
            player.temp_stat_modifiers["putting"] = (
                player.temp_stat_modifiers.get("putting", 0) + 2)

        # Event counter
        player.events_this_season += 1

        # Sponsor "played" progress
        if player.active_sponsor:
            t_type = player.active_sponsor["target"]["type"]
            if t_type == "played":
                player.sponsor_progress[t_type] = (
                    player.sponsor_progress.get(t_type, 0) + 1)

        # Staff salaries
        try:
            from src.career.staff import STAFF_TYPES
            for sid in player.hired_staff:
                salary = STAFF_TYPES.get(sid, {}).get("salary", 0)
                player.spend_money(salary)
        except Exception:
            pass

        # Achievements
        if self.skills_result.get("long_drive", {}) and \
                self.skills_result["long_drive"].get("won"):
            player.unlock_achievement("skills_long_drive")
        if self.skills_result.get("cttp", {}) and \
                self.skills_result["cttp"].get("won"):
            player.unlock_achievement("skills_cttp")
        player._check_achievements()

        # Autosave
        try:
            from src.utils.save_system import save_game
            save_game(player)
        except Exception:
            pass

        return {"wins": wins, "prize": total_prize, "points": pts}
