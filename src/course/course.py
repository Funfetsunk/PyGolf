"""
Course — container for an 18-hole golf course.
"""


class Course:
    """An ordered collection of Hole objects with metadata."""

    def __init__(self, name, holes):
        self.name  = name
        self.holes = holes          # list[Hole], length 1–18

    # ── Basic info ────────────────────────────────────────────────────────────

    @property
    def total_holes(self):
        return len(self.holes)

    @property
    def par(self):
        return sum(h.par for h in self.holes)

    @property
    def front_par(self):
        return sum(h.par for h in self.holes[:9])

    @property
    def back_par(self):
        return sum(h.par for h in self.holes[9:])

    # ── Access ────────────────────────────────────────────────────────────────

    def get_hole(self, index):
        """Return the Hole at zero-based index."""
        return self.holes[index]

    # ── Score helpers ────────────────────────────────────────────────────────

    def total_par_through(self, hole_count):
        """Cumulative par for the first `hole_count` holes."""
        return sum(h.par for h in self.holes[:hole_count])
