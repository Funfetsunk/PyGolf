# Changelog

All notable changes to Let's Golf! are documented here.

## [Unreleased] — Phase 1: Course Conditions & Scoring

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

