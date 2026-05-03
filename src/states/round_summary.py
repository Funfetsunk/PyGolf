"""
RoundSummaryState — end of one 18-hole round.

Tournament mode  (game.current_tournament is set)
  Shows the top-10 leaderboard for the tournament so far.  If the player
  is outside the top 10 they appear below a separator with their actual
  position.  Round 1-3 has "Play Round N+1"; round 4 has "See Results".

Free-play mode (no tournament)
  Shows full 18-hole scorecard with "Play Again" / "Main Menu" buttons.
"""

import pygame

from src.ui.scorecard import Scorecard
from src.ui           import fonts

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG        = ( 10,  16,  10)
C_PANEL     = ( 20,  30,  20)
C_BORDER    = ( 65,  95,  65)
C_HDR       = ( 28,  42,  28)
C_WHITE     = (255, 255, 255)
C_GRAY      = (165, 168, 160)
C_GREEN     = ( 55, 185,  55)
C_RED       = (215,  50,  50)
C_YELLOW    = (215, 175,  50)
C_GOLD      = (210, 170,  30)
C_BTN       = ( 35, 100,  35)
C_BTN_HOV   = ( 55, 145,  55)
C_PLAYER_BG = ( 20,  55,  20)
C_PLAYER_BD = ( 60, 160,  60)

from src.constants import SCREEN_W, SCREEN_H

LB_ROW_H   = 30   # leaderboard row height

_ROUND_DESCRIPTIONS = [
    (-20,  "Phenomenal Round!",    (180, 220,  80)),
    (-10,  "Exceptional Round!",   ( 55, 185,  55)),
    ( -5,  "Excellent Round!",     ( 55, 185,  55)),
    ( -1,  "Great Round!",         ( 55, 185,  55)),
    (  0,  "Round of Par",         (210, 210, 210)),
    (  4,  "Decent Round",         (200, 200, 160)),
    (  9,  "Room for Improvement", (200, 160, 100)),
    ( 18,  "Tough Day Out There",  (215,  80,  80)),
    (999,  "Keep Practising!",     (180,  50,  50)),
]


def _round_description(total_diff):
    for threshold, text, color in _ROUND_DESCRIPTIONS:
        if total_diff <= threshold:
            return text, color
    return "Keep Practising!", (180, 50, 50)


def _vs_par_str(diff):
    if diff == 0:
        return "E"
    return f"+{diff}" if diff > 0 else str(diff)


def _vs_par_color(diff):
    if diff < 0:
        return C_GREEN
    if diff > 0:
        return C_RED
    return C_WHITE


