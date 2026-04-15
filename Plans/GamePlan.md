# Let's Golf! — Game Development Plan

## Technology Decision

### Language: Python 3.11+
### Framework: Pygame 2.x

**Why Python + Pygame?**

The spec calls for beginner-friendly code, simple setup, minimal dependencies, and a desktop 2D pixel art game. Python + Pygame is the strongest match:

- **One dependency**: `pip install pygame` — no engine to install, no build toolchain
- **Beginner-readable**: Python reads like English; the code is easy to follow and modify
- **Proven for 2D games**: Pygame is a mature library (20+ years) with excellent documentation and community support
- **Mouse input**: Pygame has first-class mouse event handling — perfect for click-drag shot mechanics
- **Pixel art rendering**: Pygame renders pixel art natively without anti-aliasing artifacts
- **Cross-platform**: Runs on Windows, macOS, and Linux without changes
- **Save system**: Python's built-in `json` and `pickle` modules handle save files without extra libraries

**Alternatives considered and rejected:**
- *Godot / GDScript*: Requires installing a separate engine and learning a custom IDE — too much friction
- *JavaScript + Phaser*: Browser-first, needs Node.js, packaging for desktop is awkward
- *C# + MonoGame*: .NET setup is complex; not beginner-friendly

---

## Project Structure

```
Golf/
├── main.py                    # Entry point — launches the game
├── requirements.txt           # pygame==2.x
├── Plans/
│   └── GamePlan.md            # This file
├── assets/
│   ├── images/
│   │   ├── tiles/             # Terrain tiles (fairway, rough, bunker, water, tree, tee, green)
│   │   ├── sprites/           # Ball, flag, golfer silhouette
│   │   └── ui/                # Buttons, panels, icons, club icons
│   ├── sounds/
│   │   ├── swing.wav
│   │   ├── hit.wav
│   │   ├── splash.wav
│   │   ├── bunker.wav
│   │   ├── crowd_ambient.wav
│   │   └── birds.wav
│   └── fonts/
│       └── pixel_font.ttf     # Pixel-style font (or fallback to pygame default)
├── src/
│   ├── game.py                # Game class — main loop, state manager
│   ├── states/                # One file per game screen/state
│   │   ├── __init__.py
│   │   ├── main_menu.py       # Title screen, load/new game
│   │   ├── character_creation.py  # Name golfer, distribute starting stats
│   │   ├── career_hub.py      # Between-round hub: shop, training, schedule
│   │   ├── golf_round.py      # The actual game — hit shots, navigate holes
│   │   ├── hole_transition.py # Scorecard between holes
│   │   ├── round_summary.py   # End of round scores vs opponents
│   │   ├── tournament_results.py  # Full tournament standings + prize money
│   │   └── tour_standings.py  # Season-long leaderboard / promotion/relegation
│   ├── golf/
│   │   ├── __init__.py
│   │   ├── ball.py            # Ball position, velocity, terrain collision, animation
│   │   ├── shot.py            # Shot input handling, power meter, direction, shaping
│   │   ├── club.py            # Club class — distances, accuracy modifiers, unlock cost
│   │   └── terrain.py         # Terrain enum + distance/accuracy multipliers
│   ├── course/
│   │   ├── __init__.py
│   │   ├── course.py          # Course class — list of holes, par, metadata
│   │   ├── hole.py            # Hole layout, terrain grid, tee/pin positions
│   │   └── renderer.py        # Draws the course tile map + overlays
│   ├── career/
│   │   ├── __init__.py
│   │   ├── player.py          # Player stats, inventory, money, career history
│   │   ├── opponent.py        # AI golfer — name, stats, score simulation
│   │   ├── tour.py            # Tour class — name, level, schedule, competitor pool
│   │   ├── tournament.py      # Single tournament — rounds, scores, prize fund
│   │   └── rankings.py        # World ranking points, leaderboard
│   ├── data/
│   │   ├── __init__.py
│   │   ├── clubs_data.py      # All club definitions (driver to putter)
│   │   ├── courses_data.py    # All course/hole layouts
│   │   ├── tours_data.py      # Tour configs: schedule, entry requirements, prize funds
│   │   └── opponents_data.py  # Named AI golfer pool per tour level
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── button.py          # Reusable clickable button widget
│   │   ├── panel.py           # Background panel helper
│   │   ├── hud.py             # In-round HUD: club selector, power bar, mini-map
│   │   └── scorecard.py       # Scorecard table renderer
│   └── utils/
│       ├── __init__.py
│       ├── save_system.py     # JSON save/load — saves after every completed round
│       ├── sound_manager.py   # Loads and plays sounds, volume control
│       └── math_utils.py      # Vector helpers, angle conversion, trajectory calc
└── saves/                     # Auto-created at runtime; .json save files live here
```

