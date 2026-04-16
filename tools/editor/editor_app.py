"""
editor_app.py — top-level editor application loop (Phase E3).

Layout (1440 × 900)
────────────────────
  Toolbar        : y=0,    h=48
  Left panel     : x=0,    y=48,   w=240, h=828
    Tileset panel:                         h=480
    Attribute panel:                       h=348
  Canvas         : x=240,  y=48,   w=980, h=828
  Right panel    : x=1220, y=48,   w=220, h=828
    Hole info    :                         (par, yds, SI, set tee/pin)
    Course info  :                         (name, tour, holes list)
  Status bar     : y=876,  h=24

Controls
────────
  Left-click / drag         → paint visual tile
  A + left-click / drag     → paint attribute brush
  F + left-click            → flood fill (A held = attribute layer)
  Right-click               → eyedropper
  Space/Middle + drag       → pan
  Scroll wheel              → zoom
  After [Set Tee]/[Set Pin] → next canvas click places marker
"""

import os
import sys

import pygame
import pygame_gui

from tools.editor.canvas          import CourseCanvas
from tools.editor.tileset_panel   import TilesetPanel
from tools.editor.attribute_panel import AttributePanel
from tools.editor.hole_panel      import HolePanel
from tools.editor.dialogs import (
    ask_open_png, ask_open_file, ask_save_file,
    make_empty_course, make_empty_hole,
    flush_hole_to_course, load_hole_from_course,
    save_course, load_course, validate_course,
)

# ── Layout constants ──────────────────────────────────────────────────────────
SCREEN_W       = 1440
SCREEN_H       = 900
TOOLBAR_H      = 48
STATUS_H       = 24
LEFT_PANEL_W   = 240
RIGHT_PANEL_W  = 220
CANVAS_W       = SCREEN_W - LEFT_PANEL_W - RIGHT_PANEL_W   # 980
CANVAS_H       = SCREEN_H - TOOLBAR_H - STATUS_H            # 828
TILESET_H      = 480
ATTR_H         = CANVAS_H - TILESET_H                       # 348

CANVAS_RECT      = pygame.Rect(LEFT_PANEL_W,  TOOLBAR_H, CANVAS_W, CANVAS_H)
TILESET_RECT     = pygame.Rect(0,             TOOLBAR_H, LEFT_PANEL_W, TILESET_H)
ATTR_RECT        = pygame.Rect(0,             TOOLBAR_H + TILESET_H, LEFT_PANEL_W, ATTR_H)
RIGHT_PANEL_RECT = pygame.Rect(SCREEN_W - RIGHT_PANEL_W, TOOLBAR_H, RIGHT_PANEL_W, CANVAS_H)

# Colours
C_BG        = (30,  30,  30)
C_TOOLBAR   = (45,  45,  45)
C_STATUS_BG = (38,  38,  38)
C_STATUS_FG = (180, 180, 180)
C_BORDER    = (65,  65,  65)


