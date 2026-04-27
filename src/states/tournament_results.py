"""
TournamentResultsState — full leaderboard after a 4-round tournament.

Shows:
  • Tournament name and prize fund
  • Full sorted leaderboard with per-round scores and total vs par
  • Player row highlighted in green
  • Prize money and season points earned
  • Button → Season Standings
"""

import pygame

from src.career.tournament import TOUR_DISPLAY_NAMES
from src.ui                import fonts

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG        = ( 10,  16,  10)
C_PANEL     = ( 18,  26,  18)
C_BORDER    = ( 58,  98,  58)
C_HDR       = ( 28,  42,  28)
C_WHITE     = (255, 255, 255)
C_GRAY      = (155, 158, 150)
C_GREEN     = ( 55, 185,  55)
C_RED       = (215,  50,  50)
C_YELLOW    = (215, 175,  50)
C_GOLD      = (210, 170,  30)
C_PLAYER_BG = ( 20,  55,  20)
C_PLAYER_BD = ( 60, 160,  60)
C_BTN       = ( 28,  78,  28)
C_BTN_HOV   = ( 48, 120,  48)

from src.constants import SCREEN_W, SCREEN_H

ROW_H      = 22
MAX_ROWS   = 22   # rows visible without scrolling


def _vs_par_str(vp: int) -> str:
    if vp == 0:
        return "E"
    return f"+{vp}" if vp > 0 else str(vp)


def _vs_par_color(vp: int) -> tuple:
    if vp < 0:
        return C_GREEN
    if vp > 0:
        return C_RED
    return C_WHITE


