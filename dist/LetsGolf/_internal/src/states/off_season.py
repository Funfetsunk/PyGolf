"""
OffSeasonState — off-season activity screen shown between seasons.

Appears after the Year-End Awards ceremony before the new season begins.
The player can:
  • Train stats at a 30% discount (up to 5 actions).
  • Purchase one club set at a 20% discount.
  • Rest to recover Fitness +3.

Also shows a season recap, rival comments, arc status, and a procedurally
generated press headline.

Calls player.reset_season() when the player clicks "Start New Season",
then transitions to the new-season CareerHubState.
"""

import pygame

from src.golf.club         import CLUB_SETS, CLUB_SET_ORDER
from src.career.player     import STAT_KEYS, MAX_STAT
from src.career.tournament import TOUR_DISPLAY_NAMES
from src.constants         import SCREEN_W, SCREEN_H
from src.ui                import fonts

# ── Colours (cool winter palette — distinct from the hub's green) ─────────────
C_BG      = (  8,  12,  20)
C_PANEL   = ( 16,  24,  38)
C_BORDER  = ( 45,  70, 110)
C_HDR     = ( 22,  38,  62)
C_WHITE   = (255, 255, 255)
C_GRAY    = (130, 138, 150)
C_GOLD    = (210, 175,  35)
C_GREEN   = ( 55, 185,  55)
C_RED     = (200,  50,  50)
C_BLUE    = ( 80, 150, 220)
C_BTN     = ( 28,  55,  95)
C_BTN_HOV = ( 50,  90, 150)
C_BTN_DIS = ( 42,  48,  58)
C_BTN_GO  = ( 20,  88,  20)
C_BTN_GOH = ( 40, 140,  40)

STAT_LABELS = {
    "power":      "Power",
    "accuracy":   "Accuracy",
    "short_game": "Short Game",
    "putting":    "Putting",
    "mental":     "Mental",
    "fitness":    "Fitness",
}

MAX_TRAIN_ACTIONS = 5

# Panel geometry (absolute screen coordinates)
_RP_X, _RP_Y, _RP_W, _RP_H = 15,  80, 545, 555   # recap panel
_AP_X, _AP_Y, _AP_W, _AP_H = 575, 80, 690, 555   # activities panel
_BTN_W = 78   # right-side action buttons inside the activities panel


