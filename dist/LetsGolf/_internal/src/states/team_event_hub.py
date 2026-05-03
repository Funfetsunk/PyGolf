"""
TeamEventHubState — International Team Event.

A prestige event held every 4 career seasons.

Structure
─────────
  Entry screen  : show two teams, player picks a foursomes partner.
  Day 1         : Foursomes — alternate shots with an AI partner vs two AI
                  opponents (uses GolfRoundState with alternate_shot_mode).
  Day 2         : Singles — simulated match vs one opposing team member.
  Result        : overall team points decide the winner.
"""

import random
import pygame

from src.ui        import fonts
from src.constants import SCREEN_W, SCREEN_H

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG      = ( 10,  15,  30)
C_PANEL   = ( 18,  28,  50)
C_BORDER  = ( 60,  90, 160)
C_WHITE   = (255, 255, 255)
C_GRAY    = (155, 158, 175)
C_GOLD    = (215, 175,  50)
C_GREEN   = ( 55, 185,  55)
C_RED     = (215,  50,  50)
C_BLUE    = ( 80, 130, 220)
C_BTN     = ( 28,  55, 120)
C_BTN_HOV = ( 50,  90, 180)


class TeamEventSession:
    """Lightweight tournament-like object for the International Team Event.

    Stored as game.current_tournament while the team event is active.
    Carries all state across GolfRoundState transitions so HoleTransitionState
    does not need to be modified.
    """

    event_type = "team_event"
    format     = "stroke"   # foursomes day uses stroke scoring
    name       = "International Team Event"

    # Attributes consumed by GolfRoundState's condition-extraction block
    pin_positions:       list  = []
    green_speed:         str   = "normal"
    firmness:            str   = "normal"
    weather:             str   = "clear"
    wind_strength_floor: int   = 1

    def __init__(self, player_name: str, tour_level: int,
                 opponent_pool: list[str]):
        self.tour_level = tour_level
        self.foursomes_active = True   # True → GolfRoundState enables alternate shots

        # ── Team generation ───────────────────────────────────────────────────
        # Home team: player + 5 AI teammates drawn from the pool
        pool = list(opponent_pool)
        random.shuffle(pool)
        home_ai   = pool[:5]
        away_team = pool[5:11]

        self.team_home: list[str] = [player_name] + home_ai
        self.team_away: list[str] = away_team

        # ── Foursomes pairing ─────────────────────────────────────────────────
        self.player_partner = home_ai[0] if home_ai else "Partner"
        self.foursomes_opponents = away_team[:2] if len(away_team) >= 2 else away_team

        # Pre-simulate the opposing pair's foursomes score.
        # Tour 1 opponents average ~78; Tour 6 average ~68 per round.
        base = max(66, 80 - (tour_level - 1) * 2)
        self.foursomes_opp_score = base + random.randint(-4, 6)

        # ── Day 2 singles ─────────────────────────────────────────────────────
        self.singles_opponent = away_team[2] if len(away_team) > 2 else away_team[0]

        # ── Result tracking ───────────────────────────────────────────────────
        self.foursomes_player_score: int | None = None
        self.foursomes_result: str | None = None   # "win" | "loss" | "halved"
        self.singles_result:    str | None = None   # "win" | "loss"
        self.team_points_home  = 0
        self.team_points_away  = 0

    # ── Called by GolfRoundState stubs ────────────────────────────────────────

    def apply_pin_positions(self, course) -> None:
        pass   # no special pin positions for team event

    def get_live_leaderboard(self, holes_done, scores):
        return []   # no live leaderboard during foursomes

    def get_match_status(self, scores):
        return None   # not a match play round

    # ── Result finalisation ───────────────────────────────────────────────────

    def finalize_foursomes(self, player_scores: list[int]) -> None:
        self.foursomes_player_score = sum(player_scores)
        self.foursomes_active = False
        if self.foursomes_player_score <= self.foursomes_opp_score:
            self.foursomes_result = "win"
            self.team_points_home += 1
        elif self.foursomes_player_score == self.foursomes_opp_score:
            self.foursomes_result = "halved"
            self.team_points_home += 0.5
            self.team_points_away += 0.5
        else:
            self.foursomes_result = "loss"
            self.team_points_away += 1

    def simulate_singles(self, player_level: int) -> None:
        """Simulate Day 2 singles outcome based on tour level."""
        # Player has ~55 % win chance at own tour level; adjusts slightly by level.
        win_chance = 0.50 + (player_level - 3) * 0.03
        if random.random() < max(0.30, min(0.75, win_chance)):
            self.singles_result = "win"
            self.team_points_home += 1
        else:
            self.singles_result = "loss"
            self.team_points_away += 1

    @property
    def home_won(self) -> bool:
        return self.team_points_home > self.team_points_away


