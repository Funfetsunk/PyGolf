"""
YearEndAwardsState — end-of-season ceremony before the new season begins.

Three awards are evaluated:
  Player of the Year   — highest season ranking points
  Rookie of the Year   — top-5 finish on Tours 1-2, first season on that tour
  Comeback Player      — improved finishing position by 5+ places vs last season

Applies reward money / reputation when the player wins, records the award in
player.year_end_awards, stores the player's finishing position as
previous_season_position for future comeback calculations, then calls
player.reset_season() and transitions to CareerHubState.
"""

import pygame

from src.constants import SCREEN_W, SCREEN_H
from src.ui        import fonts

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG      = ( 10,  16,  10)
C_PANEL   = ( 18,  28,  18)
C_PANEL_W = ( 22,  38,  22)  # "you won" card tint
C_PANEL_L = ( 28,  22,  14)  # "loss" card tint
C_PANEL_N = ( 18,  22,  26)  # "not eligible" card tint
C_BORDER  = ( 55,  90,  55)
C_BORDER_W= (180, 150,  20)
C_WHITE   = (255, 255, 255)
C_GRAY    = (130, 138, 120)
C_GREEN   = ( 55, 185,  55)
C_GOLD    = (210, 170,  30)
C_RED     = (200,  55,  55)
C_BTN     = ( 28,  75,  28)
C_BTN_H   = ( 50, 120,  50)

_CARD_W = 370
_CARD_H = 320
_CARD_Y = 140
_GAP    = 35
# total span = 3 * 370 + 2 * 35 = 1180, centred in 1280 → x0 = 50
_CARD_X0 = (SCREEN_W - 3 * _CARD_W - 2 * _GAP) // 2


def _build_standings(player) -> list[tuple[int, str]]:
    """Return sorted (points, name) list — highest first."""
    entries = [(player.season_points, "You")]
    for name, pts in player.opp_season_points.items():
        entries.append((pts, name))
    return sorted(entries, key=lambda e: (-e[0], e[1]))


def _player_position(standings: list[tuple[int, str]]) -> int:
    for i, (_, name) in enumerate(standings):
        if name == "You":
            return i + 1
    return len(standings)