class RoundSummaryState:
    """End-of-round screen."""

    def __init__(self, game, course, scores):
        self.game   = game
        self.course = course
        self.scores = scores

        self.scorecard = Scorecard(course)

        # ── Tournament bookkeeping + autosave ──────────────────────────────────
        # Delegated to CareerService so this screen doesn't directly mutate
        # the player or touch the save system.
        self._tournament = game.current_tournament
        from src.career.service import CareerService
        self._tourn_result = CareerService(game).record_round(course, scores)

        # ── Q-School cut line (Phase 14) ──────────────────────────────────────
        # Computed once, immediately after recording round 1.
        self._qschool_cut_status: str | None = None  # "safe"/"bubble"/"cut"
        self._qschool_cut_line: int | None   = None
        self._qschool_player_pos: int | None = None
        if (self._tournament is not None
                and getattr(self._tournament, "is_qschool", False)
                and len(self._tournament.player_rounds) == 1
                and not getattr(self._tournament, "missed_cut", False)):
            self._compute_qschool_cut()

        # ── Fonts ─────────────────────────────────────────────────────────────
        self.font_title  = fonts.heading(42)
        self.font_large  = fonts.heading(28)
        self.font_medium = fonts.body(20)
        self.font_small  = fonts.body(15)
        self.font_lb     = fonts.body(16)
        self.font_lb_hdr = fonts.heading(14)

        # ── Layout ────────────────────────────────────────────────────────────
        sc_w = min(1140, SCREEN_W - 40)
        sc_h = 215
        self.sc_rect = pygame.Rect((SCREEN_W - sc_w) // 2, 230, sc_w, sc_h)

        btn_w, btn_h = 260, 52
        gap      = 20
        total_bw = btn_w * 2 + gap
        bx = SCREEN_W // 2 - total_bw // 2
        by = SCREEN_H - 72
        self.btn_action = pygame.Rect(bx + btn_w + gap, by, btn_w, btn_h)
        self.btn_menu   = pygame.Rect(bx,               by, btn_w, btn_h)
        self._hover_act  = False
        self._hover_menu = False

    # ── Computed stats ────────────────────────────────────────────────────────

    @property
    def _total_strokes(self): return sum(self.scores)
    @property
    def _total_diff(self):    return self._total_strokes - self.course.par
    @property
    def _front_strokes(self): return sum(self.scores[:9])
    @property
    def _back_strokes(self):  return sum(self.scores[9:])

    def _best_hole(self):
        best_d, best_i = 999, 0
        for i, s in enumerate(self.scores):
            d = s - self.course.get_hole(i).par
            if d < best_d:
                best_d, best_i = d, i
        return best_i, best_d

    def _worst_hole(self):
        worst_d, worst_i = -999, 0
        for i, s in enumerate(self.scores):
            d = s - self.course.get_hole(i).par
            if d > worst_d:
                worst_d, worst_i = d, i
        return worst_i, worst_d

    def _compute_qschool_cut(self):
        """Determine Q-School round-1 cut and update the tournament."""
        from src.career.tournament import QSCHOOL_CUT_POSITION
        t  = self._tournament
        lb = t.get_leaderboard()
        cut_idx = min(QSCHOOL_CUT_POSITION, len(lb)) - 1
        t.cut_line = lb[cut_idx]["vs_par"] if cut_idx >= 0 else 0
        self._qschool_cut_line = t.cut_line
        player_pos = next((i + 1 for i, e in enumerate(lb) if e["is_player"]), None)
        self._qschool_player_pos = player_pos
        if player_pos is not None and player_pos > QSCHOOL_CUT_POSITION:
            t.missed_cut = True
            self._qschool_cut_status = "cut"
        elif player_pos is not None and player_pos >= QSCHOOL_CUT_POSITION - 2:
            self._qschool_cut_status = "bubble"
        else:
            self._qschool_cut_status = "safe"

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_action.collidepoint(event.pos):
                self._on_action()
            elif self.btn_menu.collidepoint(event.pos):
                self._return_to_menu()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                self._on_action()
            elif event.key == pygame.K_ESCAPE:
                self._return_to_menu()
        elif event.type == pygame.MOUSEMOTION:
            self._hover_act  = self.btn_action.collidepoint(event.pos)
            self._hover_menu = self.btn_menu.collidepoint(event.pos)

    def _on_action(self):
        t = self._tournament
        if t is None:
            self._play_again()
        elif t.is_complete():
            self._see_tournament_results()
        else:
            self._play_next_round()

    def _play_again(self):
        from src.states.golf_round import GolfRoundState
        self.game.change_state(GolfRoundState(self.game, self.course, 0, []))

    def _play_next_round(self):
        from src.states.golf_round import GolfRoundState
        self.game.change_state(GolfRoundState(self.game, self.course, 0, []))

    def _see_tournament_results(self):
        from src.states.tournament_results import TournamentResultsState
        self.game.change_state(
            TournamentResultsState(self.game, self._tournament,
                                   self._tourn_result or {}))

    def _return_to_menu(self):
        from src.states.main_menu import MainMenuState
        self.game.change_state(MainMenuState(self.game))

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        pass

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(C_BG)
        cx = SCREEN_W // 2
        t  = self._tournament

        total_diff = self._total_diff
        diff_str   = _vs_par_str(total_diff)

        # ── Title ─────────────────────────────────────────────────────────────
        if t is None:
            rnd_txt = "Round Complete"
        elif t.total_rounds > 1:
            rnd_txt = f"Round {len(t.player_rounds)} of {t.total_rounds} Complete"
        else:
            rnd_txt = f"Event Complete  —  {t.name}"
        title = self.font_title.render(rnd_txt, True, C_WHITE)
        surface.blit(title, (cx - title.get_width() // 2, 14))

        course_lbl = self.font_medium.render(self.course.name, True, C_GRAY)
        surface.blit(course_lbl, (cx - course_lbl.get_width() // 2, 64))

        if t is not None and t.total_rounds > 1:
            ctx = self.font_medium.render(t.name, True, (100, 180, 80))
            surface.blit(ctx, (cx - ctx.get_width() // 2, 90))

        # ── This round's score ────────────────────────────────────────────────
        offset_y = 122
        is_sford = t is not None and getattr(t, "format", "stroke") == "stableford"
        if is_sford:
            from src.career.tournament import Tournament as _T
            round_pts = sum(
                _T.stableford_points(self.scores[i] - self.course.get_hole(i).par)
                for i in range(len(self.scores)))
            score_txt = self.font_large.render(
                f"Round score:  {round_pts} pts  ({self._total_strokes} strokes, {diff_str})",
                True, C_GOLD)
        else:
            score_color = _vs_par_color(total_diff)
            score_txt   = self.font_large.render(
                f"Round score:  {self._total_strokes}  ({diff_str})  •  Par {self.course.par}",
                True, score_color)
        surface.blit(score_txt, (cx - score_txt.get_width() // 2, offset_y))

        desc, desc_color = _round_description(total_diff)
        desc_surf = self.font_medium.render(desc, True, desc_color)
        surface.blit(desc_surf, (cx - desc_surf.get_width() // 2, offset_y + 34))

        # ── Q-School cut line banner (Phase 14) ──────────────────────────────
        qs_banner_h = 0
        if self._qschool_cut_line is not None and self._qschool_cut_status is not None:
            qs_banner_h = 38
            from src.career.tournament import QSCHOOL_CUT_POSITION
            cut_str = _vs_par_str(self._qschool_cut_line)
            status = self._qschool_cut_status
            if status == "cut":
                banner_col = C_RED
                status_txt = f"Below cut — Round 2 not played (cut: {cut_str}, pos: {self._qschool_player_pos})"
            elif status == "bubble":
                banner_col = C_YELLOW
                status_txt = f"On the bubble — narrowly made cut (cut: {cut_str}, pos: {self._qschool_player_pos})"
            else:
                banner_col = C_GREEN
                status_txt = f"Safe — made the cut (cut: {cut_str}, pos: {self._qschool_player_pos})"
            cut_lbl = self.font_medium.render(
                f"Q-School Cut  •  Top {QSCHOOL_CUT_POSITION} advance  •  {status_txt}",
                True, banner_col)
            surface.blit(cut_lbl, (cx - cut_lbl.get_width() // 2, offset_y + 72))

        # ── Main content: leaderboard (tournament) or scorecard (free play) ───
        content_y = offset_y + 72 + qs_banner_h
        if t is not None:
            fmt = getattr(t, "format", "stroke")
            if fmt == "stableford":
                self._draw_stableford_leaderboard(surface, t, content_y)
            elif fmt == "skins":
                self._draw_skins_summary(surface, t, content_y)
            else:
                self._draw_leaderboard(surface, t, content_y)
        else:
            self._draw_scorecard_section(surface, content_y)

        # ── Buttons ───────────────────────────────────────────────────────────
        menu_bg = (55, 30, 30) if self._hover_menu else (38, 20, 20)
        pygame.draw.rect(surface, menu_bg, self.btn_menu, border_radius=8)
        pygame.draw.rect(surface, C_RED,   self.btn_menu, 2, border_radius=8)
        ml = self.font_medium.render("Main Menu  (Esc)", True, C_WHITE)
        surface.blit(ml, ml.get_rect(center=self.btn_menu.center))

        if t is None:
            act_lbl = "Play Again  (Enter)"
        elif t.is_complete():
            act_lbl = "See Results  (Enter)"
        else:
            act_lbl = f"Play Round {t.current_round_number}  (Enter)"

        act_bg = C_BTN_HOV if self._hover_act else C_BTN
        pygame.draw.rect(surface, act_bg,  self.btn_action, border_radius=8)
        pygame.draw.rect(surface, C_GREEN, self.btn_action, 2, border_radius=8)
        al = self.font_medium.render(act_lbl, True, C_WHITE)
        surface.blit(al, al.get_rect(center=self.btn_action.center))

    # ── Leaderboard (tournament mode) ─────────────────────────────────────────

    def _draw_leaderboard(self, surface, tournament, top_y):
        lb        = tournament.get_leaderboard()
        rounds_done = len(tournament.player_rounds)
        top10     = lb[:10]
        player_entry = next((e for e in lb if e["is_player"]), None)
        player_pos   = next((i + 1 for i, e in enumerate(lb) if e["is_player"]), None)
        player_in_top10 = player_pos is not None and player_pos <= 10

        # Table dimensions
        tw   = 860
        tx   = cx = SCREEN_W // 2 - tw // 2

        # Column x positions: Pos, Name, Rd1..Rd4 (only played), Total
        col_pos   = tx
        col_name  = tx + 48
        col_rds   = col_name + 220
        rd_w      = 68
        col_total = col_rds + rounds_done * rd_w + 12

        # Header row
        pygame.draw.rect(surface, C_HDR,
                         pygame.Rect(tx, top_y, tw, 24), border_radius=4)
        surface.blit(self.font_lb_hdr.render("Pos",   True, (150, 200, 120)),
                     (col_pos  + 4, top_y + 4))
        surface.blit(self.font_lb_hdr.render("Player", True, (150, 200, 120)),
                     (col_name + 4, top_y + 4))
        for r in range(rounds_done):
            surface.blit(self.font_lb_hdr.render(f"Rd {r+1}", True, (150, 200, 120)),
                         (col_rds + r * rd_w + 4, top_y + 4))
        surface.blit(self.font_lb_hdr.render("Total", True, (150, 200, 120)),
                     (col_total + 4, top_y + 4))

        def draw_row(row_y, pos, entry, is_player):
            if is_player:
                pygame.draw.rect(surface, C_PLAYER_BG,
                                 pygame.Rect(tx, row_y, tw, LB_ROW_H - 2),
                                 border_radius=2)
                pygame.draw.rect(surface, C_PLAYER_BD,
                                 pygame.Rect(tx, row_y, tw, LB_ROW_H - 2), 1,
                                 border_radius=2)
            elif pos % 2 == 0:
                pygame.draw.rect(surface, (16, 24, 16),
                                 pygame.Rect(tx, row_y, tw, LB_ROW_H - 2))

            tc = C_WHITE if is_player else (200, 210, 200)

            # Position
            surface.blit(self.font_lb.render(str(pos), True, tc),
                         (col_pos + 4, row_y + 6))

            name_str = entry["name"]
            surface.blit(self.font_lb.render(name_str, True, tc),
                         (col_name + 4, row_y + 6))

            # Per-round scores
            par = tournament.course_par
            for ri, rnd_strokes in enumerate(entry["rounds"]):
                vp  = rnd_strokes - par
                txt = _vs_par_str(vp)
                col_c = (_vs_par_color(vp) if is_player
                         else (160, 200, 160) if vp < 0
                         else (200, 160, 160) if vp > 0
                         else (180, 180, 180))
                surface.blit(self.font_lb.render(txt, True, col_c),
                             (col_rds + ri * rd_w + 4, row_y + 6))

            # Total vs par
            vp  = entry["vs_par"]
            txt = _vs_par_str(vp)
            total_c = _vs_par_color(vp) if is_player else (190, 190, 190)
            surface.blit(self.font_lb.render(txt, True, total_c),
                         (col_total + 4, row_y + 6))

        # Draw top 10 rows
        for i, entry in enumerate(top10):
            row_y = top_y + 24 + i * LB_ROW_H
            draw_row(row_y, i + 1, entry, entry["is_player"])

        # If player is outside top 10, draw separator then their row
        if not player_in_top10 and player_entry is not None:
            sep_y = top_y + 24 + 10 * LB_ROW_H + 4
            # Dotted separator
            for x in range(tx, tx + tw, 8):
                pygame.draw.line(surface, (60, 80, 60),
                                 (x, sep_y + 2), (x + 4, sep_y + 2))
            ellipsis = self.font_lb_hdr.render("· · ·", True, C_GRAY)
            surface.blit(ellipsis, (cx - ellipsis.get_width() // 2, sep_y - 2))

            player_row_y = sep_y + 14
            draw_row(player_row_y, player_pos, player_entry, True)

    # ── Stableford leaderboard ────────────────────────────────────────────────

    def _draw_stableford_leaderboard(self, surface, tournament, top_y):
        lb        = tournament.get_stableford_final_leaderboard()
        top10     = lb[:10]
        player_entry = next((e for e in lb if e["is_player"]), None)
        player_pos   = next((i + 1 for i, e in enumerate(lb) if e["is_player"]), None)
        player_in_top10 = player_pos is not None and player_pos <= 10

        tw = 860
        tx = SCREEN_W // 2 - tw // 2
        cx = SCREEN_W // 2

        rounds_done = len(tournament.player_rounds)
        col_pos   = tx
        col_name  = tx + 48
        col_rds   = col_name + 220
        rd_w      = 68
        col_total = col_rds + rounds_done * rd_w + 12

        pygame.draw.rect(surface, C_HDR,
                         pygame.Rect(tx, top_y, tw, 24), border_radius=4)
        surface.blit(self.font_lb_hdr.render("Pos",   True, (150, 200, 120)),
                     (col_pos  + 4, top_y + 4))
        surface.blit(self.font_lb_hdr.render("Player", True, (150, 200, 120)),
                     (col_name + 4, top_y + 4))
        for r in range(rounds_done):
            surface.blit(self.font_lb_hdr.render(f"Rd {r+1} Pts", True, (150, 200, 120)),
                         (col_rds + r * rd_w + 4, top_y + 4))
        surface.blit(self.font_lb_hdr.render("Total Pts", True, (150, 200, 120)),
                     (col_total + 4, top_y + 4))

        def draw_row(row_y, pos, entry, is_player):
            if is_player:
                pygame.draw.rect(surface, C_PLAYER_BG,
                                 pygame.Rect(tx, row_y, tw, LB_ROW_H - 2), border_radius=2)
                pygame.draw.rect(surface, C_PLAYER_BD,
                                 pygame.Rect(tx, row_y, tw, LB_ROW_H - 2), 1, border_radius=2)
            elif pos % 2 == 0:
                pygame.draw.rect(surface, (16, 24, 16),
                                 pygame.Rect(tx, row_y, tw, LB_ROW_H - 2))
            tc = C_WHITE if is_player else (200, 210, 200)
            surface.blit(self.font_lb.render(str(pos), True, tc), (col_pos + 4, row_y + 6))
            name_str = entry["name"]
            surface.blit(self.font_lb.render(name_str, True, tc), (col_name + 4, row_y + 6))
            for ri, rnd_pts in enumerate(entry["rounds"]):
                surface.blit(self.font_lb.render(str(rnd_pts), True, tc),
                             (col_rds + ri * rd_w + 4, row_y + 6))
            total_c = C_GOLD if is_player else (190, 190, 190)
            surface.blit(self.font_lb.render(str(entry["total"]), True, total_c),
                         (col_total + 4, row_y + 6))

        for i, entry in enumerate(top10):
            draw_row(top_y + 24 + i * LB_ROW_H, i + 1, entry, entry["is_player"])

        if not player_in_top10 and player_entry is not None:
            sep_y = top_y + 24 + 10 * LB_ROW_H + 4
            for x in range(tx, tx + tw, 8):
                pygame.draw.line(surface, (60, 80, 60), (x, sep_y + 2), (x + 4, sep_y + 2))
            ellipsis = self.font_lb_hdr.render("· · ·", True, C_GRAY)
            surface.blit(ellipsis, (cx - ellipsis.get_width() // 2, sep_y - 2))
            draw_row(sep_y + 14, player_pos, player_entry, True)

    # ── Skins summary ─────────────────────────────────────────────────────────

    def _draw_skins_summary(self, surface, tournament, top_y):
        """Skins event: per-hole skin results and total prize."""
        cx = SCREEN_W // 2
        skins_won_count = sum(1 for w in tournament.skins_won if w)
        total_prize     = sum(tournament.skins_prize_per_hole)

        # Header bar
        pygame.draw.rect(surface, C_HDR,
                         pygame.Rect(cx - 430, top_y, 860, 28), border_radius=4)
        hdr = self.font_lb_hdr.render(
            f"Skins Summary  |  {skins_won_count} skin(s) won  |  "
            f"Total prize:  ${total_prize:,}",
            True, C_GOLD)
        surface.blit(hdr, (cx - hdr.get_width() // 2, top_y + 6))

        # Two-column grid: front 9 left, back 9 right
        grid_top  = top_y + 36
        row_h     = 26
        col_left  = cx - 430
        col_right = cx + 10

        for i in range(9):
            for side in range(2):
                hole_i = i + side * 9
                if hole_i >= len(tournament.hole_pars):
                    continue
                x   = col_left if side == 0 else col_right
                y   = grid_top + i * row_h
                won = (tournament.skins_won[hole_i]
                       if hole_i < len(tournament.skins_won) else False)
                prize = (tournament.skins_prize_per_hole[hole_i]
                         if hole_i < len(tournament.skins_prize_per_hole) else 0)

                if won:
                    row_txt = f"Hole {hole_i + 1:2d}   Skin Won   +${prize:,}"
                    row_col = C_GREEN
                else:
                    row_txt = f"Hole {hole_i + 1:2d}   —"
                    row_col = C_GRAY
                surface.blit(self.font_small.render(row_txt, True, row_col), (x, y))

        # Total prize box
        prize_y = grid_top + 9 * row_h + 10
        prize_lbl = self.font_large.render(
            f"Prize money:  ${total_prize:,}", True, C_GOLD)
        surface.blit(prize_lbl, (cx - prize_lbl.get_width() // 2, prize_y))

    # ── Scorecard section (free-play mode) ────────────────────────────────────

    def _draw_scorecard_section(self, surface, top_y):
        cx = SCREEN_W // 2

        sc_title = self.font_small.render("SCORECARD", True, C_GRAY)
        surface.blit(sc_title,
                     (self.sc_rect.x, top_y - sc_title.get_height() - 2))

        # Reposition sc_rect to start at top_y
        sc = pygame.Rect(self.sc_rect.x, top_y, self.sc_rect.width, self.sc_rect.height)
        self.scorecard.draw(surface, sc, self.scores)

        fp  = self.course.front_par
        bp  = self.course.back_par
        fd  = self._front_strokes - fp
        bd  = self._back_strokes  - bp
        split_txt = (f"Front: {self._front_strokes} ({_vs_par_str(fd)})   "
                     f"Back: {self._back_strokes} ({_vs_par_str(bd)})")
        split_surf = self.font_small.render(split_txt, True, C_GRAY)
        surface.blit(split_surf, (cx - split_surf.get_width() // 2,
                                   sc.bottom + 8))

        best_i,  best_d  = self._best_hole()
        worst_i, worst_d = self._worst_hole()

        def diff_label(d):
            labels = {-3: "Albatross", -2: "Eagle", -1: "Birdie",
                       0: "Par", 1: "Bogey", 2: "Double Bogey"}
            return labels.get(d, f"+{d}" if d > 0 else str(d))

        stats_y  = sc.bottom + 30
        best_s   = self.font_small.render(
            f"Best hole: #{best_i + 1}  —  {diff_label(best_d)}", True, C_GREEN)
        worst_s  = self.font_small.render(
            f"Toughest: #{worst_i + 1}  —  {diff_label(worst_d)}", True, C_RED)
        gap      = 40
        total_bw = best_s.get_width() + gap + worst_s.get_width()
        bx       = cx - total_bw // 2
        surface.blit(best_s,  (bx, stats_y))
        surface.blit(worst_s, (bx + best_s.get_width() + gap, stats_y))

        pygame.draw.line(surface, C_BORDER,
                         (60, stats_y + 22), (SCREEN_W - 60, stats_y + 22))

    @staticmethod
    def _ordinal(n: int) -> str:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(
            n % 10 if n % 100 not in (11, 12, 13) else 0, "th")
        return f"{n}{suffix}"
