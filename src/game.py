"""
Game — main game class that owns the state stack and drives the update/draw loop.

The state stack works like a history list:
  - push_state()   → add a new screen on top (e.g. pause menu over game)
  - pop_state()    → go back to the previous screen
  - change_state() → replace the current screen with a new one
"""


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.state_stack = []

        # Phase 2: load the full 18-hole course and start at hole 1
        from src.data.courses_data import make_greenfields_course
        from src.states.golf_round import GolfRoundState
        course = make_greenfields_course()
        self.state_stack.append(GolfRoundState(self, course, hole_index=0, scores=[]))

    # ── State management ──────────────────────────────────────────────────────

    @property
    def current_state(self):
        """The state currently on top of the stack."""
        return self.state_stack[-1] if self.state_stack else None

    def push_state(self, state):
        """Push a new state on top (previous state is paused but not removed)."""
        self.state_stack.append(state)

    def pop_state(self):
        """Remove the top state and return to the one below it."""
        if self.state_stack:
            self.state_stack.pop()

    def change_state(self, state):
        """Replace the current top state with a new one."""
        if self.state_stack:
            self.state_stack.pop()
        self.state_stack.append(state)

    # ── Loop delegates ────────────────────────────────────────────────────────

    def handle_event(self, event):
        if self.current_state:
            self.current_state.handle_event(event)

    def update(self, dt):
        if self.current_state:
            self.current_state.update(dt)

    def draw(self):
        if self.current_state:
            self.current_state.draw(self.screen)