class EditorApp:
    """Main course editor application."""

    def __init__(self):
        pygame.display.set_caption("Golf Course Editor  —  Phase E3")
        self._screen  = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self._clock   = pygame.time.Clock()
        self._running = True

        theme_path = os.path.join(os.path.dirname(__file__), "editor_theme.json")
        self._ui = pygame_gui.UIManager(
            (SCREEN_W, SCREEN_H),
            theme_path if os.path.exists(theme_path) else None,
        )

        # Tilesets: id → pygame.Surface
        self._tilesets: dict[str, pygame.Surface] = {}
        self._tileset_paths: dict[str, str]       = {}

        # Course state
        self._course        = make_empty_course()
        self._filepath: str | None = None
        self._dirty         = False
        self._current_hole  = 0

        # Sub-components
        self._canvas  = CourseCanvas(CANVAS_RECT)
        self._tileset = TilesetPanel(TILESET_RECT)
        self._attr    = AttributePanel(ATTR_RECT)
        self._hole_panel = HolePanel(RIGHT_PANEL_RECT, self._ui)

        # Sync canvas defaults
        self._canvas.active_attribute    = self._attr.selected
        self._canvas.auto_derive_enabled = self._attr.auto_derive

        # Load hole 0 into canvas
        self._load_hole(0)

        # Fonts / message overlay
        self._status_font = pygame.font.SysFont("monospace", 13)
        self._msg_font    = pygame.font.SysFont("monospace", 14)
        self._status_msg  = ""
        self._msg_timer   = 0.0

        self._setup_toolbar()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _setup_toolbar(self):
        bh = 30
        by = (TOOLBAR_H - bh) // 2

        def btn(label, x, w):
            return pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x, by, w, bh),
                text=label,
                manager=self._ui,
            )

        self._btn_new    = btn("New",        8,   60)
        self._btn_open   = btn("Open",       72,  60)
        self._btn_save   = btn("Save",       136, 60)
        self._btn_import = btn("Import PNG", 220, 110)
        self._btn_grid   = btn("Grid",       360, 56)
        self._btn_zoom_m = btn("Zoom -",     420, 64)
        self._btn_zoom_p = btn("Zoom +",     488, 64)
        self._btn_view_v = btn("V",          580, 32)
        self._btn_view_a = btn("A",          616, 32)
        self._btn_view_b = btn("B",          652, 32)

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while self._running:
            dt = self._clock.tick(60) / 1000.0
            self._msg_timer = max(0.0, self._msg_timer - dt)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    continue

                self._ui.process_events(event)

                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    self._on_button(event.ui_element)
                    continue

                # Hole panel (right)
                action = self._hole_panel.handle_event(event)
                if action:
                    self._on_hole_action(action)
                    continue

                # Attribute panel (bottom-left)
                if self._attr.handle_event(event):
                    self._canvas.active_attribute    = self._attr.selected
                    self._canvas.auto_derive_enabled = self._attr.auto_derive
                    continue

                # Tileset panel (top-left)
                if self._tileset.handle_event(event, self._tilesets):
                    if self._tileset.selected_tile is not None:
                        self._canvas.active_brush   = self._tileset.selected_tile
                        self._tileset.selected_tile = None
                    continue

                # Canvas
                consumed = self._canvas.handle_event(event, self._tilesets)
                if consumed and event.type == pygame.MOUSEBUTTONDOWN:
                    self._dirty = True

            self._ui.update(dt)
            self._draw()

        pygame.quit()
        sys.exit()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw(self):
        self._screen.fill(C_BG)

        pygame.draw.rect(self._screen, C_TOOLBAR,
                         pygame.Rect(0, 0, SCREEN_W, TOOLBAR_H))
        pygame.draw.line(self._screen, C_BORDER,
                         (0, TOOLBAR_H - 1), (SCREEN_W, TOOLBAR_H - 1))

        self._tint_view_buttons()

        self._canvas.draw(self._screen, self._tilesets)

        self._tileset.draw(self._screen, self._tilesets,
                           active_brush=self._canvas.active_brush)
        self._attr.draw(self._screen)

        # Right panel
        self._hole_panel.draw(self._screen, set_mode=self._canvas.set_mode)

        self._draw_status()
        self._ui.draw_ui(self._screen)
        pygame.display.flip()

    def _tint_view_buttons(self):
        mapping = {
            "visual":     self._btn_view_v,
            "attributes": self._btn_view_a,
            "both":       self._btn_view_b,
        }
        for mode, btn in mapping.items():
            r      = btn.rect
            active = (mode == self._canvas.view_mode)
            pygame.draw.rect(
                self._screen,
                (80, 160, 255) if active else (60, 60, 60),
                (r.x, r.bottom + 1, r.width, 3),
            )

    def _draw_status(self):
        sy = SCREEN_H - STATUS_H
        pygame.draw.rect(self._screen, C_STATUS_BG,
                         pygame.Rect(0, sy, SCREEN_W, STATUS_H))
        pygame.draw.line(self._screen, C_BORDER, (0, sy), (SCREEN_W, sy))

        tile_txt = ""
        if self._canvas.hovered_tile is not None:
            c, r = self._canvas.hovered_tile
            attr_char = self._canvas.attribute_grid[r][c]
            from src.golf.terrain import CHAR_TO_TERRAIN, TERRAIN_PROPS
            terr  = CHAR_TO_TERRAIN.get(attr_char)
            tname = TERRAIN_PROPS[terr]["name"] if terr else "?"
            tile_txt = f"({c},{r})  {tname}"

        brush_txt = ""
        if self._canvas.active_brush:
            tid, sc, sr = self._canvas.active_brush
            brush_txt = f"Tile:{tid}({sc},{sr})"

        attr_txt  = f"Attr:{self._canvas.active_attribute.name}"
        zoom_txt  = f"{self._canvas.zoom:.1f}×"
        mode_txt  = self._canvas.view_mode.upper()
        hole_txt  = f"H{self._current_hole + 1}/{len(self._course['holes'])}"
        file_name = os.path.basename(self._filepath) if self._filepath else "Untitled"
        dirty_sfx = " *" if self._dirty else ""

        set_mode_txt = ""
        if self._canvas.set_mode:
            set_mode_txt = f"[PLACE {self._canvas.set_mode.upper()}]"

        parts = [p for p in [tile_txt, brush_txt, attr_txt, zoom_txt,
                              mode_txt, hole_txt, set_mode_txt,
                              file_name + dirty_sfx] if p]
        status = "  |  ".join(parts)

        surf = self._status_font.render(status, True, C_STATUS_FG)
        self._screen.blit(surf, (8, sy + (STATUS_H - surf.get_height()) // 2))

        if self._msg_timer > 0:
            msg = self._msg_font.render(self._status_msg, True, (120, 220, 120))
            self._screen.blit(msg, (SCREEN_W - msg.get_width() - 16,
                                    sy + (STATUS_H - msg.get_height()) // 2))

    # ── Button handling ───────────────────────────────────────────────────────

    def _on_button(self, element):
        if element == self._btn_new:
            self._cmd_new()
        elif element == self._btn_open:
            self._cmd_open()
        elif element == self._btn_save:
            self._cmd_save()
        elif element == self._btn_import:
            self._cmd_import()
        elif element == self._btn_grid:
            self._canvas.show_grid = not self._canvas.show_grid
        elif element == self._btn_zoom_m:
            self._canvas.zoom_out()
        elif element == self._btn_zoom_p:
            self._canvas.zoom_in()
        elif element == self._btn_view_v:
            self._canvas.view_mode = "visual"
        elif element == self._btn_view_a:
            self._canvas.view_mode = "attributes"
        elif element == self._btn_view_b:
            self._canvas.view_mode = "both"

    # ── Hole-panel action routing ─────────────────────────────────────────────

    def _on_hole_action(self, action: str):
        if action == "prev_hole":
            self._switch_hole(self._current_hole - 1)
        elif action == "next_hole":
            self._switch_hole(self._current_hole + 1)
        elif action == "arm_tee":
            self._canvas.enter_set_mode("tee")
        elif action == "arm_pin":
            self._canvas.enter_set_mode("pin")
        elif action == "add_hole":
            self._add_hole()
        elif action == "del_hole":
            self._del_hole()
        elif action.startswith("go_hole:"):
            idx = int(action.split(":")[1])
            self._switch_hole(idx)

    # ── Hole management ───────────────────────────────────────────────────────

    def _flush_current_hole(self):
        """Write canvas + panel state back into _course["holes"][_current_hole]."""
        par, yds, si = self._hole_panel.get_hole_meta()
        name, tour   = self._hole_panel.get_course_meta()
        flush_hole_to_course(
            self._course,
            self._current_hole,
            self._canvas.visual_grid,
            self._canvas.attribute_grid,
            self._canvas.tee_pos,
            self._canvas.pin_pos,
            par, yds, si,
        )
        self._course["course"]["name"] = name
        self._course["course"]["tour"] = tour

    def _load_hole(self, index: int):
        """Load hole data from _course into canvas and hole panel."""
        visual, attrs, tee, pin, cols, rows = load_hole_from_course(
            self._course, index)
        self._canvas.load_grids(visual, attrs)
        self._canvas.tee_pos = tee
        self._canvas.pin_pos = pin
        self._canvas.clear_set_mode()

        holes = self._course["holes"]
        self._hole_panel.populate_hole(holes[index] if index < len(holes) else {})
        self._hole_panel.set_current_hole(index, len(holes))

    def _switch_hole(self, new_index: int):
        total = len(self._course["holes"])
        if not (0 <= new_index < total):
            return
        if new_index == self._current_hole:
            return
        self._flush_current_hole()
        self._current_hole = new_index
        self._load_hole(new_index)
        self._dirty = True

    def _add_hole(self):
        if len(self._course["holes"]) >= 18:
            self._show_msg("Maximum of 18 holes.")
            return
        self._flush_current_hole()
        new_num = len(self._course["holes"]) + 1
        self._course["holes"].append(
            make_empty_hole(self._canvas.cols, self._canvas.rows, new_num))
        new_idx = len(self._course["holes"]) - 1
        self._current_hole = new_idx
        self._load_hole(new_idx)
        self._dirty = True
        self._show_msg(f"Added hole {new_num}.")

    def _del_hole(self):
        if len(self._course["holes"]) <= 1:
            self._show_msg("Cannot delete the last hole.")
            return
        self._course["holes"].pop(self._current_hole)
        new_idx = min(self._current_hole, len(self._course["holes"]) - 1)
        self._current_hole = new_idx
        self._load_hole(new_idx)
        self._dirty = True
        self._show_msg(f"Hole deleted — now on hole {new_idx + 1}.")

    # ── File commands ─────────────────────────────────────────────────────────

    def _cmd_new(self):
        self._course        = make_empty_course()
        self._filepath      = None
        self._dirty         = False
        self._current_hole  = 0
        self._canvas.reset()
        self._tileset.clear()
        self._tilesets.clear()
        self._tileset_paths.clear()
        self._load_hole(0)
        self._hole_panel.populate_course(
            self._course["course"], 1, 0)
        self._show_msg("New course created.")

    def _cmd_import(self):
        path = ask_open_png(initial_dir="assets/tilemaps")
        if not path:
            return
        stem = os.path.splitext(os.path.basename(path))[0]
        try:
            sheet = pygame.image.load(path).convert_alpha()
        except pygame.error as exc:
            self._show_msg(f"Load failed: {exc}")
            return
        try:
            rel = os.path.relpath(path).replace("\\", "/")
        except ValueError:
            rel = path.replace("\\", "/")
        self._tilesets[stem]      = sheet
        self._tileset_paths[stem] = rel
        self._tileset.add_tileset(stem, sheet)
        cols = sheet.get_width()  // 16
        rows = sheet.get_height() // 16
        self._show_msg(f"Loaded: {stem}  ({cols}×{rows} tiles)")

    def _cmd_save(self):
        # Flush current hole state into course dict
        self._flush_current_hole()

        # Validate
        issues = validate_course(self._course)
        errors   = [m for lvl, m in issues if lvl == "error"]
        warnings = [m for lvl, m in issues if lvl == "warning"]

        if errors:
            for msg in errors:
                print(f"[ERROR] {msg}")
            self._show_msg(
                f"Save blocked — {len(errors)} error(s). See console.", 5.0)
            return

        if warnings:
            for msg in warnings:
                print(f"[WARNING] {msg}")
            self._show_msg(
                f"Saved with {len(warnings)} warning(s). See console.", 4.0)

        if not self._filepath:
            tour = self._course["course"].get("tour", "development")
            path = ask_save_file(
                initial_dir=os.path.join("data", "courses", tour))
            if not path:
                return
            self._filepath = path

        try:
            save_course(self._course, self._filepath, self._tileset_paths)
            self._dirty = False
            if not warnings:
                self._show_msg("Saved.")
        except Exception as exc:
            self._show_msg(f"Save error: {exc}")

    def _cmd_open(self):
        path = ask_open_file(initial_dir="data/courses")
        if not path:
            return
        try:
            course_data, tileset_specs = load_course(path)
        except Exception as exc:
            self._show_msg(f"Load error: {exc}")
            return

        # Reload tilesets
        self._tilesets.clear()
        self._tileset_paths.clear()
        self._tileset.clear()
        for spec in tileset_specs:
            tid, tpath = spec["id"], spec["path"]
            if not os.path.exists(tpath):
                self._show_msg(f"Missing tileset: {tpath}")
                continue
            try:
                sheet = pygame.image.load(tpath).convert_alpha()
                self._tilesets[tid]      = sheet
                self._tileset_paths[tid] = tpath.replace("\\", "/")
                self._tileset.add_tileset(tid, sheet)
            except pygame.error as exc:
                self._show_msg(f"Tileset error: {exc}")

        self._course       = course_data
        self._filepath     = path
        self._dirty        = False
        self._current_hole = 0

        self._load_hole(0)
        self._hole_panel.populate_course(
            course_data["course"],
            len(course_data.get("holes", [])),
            0,
        )
        self._show_msg(
            f"Opened: {os.path.basename(path)}  "
            f"({len(course_data.get('holes', []))} hole(s))")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _show_msg(self, text: str, duration: float = 3.0):
        self._status_msg = text
        self._msg_timer  = duration
