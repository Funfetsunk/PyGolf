# Let's Golf! ⛳

A top-down 2D pixel art golf career game built in Python. Work your way up from the Amateur Circuit to the Grand Tour, win the 4 Majors, and reach World No. 1.

See [CHANGELOG.md](CHANGELOG.md) for a history of changes.

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Funfetsunk/PyGolf.git
cd PyGolf

# 2. Install the one dependency
pip install pygame-ce

# 3. Play
python main.py
```

> **Note:** The game uses `pygame-ce` (the community edition fork), not standard `pygame`. If you have standard `pygame` installed, uninstall it first: `pip uninstall pygame`

**Python 3.11+ required.**

---

## What Is It?

Let's Golf! is a full career golf game where you create a golfer and guide them from local amateur tournaments all the way to the sport's biggest stage. Between rounds you train your stats, upgrade your clubs, hire staff, sign sponsorship deals, and take on practice activities to sharpen your game.

The game is entirely mouse-driven and plays out in top-down 2D with tile-based courses.

---

## Controls

| Action | Control |
|---|---|
| Start aiming | Left-click on the ball |
| Set power & direction | Drag away from the ball |
| Hit the shot | Release the mouse button |
| Cancel shot | Right-click |
| Change club | Scroll wheel  or  ← → arrow keys |
| Select club from bag | Click the club name in the HUD |
| Set shot shape (Draw/Straight/Fade) | Click the shape buttons in the HUD |

---

## Features

### On the Course

- **Click-drag-release** shot mechanic with a live power bar and aim line
- **Shot shaping** — play Draws (right-to-left curve) and Fades (left-to-right) as well as straight shots
- **Wind** — randomised direction and strength each hole, shown by a compass arrow in the HUD
- **Terrain system** — every surface affects your shot differently:

| Terrain | Distance | Accuracy |
|---|---|---|
| Tee / Fairway | Full | Full |
| Rough | −25% | −30% |
| Deep Rough | −45% | −50% |
| Bunker | −40% | −22% |
| Trees | −60% | −70% |
| Water | Penalty + drop | — |

- **Camera** follows the ball in flight; a pin indicator and distance readout keep you oriented
- **Putting** — putter auto-selects on the green; short putts are unaffected by wind
- **Hole-in-one, Eagle, Birdie, Par, Bogey** — all called out with sound and colour

### Course Conditions

Every tournament generates a unique setup that affects how the course plays:

- **Pin Positions** — each hole is assigned a Front, Standard, or Tucked pin; Majors always use Tucked
- **Green Speed** — Slow / Normal / Fast / Slick; scales putter distance (0.85× to 1.35×)
- **Fairway Firmness** — Soft / Normal / Firm / Hard; affects how far the ball rolls after landing (0.70× to 1.45×)
- **Weather** — Clear / Rain / Cold / Heat / Fog; each applies distinct distance and accuracy modifiers; fog adds a tint overlay
- **Major Hard Setup** — Majors enforce tucked pins, fast or better greens, and a minimum wind of 2 (never calm)
- **Conditions HUD Panel** — a compact 2×2 grid in the HUD shows Pin / Greens / Ground / Weather for the current round, colour-coded by difficulty

### Event Formats

Three scoring formats appear across the tour schedule:

- **Stroke Play** — standard format; lowest total strokes wins
- **Stableford** — points per hole (Albatross 5 · Eagle 4 · Birdie 3 · Par 2 · Bogey 1 · Double bogey+ 0); highest points wins; leaderboards show a **Pts** column
- **Match Play Championship** — bracket event on Tour 2 and above; the player faces up to 4 opponents (Quarter-Final → Semi-Final → Final). Win a hole to go 1 UP; tie a hole to halve it. Match ends early when a player's lead exceeds the remaining holes. A live match status overlay tracks the standing hole by hole, and a dedicated Match Result screen follows each match
- **Skills Competition** — long-drive format event on Tours 3–6; a `LongDriveState` session tracked by `SkillsSession`; precedes each major on Tour 6
- **Skins** — each hole has a cash value; tie a hole and the skin carries over

### Career Progression

Six tour levels, each with its own season schedule, courses, prize fund, and AI field:

| Level | Tour | Events/Season | Prize Fund |
|---|---|---|---|
| 1 | Amateur Tour | 8 | — |
| 2 | Challenger Tour | 10 | $10,000 |
| 3 | Development Tour | 13 | $25,000 |
| 4 | Continental Tour | 15 | $75,000 |
| 5 | World Tour | 17 | $200,000 |
| 6 | The Grand Tour | 22 | $1,000,000 |

- Season schedules are **deterministic** — event types (stroke play, match play, stableford, skins, skills, majors) appear at fixed positions each season
- Each season ends with a **Tour Championship** finale; the winner earns a `promotion_wildcard` and is promoted regardless of standings points
- Finish in the **top positions** at season end to earn promotion
- Tour 4 → 5 requires passing a **Q-School Qualifier** against a World Tour field (two attempts per eligible season)
- Tour 5 → 6 also requires a **World Ranking of top 50**
- Each tour/season combination has a named **Season Arc** — a specific objective with a money reward (e.g. "The Rookie Year — finish top 3 in standings"); unspecified combinations fall back to a generic arc

### Between Rounds — Career Hub

**Training**
- Spend prize money to raise any of your 6 stats: Power, Accuracy, Short Game, Putting, Mental, Fitness
- Each stat directly affects your shots in play
- Four **Practice Minigames** are available from the Training panel between events (each has a one-event cooldown):
  - **Driving Range** — maximize carry distance
  - **Putting Green** — sink putts for stat XP
  - **Bunker Escape** — escape sand within a shot limit
  - **Closest to Pin** — approach shots judged by proximity

**Equipment**
- Upgrade your club set through 6 tiers (Starter → Professional), unlocked as you reach higher tours
- **Club Fitting** *(before a major)* — spend $500 to fit your Driver for +5% accuracy for that event only
- **Club Wear** — clubs accumulate accuracy loss over repeated use; visible in the Equipment panel
- **Re-groove** — spend $150 in the Maintenance section to reset wear on any degraded club
- **Prototype Driver** — obtainable via narrative event; use it 5× and finish top 10 to permanently unlock Accuracy +1

**Staff** *(Continental Tour and above)*
- Hire a Coach, Caddie, Sports Psychologist, or Fitness Trainer, each giving permanent stat bonuses

**Sponsors** *(Continental Tour and above)*
- Sign deals for a signing fee plus a season bonus if you hit a performance target (top-5 finishes, wins, etc.)
- Sponsor availability is gated by your **Reputation** — earned by winning events and majors

**Career Stats**
- Full career history in a 3-column layout: season stats, career totals, and format/achievement progress
- Achievements across scoring, format, adversity, and rival categories

### Narrative Events

Between events the game can trigger a **Narrative Event** screen offering a choice between two options. Effects include signing a sponsor, temporary stat buffs or debuffs, skipping an event, equipping a prototype club, or setting a slump objective. Events are gated by tour level, season, and career state.

### Rival System

- After each stroke-play event, opponents who finish within 3 strokes accumulate `close_finishes`; once any opponent reaches 5 close finishes they become your rival (one rival per career)
- **Head-to-head record** (W / L / Halved) is tracked against your rival each event
- Rival name and H2H record appear in the Hall of Fame

### World Rankings & Year-End Awards

- From the Continental Tour onward, every result earns ranking points against a field of 200 simulated professionals
- Reaching World No. 1 is the final career milestone
- At season end, a **Year-End Awards** screen recognises seasonal achievements; `previous_season_position` powers the award logic
- From career season 5 onward, **Fitness degrades** by 1 point per season (floor: 40), modelling the physical toll of a long career

### The Grand Tour & Majors

Four major championships are held at fixed points in the 22-event Grand Tour season (events 4, 10, 16, 22), each preceded by a Skills Competition:

- The Green Jacket Invitational
- The Heritage Open
- The Royal Championship
- The Grand Classic

Majors are 2-round events with a prize fund of $4,500,000 and award double world ranking points.

**Win condition:** win all 4 Majors AND reach World No. 1.

### Hall of Fame

The Hall of Fame screen is a four-box layout:
- **Top-left** — Major Championships (each major shown with ★ won / ○ not yet)
- **Top-right** — Career Statistics (seasons, events, wins, top-5/top-10, best round, earnings, peak world rank)
- **Bottom-left** — Rival & Year-End Awards (rival name, head-to-head record, awards list)
- **Bottom-right** — Achievements

A **Grand Slam Champion · World No. 1** banner appears when both conditions are met simultaneously.

### Saving

The game auto-saves after every round. Multiple save slots are supported; load and delete saves from the main menu.

---

## Project Structure

```
PyGolf/
├── main.py              ← run this to play
├── editor.py            ← course editor (developer tool)
├── requirements.txt
├── src/
│   ├── game.py          ← state machine & main loop
│   ├── career/          ← player, opponents, tournaments, staff, sponsors, rankings
│   ├── course/          ← hole layout, renderer, course loader
│   ├── data/            ← courses, tour configs, opponent pools, schedule templates
│   ├── golf/            ← ball physics, shot mechanics, clubs, terrain
│   ├── states/          ← one file per screen (menu, hub, round, results…)
│   ├── ui/              ← HUD, scorecard
│   └── utils/           ← save system, sound manager, maths helpers
├── assets/
│   ├── tilemaps/        ← terrain tile PNGs used by the renderer
│   └── sounds/          ← drop WAV/OGG files here to replace synthetic audio
├── data/
│   └── courses/         ← JSON course files output by the editor
└── saves/               ← auto-created; not committed to the repo
```

---

## Course Editor

A separate tile-based course editor is included for building new holes:

```bash
pip install pygame-ce pygame_gui
python editor.py
```

The editor lets you paint terrain tiles, set gameplay attributes (fairway, rough, bunker, water, etc.), place tee and pin positions, and export finished courses directly into the game's JSON format.

---

## Audio

The game generates all sounds synthetically at startup — no audio files are required to run. If you want higher-quality audio, drop your own WAV or OGG files into `assets/sounds/` using these names:

`swing.wav` · `hit.wav` · `hit_rough.wav` · `hit_bunker.wav` · `hit_water.wav` · `hit_trees.wav` · `ball_in_hole.wav` · `birdie.wav` · `eagle.wav` · `hole_in_one.wav` · `ambient_crowd.ogg` · `bird_tweet.wav`

Volume for Master, Sound Effects, and Ambient can be adjusted in the Settings panel on the main menu.

---

## Play on your phone (Android / iOS)

The game ships with a web build path using [pygbag](https://pypi.org/project/pygbag/), which compiles the Python + pygame-ce code to WebAssembly. There is **no APK** — you play it in the phone's browser (Chrome, Safari, etc.), and it feels like a native app when launched from the home screen.

```bash
# One-off: install the web-build tool
pip install pygbag

