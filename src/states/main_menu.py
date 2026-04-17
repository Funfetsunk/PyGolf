"""
MainMenuState — the title / start screen.

Buttons
-------
  New Game  → CharacterCreationState
  Load Game → shows save slots (or grayed out if no saves exist)
  Quit
"""

import os
import sys

import pygame

from src.utils.save_system import list_saves, get_save_preview, load_game

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG        = (  6,  12,   6)
C_PANEL     = ( 14,  22,  14)
C_TITLE     = (168, 224,  88)
C_SUB       = (100, 148,  60)
C_BTN       = ( 28,  78,  28)
C_BTN_HOV   = ( 48, 120,  48)
C_BTN_DIS   = ( 32,  44,  32)
C_BORDER    = ( 58,  98,  58)
C_BORDER_DIS= ( 48,  60,  48)
C_WHITE     = (255, 255, 255)
C_GRAY      = (130, 130, 130)
C_GOLD      = (210, 170,  30)
C_RED       = (200,  55,  55)

SCREEN_W = 1280
SCREEN_H = 720

TOUR_NAMES = {
    1: "Amateur Circuit",
    2: "Challenger Tour",
    3: "Development Tour",
    4: "Continental Tour",
    5: "World Tour",
    6: "The Grand Tour",
}


class MainMenuState:
    """Title screen — new game, load game, quit."""

    def __init__(self, game):
        self.game = game

        self.font_title  = pygame.font.SysFont("arial", 72, bold=True)
        self.font_sub    = pygame.font.SysFont("arial", 22)
        self.font_btn    = pygame.font.SysFont("arial", 24, bold=True)
        self.font_medium = pygame.font.SysFont("arial", 18)
        self.font_small  = pygame.font.SysFont("arial", 14)

        self._saves       = list_saves()
        self._previews    = [get_save_preview(p) for p in self._saves[:5]]
        self._hovered_btn = None
        self._hovered_save= None
        self._show_saves  = False   # True = save-slot panel is open

        cx = SCREEN_W // 2
        bw, bh = 300, 56

        self._btn_new  = pygame.Rect(cx - bw // 2, 340, bw, bh)
        self._btn_load = pygame.Rect(cx - bw // 2, 414, bw, bh)
        self._btn_quit = pygame.Rect(cx - bw // 2, 488, bw, bh)

        # Save-slot panel (shown when Load is clicked and saves exist)
        sp_w, sp_h = 520, 380
        self._save_panel = pygame.Rect(
            cx - sp_w // 2, (SCREEN_H - sp_h) // 2, sp_w, sp_h)
        self._save_rects: list[pygame.Rect] = []
        self._btn_cancel = pygame.Rect(
            self._save_panel.centerx - 100,
            self._save_panel.bottom - 52,
            200, 38)

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event):
        if self._show_saves:
            self._handle_save_panel_event(event)
            return

        if event.type == pygame.MOUSEMOTION:
            p = event.pos
            self._hovered_btn = None
            for name, rect in [("new", self._btn_new),
                                ("load", self._btn_load),
                                ("quit", self._btn_quit)]:
                if rect.collidepoint(p):
                    self._hovered_btn = name

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            p = event.pos
            if self._btn_new.collidepoint(p):
                self._go_new_game()
            elif self._btn_load.collidepoint(p) and self._saves:
                if len(self._saves) == 1:
                    self._load_save(self._previews[0])
                else:
                    self._show_saves = True
            elif self._btn_quit.collidepoint(p):
                pygame.quit()
                sys.exit()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n:
                self._go_new_game()
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    def _handle_save_panel_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hovered_save = None
            for i, r in enumerate(self._save_rects):
                if r.collidepoint(event.pos):
                    self._hovered_save = i

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_cancel.collidepoint(event.pos):
                self._show_saves = False
                return
            for i, r in enumerate(self._save_rects):
                if r.collidepoint(event.pos):
                    self._load_save(self._previews[i])
                    return
            # Click outside panel = cancel
            if not self._save_panel.collidepoint(event.pos):
                self._show_saves = False

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._show_saves = False

    # ── Actions ───────────────────────────────────────────────────────────────

    def _go_new_game(self):
        from src.states.character_creation import CharacterCreationState
        self.game.change_state(CharacterCreationState(self.game))

    def _load_save(self, preview: dict):
        try:
            player = load_game(preview["path"])
        except Exception as e:
            print(f"Failed to load save: {e}")
            return
        self.game.player = player
        self._launch_round()

    def _launch_round(self):
        from src.data.courses_data import make_greenfields_course
        from src.states.golf_round import GolfRoundState
        course = make_greenfields_course()
        self.game.change_state(GolfRoundState(self.game, course, 0, []))

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        pass

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(C_BG)

        cx = SCREEN_W // 2

        # ── Title ─────────────────────────────────────────────────────────────
        title = self.font_title.render("Let's Golf!", True, C_TITLE)
        surface.blit(title, (cx - title.get_width() // 2, 150))

        sub = self.font_sub.render("A Career Golf Adventure", True, C_SUB)
        surface.blit(sub, (cx - sub.get_width() // 2, 248))

        # ── Buttons ───────────────────────────────────────────────────────────
        load_disabled = not self._saves

        for name, rect, label in [
            ("new",  self._btn_new,  "New Game"),
            ("load", self._btn_load, "Load Game"),
            ("quit", self._btn_quit, "Quit"),
        ]:
            disabled = (name == "load" and load_disabled)
            hovered  = self._hovered_btn == name and not disabled
            bg   = C_BTN_DIS if disabled else (C_BTN_HOV if hovered else C_BTN)
            bord = C_BORDER_DIS if disabled else C_BORDER
            pygame.draw.rect(surface, bg,   rect, border_radius=8)
            pygame.draw.rect(surface, bord, rect, 2, border_radius=8)
            tc = C_GRAY if disabled else C_WHITE
            lbl = self.font_btn.render(label, True, tc)
            surface.blit(lbl, lbl.get_rect(center=rect.center))

        # Hint below load button
        if load_disabled:
            hint = self.font_small.render("No save files found", True, (70, 85, 70))
        else:
            info = self._previews[0]
            tour = TOUR_NAMES.get(info.get("tour_level", 1), "Amateur Circuit")
            hint = self.font_small.render(
                f"Last: {info['name']}  •  {tour}  •  "
                f"{info.get('events_played', 0)} events played",
                True, (90, 140, 70))
        surface.blit(hint, (cx - hint.get_width() // 2,
                            self._btn_load.bottom + 6))

        # Controls hint at bottom
        ctrl = self.font_small.render(
            "N = New Game   •   Esc = Quit", True, (55, 75, 55))
        surface.blit(ctrl, (cx - ctrl.get_width() // 2, SCREEN_H - 30))

        # ── Save panel overlay ────────────────────────────────────────────────
        if self._show_saves:
            self._draw_save_panel(surface)

    def _draw_save_panel(self, surface):
        # Dim background
        dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        surface.blit(dim, (0, 0))

        r = self._save_panel
        pygame.draw.rect(surface, C_PANEL,  r, border_radius=10)
        pygame.draw.rect(surface, C_BORDER, r, 2, border_radius=10)

        title = self.font_btn.render("Select Save File", True, C_WHITE)
        surface.blit(title, (r.centerx - title.get_width() // 2, r.y + 16))

        pygame.draw.line(surface, C_BORDER,
                         (r.x + 16, r.y + 46), (r.right - 16, r.y + 46))

        # Save slot rows
        self._save_rects = []
        row_h = 60
        for i, preview in enumerate(self._previews):
            slot = pygame.Rect(r.x + 16, r.y + 56 + i * (row_h + 4),
                               r.width - 32, row_h)
            self._save_rects.append(slot)
            hovered = self._hovered_save == i
            bg = (38, 68, 38) if hovered else (24, 38, 24)
            pygame.draw.rect(surface, bg, slot, border_radius=6)
            pygame.draw.rect(surface, C_BORDER, slot, 1, border_radius=6)

            name_s = self.font_medium.render(preview.get("name", "?"), True, C_WHITE)
            surface.blit(name_s, (slot.x + 12, slot.y + 8))

            tour = TOUR_NAMES.get(preview.get("tour_level", 1), "Amateur")
            info_str = (f"{preview.get('nationality', '')}   "
                        f"{tour}   "
                        f"{preview.get('events_played', 0)} events   "
                        f"${preview.get('money', 0)}")
            info_s = self.font_small.render(info_str, True, C_GRAY)
            surface.blit(info_s, (slot.x + 12, slot.y + 34))

        # Cancel button
        pygame.draw.rect(surface, (55, 30, 30), self._btn_cancel, border_radius=6)
        pygame.draw.rect(surface, C_RED, self._btn_cancel, 1, border_radius=6)
        cl = self.font_medium.render("Cancel", True, C_WHITE)
        surface.blit(cl, cl.get_rect(center=self._btn_cancel.center))
