"""
Tournament — one event in a tour season.

Standard event : 1 round (18 holes).  Complete after the player finishes
                 their round.

Major event    : 2 rounds (Grand Tour only).  Complete after the player
                 finishes both rounds.

Opponents' hole-by-hole scores are pre-simulated at tournament creation so
the outcome is fixed — the player just needs to beat those scores.

Live leaderboard
----------------
get_live_leaderboard(holes_done, current_hole_scores) compares the player's
score through the first N holes against every opponent's score through the
same N holes.  This gives a fair running comparison after every hole.

Phase 1 additions
-----------------
format        : scoring format ("stroke" / "stableford" / "match" / "skins" / "proam")
green_speed   : "slow" / "normal" / "fast" / "slick"
firmness      : "soft" / "normal" / "firm" / "hard"
weather       : "clear" / "rain" / "cold" / "heat" / "fog"
pin_positions : list of per-hole pin variant names ("front"/"standard"/"tucked")
wind_strength_floor : minimum wind strength per hole (2 for majors, else 0)

Phase 3 additions
-----------------
skins         : skin_value, skins_carried, skins_won, skins_prize_per_hole
proam         : partner_scores (pre-simulated amateur best-ball per hole)

Phase 4 additions
-----------------
event_type    : "regular" | "proam" | "stableford" | "skins" | "matchplay"
                | "championship" | "major"
is_opener     : True for event 1 of the season (Pro-Am)
is_finale     : True for the season-closing Tour Championship
starting_score_offset : dict mapping names to stroke adjustments for the
                Tour Championship (top 3 in standings get -3/-2/-1)
promotion_wildcard : True when the player wins the Tour Championship
"""

# ── Scoring format constants ──────────────────────────────────────────────────
FORMAT_STROKE_PLAY = "stroke"
FORMAT_STABLEFORD  = "stableford"
FORMAT_MATCH_PLAY  = "match"
FORMAT_SKINS       = "skins"
FORMAT_PROAM       = "proam"

# ── Course condition tables ────────────────────────────────────────────────────
# Putter distance multipliers. A 40-yard putt becomes: slow=34, normal=40, fast=47, slick=54 yards.
GREEN_SPEEDS = {"slow": 0.85, "normal": 1.0, "fast": 1.18, "slick": 1.35}

FIRMNESS = {"soft": 0.70, "normal": 1.0, "firm": 1.20, "hard": 1.45}

# Base skin value per tour level (× carryover multiplier in play)
SKIN_VALUES = {1: 100, 2: 500, 3: 1_000, 4: 2_500, 5: 5_000, 6: 10_000}

WEATHER_TYPES = {
    "clear": {"acc_mod":  0.00, "dist_mod":  0.00, "roll_mod":  0.00},
    "rain":  {"acc_mod": -0.05, "dist_mod":  0.00, "roll_mod": -0.15},
    "cold":  {"acc_mod":  0.00, "dist_mod": -0.05, "roll_mod":  0.00},
    "heat":  {"acc_mod":  0.00, "dist_mod":  0.07, "roll_mod":  0.00},
    "fog":   {"acc_mod": -0.03, "dist_mod":  0.00, "roll_mod":  0.00},
}

# Prize fund (total $) per tour level
PRIZE_FUNDS = {
    1: 0,
    2: 10_000,
    3: 25_000,
    4: 75_000,
    5: 200_000,
    6: 1_000_000,
}

# Majors use their own prize fund (set in majors.py; this is a fallback)
MAJOR_PRIZE_FUND = 4_500_000

# Events per season per tour level
EVENTS_PER_SEASON = {1: 8, 2: 10, 3: 13, 4: 15, 5: 17, 6: 22}

# Top-N season-points finishes required to qualify for the Tour Championship
TOUR_CHAMPIONSHIP_QUALIFIERS = {1: 15, 2: 15, 3: 12, 4: 12, 5: 10, 6: 10}

# Top-N finish required for promotion at end of season
PROMOTION_THRESHOLD = {1: 3, 2: 5, 3: 3, 4: 5, 5: 10, 6: None}