---

## Game Architecture

### State Machine
The game uses a simple stack-based state machine in `game.py`. Each screen is a `State` subclass with `update()`, `draw()`, and `handle_event()` methods. Transitioning between states pushes or pops from the stack.

```
MainMenu → CharacterCreation → CareerHub ↔ GolfRound
                                         ↕
                               TournamentResults → TourStandings
```

### Shot Mechanic (Click-Drag-Click)
1. Player **left-clicks** to start aiming. A direction line appears from the ball.
2. Player **drags** the mouse — distance from ball sets power (shown on power bar), direction of drag sets aim line.
3. An optional **shot shape selector** (draw / straight / fade) applies a curve modifier.
4. Player **left-clicks again** to execute the shot.
5. Ball travels using a simplified physics model: initial velocity vector, terrain friction on landing, bounce on hard surfaces.

### Shot Shaping
Three modes: **Draw** (right-to-left curve), **Straight**, **Fade** (left-to-right curve).
Implemented as a lateral offset applied to the ball's trajectory over time, scaled by club type and player accuracy stat.

### Terrain System
Each hole is stored as a 2D grid of terrain tiles. Every terrain type has distance and accuracy multipliers:

| Terrain     | Distance Modifier | Accuracy Modifier | Notes                        |
|-------------|-------------------|-------------------|------------------------------|
| Tee Box     | 1.0               | 1.0               | No penalty                   |
| Fairway     | 1.0               | 1.0               | No penalty                   |
| Rough       | 0.75              | 0.80              | Shorter, less accurate       |
| Deep Rough  | 0.55              | 0.60              | Severe penalty                |
| Bunker      | 0.60              | 0.70              | Distance and accuracy hit    |
| Water       | —                 | —                 | 1-stroke penalty, drop zone  |
| Trees       | 0.40              | 0.30              | Major penalty if in trees    |
| Green       | —                 | —                 | Putting mode activates       |

---

## Career Structure

### Tour Levels (6 total)

| Level | Name                    | Events/Season | Prize Fund   | Promotion Condition             |
|-------|-------------------------|---------------|--------------|---------------------------------|
| 1     | Amateur Circuit         | 8 events      | Trophies only| Top 3 overall in season         |
| 2     | Challenger Tour         | 10 events     | Small prize  | Top 5 in season standings       |
| 3     | Development Tour        | 12 events     | Medium prize | Top 3 in season standings       |
| 4     | Continental Tour        | 14 events     | Good prize   | Top 5 + Q-school event          |
| 5     | World Tour              | 16 events     | Large prize  | Top 10 + world ranking ≥ 50     |
| 6     | The Grand Tour (= PGA)  | 18 events     | Major prize  | Win all 4 Majors + world no. 1  |

### The 4 Majors (Grand Tour only)
1. **The Open** (links course, windy conditions)
2. **The Masters Classic** (Augusta-style, tournament of champions format)
3. **The National Championship** (US Open-style, tough rough)
4. **The Heritage Cup** (US PGA-style, target golf)

### Player Stats
- **Power** — maximum drive distance
- **Accuracy** — how tightly shots cluster around target
- **Short Game** — chipping and pitching quality
- **Putting** — putting distance control and read quality
- **Mental** — reduces pressure penalties in high-stakes rounds
- **Fitness** — reduces fatigue penalty over a long season