# Serve locally for testing — visit http://<dev-machine-ip>:8000 on your phone
pygbag main.py

# Produce a deployable bundle in ./build/web/
pygbag --build main.py
```

Upload the contents of `build/web/` to any static host (GitHub Pages, Netlify, Cloudflare Pages, …) and share the URL. Players tap **Add to Home Screen** in the browser menu to get an app-style launcher.

**Tips for the best phone experience**
- **Rotate to landscape.** The game targets 1280×720 and will show a "rotate your phone" prompt in portrait; after your first tap it will also request fullscreen and try to pin the orientation.
- **Tap the ball, then drag.** The tap zone around the ball is enlarged for fingertips (no need to hit the pixel exactly).
- **Audio unlocks on first tap.** Browsers won't start audio until the user interacts — you'll hear the first swing but the ambient track may only kick in on the next hole.
- **Career saves live in browser localStorage**, so they persist across sessions. Clearing the site's data in browser settings will wipe career progress — don't do that mid-season.

---

## Dependencies

| Package | Purpose | Install |
|---|---|---|
| `pygame-ce` | Game rendering, input, audio | `pip install pygame-ce` |
| `pygame_gui` | Editor UI panels | `pip install pygame_gui` *(editor only)* |
| `pygbag` | Build for web / Android browsers | `pip install pygbag` *(web build only)* |

No other runtime dependencies. Everything else uses the Python standard library.