class OffSeasonState:
    """Off-season activity hub — train cheap, buy equipment, or rest."""

    def __init__(self, game, season_recap: dict):
        self.game    = game
        self.player  = game.player
        self._recap  = season_recap   # stats captured before reset_season

        self.font_hdr   = fonts.heading(18)
        self.font_med   = fonts.body(14)
        self.font_small = fonts.body(12)

        # Activity state (ephemeral — not persisted)
        self._train_used   = 0
        self._equip_bought = False
        self._rested       = False

        self._hov       = None
        self._msg       = ""
        self._msg_timer = 0.0

        self._build_layout()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        """Pre-compute all button rects so hit-testing is fast and in sync
        with the draw pass, which uses the same ay progression."""
        p      = self.player
        ax     = _AP_X + 12
        btn_x  = _AP_X + _AP_W - 12 - _BTN_W

        # ay mirrors the draw-pass progress through the activities panel
        ay = _AP_Y + 28 + 18   # panel header (28) + train section header (18)

        # Training buttons — one per stat
        self._train_btns: list[tuple[str, pygame.Rect]] = []
        for key in STAT_KEYS:
            self._train_btns.append((key, pygame.Rect(btn_x, ay + 3, _BTN_W, 22)))
            ay += 36

        # Equipment sale buttons — only tiers above the current set
        ay += 8 + 18   # divider gap + equipment section header
        cur_idx = CLUB_SET_ORDER.index(p.club_set_name)
        upgrades = CLUB_SET_ORDER[cur_idx + 1:]
        self._equip_btns: list[tuple[str, pygame.Rect]] = []
        if upgrades:
            for set_name in upgrades:
                self._equip_btns.append(
                    (set_name, pygame.Rect(btn_x, ay + 3, _BTN_W, 22)))
                ay += 28
        else:
            ay += 20   # "No upgrades" text placeholder

        # Rest button
        ay += 8 + 18 + 18   # divider + rest header + fitness text line
        self._btn_rest = pygame.Rect(ax, ay, 160, 26)

        # Continue button (bottom centre of screen)
        bw, bh = 320, 44
        self._btn_continue = pygame.Rect(
            SCREEN_W // 2 - bw // 2, SCREEN_H - 60, bw, bh)

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hov = self._hit_test(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hit = self._hit_test(event.pos)
            if hit == "continue":
                self._on_continue()
            elif hit == "rest":
                self._do_rest()
            elif hit and hit.startswith("train:"):
                self._do_train(hit[6:])
            elif hit and hit.startswith("buy:"):
                self._do_buy(hit[4:])

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._on_continue()

    def _hit_test(self, pos) -> str | None:
        if self._btn_continue.collidepoint(pos):
            return "continue"
        # Rest button — only active before resting
        if not self._rested and self._btn_rest.collidepoint(pos):
            return "rest"
        # Training buttons — available while actions remain
        if self._train_used < MAX_TRAIN_ACTIONS:
            for key, btn_r in self._train_btns:
                if btn_r.collidepoint(pos):
                    return f"train:{key}"
        # Equipment buttons — available before first purchase
        if not self._equip_bought:
            for sn, btn_r in self._equip_btns:
                if btn_r.collidepoint(pos):
                    return f"buy:{sn}"
        return None

    # ── Actions ───────────────────────────────────────────────────────────────

    def _do_train(self, key: str):
        p = self.player
        if self._train_used >= MAX_TRAIN_ACTIONS:
            self._flash("No training actions remaining.")
            return
        base_cost = p.training_cost(key)
        if base_cost is None:
            self._flash(f"{STAT_LABELS[key]} is already maxed.")
            return
        cost = max(1, int(base_cost * 0.7))
        if p.money < cost:
            self._flash(f"Need ${cost:,} to train {STAT_LABELS[key]}.")
            return
        p.spend_money(cost)
        p.stats[key]      = min(MAX_STAT, p.stats[key] + 1)
        self._train_used += 1
        remaining = MAX_TRAIN_ACTIONS - self._train_used
        self._flash(
            f"{STAT_LABELS[key]} → {p.stats[key]}!  (${cost:,})  •  "
            f"{remaining} action{'s' if remaining != 1 else ''} left")

    def _do_buy(self, set_name: str):
        p = self.player
        if self._equip_bought:
            self._flash("Equipment sale: one purchase per off-season.")
            return
        info = CLUB_SETS.get(set_name)
        if not info:
            return
        if info["min_tour"] > p.tour_level:
            self._flash(f"Requires Tour Level {info['min_tour']}.")
            return
        cur_idx = CLUB_SET_ORDER.index(p.club_set_name)
        tgt_idx = CLUB_SET_ORDER.index(set_name)
        if tgt_idx <= cur_idx:
            self._flash("You already own equal or better clubs.")
            return
        cost = max(1, int(info["cost"] * 0.8))
        if p.money < cost:
            self._flash(f"Need ${cost:,} for {info['label']} (sale price).")
            return
        p.spend_money(cost)
        p.club_set_name    = set_name
        self._equip_bought = True
        self._flash(f"Bought {info['label']} at 20% off!  (${cost:,})")

    def _do_rest(self):
        p = self.player
        if self._rested:
            self._flash("Already rested this off-season.")
            return
        old = p.stats["fitness"]
        p.stats["fitness"] = min(MAX_STAT, old + 3)
        self._rested       = True
        self._flash(f"Rested!  Fitness: {old} → {p.stats['fitness']}")

    def _on_continue(self):
        p = self.player
        self.game.current_tournament = None
        p.reset_season()

        from src.utils.save_system import save_game
        try:
            save_game(p)
        except Exception:
            pass

        from src.states.career_hub import CareerHubState
        self.game.change_state(CareerHubState(self.game))

    def _flash(self, msg: str):
        self._msg       = msg
        self._msg_timer = 3.5

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float):
        if self._msg_timer > 0:
            self._msg_timer -= dt

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(C_BG)
        p  = self.player
        cx = SCREEN_W // 2

        # ── Title & headline ──────────────────────────────────────────────────
        title_s = self.font_hdr.render(
            f"Off-Season  •  After Season {self._recap.get('season', p.season)}",
            True, C_BLUE)
        surface.blit(title_s, (cx - title_s.get_width() // 2, 12))

        hl  = _generate_headline(p, self._recap)
        hs  = self.font_small.render(hl, True, (160, 160, 120))
        surface.blit(hs, (cx - hs.get_width() // 2, 38))
        pygame.draw.line(surface, C_BORDER, (15, 68), (SCREEN_W - 15, 68), 1)

        # ── Recap panel ───────────────────────────────────────────────────────
        rp = pygame.Rect(_RP_X, _RP_Y, _RP_W, _RP_H)
        pygame.draw.rect(surface, C_PANEL, rp, border_radius=6)
        pygame.draw.rect(surface, C_BORDER, rp, 1, border_radius=6)
        self._section_hdr(surface, "SEASON RECAP", rp.x, rp.y, rp.width)

        recap = self._recap
        lx, ty = rp.x + 12, rp.y + 36
        vx     = rp.x + 220

        tour_name = TOUR_DISPLAY_NAMES.get(recap.get("tour_level", p.tour_level), "Tour")
        pos       = recap.get("position", "?")
        pos_str   = (f"{pos}{_ordinal_suffix(pos)}" if isinstance(pos, int) else str(pos))

        recap_rows = [
            ("Season",          str(recap.get("season", p.season))),
            ("Tour",            tour_name),
            ("Events Played",   str(recap.get("events_played", 0))),
            ("Final Standing",  pos_str),
            ("Season Points",   str(recap.get("season_points", 0))),
            ("Career Wins",     str(p.career_wins)),
            ("Career Earnings", f"${p.total_earnings:,}"),
        ]
        for label, val in recap_rows:
            ls = self.font_small.render(label + ":", True, C_GRAY)
            vs = self.font_small.render(val, True, C_WHITE)
            surface.blit(ls, (lx, ty))
            surface.blit(vs, (vx, ty))
            ty += 20

        # Promotion banner
        if recap.get("promoted"):
            new_tour = TOUR_DISPLAY_NAMES.get(recap.get("new_tour_level"), "Tour")
            ty += 6
            prom_s = self.font_hdr.render(f"★  Promoted to {new_tour}!", True, C_GOLD)
            surface.blit(prom_s, (lx, ty)); ty += 26

        ty += 8

        # Rival comment
        rival = getattr(p, "rival_name", None)
        if rival:
            pygame.draw.line(surface, C_BORDER, (lx, ty), (rp.right - 12, ty), 1)
            ty += 8
            rh = self.font_small.render("RIVAL UPDATE", True, C_GOLD)
            surface.blit(rh, (lx, ty)); ty += 16
            h2h = getattr(p, "rival_head_to_head",
                          {"wins": 0, "losses": 0, "halved": 0})
            rv_s = self.font_small.render(
                f"{rival}  —  "
                f"W{h2h.get('wins',0)} / L{h2h.get('losses',0)} / H{h2h.get('halved',0)}",
                True, C_WHITE)
            surface.blit(rv_s, (lx, ty)); ty += 18
            rc_s = self.font_small.render(
                _rival_comment(p, recap), True, C_GRAY)
            surface.blit(rc_s, (lx, ty)); ty += 20

        ty += 4

        # Arc status
        try:
            from src.data.narrative_events import get_arc
            arc = get_arc(getattr(p, "current_arc_id", None))
            if arc:
                pygame.draw.line(surface, C_BORDER,
                                 (lx, ty), (rp.right - 12, ty), 1)
                ty += 8
                arc_done = getattr(p, "arc_completed", False)
                arc_col  = C_GREEN if arc_done else C_GOLD
                arc_s    = self.font_small.render(
                    f"Arc: {arc['title']}  "
                    f"{'✓ Complete' if arc_done else '○ In progress'}",
                    True, arc_col)
                surface.blit(arc_s, (lx, ty)); ty += 18
        except Exception:
            pass

        ty += 4

        # Fitness degradation warning
        career_s = getattr(p, "career_season", p.season)
        if career_s >= 5:
            pygame.draw.line(surface, C_BORDER, (lx, ty), (rp.right - 12, ty), 1)
            ty += 8
            deg_s = self.font_small.render(
                f"Season {career_s} of your career — "
                f"Fitness will decline by 1 this off-season.",
                True, C_RED)
            surface.blit(deg_s, (lx, ty))

        # ── Activities panel ──────────────────────────────────────────────────
        ap = pygame.Rect(_AP_X, _AP_Y, _AP_W, _AP_H)
        pygame.draw.rect(surface, C_PANEL, ap, border_radius=6)
        pygame.draw.rect(surface, C_BORDER, ap, 1, border_radius=6)
        self._section_hdr(surface, "OFF-SEASON ACTIVITIES",
                          ap.x, ap.y, ap.width)

        ax = ap.x + 12
        ay = ap.y + 28   # just below section header

        # ── Training ─────────────────────────────────────────────────────────
        remain   = MAX_TRAIN_ACTIONS - self._train_used
        tr_label = (f"TRAINING  (30% off  •  {remain}/{MAX_TRAIN_ACTIONS} actions left)"
                    if remain > 0
                    else "TRAINING  (no actions remaining)")
        tr_hdr = self.font_small.render(
            tr_label, True, C_GOLD if remain > 0 else C_GRAY)
        surface.blit(tr_hdr, (ax, ay)); ay += 18

        for key, btn_r in self._train_btns:
            val      = p.stats[key]
            base_c   = p.training_cost(key)
            maxed    = (base_c is None)
            disc_c   = None if maxed else max(1, int(base_c * 0.7))
            exhausted = (remain == 0)

            ls = self.font_small.render(
                f"{STAT_LABELS[key]}: {val}",
                True, C_GRAY if maxed else C_WHITE)
            surface.blit(ls, (ax, ay + 4))

            if maxed:
                cost_txt, cc = "MAX", C_GRAY
            elif exhausted or p.money < (disc_c or 0):
                cost_txt, cc = f"${disc_c:,}", C_GRAY
            else:
                cost_txt, cc = f"${disc_c:,}", C_GOLD
            cs = self.font_small.render(cost_txt, True, cc)
            surface.blit(cs, (ax + 200, ay + 4))

            can = (not maxed) and (not exhausted) and p.money >= (disc_c or 0)
            hk  = f"train:{key}"
            bg  = (C_BTN_DIS if (maxed or exhausted or not can)
                   else C_BTN_HOV if self._hov == hk else C_BTN)
            pygame.draw.rect(surface, bg, btn_r, border_radius=4)
            pygame.draw.rect(surface, C_BORDER, btn_r, 1, border_radius=4)
            bl = self.font_small.render(
                "+1", True,
                C_GRAY if (maxed or exhausted or not can) else C_WHITE)
            surface.blit(bl, bl.get_rect(center=btn_r.center))
            ay += 36

        # ── Equipment sale ────────────────────────────────────────────────────
        pygame.draw.line(surface, C_BORDER,
                         (ax, ay + 4), (ap.right - 12, ay + 4), 1)
        ay += 12
        eq_label = ("EQUIPMENT SALE  (20% off  •  one purchase per off-season)"
                    if not self._equip_bought
                    else "EQUIPMENT SALE  (purchase made)")
        eq_hdr = self.font_small.render(
            eq_label, True, C_GOLD if not self._equip_bought else C_GRAY)
        surface.blit(eq_hdr, (ax, ay)); ay += 18

        if self._equip_btns:
            cur_idx = CLUB_SET_ORDER.index(p.club_set_name)
            for set_name, btn_r in self._equip_btns:
                info    = CLUB_SETS[set_name]
                locked  = info["min_tour"] > p.tour_level
                tgt_idx = CLUB_SET_ORDER.index(set_name)
                owned   = tgt_idx <= cur_idx
                disc_c  = max(1, int(info["cost"] * 0.8))
                can_buy = (not self._equip_bought and not locked
                           and not owned and p.money >= disc_c)

                col  = C_GOLD if owned else (C_GRAY if locked else C_WHITE)
                name_s = self.font_small.render(
                    f"{info['label']}  "
                    f"(was ${info['cost']:,}  →  ${disc_c:,})",
                    True, col)
                surface.blit(name_s, (ax, ay + 4))

                hk = f"buy:{set_name}"
                if owned:
                    bg, bt, tc = C_BTN_DIS, "Owned", C_GREEN
                elif self._equip_bought or locked:
                    bg, bt, tc = C_BTN_DIS, "Locked" if locked else "—", C_GRAY
                else:
                    bg = C_BTN_HOV if self._hov == hk else (C_BTN if can_buy
                                                             else C_BTN_DIS)
                    bt, tc = "Buy", (C_WHITE if can_buy else C_GRAY)
                pygame.draw.rect(surface, bg, btn_r, border_radius=4)
                pygame.draw.rect(surface, C_BORDER, btn_r, 1, border_radius=4)
                bl = self.font_small.render(bt, True, tc)
                surface.blit(bl, bl.get_rect(center=btn_r.center))
                ay += 28
        else:
            ns = self.font_small.render("No upgrades available", True, C_GRAY)
            surface.blit(ns, (ax, ay)); ay += 20

        # ── Rest ─────────────────────────────────────────────────────────────
        pygame.draw.line(surface, C_BORDER,
                         (ax, ay + 6), (ap.right - 12, ay + 6), 1)
        ay += 14
        rest_label = ("REST  (Fitness +3  •  once per off-season)"
                      if not self._rested else "REST  (done)")
        rest_hdr = self.font_small.render(
            rest_label, True, C_GOLD if not self._rested else C_GRAY)
        surface.blit(rest_hdr, (ax, ay)); ay += 18

        fit_val = p.stats["fitness"]
        fit_s   = self.font_small.render(
            f"Current Fitness: {fit_val}  •  Max: {MAX_STAT}",
            True, C_WHITE)
        surface.blit(fit_s, (ax, ay)); ay += 18

        hk      = "rest"
        rest_bg = (C_BTN_DIS if self._rested
                   else C_BTN_HOV if self._hov == hk else C_BTN)
        pygame.draw.rect(surface, rest_bg, self._btn_rest, border_radius=4)
        pygame.draw.rect(surface, C_BORDER, self._btn_rest, 1, border_radius=4)
        rl_s = self.font_small.render(
            "Rested!" if self._rested else "Take a Rest Week",
            True, C_GRAY if self._rested else C_WHITE)
        surface.blit(rl_s, rl_s.get_rect(center=self._btn_rest.center))

        # ── Flash message ─────────────────────────────────────────────────────
        if self._msg_timer > 0:
            ms  = self.font_small.render(self._msg, True, C_GOLD)
            pad = 14
            ban = pygame.Rect(
                cx - ms.get_width() // 2 - pad,
                SCREEN_H - 120,
                ms.get_width() + pad * 2, 24)
            pygame.draw.rect(surface, (12, 16, 24), ban, border_radius=4)
            pygame.draw.rect(surface, C_GOLD, ban, 1, border_radius=4)
            surface.blit(ms, ms.get_rect(center=ban.center))

        # ── Continue button ───────────────────────────────────────────────────
        bg = C_BTN_GOH if self._hov == "continue" else C_BTN_GO
        pygame.draw.rect(surface, bg, self._btn_continue, border_radius=8)
        pygame.draw.rect(surface, C_GREEN, self._btn_continue, 2, border_radius=8)
        cl = self.font_hdr.render("Start New Season  →", True, C_WHITE)
        surface.blit(cl, cl.get_rect(center=self._btn_continue.center))

    def _section_hdr(self, surface, label, x, y, w):
        pygame.draw.rect(surface, C_HDR,
                         pygame.Rect(x, y, w, 28), border_radius=6)
        ts = self.font_small.render(label, True, (120, 170, 220))
        surface.blit(ts, (x + 10, y + 7))


# ── Module-level helpers ──────────────────────────────────────────────────────

def _ordinal_suffix(n: int) -> str:
    s = {1: "st", 2: "nd", 3: "rd"}.get(
        n % 10 if n % 100 not in (11, 12, 13) else 0, "th")
    return s


def _generate_headline(p, recap: dict) -> str:
    """Procedural press headline based on the season just completed."""
    pos  = recap.get("position", 99)
    wins = p.career_wins
    name = p.name
    if pos == 1:
        return f'"{name} closes the season as the dominant force in the standings."'
    elif pos <= 3:
        return f'"{name} posts a strong top-3 campaign — a contender for the year ahead."'
    elif pos <= 8:
        if wins >= 1:
            return f'"{name} showed flashes of brilliance — the wins are there."'
        return f'"{name} puts together a solid season amid stiff competition."'
    elif wins >= 3:
        return (f'"Despite the standings, {name} has the wins '
                f'to silence any doubters."')
    elif wins >= 1:
        return f'"{name} had moments to savour — the goal is more of the same."'
    else:
        return f'"{name} will be looking to hit the ground running next season."'


def _rival_comment(p, recap: dict) -> str:
    """Short comment on the season-long rivalry."""
    rival = getattr(p, "rival_name", None)
    if not rival:
        return ""
    h2h    = getattr(p, "rival_head_to_head",
                     {"wins": 0, "losses": 0, "halved": 0})
    wins   = h2h.get("wins",   0)
    losses = h2h.get("losses", 0)
    if wins > losses:
        return f"You had the edge on {rival} this season."
    elif losses > wins:
        return f"{rival} had the better of you this time around."
    else:
        return f"An even battle with {rival} — more of the same expected."
