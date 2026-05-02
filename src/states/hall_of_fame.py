"""
HallOfFameState — win condition screen.

Shown when the player wins all 4 Majors AND reaches World Ranking #1.
Celebrates the career achievement with a full-screen congratulations display.
"""

import math
import random
import pygame

from src.career.majors   import MAJORS, MAJOR_ORDER
from src.career.rankings import rank_label
from src.golf.club       import CLUB_SETS
from src.career.tournament import TOUR_DISPLAY_NAMES
from src.ui                import fonts
from src.constants        import SCREEN_W, SCREEN_H

C_BG      = (  5,  10,   5)
C_GOLD    = (255, 215,  50)
C_GOLD2   = (210, 170,  30)
C_WHITE   = (255, 255, 255)
C_GREEN   = ( 55, 210,  55)
C_GRAY    = (150, 155, 140)
C_BTN     = ( 28,  78,  28)
C_BTN_HOV = ( 55, 140,  55)
C_BTN_RED = ( 78,  28,  28)
C_BTN_RHV = (120,  50,  50)
C_STAR    = (255, 230,  80)


class _Particle:
    """Simple confetti particle for the celebration effect."""
    __slots__ = ("x", "y", "vx", "vy", "color", "size", "life")

    def __init__(self):
        self.x     = random.uniform(0, SCREEN_W)
        self.y     = random.uniform(-40, 0)
        self.vx    = random.uniform(-60, 60)
        self.vy    = random.uniform(80, 200)
        self.color = random.choice([
            (255, 220, 50), (80, 200, 80), (80, 150, 255),
            (255, 80, 120), (255, 160, 40), (200, 80, 255),
        ])
        self.size  = random.randint(4, 9)
        self.life  = random.uniform(3.0, 7.0)

    def update(self, dt):
        self.x   += self.vx * dt
        self.y   += self.vy * dt
        self.life -= dt

    @property
    def alive(self):
        return self.life > 0 and self.y < SCREEN_H + 20