Stats are raised by spending money at the training facility (Career Hub).

### Equipment
Clubs are organised into sets. Each club has:
- Base distance (yards)
- Accuracy rating
- Shot shaping range
- Purchase cost
- Unlock tour level

### Staff (Pro Tour only)
| Staff Role       | Benefit                              |
|------------------|--------------------------------------|
| Coach            | +stat XP multiplier from training    |
| Caddie           | Reveals wind data, suggests club     |
| Sports Psychologist | Reduces pressure penalties        |
| Fitness Trainer  | Slower fitness decline per season    |

### Sponsorships (Pro Tour only)
Sponsors provide weekly income but require performance conditions:
- "Win at least 2 events this season"
- "Finish top 10 in a Major"
- "Maintain top 30 world ranking"

---

## Development Phases

### Phase 1 — Foundation (Core Loop)
**Goal:** A single hole is playable end-to-end.

- [ ] `main.py` entry point and window setup
- [ ] `game.py` state machine
- [ ] `states/golf_round.py` — minimal playable hole
- [ ] `golf/ball.py` — ball rendering and basic movement
- [ ] `golf/shot.py` — click-drag-click input, power bar
- [ ] `golf/terrain.py` — terrain enum and modifiers
- [ ] `course/hole.py` — hardcoded single hole layout
- [ ] `course/renderer.py` — tile-based course drawing
- [ ] `ui/hud.py` — club display, stroke counter, power bar

**Deliverable:** You can tee up and play one hole, counting strokes until the ball is in the hole.

---

### Phase 2 — Full Round
**Goal:** Play 18 holes and see a scorecard.

- [ ] `course/course.py` — 18-hole course container
- [ ] `data/courses_data.py` — first full course (Par 72)
- [ ] `states/hole_transition.py` — between-hole scorecard
- [ ] `states/round_summary.py` — post-round totals
- [ ] `golf/club.py` — full club bag (driver, woods, irons, wedges, putter)
- [ ] `ui/hud.py` — club selector (scroll wheel / click)
- [ ] `ui/scorecard.py` — scorecard table

**Deliverable:** A full 18-hole round with scoring.

---

### Phase 3 — Shot Shaping & Physics Polish
**Goal:** Draw/fade feels meaningful; terrain affects play.

- [ ] Shot shape selector (Draw / Straight / Fade) in HUD
- [ ] Trajectory curve logic in `golf/ball.py`
- [ ] Terrain collision detection — ball lands and modifier is applied
- [ ] Water hazard penalty (drop, +1 stroke)
- [ ] Wind system — direction and speed affect trajectory
- [ ] Wind display in HUD

**Deliverable:** Shots curve, terrain matters, wind is a factor.

---

### Phase 4 — Career & Character
**Goal:** Player exists with a profile; results are tracked.

- [ ] `states/main_menu.py` — new game / load game
- [ ] `states/character_creation.py` — name, nationality, stat distribution
- [ ] `career/player.py` — stats, money, inventory, career log
- [ ] `utils/save_system.py` — save to JSON after every round
- [ ] Load save on startup

**Deliverable:** Game saves and loads; player has identity.

---

### Phase 5 — Opponents & Tournaments
**Goal:** You are competing against simulated players.

- [ ] `career/opponent.py` — AI golfer with stats; score simulation function
- [ ] `data/opponents_data.py` — 30+ named opponents per tour level
- [ ] `career/tournament.py` — 4-round tournament, scores per round
- [ ] `states/tournament_results.py` — full leaderboard with prize money
- [ ] `states/tour_standings.py` — season-long standings, promotion/relegation

**Deliverable:** Competing in a full tournament against named opponents.

---

### Phase 6 — Tour Structure & Career Progression
**Goal:** Work through all 6 tour levels.

- [ ] `career/tour.py` — tour level configs and schedules
- [ ] `data/tours_data.py` — all 6 tours, each with own courses and competitors
- [ ] Promotion/relegation logic end-of-season
- [ ] `states/career_hub.py` — training shop, equipment shop, schedule view
- [ ] Multiple courses (at least 2 per tour level = 12 courses minimum)

