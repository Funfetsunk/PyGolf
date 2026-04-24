"""
MatchResultState — displayed after each match play round completes.

Shows:
  • Match result (won X&Y / lost X&Y / tied 19th hole)
  • Hole-by-hole summary (holes won / halved / lost)
  • Opponent name and bracket round info
  • Next steps: continue to next match or see tournament results

Navigation
──────────
  Player won, more rounds remain  → new GolfRoundState (next opponent)
  Player won final match          → TournamentResultsState (winner)
  Player lost                     → TournamentResultsState (eliminated)
"""

import pygame

from src.ui    import fonts
from src.constants import SCREEN_W, SCREEN_H

C_BG        = ( 10,  14,  20)
C_PANEL     = ( 16,  22,  34)
C_BORDER    = ( 60,  80, 130)
C_WHITE     = (255, 255, 255)
C_GRAY      = (155, 158, 165)
C_GREEN     = ( 55, 185,  55)
C_RED       = (215,  50,  50)
C_GOLD      = (215, 175,  50)
C_BLUE      = ( 80, 130, 220)
C_BTN       = ( 28,  55, 110)
C_BTN_HOV   = ( 50,  90, 160)


class MatchResultState:
    """Shows the outcome of a single match play match and routes to next step."""

    def __init__(self, game, course, scores: list):
        self.game   = game
        self.course = course
        self.scores = list(scores)

        t = game.current_tournament
        self._tournament = t

        # Compute result before any bracket advancement
        self._result = t.get_match_result(scores)
        self._player_won = (self._result["result"] == "win")

        # Record the completed round scores into the tournament
        t.record_player_round(scores)

        # Log this round in the career log
        if game.player:
            game.player.log_round(course.name, sum(scores), course.par)

        # Determine what happens when the player clicks Continue
        if self._player_won:
            has_more = t.advance_bracket()
            if has_more:
                self._next_action   = "next_match"
                self._tourn_result  = None
            else:
                # Won the entire bracket — finalise tournament
                t._match_final_position = 1
                self._next_action  = "tournament_results"
                self._tourn_result = self._finalise_tournament()
        else:
            # Eliminated — compute finishing position by round reached
            rounds_won = t.match_round   # 0-indexed rounds completed successfully
            total      = len(t.bracket)
            pos = max(2, total - rounds_won + 1)
            t._match_final_position = pos
            t.match_eliminated      = True
            self._next_action  = "tournament_results"
            self._tourn_result = self._finalise_tournament()

        # ── UI ────────────────────────────────────────────────────────────────
        self.font_title  = fonts.heading(44)
        self.font_large  = fonts.heading(28)
        self.font_medium = fonts.body(20)
        self.font_small  = fonts.body(15)

        btn_w, btn_h = 280, 52
        self.btn_cont = pygame.Rect(
            SCREEN_W // 2 - btn_w // 2, SCREEN_H - 80, btn_w, btn_h)
        self._btn_hover = False

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _finalise_tournament(self) -> dict:
        """Apply tournament result to player, autosave, return result dict."""
        t  = self._tournament
        p  = self.game.player
        if p is None:
            return {}
        result = p.apply_tournament_result(t)
        try:
            from src.utils.save_system import save_game
            save_game(p, None)   # tournament complete — no need to persist it
        except Exception as e:
            print(f"Match result autosave failed: {e}")
        return result

    def _round_label(self, rnd: int, total: int) -> str:
        if total <= 1:
            return "Final"
        if rnd >= total - 1:
            return "Final"
        if rnd >= total - 2:
            return "Semi-Final"
        if rnd >= total - 3:
            return "Quarter-Final"
        return f"Round {rnd + 1}"

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_cont.collidepoint(event.pos):
                self._go_next()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._go_next()
        elif event.type == pygame.MOUSEMOTION:
            self._btn_hover = self.btn_cont.collidepoint(event.pos)

    def _go_next(self):
        if self._next_action == "next_match":
            from src.states.golf_round import GolfRoundState
            self.game.change_state(
                GolfRoundState(self.game, self.course, 0, []))
        else:
            from src.states.tournament_results import TournamentResultsState
            self.game.change_state(
                TournamentResultsState(
                    self.game, self._tournament,
                    self._tourn_result or {}))

    def update(self, dt):
        pass

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(C_BG)
        cx = SCREEN_W // 2
        r  = self._result

        # ── Header ────────────────────────────────────────────────────────────
        round_label = self._round_label(r["round"], r["total_rounds"])
        hdr = self.font_small.render(
            f"Match Play  —  {round_label}", True, C_GRAY)
        surface.blit(hdr, (cx - hdr.get_width() // 2, 24))

        # ── Result banner ─────────────────────────────────────────────────────
        if self._player_won:
            title_txt   = "You Won!"
            title_col   = C_GOLD
            margin_col  = C_GREEN
        else:
            title_txt   = "You Lost"
            title_col   = C_RED
            margin_col  = C_RED

        title = self.font_title.render(title_txt, True, title_col)
        surface.blit(title, (cx - title.get_width() // 2, 58))

        margin = self.font_large.render(r["margin"], True, margin_col)
        surface.blit(margin, (cx - margin.get_width() // 2, 116))

        # ── Match summary panel ────────────────────────────────────────────────
        pw, ph = 480, 150
        px = cx - pw // 2
        py = 170
        panel = pygame.Rect(px, py, pw, ph)
        pygame.draw.rect(surface, C_PANEL, panel, border_radius=10)
        pygame.draw.rect(surface, C_BORDER, panel, 2, border_radius=10)

        opp_name = r["opponent"] or "Opponent"
        opp_lbl  = self.font_medium.render(f"vs  {opp_name}", True, C_WHITE)
        surface.blit(opp_lbl, (cx - opp_lbl.get_width() // 2, py + 14))

        pu = r["player_up"]
        ou = r["opp_up"]
        halved = r["holes_played"] - pu - ou

        cols = [
            ("You", str(pu),     C_GREEN if pu > ou else C_WHITE),
            ("Halved", str(halved), C_GRAY),
            (opp_name[:12], str(ou), C_RED if ou > pu else C_WHITE),
        ]
        col_w = pw // 3
        for i, (lbl, val, col) in enumerate(cols):
            cx_col = px + i * col_w + col_w // 2
            l_surf = self.font_small.render(lbl, True, C_GRAY)
            v_surf = self.font_large.render(val, True, col)
            surface.blit(l_surf, (cx_col - l_surf.get_width() // 2, py + 50))
            surface.blit(v_surf, (cx_col - v_surf.get_width() // 2, py + 72))

        thru = self.font_small.render(
            f"{r['holes_played']} holes played", True, C_GRAY)
        surface.blit(thru, (cx - thru.get_width() // 2, py + ph - 26))

        # ── Next section ──────────────────────────────────────────────────────
        next_y = panel.bottom + 28

        if self._next_action == "next_match":
            t = self._tournament
            next_opp = t.match_opponent or "?"
            next_rnd  = self._round_label(t.match_round, t.total_rounds)
            txt = self.font_medium.render(
                f"Next:  {next_rnd}  vs  {next_opp}", True, C_BLUE)
            surface.blit(txt, (cx - txt.get_width() // 2, next_y))
            btn_label = "Play Next Match"
        elif self._player_won:
            won_txt = self.font_medium.render(
                "Match Play Champion!", True, C_GOLD)
            surface.blit(won_txt, (cx - won_txt.get_width() // 2, next_y))
            if self._tourn_result:
                prize = self._tourn_result.get("prize", 0)
                pts   = self._tourn_result.get("points", 0)
                info  = self.font_small.render(
                    f"Prize: ${prize:,}   Season Points: {pts}", True, C_GRAY)
                surface.blit(info, (cx - info.get_width() // 2, next_y + 30))
            btn_label = "See Results"
        else:
            elim_txt = self.font_medium.render(
                f"Eliminated in {round_label}", True, C_GRAY)
            surface.blit(elim_txt, (cx - elim_txt.get_width() // 2, next_y))
            if self._tourn_result:
                prize = self._tourn_result.get("prize", 0)
                pts   = self._tourn_result.get("points", 0)
                info  = self.font_small.render(
                    f"Prize: ${prize:,}   Season Points: {pts}", True, C_GRAY)
                surface.blit(info, (cx - info.get_width() // 2, next_y + 30))
            btn_label = "See Results"

        # ── Continue button ───────────────────────────────────────────────────
        btn_col = C_BTN_HOV if self._btn_hover else C_BTN
        pygame.draw.rect(surface, btn_col, self.btn_cont, border_radius=9)
        pygame.draw.rect(surface, C_BLUE,  self.btn_cont, 2, border_radius=9)
        btn_lbl = self.font_medium.render(btn_label, True, C_WHITE)
        surface.blit(btn_lbl, btn_lbl.get_rect(center=self.btn_cont.center))