class YearEndAwardsState:
    """End-of-season awards ceremony."""

    def __init__(self, game, promotion_info: dict, is_qschool: bool = False):
        self.game           = game
        self.player         = game.player
        self._promo_info    = promotion_info or {}
        self._is_qschool    = is_qschool

        self.font_title  = fonts.heading(30)
        self.font_hdr    = fonts.heading(18)
        self.font_med    = fonts.body(15)
        self.font_small  = fonts.body(13)

        p = self.player
        standings         = _build_standings(p)
        self._player_pos  = _player_position(standings)
        self._standings   = standings

        # ── Compute each award ────────────────────────────────────────────────
        self._awards = [
            self._compute_poy(standings),
            self._compute_roty(standings),
            self._compute_cpoy(),
        ]

        self._hov  = None
        bw, bh = 300, 48
        self._btn = pygame.Rect(SCREEN_W // 2 - bw // 2, SCREEN_H - 72, bw, bh)

    # ── Award computation ─────────────────────────────────────────────────────

    def _compute_poy(self, standings: list) -> dict:
        """Player of the Year — highest season points."""
        winner_pts, winner_name = standings[0] if standings else (0, "—")
        player_won = (winner_name == "You")

        return {
            "id":      "player_of_year",
            "title":   "Player of the Year",
            "eligible": True,
            "won":      player_won,
            "winner":   "You" if player_won else winner_name,
            "desc":     "Highest ranking points this season",
            "reward":   "+$2,000  +10 reputation" if player_won else "",
        }

    def _compute_roty(self, standings: list) -> dict:
        """Rookie of the Year — Tours 1–2, first season on this tour, top-5."""
        p   = self.player
        eligible = (p.tour_level <= 2
                    and getattr(p, "seasons_on_current_tour", 1) == 1)

        won = False
        if eligible and self._player_pos <= 5:
            won = True

        opp_roty = ""
        if eligible and not won:
            # Find top non-player finisher
            for _, name in standings[:5]:
                if name != "You":
                    opp_roty = name
                    break

        return {
            "id":       "rookie_of_year",
            "title":    "Rookie of the Year",
            "eligible":  eligible,
            "won":       won,
            "winner":    ("You" if won
                          else opp_roty if eligible
                          else "—"),
            "desc":      "First season on tour, top-5 finish",
            "reward":    "+10 reputation" if won else "",
        }

    def _compute_cpoy(self) -> dict:
        """Comeback Player — improved finishing position by 5+ places."""
        p    = self.player
        prev = getattr(p, "previous_season_position", None)
        eligible = prev is not None
        won = eligible and (self._player_pos <= prev - 5)

        return {
            "id":       "comeback_player",
            "title":    "Comeback Player",
            "eligible":  eligible,
            "won":       won,
            "winner":    "You" if won else "—",
            "desc":      (f"Improved from {prev}{_ordinal_suffix(prev)} to "
                          f"{self._player_pos}{_ordinal_suffix(self._player_pos)}"
                          if eligible
                          else "No previous season on record"),
            "reward":    "+$1,000  +5 reputation" if won else "",
        }

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hov = "btn" if self._btn.collidepoint(event.pos) else None

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn.collidepoint(event.pos):
                self._on_continue()

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._on_continue()

    def _on_continue(self):
        p    = self.player
        info = self._promo_info

        # ── Apply awards ──────────────────────────────────────────────────────
        season_label = f"S{p.season}"
        for award in self._awards:
            if award["won"]:
                aid = f"{award['id']}_{season_label}"
                p.year_end_awards.append(aid)
                if award["id"] == "player_of_year":
                    p.earn_money(2_000)
                    p.total_earnings += 2_000
                    p.gain_reputation(10)
                elif award["id"] == "rookie_of_year":
                    p.gain_reputation(10)
                elif award["id"] == "comeback_player":
                    p.earn_money(1_000)
                    p.total_earnings += 1_000
                    p.gain_reputation(5)

        # ── Store this season's finish for next year's comeback check ─────────
        p.previous_season_position = self._player_pos

        # ── Capture recap before applying promotion ───────────────────────────
        season_recap = {
            "season":         p.season,
            "tour_level":     p.tour_level,
            "season_points":  p.season_points,
            "position":       self._player_pos,
            "events_played":  p.events_this_season,
            "promoted":       bool(info.get("promoted")),
            "new_tour_level": info.get("new_level", p.tour_level),
        }

        # ── Apply promotion / relegation ──────────────────────────────────────
        if info.get("promoted"):
            p.tour_level                 = info["new_level"]
            p.qschool_pending            = False
            p.qschool_attempts_remaining = 0
            p.seasons_on_current_tour    = 0  # reset_season will increment to 1
        elif info.get("qschool_qualified"):
            p.qschool_pending            = True
            p.qschool_attempts_remaining = 2
        elif self._is_qschool and not info.get("promoted"):
            if p.qschool_attempts_remaining > 0:
                p.qschool_pending = True

        # ── Save, then hand off to OffSeasonState ─────────────────────────────
        # reset_season() is deferred to OffSeasonState._on_continue() so the
        # off-season screen has access to this season's stats before they clear.
        from src.utils.save_system import save_game
        try:
            save_game(p)
        except Exception:
            pass

        from src.states.off_season import OffSeasonState
        self.game.change_state(OffSeasonState(self.game, season_recap))

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        pass

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(C_BG)
        p  = self.player
        cx = SCREEN_W // 2

        # ── Title ─────────────────────────────────────────────────────────────
        title = self.font_title.render("Year-End Awards", True, C_GOLD)
        surface.blit(title, (cx - title.get_width() // 2, 18))

        from src.career.tournament import TOUR_DISPLAY_NAMES
        tour = TOUR_DISPLAY_NAMES.get(p.tour_level, "Tour")
        sub  = self.font_med.render(
            f"{tour}  •  Season {p.season}  •  "
            f"You finished {self._player_pos}{_ordinal_suffix(self._player_pos)}",
            True, (120, 170, 100))
        surface.blit(sub, (cx - sub.get_width() // 2, 56))

        # Season points summary
        pts = self.font_small.render(
            f"Season points: {p.season_points}", True, C_GRAY)
        surface.blit(pts, (cx - pts.get_width() // 2, 80))

        # ── Award cards ───────────────────────────────────────────────────────
        for i, award in enumerate(self._awards):
            cx_card = _CARD_X0 + i * (_CARD_W + _GAP) + _CARD_W // 2
            self._draw_card(surface,
                            _CARD_X0 + i * (_CARD_W + _GAP), _CARD_Y,
                            cx_card, award)

        # ── Continue button ───────────────────────────────────────────────────
        bg = C_BTN_H if self._hov == "btn" else C_BTN
        pygame.draw.rect(surface, bg, self._btn, border_radius=8)
        pygame.draw.rect(surface, C_GREEN, self._btn, 2, border_radius=8)
        lbl = self.font_med.render("Start New Season  >", True, C_WHITE)
        surface.blit(lbl, lbl.get_rect(center=self._btn.center))

    def _draw_card(self, surface, x, y, cx, award: dict):
        won      = award["won"]
        eligible = award["eligible"]

        # Card background & border
        card_r = pygame.Rect(x, y, _CARD_W, _CARD_H)
        if won:
            bg     = C_PANEL_W
            border = C_BORDER_W
        elif not eligible:
            bg     = C_PANEL_N
            border = (50, 58, 80)
        else:
            bg     = C_PANEL_L
            border = C_BORDER
        pygame.draw.rect(surface, bg, card_r, border_radius=10)
        pygame.draw.rect(surface, border, card_r, 2, border_radius=10)

        py = y + 14

        # Award title
        title = self.font_hdr.render(award["title"], True,
                                     C_GOLD if won else C_WHITE if eligible else C_GRAY)
        surface.blit(title, (cx - title.get_width() // 2, py)); py += 30

        # Divider
        pygame.draw.line(surface, border,
                         (x + 16, py), (x + _CARD_W - 16, py), 1)
        py += 12

        # Winner label
        wlbl = self.font_small.render("Winner", True, C_GRAY)
        surface.blit(wlbl, (cx - wlbl.get_width() // 2, py)); py += 18

        # Winner name
        wname_col = C_GOLD if won else (C_GRAY if not eligible else C_WHITE)
        wname = self.font_hdr.render(award["winner"], True, wname_col)
        surface.blit(wname, (cx - wname.get_width() // 2, py)); py += 32

        # Result tag
        if won:
            tag    = "★  YOU WIN!  ★"
            tag_col = C_GOLD
        elif not eligible:
            tag    = "Not eligible"
            tag_col = (100, 110, 140)
        else:
            tag    = "Runner-Up"
            tag_col = C_GRAY
        ts = self.font_med.render(tag, True, tag_col)
        surface.blit(ts, (cx - ts.get_width() // 2, py)); py += 28

        # Divider
        pygame.draw.line(surface, border,
                         (x + 16, py), (x + _CARD_W - 16, py), 1)
        py += 12

        # Description
        for line in _wrap(award["desc"], self.font_small, _CARD_W - 32):
            ds = self.font_small.render(line, True, C_GRAY)
            surface.blit(ds, (cx - ds.get_width() // 2, py)); py += 16

        # Reward text
        if award["reward"]:
            py += 6
            rs = self.font_small.render(award["reward"], True, C_GREEN)
            surface.blit(rs, (cx - rs.get_width() // 2, py))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ordinal_suffix(n: int) -> str:
    s = {1: "st", 2: "nd", 3: "rd"}.get(
        n % 10 if n % 100 not in (11, 12, 13) else 0, "th")
    return s


def _wrap(text: str, font, max_w: int) -> list[str]:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines
