"""
Game — main game class that owns the state stack and drives the update/draw loop.

The state stack works like a history list:
  - push_state()   → add a new screen on top (e.g. pause menu over game)
  - pop_state()    → go back to the previous screen
  - change_state() → replace the current screen (with optional fade transition)

Fade transitions
----------------
change_state(state, fade=True) triggers a black fade-out, swaps the state,
then fades back in.  Total transition time ≈ 0.45 s.
"""

import pygame


_FADE_SPEED = 560   # alpha units per second (255 / 0.45 s ≈ 567)


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.state_stack = []
        self.player = None
        self.current_tournament = None

        # Fade-transition state
        self._fade_alpha:   float           = 0.0
        self._fade_phase:   str | None      = None   # "out" | "in" | None
        self._pending_state                 = None
        self._fade_surface: pygame.Surface | None = None

        from src.states.main_menu import MainMenuState
        self.state_stack.append(MainMenuState(self))

    # ── State management ──────────────────────────────────────────────────────

    @property
    def current_state(self):
        return self.state_stack[-1] if self.state_stack else None

    def push_state(self, state):
        self.state_stack.append(state)

    def pop_state(self):
        if self.state_stack:
            self.state_stack.pop()

    def change_state(self, state, fade: bool = True):
        """Replace the current top state, optionally with a fade transition."""
        if fade and self.state_stack and self._fade_phase is None:
            self._pending_state = state
            self._fade_phase    = "out"
            self._fade_alpha    = 0.0
        else:
            # Immediate swap (used internally when fade completes, or fade=False)
            if self.state_stack:
                self.state_stack.pop()
            self.state_stack.append(state)

    # ── Loop delegates ────────────────────────────────────────────────────────

    def handle_event(self, event):
        # Block input during transition
        if self._fade_phase is not None:
            return
        if self.current_state:
            self.current_state.handle_event(event)

    def update(self, dt):
        # Update fade
        if self._fade_phase == "out":
            self._fade_alpha = min(255.0, self._fade_alpha + _FADE_SPEED * dt)
            if self._fade_alpha >= 255.0:
                # Swap the state at full black
                if self.state_stack:
                    self.state_stack.pop()
                self.state_stack.append(self._pending_state)
                self._pending_state = None
                self._fade_phase    = "in"
        elif self._fade_phase == "in":
            self._fade_alpha = max(0.0, self._fade_alpha - _FADE_SPEED * dt)
            if self._fade_alpha <= 0.0:
                self._fade_phase = None

        if self.current_state:
            self.current_state.update(dt)

    def draw(self):
        if self.current_state:
            self.current_state.draw(self.screen)

        # Overlay the fade rectangle
        if self._fade_phase is not None and self._fade_alpha > 0:
            if (self._fade_surface is None or
                    self._fade_surface.get_size() != self.screen.get_size()):
                self._fade_surface = pygame.Surface(self.screen.get_size())
                self._fade_surface.fill((0, 0, 0))
            self._fade_surface.set_alpha(int(self._fade_alpha))
            self.screen.blit(self._fade_surface, (0, 0))
