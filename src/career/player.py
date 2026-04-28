"""
Player — the human golfer's profile, stats, inventory, and career history.
"""

from src.golf.club         import STARTER_BAG, get_club_bag, CLUB_SETS, CLUB_SET_ORDER
from src.golf.ball_types   import BALL_TYPES, BALL_ORDER
from src.career.staff       import STAFF_TYPES
from src.career.sponsorship import is_target_met
from src.career.majors      import MAJOR_ORDER
from src.data.schedule_data import generate_season_schedule

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

# ── Achievements registry ─────────────────────────────────────────────────────
ACHIEVEMENTS = {
    # ── Existing ──────────────────────────────────────────────────────────────
    "first_round":      {"label": "First Step",       "desc": "Play your first round"},
    "first_subpar":     {"label": "Under Par",         "desc": "Finish a round under par"},
    "first_top5":       {"label": "Top 5",             "desc": "Finish in the top 5"},
    "first_win":        {"label": "Winner!",           "desc": "Win your first tournament"},
    "challenger":       {"label": "Going Up",          "desc": "Reach the Challenger Tour"},
    "going_pro":        {"label": "Turning Pro",       "desc": "Reach the Continental Tour"},
    "grand_tour":       {"label": "Grand Stage",       "desc": "Reach the Grand Tour"},
    "max_stat":         {"label": "Dedicated",         "desc": "Max out a stat to 80"},
    "pro_clubs":        {"label": "Gear Up",           "desc": "Buy the Pro Set or better"},
    "hired_staff":      {"label": "Team Player",       "desc": "Hire your first staff member"},
    "millionaire":      {"label": "Millionaire",       "desc": "Earn $1,000,000 in career prize money"},
    "veteran":          {"label": "Veteran",           "desc": "Play 50 events"},
    "hat_trick":        {"label": "Hat Trick",         "desc": "Win 3 tournaments"},
    "first_major":      {"label": "Major Winner",      "desc": "Win your first Major championship"},
    "grand_slam":       {"label": "Grand Slam",        "desc": "Win all 4 Majors"},
    "world_no1":        {"label": "World No. 1",       "desc": "Reach World Ranking #1"},
    # ── Scoring ───────────────────────────────────────────────────────────────
    "first_birdie":     {"label": "First Birdie",      "desc": "Score your first birdie"},
    "first_eagle":      {"label": "Eagle Eye",         "desc": "Score your first eagle"},
    "hole_in_one":      {"label": "Ace!",              "desc": "Score a hole-in-one"},
    "break_70":         {"label": "Below 70",          "desc": "Shoot under 70 for a round"},
    "break_65":         {"label": "Elite Round",       "desc": "Shoot under 65 for a round"},
    "bogey_free":       {"label": "Bogey Free",        "desc": "Complete a round without a bogey"},
    "five_birdies_run": {"label": "On Fire",           "desc": "Make 5 birdies in a row"},
    # ── Career ────────────────────────────────────────────────────────────────
    "win_all_tours":    {"label": "Tour Conqueror",    "desc": "Win an event on every tour level"},
    "win_major":        {"label": "Major Champion",    "desc": "Win any Major championship"},
    "centurion":        {"label": "Centurion",         "desc": "Play 100 events"},
    # ── Formats ───────────────────────────────────────────────────────────────
    "win_match_play":   {"label": "Closer",            "desc": "Win a Match Play Championship"},
    "win_skins":        {"label": "Skin Collector",    "desc": "Win a Skins event"},
    "win_stableford":   {"label": "Points Wizard",     "desc": "Win a Stableford event"},
    # ── Adversity ─────────────────────────────────────────────────────────────
    "comeback_win":     {"label": "The Comeback",      "desc": "Win after being 5+ strokes down in round 2"},
    "long_putt":        {"label": "Long Range",        "desc": "Hole a putt from over 35 yards"},
    "tree_par":         {"label": "Timber!",           "desc": "Escape from trees and still make par"},
    "rain_win":         {"label": "All Weather",       "desc": "Win an event played in rain"},
    # ── Skills ────────────────────────────────────────────────────────────────
    "skills_long_drive":{"label": "Big Hitter",        "desc": "Win the Long Drive Competition"},
    "skills_cttp":      {"label": "Pin Seeker",        "desc": "Win Closest to the Pin"},
    # ── Rival ─────────────────────────────────────────────────────────────────
    "beat_rival_major": {"label": "Rivalry Settled",   "desc": "Beat your rival in a Major"},
}


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

        self.club_set_name = "starter"

        # Balls: owned set + active choice. Range ball is the freebie.
        self.owned_balls: list[str] = ["range"]
        self.ball_type:   str       = "range"

        # Season tracking
        self.season_points:       int  = 0
        self.events_this_season:  int  = 0
        self.opp_season_points:   dict = {}

        # Career stats
        self.career_wins:    int       = 0
        self.career_top5:    int       = 0
        self.career_top10:   int       = 0
        self.total_earnings: int       = 0
        self.best_round:     int | None = None  # best score vs par (most negative)

        # Staff & sponsorship
        self.hired_staff:     list[str]   = []
        self.active_sponsor:  dict | None = None
        self.sponsor_progress: dict       = {}

        # Achievements
        self.achievements: list[str] = []

        # World rankings & majors
        self.world_ranking_points: float      = 0.0
        self.world_rank:           int        = 201   # starts unranked
        self.majors_won:           list[str]  = []

        # Q-School qualifying flag (set when Tour 4 season ends top-5) and
        # the number of Q-School attempts remaining before the player must
        # re-qualify with another top-5 season finish.
        self.qschool_pending: bool           = False
        self.qschool_attempts_remaining: int = 0

        # One-time tutorial shown on the player's first round.
        self.tutorial_seen: bool = False

        # Practice-mode flag: when True, CareerService skips autosaving so
        # a "try this course" round doesn't overwrite real career saves.
        # Not persisted — only set at runtime by the course-picker flow.
        self.practice_mode: bool = False

        # Phase 4 — season schedule (event slots for the current season)
        self.season_schedule: list[dict] = generate_season_schedule(1, 1)

        # Phase 6 — extended stats
        self.wins_per_tour:   dict[int, int] = {}
        self.course_records:  dict[str, int] = {}
        self.hole_in_ones:    list[dict]     = []

        # Phase 5 — rival tracker
        self.rival_name: str | None = None
        self.rival_head_to_head: dict = {"wins": 0, "losses": 0, "halved": 0}
        self.close_finishes: dict[str, int] = {}

        # Phase 5 — narrative / reputation
        self.narrative_events_seen: list[str] = []
        self.reputation: int = 0
        self.temp_stat_modifiers: dict[str, int] = {}
        self.slump_objective: dict | None = None

        # Phase 5 — season arc
        self.current_arc_id: str | None = None
        self.arc_completed: bool = False

        # Phase 7 — practice minigames
        self.practice_cooldowns: dict[str, int] = {}
        self.cttp_best_yards: float | None = None
        self.practice_stat_seasons: dict[str, int] = {}
        self.temp_event_buffs: dict[str, int] = {}

        # Phase 9 — year-end awards & career tracking
        self.previous_season_position: int | None = None
        self.year_end_awards: list[str] = []
        self.seasons_on_current_tour: int = 1
        self.world_rank_peak: int = 201

        # Phase 10 — multi-year career
        self.career_season: int = 1

        # Phase 11 — equipment extras
        self.club_fitting_active: dict | None = None   # {club, bonus} clears after round
        self.prototype_club: dict | None = None        # serialised as dict
        self.prototype_uses_goal: int = 5
        self.club_wear: dict[str, float] = {}          # club name → accuracy loss (0–0.10)

    @property
    def clubs(self):
        return get_club_bag(self.club_set_name)

    # ── Stat bonuses from character creation ──────────────────────────────────

    def set_bonus_stats(self, bonus: dict[str, int]) -> None:
        for k, v in bonus.items():
            if k in self.stats:
                self.stats[k] = min(MAX_STAT, BASE_STAT + v)

    # ── Training ──────────────────────────────────────────────────────────────

    def training_cost(self, stat_key: str) -> int | None:
        """Cost to raise stat_key by 1, or None if already at MAX_STAT."""
        current = self.stats.get(stat_key, BASE_STAT)
        if current >= MAX_STAT:
            return None
        above_base = current - BASE_STAT   # 0..29
        return (above_base + 1) * 200       # $200 → $6 000

    def train_stat(self, stat_key: str) -> bool:
        """Spend money to increase a stat by 1. Returns True on success."""
        cost = self.training_cost(stat_key)
        if cost is None:
            return False
        if self.spend_money(cost):
            self.stats[stat_key] = min(MAX_STAT, self.stats[stat_key] + 1)
            self._check_achievements()
            return True
        return False

    # ── Equipment ─────────────────────────────────────────────────────────────

    def regrove_club(self, club_name: str) -> bool:
        """Pay $150 to reset wear on one club. Returns True on success."""
        if not self.spend_money(150):
            return False
        self.club_wear.pop(club_name, None)
        return True

    def upgrade_club_set(self, set_name: str) -> bool:
        """
        Buy a club set.  Returns True on success.
        Fails if: tour level too low, already own equal/better, or can't afford.
        """
        if set_name not in CLUB_SETS:
            return False
        info = CLUB_SETS[set_name]
        if info["min_tour"] > self.tour_level:
            return False
        current_idx = CLUB_SET_ORDER.index(self.club_set_name)
        target_idx  = CLUB_SET_ORDER.index(set_name)
        if target_idx <= current_idx:
            return False
        if self.spend_money(info["cost"]):
            self.club_set_name = set_name
            self._check_achievements()
            return True
        return False

    # ── Balls ─────────────────────────────────────────────────────────────────

    def buy_ball(self, ball_id: str) -> bool:
        """Buy a ball type. Returns True on success. Auto-selects the new ball."""
        info = BALL_TYPES.get(ball_id)
        if info is None:
            return False
        if ball_id in self.owned_balls:
            return False
        if info["min_tour"] > self.tour_level:
            return False
        if not self.spend_money(info["cost"]):
            return False
        self.owned_balls.append(ball_id)
        self.ball_type = ball_id
        return True

    def select_ball(self, ball_id: str) -> bool:
        if ball_id in self.owned_balls:
            self.ball_type = ball_id
            return True
        return False

    # ── Staff ─────────────────────────────────────────────────────────────────

    def staff_stat_bonus(self, stat_key: str) -> int:
        """Sum of stat bonuses from all hired staff members."""
        total = 0
        for sid in self.hired_staff:
            total += STAFF_TYPES.get(sid, {}).get("bonuses", {}).get(stat_key, 0)
        return total

    def hire_staff(self, staff_id: str) -> bool:
        """Pay hire cost and add staff member. Returns True on success."""
        if staff_id in self.hired_staff:
            return False
        info = STAFF_TYPES.get(staff_id)
        if not info:
            return False
        if info["min_tour"] > self.tour_level:
            return False
        if not self.spend_money(info["hire_cost"]):
            return False
        self.hired_staff.append(staff_id)
        self._check_achievements()
        return True

    def fire_staff(self, staff_id: str) -> bool:
        if staff_id in self.hired_staff:
            self.hired_staff.remove(staff_id)
            return True
        return False

    # ── Sponsorship ───────────────────────────────────────────────────────────

    def accept_sponsor(self, sponsor: dict) -> bool:
        """Accept a sponsor deal.  Signing fee paid immediately."""
        if self.active_sponsor is not None:
            return False
        self.active_sponsor   = dict(sponsor)
        self.sponsor_progress = {sponsor["target"]["type"]: 0}
        self.earn_money(sponsor["signing_fee"])
        return True

    def drop_sponsor(self) -> None:
        self.active_sponsor   = None
        self.sponsor_progress = {}

    def _pay_out_sponsor(self) -> None:
        """Called at season reset — pay bonus if target met."""
        if self.active_sponsor is None:
            return
        if is_target_met(self.active_sponsor, self.sponsor_progress):
            bonus = self.active_sponsor["season_bonus"]
            self.earn_money(bonus)
            self.total_earnings += bonus
        self.active_sponsor   = None
        self.sponsor_progress = {}

    # ── Career tracking ───────────────────────────────────────────────────────

    def unlock_achievement(self, key: str) -> bool:
        """Add achievement key if not already present. Returns True if newly unlocked."""
        if key not in self.achievements and key in ACHIEVEMENTS:
            self.achievements.append(key)
            return True
        return False

    def log_round(self, course_name: str, strokes: int, par: int,
                  hole_scores: list[int] | None = None,
                  hole_pars: list[int] | None = None) -> None:
        diff = strokes - par
        entry: dict = {
            "course":  course_name,
            "strokes": strokes,
            "par":     par,
            "diff":    diff,
        }
        if hole_scores is not None:
            entry["hole_scores"] = list(hole_scores)
        if hole_pars is not None:
            entry["hole_pars"] = list(hole_pars)

        # Per-hole analysis for achievements
        if hole_scores is not None and hole_pars is not None:
            diffs = [s - p for s, p in zip(hole_scores, hole_pars)]
            if all(d <= 0 for d in diffs):
                entry["bogey_free"] = True
            run = best_run = 0
            for d in diffs:
                if d < 0:
                    run     += 1
                    best_run = max(best_run, run)
                else:
                    run = 0
            if best_run >= 5:
                entry["five_birdie_run"] = True

        self.career_log.append(entry)
        self.events_played += 1
        if self.best_round is None or diff < self.best_round:
            self.best_round = diff

        # Course record
        prev = self.course_records.get(course_name, 9999)
        if strokes < prev:
            self.course_records[course_name] = strokes
            if prev < 9999:
                entry["new_course_record"] = True

        self._check_achievements()

    def check_rival(self, leaderboard: list[dict]) -> None:
        """Increment close_finishes for opponents within 3 strokes; set rival_name
        once any opponent reaches 5 close finishes and no rival is yet set."""
        player_entry = next((e for e in leaderboard if e.get("is_player")), None)
        if player_entry is None:
            return
        player_vp = player_entry.get("vs_par", 0)
        for entry in leaderboard:
            if entry.get("is_player"):
                continue
            name = entry.get("name", "")
            if not name:
                continue
            diff = abs(entry.get("vs_par", 0) - player_vp)
            if diff <= 3:
                self.close_finishes[name] = self.close_finishes.get(name, 0) + 1
                if self.rival_name is None and self.close_finishes[name] >= 5:
                    self.rival_name = name  # set once per career; never reassigned

    def update_head_to_head(self, leaderboard: list[dict]) -> None:
        """Update head-to-head record against the current rival."""
        if not self.rival_name:
            return
        player_entry = next((e for e in leaderboard if e.get("is_player")), None)
        rival_entry  = next((e for e in leaderboard
                             if e.get("name") == self.rival_name), None)
        if player_entry is None or rival_entry is None:
            return
        p_pos = leaderboard.index(player_entry) + 1
        r_pos = leaderboard.index(rival_entry)  + 1
        if p_pos < r_pos:
            self.rival_head_to_head["wins"]   = self.rival_head_to_head.get("wins",   0) + 1
        elif p_pos > r_pos:
            self.rival_head_to_head["losses"] = self.rival_head_to_head.get("losses", 0) + 1
        else:
            self.rival_head_to_head["halved"] = self.rival_head_to_head.get("halved", 0) + 1

    def gain_reputation(self, amount: int) -> None:
        self.reputation = min(100, self.reputation + amount)

    def apply_tournament_result(self, tournament) -> dict:
        # Logic lives in CareerService so the rankings/staff imports it
        # needs can be at module scope without introducing a circular import.
        from src.career.service import process_tournament_result
        return process_tournament_result(self, tournament)

    def reset_season(self) -> None:
        self._pay_out_sponsor()
        self.season                  += 1
        self.season_points            = 0
        self.events_this_season       = 0
        self.opp_season_points        = {}
        self.seasons_on_current_tour += 1
        self.season_schedule          = generate_season_schedule(self.tour_level, self.season)
        self.arc_completed            = False
        from src.data.narrative_events import get_arc_id
        self.current_arc_id = get_arc_id(self.tour_level, self.season)
        # Phase 10 — fitness degrades by 1 from career season 5 onward
        if self.career_season >= 5:
            self.stats["fitness"] = max(40, self.stats["fitness"] - 1)
        self.career_season += 1

    def earn_money(self, amount: int) -> None:
        self.money += amount

    def spend_money(self, amount: int) -> bool:
        if self.money >= amount:
            self.money -= amount
            return True
        return False

    # ── Achievements ──────────────────────────────────────────────────────────

    def has_won_game(self) -> bool:
        """Win condition: all 4 Majors won AND World No. 1."""
        all_majors = all(m in self.majors_won for m in MAJOR_ORDER)
        return all_majors and self.world_rank == 1

    def _check_achievements(self) -> None:
        """Unlock any achievements whose conditions are now met."""
        def unlock(key):
            if key not in self.achievements and key in ACHIEVEMENTS:
                self.achievements.append(key)

        # ── Existing ──────────────────────────────────────────────────────────
        if self.events_played >= 1:
            unlock("first_round")
        if self.best_round is not None and self.best_round < 0:
            unlock("first_subpar")
        if self.career_top5 >= 1:
            unlock("first_top5")
        if self.career_wins >= 1:
            unlock("first_win")
        if self.career_wins >= 3:
            unlock("hat_trick")
        if self.tour_level >= 2:
            unlock("challenger")
        if self.tour_level >= 4:
            unlock("going_pro")
        if self.tour_level >= 6:
            unlock("grand_tour")
        if any(v >= MAX_STAT for v in self.stats.values()):
            unlock("max_stat")
        club_tier = CLUB_SET_ORDER.index(self.club_set_name)
        if club_tier >= CLUB_SET_ORDER.index("pro"):
            unlock("pro_clubs")
        if len(self.hired_staff) >= 1:
            unlock("hired_staff")
        if self.total_earnings >= 1_000_000:
            unlock("millionaire")
        if self.events_played >= 50:
            unlock("veteran")
        if len(self.majors_won) >= 1:
            unlock("first_major")
            unlock("win_major")
        if len(self.majors_won) >= 4:
            unlock("grand_slam")
        if self.world_rank == 1:
            unlock("world_no1")

        # ── Scoring ───────────────────────────────────────────────────────────
        for entry in self.career_log:
            hs = entry.get("hole_scores")
            hp = entry.get("hole_pars")
            if hs and hp:
                diffs = [s - p for s, p in zip(hs, hp)]
                if any(d <= -1 for d in diffs):
                    unlock("first_birdie")
                if any(d <= -2 for d in diffs):
                    unlock("first_eagle")
            if entry.get("bogey_free"):
                unlock("bogey_free")
            if entry.get("five_birdie_run"):
                unlock("five_birdies_run")
            s = entry.get("strokes", 9999)
            if s < 70:
                unlock("break_70")
            if s < 65:
                unlock("break_65")
        if self.hole_in_ones:
            unlock("hole_in_one")

        # ── Career ────────────────────────────────────────────────────────────
        if self.events_played >= 100:
            unlock("centurion")
        if len(self.wins_per_tour) >= 6:
            unlock("win_all_tours")

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "version":            2,
            "name":               self.name,
            "nationality":        self.nationality,
            "money":              self.money,
            "tour_level":         self.tour_level,
            "season":             self.season,
            "events_played":      self.events_played,
            "stats":              dict(self.stats),
            "club_set_name":      self.club_set_name,
            "career_log":         list(self.career_log),
            "season_points":      self.season_points,
            "events_this_season": self.events_this_season,
            "opp_season_points":  dict(self.opp_season_points),
            # Phase 7 additions
            "career_wins":        self.career_wins,
            "career_top5":        self.career_top5,
            "career_top10":       self.career_top10,
            "total_earnings":     self.total_earnings,
            "best_round":         self.best_round,
            "hired_staff":        list(self.hired_staff),
            "active_sponsor":     self.active_sponsor,
            "sponsor_progress":   dict(self.sponsor_progress),
            "achievements":         list(self.achievements),
            # Phase 8 additions
            "world_ranking_points": self.world_ranking_points,
            "world_rank":           self.world_rank,
            "majors_won":           list(self.majors_won),
            "qschool_pending":              self.qschool_pending,
            "qschool_attempts_remaining":   self.qschool_attempts_remaining,
            "tutorial_seen":                self.tutorial_seen,
            "owned_balls":                  list(self.owned_balls),
            "ball_type":                    self.ball_type,
            # Phase 4
            "season_schedule":              list(self.season_schedule),
            # Phase 6
            "wins_per_tour":           dict(self.wins_per_tour),
            "course_records":          dict(self.course_records),
            "hole_in_ones":            list(self.hole_in_ones),
            # Phase 5
            "rival_name":              self.rival_name,
            "rival_head_to_head":      dict(self.rival_head_to_head),
            "close_finishes":          dict(self.close_finishes),
            "narrative_events_seen":   list(self.narrative_events_seen),
            "reputation":              self.reputation,
            "slump_objective":         self.slump_objective,
            "current_arc_id":          self.current_arc_id,
            "arc_completed":           self.arc_completed,
            # Phase 7
            "practice_cooldowns":      dict(self.practice_cooldowns),
            "cttp_best_yards":         self.cttp_best_yards,
            "practice_stat_seasons":   dict(self.practice_stat_seasons),
            "temp_event_buffs":        dict(self.temp_event_buffs),
            # Phase 9
            "previous_season_position": self.previous_season_position,
            "year_end_awards":          list(self.year_end_awards),
            "seasons_on_current_tour":  self.seasons_on_current_tour,
            "world_rank_peak":          self.world_rank_peak,
            # Phase 10
            "career_season":            self.career_season,
            # Phase 11
            "club_fitting_active":      self.club_fitting_active,
            "prototype_club":           self.prototype_club,
            "prototype_uses_goal":      self.prototype_uses_goal,
            "club_wear":                dict(self.club_wear),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        p = cls(data["name"], data.get("nationality", "American"))
        p.money               = data.get("money", STARTING_MONEY)
        p.tour_level          = data.get("tour_level", 1)
        p.season              = data.get("season", 1)
        p.events_played       = data.get("events_played", 0)
        p.stats               = {k: data.get("stats", {}).get(k, BASE_STAT)
                                 for k in STAT_KEYS}
        p.club_set_name       = data.get("club_set_name", "starter")
        p.career_log          = data.get("career_log", [])
        p.season_points       = data.get("season_points", 0)
        p.events_this_season  = data.get("events_this_season", 0)
        p.opp_season_points   = data.get("opp_season_points", {})
        # Phase 7 additions (graceful defaults for old saves)
        p.career_wins         = data.get("career_wins", 0)
        p.career_top5         = data.get("career_top5", 0)
        p.career_top10        = data.get("career_top10", 0)
        p.total_earnings      = data.get("total_earnings", 0)
        p.best_round          = data.get("best_round", None)
        p.hired_staff         = data.get("hired_staff", [])
        p.active_sponsor      = data.get("active_sponsor", None)
        p.sponsor_progress    = data.get("sponsor_progress", {})
        p.achievements          = data.get("achievements", [])
        p.world_ranking_points  = data.get("world_ranking_points", 0.0)
        p.world_rank            = data.get("world_rank", 201)
        p.majors_won            = data.get("majors_won", [])
        p.qschool_pending              = data.get("qschool_pending", False)
        p.qschool_attempts_remaining   = data.get("qschool_attempts_remaining", 0)
        p.tutorial_seen                = data.get("tutorial_seen", False)
        p.owned_balls                  = data.get("owned_balls", ["range"]) or ["range"]
        p.ball_type                    = data.get("ball_type", "range")
        if p.ball_type not in p.owned_balls:
            p.ball_type = "range"
        # Phase 4 — rebuild schedule for old saves that lack it
        p.season_schedule = data.get("season_schedule", [])
        if not p.season_schedule:
            p.season_schedule = generate_season_schedule(p.tour_level, p.season)
        # Phase 6
        p.wins_per_tour   = data.get("wins_per_tour",  {})
        p.course_records  = data.get("course_records", {})
        p.hole_in_ones    = data.get("hole_in_ones",   [])
        # Phase 5
        p.rival_name             = data.get("rival_name", None)
        p.rival_head_to_head     = data.get("rival_head_to_head",
                                            {"wins": 0, "losses": 0, "halved": 0})
        p.close_finishes         = data.get("close_finishes", {})
        p.narrative_events_seen  = data.get("narrative_events_seen", [])
        p.reputation             = data.get("reputation", 0)
        p.temp_stat_modifiers    = {}   # never persisted — reset each session
        p.slump_objective        = data.get("slump_objective", None)
        p.current_arc_id         = data.get("current_arc_id", None)
        p.arc_completed          = data.get("arc_completed", False)
        if p.current_arc_id is None:
            from src.data.narrative_events import get_arc_id
            p.current_arc_id = get_arc_id(p.tour_level, p.season)
        # Phase 7
        p.practice_cooldowns    = data.get("practice_cooldowns", {})
        p.cttp_best_yards       = data.get("cttp_best_yards", None)
        p.practice_stat_seasons = data.get("practice_stat_seasons", {})
        p.temp_event_buffs      = data.get("temp_event_buffs", {})
        # Phase 9
        p.previous_season_position = data.get("previous_season_position", None)
        p.year_end_awards          = data.get("year_end_awards", [])
        p.seasons_on_current_tour  = data.get("seasons_on_current_tour", 1)
        p.world_rank_peak          = data.get("world_rank_peak", 201)
        # Phase 10 — default to p.season for old saves (equivalent tracking)
        p.career_season            = data.get("career_season", p.season)
        # Phase 11
        p.club_fitting_active = data.get("club_fitting_active", None)
        p.prototype_club      = data.get("prototype_club", None)
        p.prototype_uses_goal = data.get("prototype_uses_goal", 5)
        p.club_wear           = data.get("club_wear", {})
        return p
