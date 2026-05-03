# Changelog

All notable changes to Let's Golf! are documented here.

## 2026-05-03 — Windows EXE Distribution (PyInstaller)

### Added
- **Standalone Windows build** via PyInstaller (`letsgolf.spec`) — produces `dist/LetsGolf/LetsGolf.exe`, no Python required
- `src/utils/paths.py` — frozen-aware path resolver; writable data (`saves/`, `settings.json`) redirect to `%APPDATA%\LetsGolf\` in the frozen build; read-only assets resolve via `sys._MEIPASS`
- Save system, sound manager, fonts, UI skin, and career hub updated to use `paths.*` helpers instead of bare relative paths
- `data/game_config.json` bundled as a read-only asset; `settings.json` excluded from bundle (user-writable)
- App icon placeholder at `assets/ui/icon.ico` — replace with a valid `.ico` to apply a custom window icon

### Changed
- `dev_config.USE_GENERATED_COURSES` set to `False` for distribution builds

---

## 2026-05-02 — Phase 13: Visual & Atmospheric Polish

### Added

#### Career Hub Visual Progression (Task 13.1)
- The Career Hub now changes its colour palette based on the current tour level — six distinct themes from green-toned Driving Range (Tour 1) through to deep navy Grand Tour Clubhouse (Tour 6)
- Theme is applied by updating `C_BG` and `C_PANEL` at the start of each `draw()` call, so all panels, tabs, and overlays pick it up automatically
- A **Location:** label (e.g. "Training Centre", "Tour Facility") is rendered top-right of the hub header

#### Course Prestige Badges (Task 13.2)
- `Course` now carries a `prestige` metadata field: `"local"` / `"regional"` / `"national"` / `"world-class"` / `"major_venue"`
- The event panel in the Career Hub renders a coloured prestige badge below the tour name label:
  - Local — grey, Regional — green, National — blue, World-class — gold, Major Venue — purple
- Badge is computed from the player's current tour level; major events always show **Major Venue**

#### Caddie Personality & Tips (Task 13.3)
- The caddie hire is expanded from one type to **three mutually exclusive variants**, each with a distinct personality and stat bonus tier:
  - **Budget Caddie** *(blunt)* — Short Game +1, Putting +1 — $4,000 hire
  - **Tour Caddie** *(tactical)* — Short Game +2, Putting +2 — $8,000 hire
  - **Elite Caddie** *(optimistic)* — Short Game +3, Putting +3 — $15,000 hire
- Hiring one caddie automatically fires any other already hired (only one caddie at a time)
- A **caddie tip** line appears at the bottom of the HUD whenever the ball is at rest and the player has not yet started aiming; tip content depends on personality:
  - *Optimistic* — a rotating set of encouraging lines keyed to the hole number
  - *Tactical* — reactive tips based on wind strength, terrain, pin position, and green speed
  - *Blunt* — only speaks when there is something critical to say (bunker, strong wind, tucked pin); otherwise silent
- Staff tab now shows a 3-row × 2-column grid to accommodate the three caddie cards

---

## 2026-05-02 — Phase 12: International Team Event

### Added

#### Team Event (Task 12.1)
- A prestige **International Team Event** triggers every 4 career seasons (tracked via `player.team_event_seasons`)
- Entry screen (`TeamEventHubState`) displays two teams of 6 — Home vs Away — and lets the player choose an AI partner for foursomes
- **Day 1 — Foursomes:** alternate-shot format built into `GolfRoundState` via `alternate_shot_mode` and `player_turn` flags; every other shot is taken by the AI partner (pre-simulated position with tour-level scatter); a "Partner's shot" toast confirms each AI turn
- **Day 2 — Singles match play:** the player faces one opponent from the opposing team using the existing match play engine
- Team result screen (`TeamEventResultState`) tallies points and records a win in `player.team_event_wins`; win badge surfaces in the Hall of Fame

---

## 2026-05-02 — Bug Fixes & Code Quality

### Fixed
- **Ball capture** now requires the ball to be moving towards the pin before it is holed, preventing false captures on a stationary ball near the cup
- **Practice rounds** now apply weather condition modifiers correctly (they were being skipped for non-tournament rounds)
- **Leaderboard hot-path** performance improved — avoids redundant re-sort on every draw call
- **Water-drop safety** — added a post-drop guard to ensure the ball is never placed back inside a water tile after a penalty drop
- **Tileset notification** — a console warning surfaces when a tileset PNG referenced by a JSON course is missing, replacing a silent fallback

### Changed
- Wind calculation extracted into a single `_compute_wind()` helper in `GolfRoundState` (was duplicated across `__init__` and `_advance`)
- Shot physics constants moved to a config file loaded at startup; `GolfRoundState` reads from that rather than using inline magic numbers
- `TilesetManager.SOURCE_TILE` corrected to 16 px to match the actual tile image size (was mismatched, causing offset rendering in the detail layer)
- Detail-layer rendering made more efficient — avoids rebuilding the sprite dict on every frame for unchanged tiles
- Circular dependency at the module root for `apply_tournament_result` removed; now imported lazily inside the function that needs it

---

## 2026-04-28 — Bug Fixes (review follow-up)

### Fixed
- **`temp_stat_modifiers` bleed** — narrative event effects (e.g. "Fitness -5 this event") are now cleared immediately after being read at the start of each `GolfRoundState`, preventing them from persisting into future events across the entire career.
- **Silent achievement failures** — all bare `except: pass` blocks in `service.py` (rival tracker, comeback win, beat-rival-major) replaced with named `except Exception as e` + `print()` logging; broken attribute access or missing fields will now surface in the console instead of silently killing achievements.
- **Sponsor reputation gate bypass** — `narrative_handler._accept_best_available_sponsor` now passes `player.reputation` to `get_available_sponsors`, so reputation-gated sponsors can no longer be obtained via the narrative event path.
- **Match play head-to-head wrong result** — rival H2H updates for match play events now use the bracket result (win/loss by `position`) rather than the stroke-play leaderboard. The final bracket opponent is correctly recovered from `tournament.bracket[match_round]` in both the win and loss paths. `check_rival` is skipped for match play because vs-par comparison is meaningless in that format.

---

## 2026-04-28 — Phases 7–11: Practice, Awards, Equipment & Career Depth

### Added

#### Practice Minigames (Phase 7)
- Four practice activities are now accessible from the **Training** panel in the Career Hub between events: **Driving Range**, **Putting Green**, **Bunker Escape**, and **Closest to Pin**
- Each minigame has a one-event cooldown — once played it is greyed out until the next event
- Cooldowns are saved and migrated cleanly on load

#### Skills Competitions (Phases 7 / Schedule)
- A **Skills Competition** event type appears in tour schedules (Tours 3–6), preceding each major on Tour 6
- Skills competitions launch a `LongDriveState` session tracked by `SkillsSession`
- The Career Hub event panel labels these correctly and routes to the right state

#### Expanded Tour Schedules (Phase 7 / Schedule)
- Tours 3–6 now have fully defined deterministic season schedules replacing the old hand-rolled event index checks
- Tour 3 (Development): 13 events including skills, skins, stableford, and a season championship finale
- Tour 4 (Continental): 15 events with skills, match play, skins, stableford, and finale
- Tour 5 (World): 17 events with skills, match play, skins, stableford, and finale
- Tour 6 (Grand Tour): 22-event season with 4 majors at fixed positions (events 4, 10, 16, 22), preceded by skills competitions at events 3, 9, 15, 21

#### Year-End Awards (Phase 9)
- The game now tracks `year_end_awards` across a player's career
- `previous_season_position` is recorded each season to power award logic
- New `YearEndAwardsState` screen presented at season end

#### Hall of Fame — Expanded Layout (Phase 9)
- The Hall of Fame screen is redesigned into a **four-box layout**:
  - **Top-left** — Major Championships (each major shown with ★ won / ○ not yet)
  - **Top-right** — Career Statistics (seasons, events, wins, top-5/top-10, best round, earnings, peak world rank)
  - **Bottom-left** — Rival & Year-End Awards (rival name, head-to-head record W/L/H, awards list)
  - **Bottom-right** — Achievements
- A **Grand Slam Champion · World No. 1** banner appears when both conditions are met simultaneously

#### Multi-Year Career Fitness Degradation (Phase 10)
- `career_season` is now tracked independently of `season` (which resets on promotion)
- From career season 5 onward, Fitness degrades by 1 point per season (floor: 40), modelling the physical toll of a long career

#### Equipment Extras (Phase 11)
- **Club Fitting** — before a major, players can spend $500 to fit their Driver for +5% accuracy for that event only; button appears in the event panel when a major is upcoming
- **Club Wear** — clubs accumulate accuracy loss over repeated use (`club_wear` dict, 0–0.10 per club)
- **Re-groove** — players can spend $150 in the Equipment panel's new Maintenance section to reset wear on any degraded club
- **Prototype Driver** — obtainable via narrative event; use it 5× and finish top 10 to permanently unlock Accuracy +1; converted via a career log entry that surfaces on the results screen
- `Club` dataclass gains `is_prototype` and `prototype_uses` fields

### Changed
- `save_format` bumped from **5 → 8** (v5→v6 Phase 7 fields, v6→v7 Phase 10 `career_season`, v7→v8 Phase 11 equipment fields); all versions default cleanly in `Player.from_dict` — no data loss on old saves

---

## 2026-04-27 — Phases 4–6: Season Structure, Rivals & Narrative

### Added

#### Season Schedule (Phase 4)
- Season schedules are now generated deterministically via `schedule_data.generate_season_schedule` and stored on the player, replacing hard-coded `event_n % N` chains
- Event metadata includes `event_type`, `format`, `is_opener`, `is_finale`, and `major_id`
- A **Tour Championship** finale event ends each season; the winner receives a `promotion_wildcard` bypassing the normal points threshold
- `TOUR_CHAMPIONSHIP_QUALIFIERS` defines how many players qualify per tour level

#### Rival Tracker (Phase 5)
- After each stroke-play event, opponents within 3 strokes of the player accumulate `close_finishes`; once any opponent reaches 5 close finishes the player's rival is set (one rival per career)
- **Head-to-head record** (W / L / Halved) is tracked against the rival each event
- Rival name and H2H record appear on the Hall of Fame screen

#### Reputation System (Phase 5)
- Players earn reputation points for wins: +5 for a regular win, +8 for a match play win, +15 for a major win
- Reputation gates sponsor availability

#### Career Narrative Events (Phase 5/6)
- Between events the game can trigger a **Narrative Event** screen with a choice of two options, each applying an effect to the player
- Effects include: signing a sponsor, temporary stat buffs/debuffs, skipping an event, equipping a prototype club, or setting a slump objective
- Events are gated by tour level, season, and career state; defined in `src/data/narrative_events.py`

#### Season Arcs (Phase 6)
- Each tour/season combination maps to a named **Season Arc** with a specific objective and money reward (e.g. "The Rookie Year — finish top 3 in standings")
- Arcs without a specific definition fall back to the generic "Make Your Mark — win 2 events" arc
- Arc completion is checked in `tour_standings.py` at season end

#### Achievements — 20 New (Phase 6)
- Four new achievement categories: **Scoring** (albatross, hole-in-one, best round), **Format** (win match play, skins, stableford), **Adversity** (rain win, comeback win), **Rival** (beat rival in a major)
- Course records and hole-in-ones are logged to the career log and surface on results screens

#### Career Stats Tab — Expanded (Phase 6)
- The Career Hub stats tab is redesigned into a 3-column layout covering season stats, career totals, and format/achievement progress

### Changed
- `save_format` bumped from **2 → 5** across three phases; all bumps default cleanly on load

---

## 2026-04-24 — Phase 2: Match Play Format

### Added

#### Match Play Championship
- Event 5 of every season on Tour 2 and above is now a **Match Play Championship**
- Bracket format: the player faces up to 4 opponents in sequence (Quarter-Final → Semi-Final → Final)
- Each match is a full 18-hole round played against one opponent
- Win a hole → 1 up. Tie a hole → halved. First player whose lead exceeds remaining holes wins early (e.g. "4&3")
- Opponent scores are pre-simulated from the tournament seed — the bracket is deterministic and consistent with saves

#### Match Play HUD Overlay
- A compact status panel appears in the bottom-left of the course viewport during match play rounds
- Shows current standing: "2 UP", "ALL SQUARE", "3 DOWN" with remaining holes count
- Updates after every hole

#### Hole-Complete Match Status
- The hole-complete overlay shows the running match score ("2 UP — 10 to play") instead of stroke totals when playing a match play event

#### Between-Hole Leaderboard (Match Play)
- The hole-transition screen replaces the stroke-play leaderboard with a match play status view showing holes won / halved / lost and holes remaining

#### Match Result Screen (`MatchResultState`)
- New full screen shown after each match concludes (either by early concession or completing 18 holes)
- Displays result (Won / Lost), margin (e.g. "3&1"), and a holes won / halved / lost breakdown
- If the player won and more bracket rounds remain: shows the next opponent and continues to the next match
- If the player won the entire bracket: shows "Match Play Champion!" and routes to the tournament results screen
- If the player was eliminated: shows which round they reached and routes to tournament results

#### Tournament Results (Match Play)
- The tournament results screen shows a bracket summary for match play events — each round listed with opponent name and Won / Lost result
- The "Match Play Champion!" banner displays for a bracket winner

#### Career Hub — Format Badge
- The event info panel in the career hub now shows a **FORMAT: Match Play Championship** badge for event 5 on Tour 2+, with a short description of the format

### Changed
- `save_format` bumped from **1 → 2**; saves from v1 are automatically migrated on load — no data is lost

---

## 2026-04-24 — Phase 1: Course Conditions & Scoring

### Added

#### Pin Positions
- Each tournament now assigns a pin position (front / standard / tucked) to every hole, drawn from a weighted random pool
- Majors force all pins to **tucked** for a harder setup
- The pin hole is now rendered dynamically each frame so it moves correctly between tournaments
- The minimap pin marker and world-space pin detection both respect the active pin position

#### Green Speed
- Tournaments generate a green speed condition: slow / normal / fast / slick
- The putter distance is scaled by the green speed multiplier (slow = 0.85×, slick = 1.35×)
- Majors guarantee a minimum of **fast** greens

#### Fairway Firmness
- Tournaments generate a firmness condition: soft / normal / firm / hard
- Ball roll distance after landing is scaled accordingly (soft = 0.70×, hard = 1.45×)
- Combined with weather roll effects and clamped to a minimum of 0.3× so the ball always moves a little

#### Weather Conditions
- Tournaments generate a weather condition: clear / rain / cold / heat / fog
- Rain reduces roll distance and slightly reduces accuracy
- Cold reduces shot distance slightly
- Heat adds a small distance bonus
- Fog slightly reduces accuracy and renders a tint overlay on the course view
- Majors exclude heat weather

#### Major Hard Setup
- On top of tucked pins and fast greens, Majors enforce a **wind floor of 2** (never calm) and exclude heat weather, making them consistently more demanding than regular events

#### Stableford Scoring
- Every 3rd event on Tour 2 and above is now a **Stableford** format event (labelled accordingly)
- Points per hole: Albatross 5 · Eagle 4 · Birdie 3 · Par 2 · Bogey 1 · Double bogey or worse 0
- The hole-transition leaderboard shows a **Pts** column instead of vs-par
- The round summary screen shows total stableford points alongside the stroke count
- The tournament results screen shows per-round points and a total points column for stableford events
- Stableford position ranking uses points (highest wins) rather than strokes (lowest wins)

#### HUD Conditions Panel
- A compact **Conditions** block appears in the right-hand HUD between the wind indicator and the minimap during any tournament round
- Shows Pin / Greens / Ground / Weather in a 2×2 grid
- Values are colour-coded: green = favourable, amber = moderate, red = difficult

### Changed
- The minimap in the HUD now resizes dynamically to fit below the conditions panel when conditions are present, rather than being a fixed-height rectangle

