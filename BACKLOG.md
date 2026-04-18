# PyGolf — Outstanding Backlog

A prioritised list of issues, improvements and ideas from the architecture / UX / UI review. Items are grouped by priority so they can be picked off in any order, and each entry names the file(s), the problem, and a minimum-viable fix.

**Status:** the items under "Recently landed" below have already been shipped in commit `0c87b33`. Everything else is still open.

---

## Recently landed (commit `0c87b33`)

- Aim-click radius raised to 50 px and a faint click-zone ring is drawn on the ball while idle.
- Shot-shape curve fraction raised to 0.15 so Draws/Fades are visibly curved.
- Toasts for trees / deep rough / bunker landings (water already had one).
- Save format is version-checked on load; corrupt slots show "(corrupt)" in the UI, disable Load, and a red banner surfaces the reason instead of a silent `print`.
- Opponent field is deterministically seeded per `(player, season, tour, event)` via `Tournament(rng_seed=...)`; seed is persisted across saves.
- One-time click-drag-release tutorial modal on the first hole of a new career, gated by `Player.tutorial_seen`.

---

## P1 — highest impact, do next

### Mid-round save / resume
- **Where:** `src/utils/save_system.py`, `src/states/golf_round.py`, `src/career/tournament.py`
- **Why:** quitting mid-round wipes the round. The tournament already persists opponent scores deterministically, so only the round's own state is missing.
- **Fix:** on every `_on_ball_landed` (and on explicit pause/quit), call `save_game(player, tournament)` with an extra `current_round_state` payload containing `hole_index`, `strokes`, `scores[]`, `ball_world_pos`. On load, if that payload exists, jump straight back into `GolfRoundState` at that hole/position.

### Q-School single-shot death gate
- **Where:** `src/career/tournament.py` (`PROMOTION_THRESHOLD`), `src/states/career_hub.py::_play_event`
- **Why:** Tour 4 → 5 currently forces a full season replay on one loss. Frustrating progression bottleneck.
- **Fix:** allow up to two Q-School attempts per season, and/or auto-qualify the player into Q-School on any top-5 finish (not just top 3). Track `qschool_attempts_remaining` on `Player`.

### Top-50 world-rank gate is invisible
- **Where:** `src/states/career_hub.py`, `src/career/player.py`
- **Why:** Tour 5 → 6 requires a top-50 world rank, but the requirement is only exposed on the Career Stats tab. Players grind Tour 5 not knowing why they're stuck.
- **Fix:** on the Career Hub promotion panel, show *"Tour 6 requires: top-10 season finish + World Rank ≤ 50 (You: #87 — climb 37 places)"*.

### Curve the live aim line to match shape
- **Where:** `src/states/golf_round.py::_draw_aim_arrow`, `src/ui/hud.py`
- **Why:** the curve fraction is doubled but the aim line is still straight — players don't see the effect until the ball flies.
- **Fix:** when `shot_shape != STRAIGHT`, draw the aim line as a quadratic bezier with a perpendicular control-point offset proportional to `SHAPE_CURVE_FRACTION`.

### Penalty toasts for OOB / missed fairway near trees
- **Where:** `src/states/golf_round.py::_handle_tree_collision`
- **Why:** the landed-in-trees toast only fires on landing; mid-flight collisions still feel silent-bouncy.
- **Fix:** the branch where the bounce starts now has a toast — double-check it reliably fires for OOB positions and add an "Out of bounds" toast when the ball hits the grid edge rather than a tree.

---

## P2 — architecture & data integrity

### Duplicated course-building helper
- **Where:** `src/data/courses_data.py:44–78` and `src/data/courses_library.py:23–59`
- **Why:** two near-identical `_make_hole` / `_h` implementations; balance changes must land twice.
- **Fix:** extract to `src/data/_hole_factory.py`, import from both.

### Two "get courses for tour" APIs
- **Where:** `src/data/tours_data.py::get_courses_for_tour` (JSON-first), `src/data/courses_library.py::get_courses_for_tour_id` (in-code).
- **Why:** which path runs depends on filesystem state. Hard to reason about and test.
- **Fix:** pick `tours_data.get_courses_for_tour` as the single entry point; have `courses_library` register with it instead of exposing its own lookup.

### v3 course loader lacks validation
- **Where:** `src/course/course_loader.py:53–70`
- **Why:** a v3 JSON missing its logic layer silently becomes all-Rough; mismatched ground/logic grid sizes render wrong.
- **Fix:** add `validate_course(data)` that checks (i) every hole has matching `ground`/`logic` dimensions, (ii) tee and pin are inside the grid, (iii) at least one tile is `X` and one is `G`. Raise a clear error with hole number.

### Tile-size constant duplicated by comment
- **Where:** `src/course/course_loader.py:21` (`_SOURCE_TILE = 16`), `tools/editor/canvas.py`
- **Why:** kept in sync by a comment. Silent wrong-scale bug waiting to happen.
- **Fix:** move the constant to `src/constants.py`, import in both sites, `assert` at editor startup.

### Resolution hard-coded across ~9 files
- **Where:** `main.py`, every state file redeclares `SCREEN_W/SCREEN_H = 1280/720`.
- **Why:** low cost to fix today, big cost to fix once a real scaling pass starts.
- **Fix:** single `src/constants.py` exporting `SCREEN_W`, `SCREEN_H`, `FPS`, `TILE_PX`; delete the duplicates.

### `saves/` directory assumed to exist on load
- **Where:** `src/utils/save_system.py::list_saves`
- **Why:** directory is created on save but not on read; `os.listdir` will crash if it was deleted between sessions.
- **Fix:** `os.makedirs(SAVE_DIR, exist_ok=True)` at the top of `list_saves`.