# ─────────────────────────────────────────────────────────────────────────────


class TeamEventHubState:
    """Entry screen for the International Team Event."""

    def __init__(self, game):
        self.game   = game
        self.player = game.player

        # Build the session and store it as the active tournament
        from src.data.opponents_data import get_opponent_pool
        opp_pool = [o.name for o in get_opponent_pool(self.player.tour_level)]
        session  = TeamEventSession(
            self.player.name,
            self.player.tour_level,
            opp_pool,
        )
        game.current_tournament = session

        # Record that the team event ran this career season
        cs = getattr(self.player, "career_season", 1)
        if cs not in self.player.team_event_seasons:
            self.player.team_event_seasons.append(cs)

        # ── Fonts ─────────────────────────────────────────────────────────────
        self.font_huge   = fonts.heading(48)
        self.font_title  = fonts.heading(30)
        self.font_hdr    = fonts.heading(18)
        self.font_med    = fonts.body(17)
        self.font_small  = fonts.body(14)

        # Partner selection (0 = first AI teammate, 1 = second, etc.)
        home_ai = session.team_home[1:]   # exclude the player entry
        self._partner_options = home_ai[:3]
        self._selected_partner_idx = 0

        # ── Buttons ───────────────────────────────────────────────────────────
        bw, bh = 280, 50
        self._btn_play   = pygame.Rect(SCREEN_W // 2 - bw // 2,
                                       SCREEN_H - 78, bw, bh)
        self._btn_skip   = pygame.Rect(SCREEN_W // 2 - bw // 2,
                                       SCREEN_H - 20, bw // 2 - 6, 28)
        self._hover      = None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _session(self) -> TeamEventSession:
        return self.game.current_tournament

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            p = event.pos
            self._hover = (
                "play" if self._btn_play.collidepoint(p) else
                "skip" if self._btn_skip.collidepoint(p) else
                None)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_play.collidepoint(event.pos):
                self._start_foursomes()
            elif self._btn_skip.collidepoint(event.pos):
                self._skip_event()
            else:
                self._handle_partner_click(event.pos)

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_foursomes()
            elif event.key == pygame.K_LEFT:
                self._selected_partner_idx = max(0, self._selected_partner_idx - 1)
            elif event.key == pygame.K_RIGHT:
                self._selected_partner_idx = min(
                    len(self._partner_options) - 1, self._selected_partner_idx + 1)

    def _handle_partner_click(self, pos):
        for i, r in enumerate(self._partner_rects()):
            if r.collidepoint(pos):
                self._selected_partner_idx = i
                # Update session partner choice
                self._session().player_partner = self._partner_options[i]
                break

    def _partner_rects(self) -> list:
        rects = []
        card_w, card_h = 200, 60
        total_w = len(self._partner_options) * (card_w + 12) - 12
        start_x = SCREEN_W // 2 - total_w // 2
        y = 400
        for i in range(len(self._partner_options)):
            rects.append(pygame.Rect(start_x + i * (card_w + 12), y, card_w, card_h))
        return rects

    def _start_foursomes(self):
        from src.data.tours_data import get_courses_for_tour
        from src.career.tour import get_tour_id
        from src.states.golf_round import GolfRoundState
        import random as _rnd

        p    = self.player
        tid  = get_tour_id(p.tour_level)
        courses = get_courses_for_tour(tid)
        if not courses:
            # Fallback to any available tour
            for lvl in range(p.tour_level, 0, -1):
                courses = get_courses_for_tour(get_tour_id(lvl))
                if courses:
                    break
        if not courses:
            self.game.change_state(self)
            return

        course = _rnd.choice(courses)
        self.game.change_state(GolfRoundState(self.game, course, 0, []))

    def _skip_event(self):
        """Skip the team event (simulate both days automatically)."""
        session = self._session()
        session.foursomes_active = False
        session.foursomes_player_score = session.foursomes_opp_score + random.randint(-3, 3)
        if session.foursomes_player_score <= session.foursomes_opp_score:
            session.foursomes_result = "win"
            session.team_points_home += 1
        else:
            session.foursomes_result = "loss"
            session.team_points_away += 1
        session.simulate_singles(self.player.tour_level)
        from src.states.team_event_result import TeamEventResultState
        self.game.change_state(TeamEventResultState(self.game, None, None))

    def update(self, dt): pass

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(C_BG)
        cx = SCREEN_W // 2
        session = self._session()

        # ── Header ────────────────────────────────────────────────────────────
        ty = 22
        hdr = self.font_huge.render("International Team Event", True, C_GOLD)
        surface.blit(hdr, (cx - hdr.get_width() // 2, ty)); ty += 58

        sub = self.font_med.render(
            "A once-in-a-career showdown — Home vs Away", True, C_GRAY)
        surface.blit(sub, (cx - sub.get_width() // 2, ty)); ty += 36

        # ── Team panels ───────────────────────────────────────────────────────
        pw, ph = 500, 220
        lx = cx - pw - 12
        rx = cx + 12
        panel_y = ty

        # Home
        pygame.draw.rect(surface, C_PANEL,  pygame.Rect(lx, panel_y, pw, ph), border_radius=10)
        pygame.draw.rect(surface, C_GREEN,  pygame.Rect(lx, panel_y, pw, ph), 2, border_radius=10)
        hh = self.font_hdr.render("HOME TEAM", True, C_GREEN)
        surface.blit(hh, (lx + 12, panel_y + 8))
        py2 = panel_y + 34
        for name in session.team_home:
            col = C_GOLD if name == self.player.name else C_WHITE
            ns  = self.font_small.render(
                ("  YOU — " if name == self.player.name else "  ") + name,
                True, col)
            surface.blit(ns, (lx + 12, py2)); py2 += 26

        # Away
        pygame.draw.rect(surface, C_PANEL,  pygame.Rect(rx, panel_y, pw, ph), border_radius=10)
        pygame.draw.rect(surface, C_RED,    pygame.Rect(rx, panel_y, pw, ph), 2, border_radius=10)
        ah = self.font_hdr.render("AWAY TEAM", True, C_RED)
        surface.blit(ah, (rx + 12, panel_y + 8))
        py2 = panel_y + 34
        for name in session.team_away:
            ns = self.font_small.render("  " + name, True, C_WHITE)
            surface.blit(ns, (rx + 12, py2)); py2 += 26

        # ── Partner selection ─────────────────────────────────────────────────
        ty = panel_y + ph + 18
        plbl = self.font_hdr.render(
            "Choose your Foursomes partner:", True, C_WHITE)
        surface.blit(plbl, (cx - plbl.get_width() // 2, ty)); ty += 30

        for i, (name, rect) in enumerate(
                zip(self._partner_options, self._partner_rects())):
            selected = (i == self._selected_partner_idx)
            bg  = (40, 80, 40) if selected else C_PANEL
            bdr = C_GREEN if selected else C_BORDER
            pygame.draw.rect(surface, bg,  rect, border_radius=8)
            pygame.draw.rect(surface, bdr, rect, 2, border_radius=8)
            ns  = self.font_med.render(name, True, C_WHITE if selected else C_GRAY)
            surface.blit(ns, ns.get_rect(center=rect.center))

        # ── Format info ───────────────────────────────────────────────────────
        ty = self._partner_rects()[0].bottom + 18 if self._partner_options else ty + 80
        fi = self.font_small.render(
            "Day 1: Foursomes (you & partner, alternate shots)   "
            "Day 2: Singles (simulated)", True, C_GRAY)
        surface.blit(fi, (cx - fi.get_width() // 2, ty))

        # ── Buttons ───────────────────────────────────────────────────────────
        play_bg = C_BTN_HOV if self._hover == "play" else C_BTN
        pygame.draw.rect(surface, play_bg, self._btn_play, border_radius=9)
        pygame.draw.rect(surface, C_BLUE,  self._btn_play, 2, border_radius=9)
        pl = self.font_hdr.render("Play Day 1 — Foursomes", True, C_WHITE)
        surface.blit(pl, pl.get_rect(center=self._btn_play.center))

        skip_bg = (55, 35, 35) if self._hover == "skip" else (38, 22, 22)
        pygame.draw.rect(surface, skip_bg, self._btn_skip, border_radius=6)
        sl = self.font_small.render("Skip Event", True, C_GRAY)
        surface.blit(sl, sl.get_rect(center=self._btn_skip.center))
