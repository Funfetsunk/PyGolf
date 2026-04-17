"""
Player — the human golfer's profile, stats, inventory, and career history.
"""

from src.golf.club import STARTER_BAG

NATIONALITIES = [
    "American", "English", "Scottish", "Irish", "Welsh",
    "Australian", "South African", "Spanish", "German", "Swedish",
    "Canadian", "Japanese", "South Korean", "Argentine", "French",
    "Italian", "Danish", "Norwegian", "New Zealander", "Zimbabwean",
]

STAT_KEYS = ["power", "accuracy", "short_game", "putting", "mental", "fitness"]
BASE_STAT  = 50
MAX_STAT   = 80

STARTING_MONEY = 500


class Player:
    """Everything that persists about the human player across the career."""

    def __init__(self, name: str, nationality: str):
        self.name        = name
        self.nationality = nationality
        self.money       = STARTING_MONEY
        self.tour_level  = 1
        self.season      = 1
        self.events_played = 0
        self.career_log: list[dict] = []

        self.stats = {k: BASE_STAT for k in STAT_KEYS}

        # Clubs stored by name — reconstructed from STARTER_BAG on load
        self._club_names: list[str] = [c.name for c in STARTER_BAG]

    @property
    def clubs(self):
        """Return club objects matching _club_names from STARTER_BAG."""
        bag = {c.name: c for c in STARTER_BAG}
        return [bag[n] for n in self._club_names if n in bag]

    def set_bonus_stats(self, bonus: dict[str, int]) -> None:
        """Apply a bonus-point allocation on top of BASE_STAT."""
        for k, v in bonus.items():
            if k in self.stats:
                self.stats[k] = min(MAX_STAT, BASE_STAT + v)

    def log_round(self, course_name: str, strokes: int, par: int) -> None:
        self.career_log.append({
            "course":  course_name,
            "strokes": strokes,
            "par":     par,
            "diff":    strokes - par,
        })
        self.events_played += 1

    def earn_money(self, amount: int) -> None:
        self.money += amount

    def spend_money(self, amount: int) -> bool:
        if self.money >= amount:
            self.money -= amount
            return True
        return False

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "version":       1,
            "name":          self.name,
            "nationality":   self.nationality,
            "money":         self.money,
            "tour_level":    self.tour_level,
            "season":        self.season,
            "events_played": self.events_played,
            "stats":         dict(self.stats),
            "club_names":    list(self._club_names),
            "career_log":    list(self.career_log),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        p = cls(data["name"], data.get("nationality", "American"))
        p.money          = data.get("money", STARTING_MONEY)
        p.tour_level     = data.get("tour_level", 1)
        p.season         = data.get("season", 1)
        p.events_played  = data.get("events_played", 0)
        p.stats          = {k: data.get("stats", {}).get(k, BASE_STAT)
                            for k in STAT_KEYS}
        p._club_names    = data.get("club_names", [c.name for c in STARTER_BAG])
        p.career_log     = data.get("career_log", [])
        return p