### `game.player` mutated directly from states
- **Where:** e.g. `src/states/round_summary.py:90` → `game.player.apply_tournament_result(...)`.
- **Why:** no single place to log, validate, or autosave career transitions. When "I was awarded a win I didn't earn" bugs land, there's no seam to instrument.
- **Fix:** introduce a thin `CareerService` that states delegate to (`apply_tournament_result`, `advance_season`, `promote_tour`); it logs, validates, and triggers autosave.

### Deferred imports inside `Player.apply_tournament_result`
- **Where:** `src/career/player.py:250,268,296` imports `staff`, `rankings`, `majors` inside methods.
- **Why:** circular-import workaround; `Player` knows too much about its dependents.
- **Fix:** move cross-cutting logic out into a processor that imports all three at module scope and mutates `Player` via plain setters.

---

## P2 — UX / gameplay feel

### Putter auto-select is silent
- **Where:** `src/states/golf_round.py:482–489`
- **Fix:** brief "Putter selected" toast (~0.5 s) when the auto-switch fires; similarly "Sand Wedge selected" on entering a bunker.

### "What should I do next?" missing in Career Hub
- **Where:** `src/states/career_hub.py`
- **Fix:** after a tournament, highlight the most valuable next action (Training if money > cheapest train cost, Equipment if a new tier just unlocked, otherwise the Play button).

### Locked club tiers say nothing
- **Where:** `src/states/career_hub.py` equipment panel
- **Fix:** tooltip on hover: "Unlocks on Continental Tour (Level 4)". Trivial once a reusable tooltip helper exists.

### Losing-streak dead-end
- **Where:** `src/states/career_hub.py` + `src/career/player.py` (`career_log`)
- **Fix:** after 3 bottom-10 finishes in a row, flash a one-line hint: "Struggling? Train your weakest stat." Pull weakest from `player.stats`.

### Audio settings unreachable mid-round
- **Where:** currently only in `src/states/main_menu.py::_draw_settings_overlay`
- **Fix:** add a gear icon on the HUD that opens the same panel; extract the panel into `src/ui/audio_settings.py`.

---

## P2 — UI / visual

### Colour-blind risk in terrain greens
- **Where:** `src/golf/terrain.py`, `src/course/renderer.py::_noisy_fill`, `_grass_blades`
- **Why:** Fairway/Rough/Deep Rough/Green are all greens. Under protanopia/deuteranopia they collapse.
- **Fix:** add a procedural pattern per rough tier (diagonal hatch on Rough, denser hatch on Deep Rough). Pattern beats hue for accessibility.

### Shot-shape buttons rely on hue alone
- **Where:** `src/ui/hud.py:169–182`
- **Fix:** add a tiny curve-arrow glyph in each button (left/straight/right); keep the colour.

### No click-press feedback on buttons
- **Where:** every state file — idle/hover only, no pressed state.
- **Fix:** extract a shared `src/ui/button.py` helper that handles hover/pressed/disabled uniformly (100 ms 0.95× scale or 0.9 alpha dip on mousedown). DRYs up copy-pasted button code across states.

### Disabled-button contrast is too subtle
- **Where:** every state file — `C_BTN_DIS ≈ (32,44,32)` vs `C_BTN ≈ (28,78,28)` is easy to miss.
- **Fix:** shift disabled to a warmer desaturated tone and drop text alpha to 50 %.

### Last-place player not marked on standings
- **Where:** `src/states/tour_standings.py`
- **Fix:** always highlight the player row, even when dead-last; a muted "—" marker makes it obvious.

### Scorecard headers tight at 13 pt
- **Where:** `src/ui/scorecard.py`
- **Fix:** bump to 15 pt or add padding.

### Generic gray-blue editor theme
- **Where:** `tools/editor/editor_theme.json`
- **Fix:** cosmetic, dev-tool. Skip unless there's appetite.

---

## P3 — nice to have

### Per-frame surface allocation in dialog overlays
- **Where:** `src/states/golf_round.py:642`, `src/states/main_menu.py:348,408,488`
- **Fix:** cache the overlay surface on first draw.

### System Arial everywhere
- **Where:** every state file uses `pygame.font.SysFont("arial", …)`.
- **Fix:** bundle a free-licensed pixel font, expose it via `src/ui/fonts.py`, fall back to Arial on load failure. Instantly sells the pixel-art aesthetic.

### Hard-coded 1280×720
- **Where:** everywhere.
- **Fix:** not a quick win — a proper scaling pass is a small project. Park until after the bigger UX items land.

### Keyboard-only play
- **Where:** `src/golf/shot.py`, `src/states/golf_round.py`
- **Fix:** also not a quick win — needs a full alternate input mode (arrow keys to aim, hold-space for power, release-space to fire). Worth noting for accessibility, defer.

---

## Ideas / bigger bets

- **Practice / driving-range mode.** One hole, no score, free club switching — reuses `GolfRoundState` with a `practice=True` flag. Best place to teach shot-shape differences without tour pressure.
- **Daily Course seed.** Date-derived deterministic course — a reason to return daily. Course generation is already data-driven, so cheap.
- **Caddie suggestions.** On higher tours, surface a "Caddie recommends 7 Iron, slight fade" tip based on distance/wind/terrain, accuracy scaling with Caddie staff tier. Good sink for an existing staff role.
- **Replay of final hole.** Save ball positions for the last hole of a tournament and let the player re-watch with an auto-pan camera. Cheap drama for wins.

---

## Review methodology

This backlog is the distilled output of an architecture + UX + UI review done 2026-04-18 against commit `6c08563`. Each item points at the file/line where it was observed. The original full review (with reasoning) lives at `C:\Users\tdp\.claude-tdp\plans\this-project-belongs-to-lexical-marshmallow.md`.