class HallOfFameState:
    """Career win screen — congratulations and career summary."""

    def __init__(self, game):
        self.game   = game
        self.player = game.player

        self.font_huge   = fonts.heading(54)
        self.font_title  = fonts.heading(34)
        self.font_hdr    = fonts.heading(18)
        self.font_med    = fonts.body(16)
        self.font_small  = fonts.body(13)

        self._hov        = None
        self._time       = 0.0
        self._particles: list[_Particle] = [_Particle() for _ in range(120)]
        self._spawn_timer = 0.0

        btn_w, btn_h = 240, 50
        gap          = 24
        total        = btn_w * 2 + gap
        bx = SCREEN_W // 2 - total // 2
        by = SCREEN_H - 70
        self._btn_continue = pygame.Rect(bx,               by, btn_w, btn_h)
        self._btn_menu     = pygame.Rect(bx + btn_w + gap, by, btn_w, btn_h)

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            self._hov = ("continue" if self._btn_continue.collidepoint(pos) else
                         "menu"     if self._btn_menu.collidepoint(pos) else None)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_continue.collidepoint(event.pos):
                self._go_hub()
            elif self._btn_menu.collidepoint(event.pos):
                self._go_menu()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._go_menu()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._go_hub()

    def _go_hub(self):
        from src.states.career_hub import CareerHubState
        self.game.change_state(CareerHubState(self.game))

    def _go_menu(self):
        from src.states.main_menu import MainMenuState
        self.game.change_state(MainMenuState(self.game))

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        self._time       += dt
        self._spawn_timer += dt

        # Spawn new confetti
        if self._spawn_timer > 0.08:
            self._spawn_timer = 0.0
            for _ in range(3):
                self._particles.append(_Particle())

        self._particles = [p for p in self._particles
                           if (p.update(dt) or True) and p.alive]

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(C_BG)
        cx = SCREEN_W // 2
        p  = self.player

        # ── Confetti ──────────────────────────────────────────────────────────
        for part in self._particles:
            pygame.draw.rect(surface, part.color,
                             pygame.Rect(int(part.x), int(part.y),
                                         part.size, part.size))

        # ── Pulsing gold border ───────────────────────────────────────────────
        pulse = int(128 + 127 * math.sin(self._time * 2.0))
        border_col = (255, pulse, 0)
        pygame.draw.rect(surface, border_col,
                         pygame.Rect(8, 8, SCREEN_W - 16, SCREEN_H - 16), 3,
                         border_radius=12)

        # ── Header ────────────────────────────────────────────────────────────
        ty = 20
        cong = self.font_huge.render("CONGRATULATIONS!", True, C_GOLD)
        surface.blit(cong, (cx - cong.get_width() // 2, ty)); ty += 56

        name_s = self.font_title.render(p.name, True, C_WHITE)
        surface.blit(name_s, (cx - name_s.get_width() // 2, ty)); ty += 40

        # Grand Slam Champion banner
        all_majors = all(m in p.majors_won for m in MAJOR_ORDER)
        if all_majors and p.world_rank == 1:
            gs = self.font_hdr.render(
                "★  GRAND SLAM CHAMPION  •  WORLD NO. 1  ★", True, C_GOLD)
            surface.blit(gs, (cx - gs.get_width() // 2, ty)); ty += 28
        else:
            ts2 = self.font_hdr.render(
                "World No. 1  •  All 4 Majors Champion", True, C_GOLD2)
            surface.blit(ts2, (cx - ts2.get_width() // 2, ty)); ty += 28

        # Stars
        ss = self.font_hdr.render("★ ★ ★ ★ ★", True, C_STAR)
        surface.blit(ss, (cx - ss.get_width() // 2, ty)); ty += 30

        # ── Four-box body layout ──────────────────────────────────────────────
        box_w = 580
        box_h = 155
        lx    = cx - box_w - 10
        rx    = cx + 10
        row1_y = ty
        row2_y = ty + box_h + 10

        # ── Top-left: Majors won ──────────────────────────────────────────────
        self._box(surface, pygame.Rect(lx, row1_y, box_w, box_h))
        mh = self.font_hdr.render("MAJOR CHAMPIONSHIPS", True, C_GOLD)
        surface.blit(mh, (lx + 12, row1_y + 7))
        my = row1_y + 30
        for mid in MAJOR_ORDER:
            info = MAJORS[mid]
            won_m = mid in p.majors_won
            icon  = "★" if won_m else "○"
            col   = C_GOLD if won_m else C_GRAY
            ms    = self.font_med.render(f"  {icon}  {info['name']}", True, col)
            surface.blit(ms, (lx + 12, my)); my += 28

        # ── Top-right: Career statistics ──────────────────────────────────────
        self._box(surface, pygame.Rect(rx, row1_y, box_w, box_h))
        sh = self.font_hdr.render("CAREER STATISTICS", True, C_GOLD)
        surface.blit(sh, (rx + 12, row1_y + 7))
        best_r = p.best_round
        best_course = next(
            (e.get("course", "") for e in reversed(p.career_log)
             if e.get("diff") == best_r and best_r is not None), "")
        best_str = (f"{best_r:+d}  {best_course}" if best_r is not None else "—")
        peak_rank = getattr(p, "world_rank_peak", p.world_rank)
        stat_rows = [
            ("Seasons",          str(p.season - 1)),
            ("Events / Wins",    f"{p.events_played} / {p.career_wins}"),
            ("Top-5 / Top-10",   f"{p.career_top5} / {p.career_top10}"),
            ("Best Round",       best_str),
            ("Career Earnings",  f"${p.total_earnings:,}"),
            ("Peak World Rank",  f"#{peak_rank}"),
        ]
        sy = row1_y + 30
        mid_x = rx + 220
        for label, val in stat_rows:
            ls = self.font_small.render(label + ":", True, C_GRAY)
            vs = self.font_small.render(val,          True, C_WHITE)
            surface.blit(ls, (rx + 12, sy))
            surface.blit(vs, (mid_x,    sy))
            sy += 20

        # ── Bottom-left: Rival & year-end awards ──────────────────────────────
        self._box(surface, pygame.Rect(lx, row2_y, box_w, box_h))
        rh = self.font_hdr.render("RIVAL & YEAR-END AWARDS", True, C_GOLD)
        surface.blit(rh, (lx + 12, row2_y + 7))
        ry = row2_y + 30

        rival = getattr(p, "rival_name", None)
        h2h   = getattr(p, "rival_head_to_head",
                        {"wins": 0, "losses": 0, "halved": 0})
        if rival:
            rv_s = self.font_small.render(
                f"Rival: {rival}   "
                f"W{h2h.get('wins',0)} / L{h2h.get('losses',0)} / H{h2h.get('halved',0)}",
                True, C_WHITE)
            surface.blit(rv_s, (lx + 12, ry)); ry += 20
        else:
            rv_s = self.font_small.render("No rival set.", True, C_GRAY)
            surface.blit(rv_s, (lx + 12, ry)); ry += 20

        ry += 4
        awards = getattr(p, "year_end_awards", [])
        if awards:
            aw_h = self.font_small.render(f"Awards won ({len(awards)}):", True, C_GOLD2)
            surface.blit(aw_h, (lx + 12, ry)); ry += 18
            # Show up to 3 most recent to leave room for arcs
            for aw in awards[-3:]:
                aw_s = self.font_small.render(f"  • {aw.replace('_', ' ').title()}", True, C_WHITE)
                surface.blit(aw_s, (lx + 12, ry)); ry += 16
        else:
            aw_s = self.font_small.render("No year-end awards.", True, C_GRAY)
            surface.blit(aw_s, (lx + 12, ry)); ry += 16

        completed_arcs = getattr(p, "completed_arcs", [])
        arc_count = len(completed_arcs)
        arc_s = self.font_small.render(
            f"Season Arcs: {arc_count} completed", True,
            C_GOLD2 if arc_count else C_GRAY)
        surface.blit(arc_s, (lx + 12, ry)); ry += 16

        # Phase 12 — team event wins
        te_wins = getattr(p, "team_event_wins", 0)
        te_s = self.font_small.render(
            f"Team Event Wins: {te_wins}", True,
            C_GOLD2 if te_wins else C_GRAY)
        surface.blit(te_s, (lx + 12, ry))

        # ── Bottom-right: Achievements ────────────────────────────────────────
        from src.career.player import ACHIEVEMENTS
        self._box(surface, pygame.Rect(rx, row2_y, box_w, box_h))
        ah = self.font_hdr.render("ACHIEVEMENTS", True, C_GOLD)
        surface.blit(ah, (rx + 12, row2_y + 7))
        earned = [k for k in p.achievements if k in ACHIEVEMENTS]
        total_ach = len(ACHIEVEMENTS)
        cnt_s = self.font_small.render(
            f"{len(earned)} / {total_ach} unlocked", True, C_WHITE)
        surface.blit(cnt_s, (rx + 12, row2_y + 30))
        # Two columns of achievement names
        half   = (len(earned) + 1) // 2
        col1   = earned[:half]
        col2   = earned[half:half * 2]
        ay     = row2_y + 50
        acol1x = rx + 12
        acol2x = rx + box_w // 2 + 10
        max_rows = (box_h - 55) // 16
        for i in range(min(max_rows, len(col1))):
            lbl = ACHIEVEMENTS[col1[i]]["label"]
            s   = self.font_small.render(f"★ {lbl}", True, C_GOLD2)
            surface.blit(s, (acol1x, ay + i * 16))
        for i in range(min(max_rows, len(col2))):
            lbl = ACHIEVEMENTS[col2[i]]["label"]
            s   = self.font_small.render(f"★ {lbl}", True, C_GOLD2)
            surface.blit(s, (acol2x, ay + i * 16))

        # ── Quote ─────────────────────────────────────────────────────────────
        q_y = row2_y + box_h + 14
        quote = f'"{p.name} — the greatest golfer of a generation."'
        qs = self.font_small.render(quote, True, (160, 160, 120))
        surface.blit(qs, (cx - qs.get_width() // 2, q_y))

        # ── Buttons ───────────────────────────────────────────────────────────
        cont_bg = C_BTN_HOV if self._hov == "continue" else C_BTN
        pygame.draw.rect(surface, cont_bg, self._btn_continue, border_radius=8)
        pygame.draw.rect(surface, C_GREEN, self._btn_continue, 2, border_radius=8)
        cl = self.font_hdr.render("Continue Career", True, C_WHITE)
        surface.blit(cl, cl.get_rect(center=self._btn_continue.center))

        menu_bg = C_BTN_RHV if self._hov == "menu" else C_BTN_RED
        pygame.draw.rect(surface, menu_bg, self._btn_menu, border_radius=8)
        pygame.draw.rect(surface, (200, 60, 60), self._btn_menu, 2, border_radius=8)
        ml = self.font_hdr.render("Main Menu", True, C_WHITE)
        surface.blit(ml, ml.get_rect(center=self._btn_menu.center))

    def _box(self, surface, r: pygame.Rect):
        pygame.draw.rect(surface, (18, 28, 18), r, border_radius=8)
        pygame.draw.rect(surface, C_GOLD2,       r, 1, border_radius=8)
