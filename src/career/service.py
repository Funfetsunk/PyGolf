"""
CareerService — thin coordinator for career-state transitions.

States used to call `game.player.apply_tournament_result(...)` and
`save_game(...)` directly, which made it hard to add logging, validation,
or alternative persistence paths without touching every call site. This
service centralises those transitions so there is one place to instrument.

It also owns the tournament-result processor so Player no longer has to
do deferred imports of `rankings` / `staff` / `majors` from inside its own
methods to dodge a circular import. Player.apply_tournament_result is a
thin wrapper over process_tournament_result().
"""

from __future__ import annotations

from src.career.rankings    import get_ranking_points, compute_world_rank
from src.career.staff        import STAFF_TYPES
from src.career.sponsorship  import is_target_met


def process_tournament_result(player, tournament) -> dict:
    """Apply a completed tournament's result to `player` and return a
    summary dict {position, prize, points}.

    Extracted from Player.apply_tournament_result so the cross-cutting
    imports (rankings, staff) can live at module scope here instead of
    being deferred into a method on Player to avoid circular imports.
    """
    position   = tournament.get_player_position()
    prize      = tournament.get_prize_money(position)
    pts        = tournament.get_season_points(position)
    is_qschool = getattr(tournament, "is_qschool", False)

    player.earn_money(prize)
    player.total_earnings     += prize
    player.events_this_season += 1

    if not is_qschool:
        player.season_points += pts

        if position == 1:
            player.career_wins += 1
        if position <= 5:
            player.career_top5 += 1
        if position <= 10:
            player.career_top10 += 1

        if position == 1 and tournament.is_major:
            major_id = getattr(tournament, "major_id", None)
            if major_id and major_id not in player.majors_won:
                player.majors_won.append(major_id)

        # Phase 6 — wins_per_tour
        if position == 1:
            tl = player.tour_level
            player.wins_per_tour[tl] = player.wins_per_tour.get(tl, 0) + 1

        # Track opponent season points (not applicable for match play — field
        # doesn't have stroke-play totals; skip to avoid misleading standings).
        fmt = getattr(tournament, "format", "stroke")
        lb  = None
        if fmt != "match":
            lb = tournament.get_leaderboard()
            for pos, entry in enumerate(lb, start=1):
                if not entry["is_player"]:
                    name = entry["name"]
                    opp_pts = tournament.get_season_points(pos)
                    player.opp_season_points[name] = (
                        player.opp_season_points.get(name, 0) + opp_pts)

    # World ranking points (Tour 4+). Q-school earns a small boost too.
    rp = get_ranking_points(player.tour_level, position, tournament.is_major)
    player.world_ranking_points += rp
    player.world_rank = compute_world_rank(player.world_ranking_points)
    peak = getattr(player, "world_rank_peak", 201)
    if player.world_rank < peak:
        player.world_rank_peak = player.world_rank

    # Sponsor target progress. If the target is met, pay the season bonus
    # immediately and clear the contract — waiting for season end left players
    # unable to collect once the target was visibly achieved (issue #5).
    sponsor_bonus = 0
    if player.active_sponsor and not is_qschool:
        t_type = player.active_sponsor["target"]["type"]
        inc = False
        if t_type == "win"    and position == 1:  inc = True
        if t_type == "top5"   and position <= 5:  inc = True
        if t_type == "top10"  and position <= 10: inc = True
        if t_type == "played":                    inc = True
        if inc:
            player.sponsor_progress[t_type] = (
                player.sponsor_progress.get(t_type, 0) + 1)
        if is_target_met(player.active_sponsor, player.sponsor_progress):
            sponsor_bonus = player.active_sponsor["season_bonus"]
            player.earn_money(sponsor_bonus)
            player.total_earnings += sponsor_bonus
            player.active_sponsor   = None
            player.sponsor_progress = {}

    # Deduct staff salaries
    for sid in player.hired_staff:
        salary = STAFF_TYPES.get(sid, {}).get("salary", 0)
        player.spend_money(salary)

    # Phase 4 — Tour Championship winner gets a promotion wildcard
    if (getattr(tournament, "is_finale", False) and position == 1
            and not is_qschool):
        tournament.promotion_wildcard = True

    # Phase 5 — rival tracker
    if not is_qschool:
        if fmt == "match":
            # check_rival uses vs_par from a stroke leaderboard, which is
            # meaningless in match play — skip it.
            # update_head_to_head: use the bracket result instead of stroke
            # positions. When the player won, advance_bracket() already ran so
            # match_opponent is None; recover the final opponent via match_round.
            if player.rival_name:
                try:
                    bracket = getattr(tournament, "bracket", [])
                    idx = (tournament.match_round - 1 if position == 1
                           else tournament.match_round)
                    match_opp = bracket[idx] if 0 <= idx < len(bracket) else None
                    if match_opp == player.rival_name:
                        h2h = player.rival_head_to_head
                        if position == 1:
                            h2h["wins"]   = h2h.get("wins",   0) + 1
                        else:
                            h2h["losses"] = h2h.get("losses", 0) + 1
                except Exception as e:
                    print(f"[career] match play H2H update error: {e}")
        else:
            if lb is None:
                try:
                    lb = tournament.get_leaderboard()
                except Exception as e:
                    print(f"[career] leaderboard unavailable for rival check: {e}")
                    lb = []
            try:
                player.check_rival(lb)
                player.update_head_to_head(lb)
            except Exception as e:
                print(f"[career] rival tracker error: {e}")

    # Phase 5 — reputation gains
    if not is_qschool and position == 1:
        if getattr(tournament, "is_major", False):
            player.gain_reputation(15)
        elif fmt == "match":
            player.gain_reputation(8)
        else:
            player.gain_reputation(5)

    # Phase 6 — format wins and special condition achievements
    if not is_qschool and position == 1:
        if fmt == "match":
            player.unlock_achievement("win_match_play")
        elif fmt == "skins":
            player.unlock_achievement("win_skins")
        elif fmt == "stableford":
            player.unlock_achievement("win_stableford")

        # rain_win
        if getattr(tournament, "weather", None) == "rain":
            player.unlock_achievement("rain_win")

        # comeback_win — player was 5+ strokes behind leader after round 1
        # Only reachable in multi-round events (majors); single-round events have len(p_rounds) < 2.
        try:
            p_rounds = getattr(tournament, "player_rounds", [])
            opp_holes = getattr(tournament, "_opp_holes", {})
            if len(p_rounds) >= 2 and opp_holes:
                p_r1 = sum(p_rounds[0])
                best_opp_r1 = min(sum(v[0]) for v in opp_holes.values() if v)
                if p_r1 - best_opp_r1 >= 5:
                    player.unlock_achievement("comeback_win")
        except Exception as e:
            print(f"[career] comeback_win check error: {e}")

        # beat_rival_major
        if getattr(tournament, "is_major", False) and player.rival_name:
            try:
                if lb is None:
                    lb = tournament.get_leaderboard()
                rival_entry  = next((e for e in lb
                                     if e.get("name") == player.rival_name), None)
                if rival_entry is not None:
                    rival_pos = lb.index(rival_entry) + 1
                    if position < rival_pos:
                        player.unlock_achievement("beat_rival_major")
            except Exception as e:
                print(f"[career] beat_rival_major check error: {e}")

    # Phase 11 — prototype club progression
    proto = getattr(player, "prototype_club", None)
    if proto is not None and not is_qschool:
        proto["prototype_uses"] = proto.get("prototype_uses", 0) + 1
        goal = getattr(player, "prototype_uses_goal", 5)
        if proto["prototype_uses"] >= goal and position <= 10:
            # Convert: give +1 accuracy stat as permanent reward
            from src.career.player import MAX_STAT
            player.stats["accuracy"] = min(MAX_STAT,
                                           player.stats.get("accuracy", 50) + 1)
            player.prototype_club = None
            player.gain_reputation(3)
            # Signal conversion via a log entry so it surfaces in the results screen
            if player.career_log:
                player.career_log[-1]["prototype_converted"] = True

    player._check_achievements()
    return {"position": position, "prize": prize, "points": pts,
            "sponsor_bonus": sponsor_bonus}


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
            try:
                hole_pars = [course.get_hole(i).par for i in range(len(scores))]
            except Exception:
                hole_pars = None
            player.log_round(course.name, sum(scores), course.par,
                             hole_scores=scores, hole_pars=hole_pars)
            self._autosave()

        return result

    # ── Persistence ────────────────────────────────────────────────────────────

    def _autosave(self) -> None:
        """Save the player and any still-active tournament. Never raises.

        Skipped entirely for players in practice_mode — the course picker
        spawns a throwaway Player and we don't want to clobber real saves.
        """
        player     = self.player
        tournament = self.game.current_tournament
        if player is None or getattr(player, "practice_mode", False):
            return
        persist_tournament = (
            tournament if not (tournament and tournament.is_complete())
            else None)
        try:
            from src.utils.save_system import save_game
            save_game(player, persist_tournament)
        except Exception as e:
            print(f"Auto-save failed: {e}")