class TournamentResultsState:
    """Full tournament leaderboard screen."""

    def __init__(self, game, tournament, result: dict):
        """
        Parameters
        ----------
        game       : Game
        tournament : Tournament  (already complete)
        result     : dict from player.apply_tournament_result()
                     keys: position, prize, points
        """
        self.game       = game
        self.tournament = tournament
        self.result     = result
        self._rival_name = getattr(game.player, "rival_name", None) if game.player else None

        self.font_title  = fonts.heading(36)
        self.font_hdr    = fonts.heading(15)
        self.font_medium = fonts.body(16)
        self.font_small  = fonts.body(14)
        self.font_large  = fonts.heading(22)

        fmt = getattr(tournament, "format", "stroke")
        self._is_stableford = (fmt == "stableford")
        self._is_matchplay  = (fmt == "match")
        if self._is_stableford:
            self._leaderboard = tournament.get_stableford_final_leaderboard()
        elif self._is_matchplay:
            # Match play uses bracket notation — build a minimal leaderboard
            self._leaderboard = self._build_matchplay_leaderboard(tournament)
        else:
            self._leaderboard = tournament.get_leaderboard()
        self._scroll        = 0
        self._btn_hov       = False

        # Table geometry
        self._table_x  = 50
        self._table_y  = 160
        self._table_w  = SCREEN_W - 100
        col_widths = [40, 200, 120, 65, 65, 65, 65, 75]
        self._col_x = []
        cx = self._table_x
        for w in col_widths:
            self._col_x.append(cx)
            cx += w

        self._table_h = MAX_ROWS * ROW_H + 24

        btn_w, btn_h = 280, 50
        self._btn = pygame.Rect(
            SCREEN_W // 2 - btn_w // 2, SCREEN_H - 68, btn_w, btn_h)

    # ── Match play leaderboard builder ───────────────────────────────────────

    @staticmethod
    def _build_matchplay_leaderboard(tournament) -> list[dict]:
        """Minimal leaderboard for match play — just shows bracket results."""
        entries = []
        player_pos = tournament._match_final_position or (len(tournament.opponents) + 1)
        entries.append({
            "name": "You", "is_player": True,
            "rounds": [], "total": 0,
            "vs_par": 0, "nationality": "",
            "_mp_result": f"Position {player_pos}",
        })
        for opp in tournament.opponents:
            entries.append({
                "name": opp.name, "is_player": False,
                "rounds": [], "total": 0,
                "vs_par": 0, "nationality": opp.nationality,
                "_mp_result": "",
            })
        return entries

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._btn_hov = self._btn.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self._btn.collidepoint(event.pos):
                self._go_standings()
            elif event.button == 4:   # scroll up
                self._scroll = max(0, self._scroll - 3)
            elif event.button == 5:   # scroll down
                max_scroll = max(0, len(self._leaderboard) - MAX_ROWS)
                self._scroll = min(max_scroll, self._scroll + 3)

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._go_standings()
            elif event.key == pygame.K_UP:
                self._scroll = max(0, self._scroll - 1)
            elif event.key == pygame.K_DOWN:
                max_scroll = max(0, len(self._leaderboard) - MAX_ROWS)
                self._scroll = min(max_scroll, self._scroll + 1)

    def _go_standings(self):
        from src.states.tour_standings import TourStandingsState
        self.game.change_state(TourStandingsState(self.game))

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        pass

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(C_BG)
        cx = SCREEN_W // 2
        t  = self.tournament
        r  = self.result

        # ── Title ─────────────────────────────────────────────────────────────
        tour_name = TOUR_DISPLAY_NAMES.get(t.tour_level, "Tour")
        title = self.font_title.render(t.name, True, C_WHITE)
        surface.blit(title, (cx - title.get_width() // 2, 16))

        sub = self.font_medium.render(tour_name, True, (100, 160, 80))
        surface.blit(sub, (cx - sub.get_width() // 2, 60))

        # ── Player result banner ──────────────────────────────────────────────
        pos_str   = self._ordinal(r["position"])
        prize_str = (f"  •  Prize: ${r['prize']:,}" if r["prize"] > 0
                     else "  •  Amateur event – no prize money")
        pts_str   = f"  •  {r['points']} season points"

        banner_txt = f"You finished {pos_str}{prize_str}{pts_str}"
        banner = self.font_large.render(banner_txt, True, C_GOLD)
        surface.blit(banner, (cx - banner.get_width() // 2, 88))

        sponsor_bonus = r.get("sponsor_bonus", 0)
        if sponsor_bonus > 0:
            sb_txt = f"Sponsor bonus: +${sponsor_bonus:,}  (contract complete)"
            sb = self.font_medium.render(sb_txt, True, C_GREEN)
            surface.blit(sb, (cx - sb.get_width() // 2, 118))

        # ── Tour Championship extras ──────────────────────────────────────────
        extra_y = 140
        if getattr(t, "is_finale", False):
            offsets = getattr(t, "starting_score_offset", {})
            non_zero = {name: v for name, v in offsets.items() if v != 0}
            if non_zero:
                parts = sorted(non_zero.items(), key=lambda x: x[1])
                offset_str = "Starting offsets: " + ", ".join(
                    f"{name} {v:+d}" for name, v in parts)
                os_lbl = self.font_small.render(offset_str, True, C_YELLOW)
                surface.blit(os_lbl, (cx - os_lbl.get_width() // 2, extra_y))
                extra_y += 18
            if getattr(t, "promotion_wildcard", False):
                wc_lbl = self.font_medium.render(
                    "Tour Championship Winner — Automatic Promotion Wildcard",
                    True, C_GOLD)
                surface.blit(wc_lbl, (cx - wc_lbl.get_width() // 2, extra_y))

        # ── Leaderboard / bracket table ───────────────────────────────────────
        if self._is_matchplay:
            self._draw_matchplay_summary(surface)
        else:
            self._draw_table(surface)

        # ── Button ────────────────────────────────────────────────────────────
        bg = C_BTN_HOV if self._btn_hov else C_BTN
        pygame.draw.rect(surface, bg, self._btn, border_radius=8)
        pygame.draw.rect(surface, C_GREEN, self._btn, 2, border_radius=8)
        lbl = self.font_medium.render("Season Standings  >", True, C_WHITE)
        surface.blit(lbl, lbl.get_rect(center=self._btn.center))

        # Scroll hint
        if len(self._leaderboard) > MAX_ROWS:
            hint = self.font_small.render("↑↓ / Scroll to see more", True, C_GRAY)
            surface.blit(hint, (cx - hint.get_width() // 2,
                                self._btn.top - 20))

    def _draw_matchplay_summary(self, surface):
        """Bracket progression summary for match play events."""
        cx = SCREEN_W // 2
        t  = self.tournament
        ty = self._table_y

        bracket    = getattr(t, "bracket", [])
        match_rnd  = getattr(t, "match_round", 0)
        player_pos = getattr(t, "_match_final_position", None)
        player_won = (player_pos == 1)

        pw, ph = 600, max(80, len(bracket) * 52 + 40)
        px = cx - pw // 2
        panel = pygame.Rect(px, ty, pw, ph)
        pygame.draw.rect(surface, (16, 22, 34), panel, border_radius=10)
        pygame.draw.rect(surface, (60, 80, 130), panel, 2, border_radius=10)

        hdr = self.font_hdr.render("Bracket Results", True, (150, 200, 120))
        surface.blit(hdr, (cx - hdr.get_width() // 2, ty + 8))

        round_names = ["Quarter-Final", "Semi-Final", "Final"]
        if len(bracket) <= 2:
            round_names = ["Semi-Final", "Final"]
        if len(bracket) == 1:
            round_names = ["Final"]

        ry = ty + 32
        for i, opp_name in enumerate(bracket):
            won_this = (i < match_rnd or (i == match_rnd and player_won))
            label_rnd = round_names[i] if i < len(round_names) else f"Round {i+1}"
            col   = (55, 185, 55) if won_this else (215, 50, 50)
            badge = "Won" if won_this else "Lost"
            line  = self.font_medium.render(
                f"{label_rnd}  vs  {opp_name}   —   {badge}", True, col)
            surface.blit(line, (cx - line.get_width() // 2, ry))
            ry += 48

        if player_won:
            champ = self.font_large.render("Match Play Champion!", True, C_GOLD)
            surface.blit(champ, (cx - champ.get_width() // 2, ry + 8))

    def _draw_table(self, surface):
        tx = self._table_x
        ty = self._table_y
        tw = self._table_w
        col = self._col_x

        # Header background
        pygame.draw.rect(surface, C_HDR,
                         pygame.Rect(tx, ty, tw, 24), border_radius=4)

        headers = (["Pos", "Name", "Nationality",
                    "Rd 1 Pts", "Rd 2 Pts", "Rd 3 Pts", "Rd 4 Pts", "Total Pts"]
                   if self._is_stableford else
                   ["Pos", "Name", "Nationality",
                    "Rd 1", "Rd 2", "Rd 3", "Rd 4", "Total"])
        for i, h in enumerate(headers):
            s = self.font_hdr.render(h, True, (150, 200, 120))
            surface.blit(s, (col[i] + 4, ty + 4))

        visible = self._leaderboard[self._scroll: self._scroll + MAX_ROWS]
        for row_i, entry in enumerate(visible):
            real_pos = self._scroll + row_i + 1
            ry       = ty + 24 + row_i * ROW_H
            is_pl    = entry["is_player"]

            # Row background
            if is_pl:
                pygame.draw.rect(surface, C_PLAYER_BG,
                                 pygame.Rect(tx, ry, tw, ROW_H - 1),
                                 border_radius=2)
                pygame.draw.rect(surface, C_PLAYER_BD,
                                 pygame.Rect(tx, ry, tw, ROW_H - 1), 1,
                                 border_radius=2)
            elif row_i % 2 == 0:
                pygame.draw.rect(surface, (16, 24, 16),
                                 pygame.Rect(tx, ry, tw, ROW_H - 1))

            is_rival = (not is_pl and entry.get("name") == self._rival_name)
            tc = C_WHITE if is_pl else ((220, 140, 50) if is_rival else (200, 210, 200))

            # Pos
            surface.blit(self.font_small.render(str(real_pos), True, tc),
                         (col[0] + 4, ry + 3))
            # Name
            name_str = ("★ " + entry["name"]) if is_pl else (("⚔ " + entry["name"]) if is_rival else entry["name"])
            surface.blit(self.font_small.render(name_str, True, tc),
                         (col[1] + 4, ry + 3))
            # Nationality
            surface.blit(self.font_small.render(entry["nationality"], True, C_GRAY),
                         (col[2] + 4, ry + 3))

            rounds = entry["rounds"]
            if self._is_stableford:
                for ri, rx in enumerate([col[3], col[4], col[5], col[6]]):
                    if ri < len(rounds):
                        surface.blit(self.font_small.render(str(rounds[ri]), True,
                                     tc if not is_pl else C_GOLD),
                                     (rx + 4, ry + 3))
                surface.blit(self.font_small.render(str(entry["total"]), True,
                             C_GOLD if is_pl else (200, 200, 200)),
                             (col[7] + 4, ry + 3))
            else:
                par = self.tournament.course_par
                for ri, rx in enumerate([col[3], col[4], col[5], col[6]]):
                    if ri < len(rounds):
                        vp  = rounds[ri] - par
                        txt = _vs_par_str(vp)
                        col_c = _vs_par_color(vp) if is_pl else (180, 180, 180)
                        surface.blit(self.font_small.render(txt, True, col_c),
                                     (rx + 4, ry + 3))
                vp  = entry["vs_par"]
                txt = _vs_par_str(vp)
                surface.blit(self.font_small.render(txt, True,
                             _vs_par_color(vp) if is_pl else (200, 200, 200)),
                             (col[7] + 4, ry + 3))

    @staticmethod
    def _ordinal(n: int) -> str:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10
                  if n % 100 not in (11, 12, 13) else 0, "th")
        return f"{n}{suffix}"
