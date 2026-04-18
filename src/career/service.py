"""
CareerService — thin coordinator for career-state transitions.

States used to call `game.player.apply_tournament_result(...)` and
`save_game(...)` directly, which made it hard to add logging, validation,
or alternative persistence paths without touching every call site. This
service centralises those transitions so there is one place to instrument.

It is deliberately small: it owns no state, just wraps calls to the Player
and save system and returns whatever the underlying methods returned.
"""

from __future__ import annotations


class CareerService:
    """Per-game coordinator for career transitions (round end, season end)."""

    def __init__(self, game):
        self.game = game

    @property
    def player(self):
        return self.game.player

    # ── Round lifecycle ────────────────────────────────────────────────────────

    def record_round(self, course, scores: list[int]) -> dict | None:
        """Record a completed round against the active tournament (if any).

        - Appends `scores` to `current_tournament.player_rounds`.
        - If the tournament just completed, applies its result to the player.
        - Logs the round in the player's career log.
        - Autosaves. The tournament is dropped from the save when complete so
          the next load starts cleanly at the Career Hub.

        Returns the dict produced by `Player.apply_tournament_result` when
        the tournament just completed, or None otherwise.
        """
        tournament = self.game.current_tournament
        player     = self.player

        result: dict | None = None
        if tournament is not None:
            tournament.record_player_round(scores)
            if tournament.is_complete() and player is not None:
                result = player.apply_tournament_result(tournament)

        if player is not None:
            player.log_round(course.name, sum(scores), course.par)
            self._autosave()

        return result

    # ── Persistence ────────────────────────────────────────────────────────────

    def _autosave(self) -> None:
        """Save the player and any still-active tournament. Never raises."""
        player     = self.player
        tournament = self.game.current_tournament
        if player is None:
            return
        persist_tournament = (
            tournament if not (tournament and tournament.is_complete())
            else None)
        try:
            from src.utils.save_system import save_game
            save_game(player, persist_tournament)
        except Exception as e:
            print(f"Auto-save failed: {e}")