**Deliverable:** Full career progression from Amateur to Grand Tour.

---

### Phase 7 — Progression Systems
**Goal:** Spending money and earning upgrades feels rewarding.

- [ ] Training facility — spend money to increase stats
- [ ] Equipment shop — unlock and buy better club sets
- [ ] Staff hiring system (pro tour unlock)
- [ ] Sponsorship system — income + performance targets
- [ ] Career stats / achievements screen

**Deliverable:** Full between-round progression loop.

---

### Phase 8 — The Grand Tour & Majors
**Goal:** Endgame is properly distinct and climactic.

- [ ] 4 Major tournaments with unique rules/conditions
- [ ] World rankings system (`career/rankings.py`)
- [ ] Win condition detection — all 4 Majors won + world no. 1
- [ ] Credits / Hall of Fame screen on completion

**Deliverable:** The game has a winnable end state.

---

### Phase 9 — Audio & Polish
**Goal:** Game feels complete.

- [ ] `utils/sound_manager.py`
- [ ] Sound effects: swing, hit, splash, bunker, crowd ambience, birds
- [ ] Volume settings in menu
- [ ] Pixel art placeholder assets for all tiles and sprites
- [ ] Animated ball roll and flag wave
- [ ] Transition animations between states

**Deliverable:** Polished, releasable game.

---

## Data Design Notes

### Course Layout Format
Each hole is stored as a 2D list of terrain codes, plus metadata:
```python
{
    "hole_number": 1,
    "par": 4,
    "stroke_index": 7,
    "tee": (2, 17),        # (col, row) on the grid
    "pin": (14, 3),
    "yardage": 420,
    "grid": [
        "WWWWWWWWWWWWWWWWWW",
        "WRRRRRRRRRRRRRRRRW",
        "WRFFFFFFFFFFFFBBRW",
        ...
    ]
}
```
Terrain codes: `F`=fairway, `R`=rough, `D`=deep rough, `B`=bunker, `W`=water, `T`=trees, `G`=green, `X`=tee box

### Save File Format (JSON)
```json
{
  "version": 1,
  "player": { "name": "...", "stats": {}, "money": 0, "clubs": [], "staff": [] },
  "career": { "tour_level": 1, "current_season": 1, "events_played": 0 },
  "season_standings": [ { "name": "...", "points": 0 } ],
  "world_rankings": [ { "name": "...", "points": 0 } ],
  "history": []
}
```

---

## Run Instructions (Final)

### 1. Install Python
Download Python 3.11+ from python.org. Ensure `pip` is available.

### 2. Install dependency
```bash
pip install pygame
```

### 3. Run the game
```bash
cd Golf
python main.py
```

### 4. How to play
- **Aim**: Left-click and drag away from the ball — the drag direction is your aim line, drag distance sets power
- **Shot shape**: Click Draw / Straight / Fade buttons before shooting
- **Club select**: Click club name or use scroll wheel to cycle through the bag
- **Execute**: Left-click again (or release drag) to hit
- **Putt**: Same mechanic on the green; putter auto-selects when on the green

---

## Milestones Summary

| Phase | Description                        | Key Output                          |
|-------|------------------------------------|-------------------------------------|
| 1     | Foundation                         | One playable hole                   |
| 2     | Full Round                         | 18-hole round with scorecard        |
| 3     | Shot Shaping & Physics             | Draw/fade + terrain + wind          |
| 4     | Career & Save System               | Named player, save/load             |
| 5     | Opponents & Tournaments            | Compete against AI field            |
| 6     | Tour Structure                     | 6-tier career progression           |
| 7     | Progression Systems                | Training, shop, staff, sponsors     |
| 8     | Grand Tour & Majors                | Win condition + end game            |
| 9     | Audio & Polish                     | Sound, animation, final assets      |

Each phase is independently testable and produces a playable build.
We build bottom-up: the golf itself first, then the career wrapper around it.