# Prize % per finishing position (index 0 = 1st)
_PRIZE_PCTS = [
    18, 11,  7,  5,  4,
     3,  3,  3,  3,  3,
     2,  2,  2,  2,  2,  2,  2,  2,  2,  2,
     1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
]

# Season-standing points per finishing position
_SEASON_PTS = [
    100, 60, 40, 30, 25,
     15, 15, 15, 15, 15,
      8,  8,  8,  8,  8,  8,  8,  8,  8,  8,
      3,  3,  3,  3,  3,  3,  3,  3,  3,  3,
]

TOUR_DISPLAY_NAMES = {
    1: "Amateur Circuit",
    2: "Challenger Tour",
    3: "Development Tour",
    4: "Continental Tour",
    5: "World Tour",
    6: "The Grand Tour",
}

# Season-points multiplier per event type (Phase 9)
RANKING_MULTIPLIERS: dict[str, float] = {
    "regular":      1.0,
    "stableford":   1.0,
    "matchplay":    1.5,
    "skins":        0.75,
    "proam":        0.5,
    "championship": 3.0,
    "skills":       0.5,
    "major":        5.0,
    "qschool":      0.0,
}


class Tournament:
    """A single tour event — 1 round for standard events, 2 for Majors."""

    def __init__(self, name: str, tour_level: int, hole_pars: list,
                 opponents: list, is_major: bool = False,
                 event_number: int = 1, total_events: int = 8,
                 major_id: str | None = None,
                 major_prize_fund: int | None = None,
                 is_qschool: bool = False,
                 rng_seed: int | None = None,
                 course_name: str | None = None,
                 format: str = FORMAT_STROKE_PLAY,
                 event_type: str = "regular",
                 is_opener: bool = False,
                 is_finale: bool = False,
                 starting_score_offset: dict | None = None):
        import random as _random
        self.name         = name
        self.tour_level   = tour_level
        # Course this event is being played on — persisted so a mid-round save
        # can rebuild the same course on resume. None only for legacy saves.
        self.course_name  = course_name
        self.hole_pars    = list(hole_pars)
        self.course_par   = sum(hole_pars)
        self.opponents    = opponents
        self.is_major     = is_major
        self.major_id     = major_id
        self.is_qschool   = is_qschool
        # Match play uses one round per bracket match; determined before simulation.
        if format == FORMAT_MATCH_PLAY and opponents:
            self.total_rounds = min(4, max(2, len(opponents)))
        else:
            self.total_rounds = 2 if is_major else 1
        self.event_number = event_number
        self.total_events = total_events
        if is_major:
            self.prize_fund = major_prize_fund or MAJOR_PRIZE_FUND
        elif is_qschool:
            self.prize_fund = 20_000   # modest qualifier prize fund
        else:
            self.prize_fund = PRIZE_FUNDS.get(tour_level, 0)

        # Deterministic seed for opponent simulation. If the caller doesn't
        # supply one, derive a stable value from event metadata so repeated
        # construction with the same args reproduces the same field.
        if rng_seed is None:
            rng_seed = hash((name, tour_level, event_number,
                             bool(is_major), bool(is_qschool))) & 0xFFFFFFFF
        self.rng_seed = int(rng_seed)
        rng = _random.Random(self.rng_seed)

        # ── Scoring format ────────────────────────────────────────────────────
        self.format    = format
        # ── Phase 4 — schedule metadata ──────────────────────────────────────
        self.event_type            = event_type
        self.is_opener             = is_opener
        self.is_finale             = is_finale
        self.starting_score_offset: dict[str, int] = starting_score_offset or {}
        self.promotion_wildcard:    bool            = False

        # ── Match play bracket (Phase 2) ──────────────────────────────────────
        if self.format == FORMAT_MATCH_PLAY and self.opponents:
            _opp_copy = list(self.opponents)
            rng.shuffle(_opp_copy)
            self.bracket: list[str] = [o.name for o in _opp_copy[:self.total_rounds]]
        else:
            self.bracket: list[str] = []
        self.match_round:    int      = 0
        self.match_opponent: str | None = self.bracket[0] if self.bracket else None
        # Set when the tournament concludes (won or eliminated) for get_player_position()
        self.match_eliminated:      bool      = False
        self._match_final_position: int | None = None

        # ── Skins — cap field to 3 opponents (Phase 3) ───────────────────────
        if self.format == FORMAT_SKINS and len(self.opponents) > 3:
            self.opponents = self.opponents[:3]

        # ── Course conditions (Phase 1) ───────────────────────────────────────
        # Pin positions — one per hole
        _pin_choices = ["front", "standard", "standard", "tucked"]
        self.pin_positions: list[str] = (
            ["tucked"] * len(hole_pars) if is_major
            else [rng.choice(_pin_choices) for _ in hole_pars]
        )

        # Green speed
        if is_major:
            self.green_speed = rng.choice(["fast", "slick"])
        elif tour_level >= 5:
            self.green_speed = rng.choices(["normal", "fast", "fast"], k=1)[0]
        elif tour_level >= 3:
            self.green_speed = rng.choices(
                ["slow", "normal", "normal", "fast"], k=1)[0]
        else:
            self.green_speed = rng.choices(["slow", "normal", "normal"], k=1)[0]

        # Fairway firmness
        self.firmness = rng.choices(
            ["soft", "normal", "normal", "firm", "hard"],
            weights=[1, 4, 4, 2, 1], k=1)[0]

        # Weather
        if is_major:
            self.weather = rng.choices(
                ["clear", "rain", "cold", "fog"],
                weights=[5, 2, 1, 1], k=1)[0]
        else:
            self.weather = rng.choices(
                ["clear", "rain", "cold", "heat", "fog"],
                weights=[5, 2, 1, 1, 1], k=1)[0]

        # Major hard setup enforcement
        if is_major:
            self.pin_positions = ["tucked"] * len(hole_pars)
            if self.green_speed not in ("fast", "slick"):
                self.green_speed = "fast"
            self.wind_strength_floor = 2
        else:
            self.wind_strength_floor = 0

        # ── Skins / Pro-Am initial state (Phase 3) ───────────────────────────
        self.skin_value: int             = (SKIN_VALUES.get(tour_level, 500)
                                            if self.format == FORMAT_SKINS else 0)
        self.skins_carried: int          = 0
        self.skins_won: list[bool]       = [False] * len(self.hole_pars)
        self.skins_prize_per_hole: list[int] = [0] * len(self.hole_pars)
        # Amateur partner best-ball: mostly bogeys, occasional birdie
        self.partner_scores: list[int]   = (
            [max(1, p + rng.randint(-1, 3)) for p in self.hole_pars]
            if self.format == FORMAT_PROAM else []
        )

        # player_rounds[i] = list of 18 hole scores for round i
        self.player_rounds: list[list[int]] = []

        # _opp_holes[name][round_idx][hole_idx] = strokes
        self._opp_holes: dict[str, list[list[int]]] = {}
        for opp in self.opponents:
            self._opp_holes[opp.name] = [
                opp.simulate_holes(self.hole_pars, rng=rng)
                for _ in range(self.total_rounds)
            ]

    # ── Match play helpers (Phase 2) ─────────────────────────────────────────

    def get_match_status(self, player_hole_scores: list) -> dict | None:
        """
        Running hole-by-hole match play status.
        Returns dict with player_up, opp_up, holes_played, remaining, early_done.
        Returns None when format is not match play.
        """
        if self.format != FORMAT_MATCH_PLAY or self.match_opponent is None:
            return None
        opp = self.match_opponent
        rnd = self.match_round
        opp_rounds = self._opp_holes.get(opp, [])
        opp_scores = opp_rounds[min(rnd, len(opp_rounds) - 1)] if opp_rounds else []

        player_up = opp_up = 0
        n = min(len(player_hole_scores), len(opp_scores), len(self.hole_pars))
        for i in range(n):
            if player_hole_scores[i] < opp_scores[i]:
                player_up += 1
            elif player_hole_scores[i] > opp_scores[i]:
                opp_up += 1

        holes_played = n
        remaining = max(0, 18 - holes_played)
        lead = abs(player_up - opp_up)

        return {
            "player_up":   player_up,
            "opp_up":      opp_up,
            "holes_played": holes_played,
            "remaining":   remaining,
            "early_done":  lead > remaining,  # concession condition
            "opponent":    opp,
            "round":       rnd,
            "total_rounds": self.total_rounds,
        }

    def get_match_result(self, player_hole_scores: list) -> dict:
        """Final match result dict — call after all holes (or concession)."""
        st = self.get_match_status(player_hole_scores)
        if st is None:
            return {"result": "win", "margin": "w/o", "player_up": 0,
                    "opp_up": 0, "holes_played": 0, "opponent": "",
                    "round": 0, "total_rounds": 1}

        pu = st["player_up"]
        ou = st["opp_up"]
        hp = st["holes_played"]
        remaining = st["remaining"]
        diff = pu - ou

        if diff > 0:
            result = "win"
            margin = (f"{diff}&{remaining}" if remaining > 0
                      else f"{diff} UP")
        elif diff < 0:
            result = "loss"
            margin = (f"{-diff}&{remaining}" if remaining > 0
                      else f"{-diff} DOWN")
        else:
            # All square after 18 — deterministic tiebreak via rng seed
            import random as _r
            _tiebreak = _r.Random(self.rng_seed + self.match_round)
            result = "win" if _tiebreak.random() > 0.5 else "loss"
            margin = "19th hole"

        return {
            "result":       result,
            "margin":       margin,
            "player_up":    pu,
            "opp_up":       ou,
            "holes_played": hp,
            "opponent":     st["opponent"],
            "round":        st["round"],
            "total_rounds": st["total_rounds"],
        }

    def advance_bracket(self) -> bool:
        """Advance to next bracket round. Returns True if more rounds remain."""
        self.match_round += 1
        if self.match_round < len(self.bracket):
            self.match_opponent = self.bracket[self.match_round]
            return True
        self.match_opponent = None
        return False

    # ── Skins helpers (Phase 3) ──────────────────────────────────────────────

    def get_skins_result(self, hole_index: int, player_score: int) -> dict:
        """
        Evaluate the skin for this hole; update skins_carried / skins_won /
        skins_prize_per_hole.  Returns:
          {"won": bool, "skin_value": int, "carried": bool}
        player must beat ALL opponents to win the skin.
        """
        rnd = 0
        opp_scores = [
            self._opp_holes[opp.name][rnd][hole_index]
            for opp in self.opponents[:3]
            if (opp.name in self._opp_holes
                and rnd < len(self._opp_holes[opp.name])
                and hole_index < len(self._opp_holes[opp.name][rnd]))
        ]
        current_value = self.skin_value * (1 + self.skins_carried)
        player_wins   = bool(opp_scores) and all(player_score < s for s in opp_scores)

        if hole_index < len(self.skins_won):
            self.skins_won[hole_index] = player_wins
        if hole_index < len(self.skins_prize_per_hole):
            self.skins_prize_per_hole[hole_index] = current_value if player_wins else 0

        if player_wins:
            self.skins_carried = 0
        else:
            self.skins_carried += 1

        return {"won": player_wins, "skin_value": current_value, "carried": not player_wins}

    # ── Pro-Am helpers (Phase 3) ──────────────────────────────────────────────

    def get_proam_hole_score(self, player_score: int, hole_index: int) -> int:
        """Return the team score: best ball of player and pre-simulated partner."""
        if not self.partner_scores or hole_index >= len(self.partner_scores):
            return player_score
        return min(player_score, self.partner_scores[hole_index])

    # ── Stableford helpers ────────────────────────────────────────────────────

    @staticmethod
    def stableford_points(score_vs_par: int) -> int:
        """Convert a hole score vs par to Stableford points."""
        return {-3: 5, -2: 4, -1: 3, 0: 2, 1: 1}.get(score_vs_par, 0)

    def get_stableford_leaderboard(self, holes_done: int,
                                   current_hole_scores: list) -> list[dict]:
        """
        Running Stableford points leaderboard.
        Same calling convention as get_live_leaderboard; entries contain
        "points" instead of "vs_par".
        """
        completed_rounds = len(self.player_rounds)
        rnd = min(self.current_round_index, self.total_rounds - 1)

        # Player: all completed rounds + current partial
        player_pts = 0
        for r_scores in self.player_rounds:
            for h, s in enumerate(r_scores):
                player_pts += self.stableford_points(s - self.hole_pars[h])
        for h, s in enumerate(current_hole_scores):
            player_pts += self.stableford_points(s - self.hole_pars[h])

        entries = [{"name": "You", "is_player": True,
                    "points": player_pts, "thru": holes_done, "nationality": ""}]

        for opp in self.opponents:
            opp_pts = 0
            for r in range(completed_rounds):
                for h, s in enumerate(self._opp_holes[opp.name][r]):
                    opp_pts += self.stableford_points(s - self.hole_pars[h])
            if completed_rounds < self.total_rounds:
                for h in range(holes_done):
                    s = self._opp_holes[opp.name][rnd][h]
                    opp_pts += self.stableford_points(s - self.hole_pars[h])
            entries.append({"name": opp.name, "is_player": False,
                            "points": opp_pts, "thru": holes_done,
                            "nationality": opp.nationality})

        return sorted(entries, key=lambda e: (-e["points"], e["name"]))

    # ── Pin position application ──────────────────────────────────────────────

    def apply_pin_positions(self, course) -> None:
        """Apply this tournament's pin positions to every hole in the course."""
        for i in range(min(len(self.pin_positions), course.total_holes)):
            hole = course.get_hole(i)
            pos  = self.pin_positions[i]
            hole.active_pin_position = pos
            # Derive offsets: "front" moves 2 tiles toward the tee;
            # "tucked" shifts 2 tiles to the right column-wise.
            tee_row = hole.tee_pos[1]
            pin_row = hole.pin_pos[1]
            row_dir = 2 if tee_row > pin_row else -2   # toward tee
            hole._pin_offsets = {
                "front":    (0,  row_dir),
                "standard": (0,  0),
                "tucked":   (2,  0),
            }

    # ── Round tracking ────────────────────────────────────────────────────────

    @property
    def current_round_index(self) -> int:
        """0-based index of the round currently being played."""
        return len(self.player_rounds)

    @property
    def current_round_number(self) -> int:
        return self.current_round_index + 1

    def record_player_round(self, hole_scores: list) -> None:
        """Record the player's completed round (list of 18 hole scores)."""
        self.player_rounds.append(list(hole_scores))

    def is_complete(self) -> bool:
        if getattr(self, "match_eliminated", False):
            return True
        return len(self.player_rounds) >= self.total_rounds

    # ── Live leaderboard (during a round) ────────────────────────────────────

    def get_live_leaderboard(self, holes_done: int,
                             current_hole_scores: list) -> list[dict]:
        """
        Running leaderboard after `holes_done` holes of the current round.
        Everyone is compared through the same number of holes for a fair
        side-by-side ranking.

        Returns list of dicts sorted by vs_par (best first):
          name, is_player, vs_par, thru, nationality
        """
        rnd = min(self.current_round_index, self.total_rounds - 1)

        # Cumulative par and strokes from fully completed rounds
        completed_par     = rnd * self.course_par
        partial_hole_par  = sum(self.hole_pars[:holes_done])

        # Player
        prev_strokes = sum(sum(r) for r in self.player_rounds)
        curr_strokes = sum(current_hole_scores)
        player_vs_par = (prev_strokes + curr_strokes) - (completed_par + partial_hole_par)

        entries = [{
            "name":        "You",
            "is_player":   True,
            "vs_par":      player_vs_par,
            "thru":        holes_done,
            "nationality": "",
        }]

        for opp in self.opponents:
            opp_prev = sum(sum(self._opp_holes[opp.name][r]) for r in range(rnd))
            opp_curr = sum(self._opp_holes[opp.name][rnd][:holes_done])
            opp_vs_par = (opp_prev + opp_curr) - (completed_par + partial_hole_par)
            entries.append({
                "name":        opp.name,
                "is_player":   False,
                "vs_par":      opp_vs_par,
                "thru":        holes_done,
                "nationality": opp.nationality,
            })

        # Apply championship starting offsets (Phase 4)
        if self.starting_score_offset:
            for e in entries:
                e["vs_par"] += self.starting_score_offset.get(e["name"], 0)

        return sorted(entries, key=lambda e: (e["vs_par"], e["name"]))

    # ── Final leaderboard (after all rounds) ─────────────────────────────────

    def get_leaderboard(self) -> list[dict]:
        """
        Final leaderboard based on all completed rounds.
        Each entry: name, is_player, rounds (list of totals), total, vs_par, nationality
        """
        rnd_count = len(self.player_rounds)
        if rnd_count == 0:
            return []

        entries = [{
            "name":        "You",
            "is_player":   True,
            "rounds":      [sum(r) for r in self.player_rounds],
            "total":       sum(sum(r) for r in self.player_rounds),
            "vs_par":      sum(sum(r) for r in self.player_rounds) - rnd_count * self.course_par,
            "nationality": "",
        }]

        for opp in self.opponents:
            rounds = [sum(self._opp_holes[opp.name][r]) for r in range(rnd_count)]
            total  = sum(rounds)
            entries.append({
                "name":        opp.name,
                "is_player":   False,
                "rounds":      rounds,
                "total":       total,
                "vs_par":      total - rnd_count * self.course_par,
                "nationality": opp.nationality,
            })

        # Apply championship starting offsets (Phase 4)
        if self.starting_score_offset:
            for e in entries:
                offset = self.starting_score_offset.get(e["name"], 0)
                e["vs_par"] += offset
                e["total"]  += offset

        return sorted(entries, key=lambda e: (e["total"], e["name"]))

    def get_stableford_final_leaderboard(self) -> list[dict]:
        """
        Final Stableford leaderboard using per-hole opponent data.
        Each entry: name, is_player, rounds (pts per round), total, points, nationality.
        Sorted by total points descending.
        """
        rnd_count = len(self.player_rounds)
        if rnd_count == 0:
            return []

        def _player_pts_round(r_scores):
            return sum(self.stableford_points(s - self.hole_pars[h])
                       for h, s in enumerate(r_scores))

        def _opp_pts_round(name, rnd):
            return sum(self.stableford_points(s - self.hole_pars[h])
                       for h, s in enumerate(self._opp_holes[name][rnd]))

        player_rnd_pts = [_player_pts_round(r) for r in self.player_rounds]
        entries = [{
            "name":        "You",
            "is_player":   True,
            "rounds":      player_rnd_pts,
            "total":       sum(player_rnd_pts),
            "points":      sum(player_rnd_pts),
            "nationality": "",
        }]

        for opp in self.opponents:
            rnd_pts = [_opp_pts_round(opp.name, r) for r in range(rnd_count)]
            entries.append({
                "name":        opp.name,
                "is_player":   False,
                "rounds":      rnd_pts,
                "total":       sum(rnd_pts),
                "points":      sum(rnd_pts),
                "nationality": opp.nationality,
            })

        return sorted(entries, key=lambda e: (-e["total"], e["name"]))

    def get_player_position(self) -> int:
        if self.format == FORMAT_MATCH_PLAY:
            if self._match_final_position is not None:
                return self._match_final_position
            return len(self.opponents) + 1
        lb = (self.get_stableford_final_leaderboard()
              if self.format == FORMAT_STABLEFORD
              else self.get_leaderboard())
        for i, e in enumerate(lb):
            if e["is_player"]:
                return i + 1
        return len(self.opponents) + 1

    # ── Prize / points ────────────────────────────────────────────────────────

    def get_prize_money(self, position: int) -> int:
        if self.prize_fund == 0:
            return 0
        idx = min(position - 1, len(_PRIZE_PCTS) - 1)
        return int(self.prize_fund * _PRIZE_PCTS[idx] / 100)

    def get_season_points(self, position: int) -> int:
        idx  = min(position - 1, len(_SEASON_PTS) - 1)
        base = _SEASON_PTS[idx]
        mult = RANKING_MULTIPLIERS.get(self.event_type, 1.0)
        return int(base * mult)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "name":                 self.name,
            "tour_level":           self.tour_level,
            "hole_pars":            self.hole_pars,
            "is_major":             self.is_major,
            "major_id":             self.major_id,
            "is_qschool":           self.is_qschool,
            "total_rounds":         self.total_rounds,
            "event_number":         self.event_number,
            "total_events":         self.total_events,
            "prize_fund":           self.prize_fund,
            "rng_seed":             self.rng_seed,
            "course_name":          self.course_name,
            "player_rounds":        [list(r) for r in self.player_rounds],
            "opp_holes":            {k: [list(r) for r in v]
                                     for k, v in self._opp_holes.items()},
            "opponents":            [o.to_dict() for o in self.opponents],
            # Phase 1 fields
            "format":               self.format,
            "pin_positions":        list(self.pin_positions),
            "green_speed":          self.green_speed,
            "firmness":             self.firmness,
            "weather":              self.weather,
            "wind_strength_floor":  self.wind_strength_floor,
            # Phase 2 — match play
            "bracket":              list(self.bracket),
            "match_round":          self.match_round,
            "match_opponent":       self.match_opponent,
            "match_eliminated":     self.match_eliminated,
            "_match_final_position": self._match_final_position,
            # Phase 3 — skins / pro-am
            "skin_value":           self.skin_value,
            "skins_carried":        self.skins_carried,
            "skins_won":            list(self.skins_won),
            "skins_prize_per_hole": list(self.skins_prize_per_hole),
            "partner_scores":       list(self.partner_scores),
            # Phase 4 — schedule metadata
            "event_type":             self.event_type,
            "is_opener":              self.is_opener,
            "is_finale":              self.is_finale,
            "starting_score_offset":  dict(self.starting_score_offset),
            "promotion_wildcard":     self.promotion_wildcard,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tournament":
        from src.career.opponent import Opponent
        opponents = [Opponent.from_dict(o) for o in data["opponents"]]

        t = cls.__new__(cls)
        t.name         = data["name"]
        t.tour_level   = data["tour_level"]
        t.hole_pars    = list(data.get("hole_pars", [4] * 18))
        t.course_par   = sum(t.hole_pars)
        t.opponents    = opponents
        t.is_major     = data.get("is_major", False)
        t.major_id     = data.get("major_id", None)
        t.is_qschool   = data.get("is_qschool", False)
        t.total_rounds = data.get("total_rounds", 1)
        t.event_number = data.get("event_number", 1)
        t.total_events = data.get("total_events", 8)
        t.prize_fund   = data.get("prize_fund", 0)
        t.rng_seed     = int(data.get("rng_seed", 0))
        t.course_name  = data.get("course_name", None)
        t.player_rounds = [list(r) for r in data.get("player_rounds", [])]
        t._opp_holes    = {k: [list(r) for r in v]
                           for k, v in data.get("opp_holes", {}).items()}
        # Phase 1 fields — defaulted so pre-Phase-1 saves still load
        t.format               = data.get("format",               FORMAT_STROKE_PLAY)
        t.pin_positions        = list(data.get("pin_positions",   []))
        t.green_speed          = data.get("green_speed",          "normal")
        t.firmness             = data.get("firmness",             "normal")
        t.weather              = data.get("weather",              "clear")
        t.wind_strength_floor  = data.get("wind_strength_floor",  0)
        # Phase 2 — match play
        t.bracket              = list(data.get("bracket",         []))
        t.match_round          = data.get("match_round",          0)
        t.match_opponent       = data.get("match_opponent",       None)
        t.match_eliminated     = data.get("match_eliminated",     False)
        t._match_final_position = data.get("_match_final_position", None)
        # Phase 3 — skins / pro-am
        t.skin_value           = data.get("skin_value",           0)
        t.skins_carried        = data.get("skins_carried",        0)
        t.skins_won            = list(data.get("skins_won",            []))
        t.skins_prize_per_hole = list(data.get("skins_prize_per_hole", []))
        t.partner_scores       = list(data.get("partner_scores",       []))
        # Phase 4 — schedule metadata
        t.event_type             = data.get("event_type",             "regular")
        t.is_opener              = data.get("is_opener",              False)
        t.is_finale              = data.get("is_finale",              False)
        t.starting_score_offset  = dict(data.get("starting_score_offset", {}))
        t.promotion_wildcard     = data.get("promotion_wildcard",     False)
        return t
