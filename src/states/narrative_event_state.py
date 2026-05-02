"""
NarrativeEventState — full-screen modal for one-time career story events.

Shows a title, body text (word-wrapped), and two choice buttons.
On button press: applies the effect, marks the event as seen, then
transitions back to CareerHubState.
"""

import pygame

from src.constants import SCREEN_W, SCREEN_H
from src.ui import fonts

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG      = (  8,  12,  20)
C_PANEL   = ( 16,  24,  40)
C_BORDER  = ( 60,  90, 150)
C_WHITE   = (255, 255, 255)
C_GRAY    = (150, 158, 170)
C_GOLD    = (210, 175,  40)
C_GREEN   = ( 55, 185,  55)
C_BTN     = ( 25,  60, 100)
C_BTN_HOV = ( 45,  95, 150)
C_BTN_B   = ( 60,  30,  10)
C_BTN_B_H = (100,  55,  25)

_PANEL_W = 760
_PANEL_H = 420


class NarrativeEventState:
    """Full-screen story-event modal with two choices."""

    def __init__(self, game, event_dict: dict):
        self.game  = game
        self.event = event_dict

        self.font_title = fonts.heading(32)
        self.font_body  = fonts.body(18)
        self.font_btn   = fonts.body(17, bold=True)
        self.font_small = fonts.body(15)

        px = SCREEN_W // 2 - _PANEL_W // 2
        py = SCREEN_H // 2 - _PANEL_H // 2
        self._panel = pygame.Rect(px, py, _PANEL_W, _PANEL_H)

        btn_w, btn_h = 330, 50
        gap  = 20
        bx_a = px + _PANEL_W // 2 - btn_w - gap // 2
        bx_b = px + _PANEL_W // 2 + gap // 2
        by   = py + _PANEL_H - btn_h - 28
        self._btn_a = pygame.Rect(bx_a, by, btn_w, btn_h)
        self._btn_b = pygame.Rect(bx_b, by, btn_w, btn_h)

        self._hov_a = False
        self._hov_b = False

        self._result_msg   = ""
        self._result_timer = 0.0

        # Pre-wrap body text
        self._body_lines = _wrap(event_dict.get("body", ""),
                                 self.font_body, _PANEL_W - 80)

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hov_a = self._btn_a.collidepoint(event.pos)
            self._hov_b = self._btn_b.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._result_timer > 0:
                self._finish()
                return
            if self._btn_a.collidepoint(event.pos):
                self._choose("a")
            elif self._btn_b.collidepoint(event.pos):
                self._choose("b")

        elif event.type == pygame.KEYDOWN:
            if self._result_timer > 0:
                self._finish()

    def _choose(self, which: str):
        choice = self.event.get(f"choice_{which}", {})
        effect = choice.get("effect", "none")
        from src.career.narrative_handler import apply_effect
        msg = apply_effect(self.game.player, effect)
        self.event_id = self.event.get("id", "")
        if self.event_id:
            self.game.player.narrative_events_seen.append(self.event_id)
        self._result_msg   = msg or choice.get("label", "")
        self._result_timer = 2.0

    def _finish(self):
        from src.states.career_hub import CareerHubState
        self.game.change_state(CareerHubState(self.game))

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        if self._result_timer > 0:
            self._result_timer -= dt
            if self._result_timer <= 0:
                self._finish()

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        # Dim background
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, (0, 0))

        p = self._panel
        pygame.draw.rect(surface, C_PANEL,  p, border_radius=12)
        pygame.draw.rect(surface, C_BORDER, p, 2, border_radius=12)

        cx = p.centerx

        # ── Title ─────────────────────────────────────────────────────────────
        title_s = self.font_title.render(self.event.get("title", ""), True, C_GOLD)
        surface.blit(title_s, (cx - title_s.get_width() // 2, p.y + 24))

        # ── Divider ───────────────────────────────────────────────────────────
        pygame.draw.line(surface, C_BORDER,
                         (p.x + 40, p.y + 70), (p.right - 40, p.y + 70), 1)

        # ── Body text ─────────────────────────────────────────────────────────
        ty = p.y + 84
        for line in self._body_lines:
            s = self.font_body.render(line, True, C_WHITE)
            surface.blit(s, (cx - s.get_width() // 2, ty))
            ty += 24

        # ── Result message ────────────────────────────────────────────────────
        if self._result_timer > 0 and self._result_msg:
            rs = self.font_btn.render(self._result_msg, True, C_GREEN)
            surface.blit(rs, (cx - rs.get_width() // 2, ty + 16))
            return

        # ── Buttons ───────────────────────────────────────────────────────────
        self._draw_btn(surface, self._btn_a,
                       self.event.get("choice_a", {}).get("label", ""),
                       self._hov_a, C_BTN, C_BTN_HOV, C_GREEN)
        self._draw_btn(surface, self._btn_b,
                       self.event.get("choice_b", {}).get("label", ""),
                       self._hov_b, C_BTN_B, C_BTN_B_H, C_GRAY)

    def _draw_btn(self, surface, r, label, hov, c_bg, c_hov, c_border):
        pygame.draw.rect(surface, c_hov if hov else c_bg, r, border_radius=8)
        pygame.draw.rect(surface, c_border, r, 2, border_radius=8)
        s = self.font_btn.render(label, True, C_WHITE)
        surface.blit(s, s.get_rect(center=r.center))


# ── Utility ───────────────────────────────────────────────────────────────────

def _wrap(text: str, font, max_width: int) -> list[str]:
    """Word-wrap *text* to fit within *max_width* pixels."""
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines
