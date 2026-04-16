"""
editor_app.py — top-level editor application loop.

Layout (1440 × 900)
────────────────────
  Toolbar        : y=0,    h=48    (pygame_gui buttons)
  Tileset panel  : x=0,    y=48,  w=240, h=480  (tileset palette)
  Attribute panel: x=0,    y=528, w=240, h=348  (terrain brush)
  Canvas         : x=240,  y=48,  w=1200, h=828 (tile painting area)
  Status bar     : y=876,  h=24

Controls summary
────────────────
  Left-click / drag         → paint visual tile
  A + left-click / drag     → paint attribute brush
  F + left-click            → flood fill (A held = attribute layer)
  Right-click               → eyedropper
  Space/Middle + drag       → pan
  Scroll wheel              → zoom
"""

import os
import sys

import pygame
import pygame_gui

from tools.editor.canvas          import CourseCanvas
from tools.editor.tileset_panel   import TilesetPanel
from tools.editor.attribute_panel import AttributePanel
from tools.editor.dialogs import (
    ask_open_png, ask_open_file, ask_save_file,
    make_empty_course, save_course, load_course,
)

# ── Layout constants ──────────────────────────────────────────────────────────
SCREEN_W      = 1440
SCREEN_H      = 900
TOOLBAR_H     = 48
STATUS_H      = 24
PANEL_W       = 240
CANVAS_H      = SCREEN_H - TOOLBAR_H - STATUS_H      # 828
TILESET_H     = 480
ATTR_H        = CANVAS_H - TILESET_H                  # 348

CANVAS_RECT   = pygame.Rect(PANEL_W,   TOOLBAR_H,           SCREEN_W - PANEL_W, CANVAS_H)
TILESET_RECT  = pygame.Rect(0,         TOOLBAR_H,            PANEL_W, TILESET_H)
ATTR_RECT     = pygame.Rect(0,         TOOLBAR_H + TILESET_H, PANEL_W, ATTR_H)

# Colours
C_BG        = (30,  30,  30)
C_TOOLBAR   = (45,  45,  45)
C_STATUS_BG = (38,  38,  38)
C_STATUS_FG = (180, 180, 180)
C_BORDER    = (65,  65,  65)


class EditorApp:
    """Main course editor application."""

    def __init__(self):
        pygame.display.set_caption("Golf Course Editor  —  Phase E2")
        self._screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self._clock  = pygame.time.Clock()
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
        self._course   = make_empty_course()
        self._filepath: str | None = None
        self._dirty    = False

        # Sub-components
        self._canvas  = CourseCanvas(CANVAS_RECT)
        self._tileset = TilesetPanel(TILESET_RECT)
        self._attr    = AttributePanel(ATTR_RECT)

        # Sync canvas defaults from attribute panel
        self._canvas.active_attribute   = self._attr.selected
        self._canvas.auto_derive_enabled = self._attr.auto_derive

        # Fonts
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

        # File operations
        self._btn_new    = btn("New",        8,   60)
        self._btn_open   = btn("Open",       72,  60)
        self._btn_save   = btn("Save",       136, 60)
        # Tileset
        self._btn_import = btn("Import PNG", 220, 110)
        # Canvas display
        self._btn_grid   = btn("Grid",       360, 56)
        self._btn_zoom_m = btn("Zoom -",     420, 64)
        self._btn_zoom_p = btn("Zoom +",     488, 64)
        # View mode toggles
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

                # Attribute panel (bottom-left)
                if self._attr.handle_event(event):
                    self._canvas.active_attribute    = self._attr.selected
                    self._canvas.auto_derive_enabled = self._attr.auto_derive
                    continue

                # Tileset panel (top-left)
                if self._tileset.handle_event(event, self._tilesets):
                    if self._tileset.selected_tile is not None:
                        self._canvas.active_brush      = self._tileset.selected_tile
                        self._tileset.selected_tile    = None
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

        # Toolbar background
        pygame.draw.rect(self._screen, C_TOOLBAR,
                         pygame.Rect(0, 0, SCREEN_W, TOOLBAR_H))
        pygame.draw.line(self._screen, C_BORDER,
                         (0, TOOLBAR_H - 1), (SCREEN_W, TOOLBAR_H - 1))

        # Highlight active view-mode button label
        self._tint_view_buttons()

        # Canvas
        self._canvas.draw(self._screen, self._tilesets)

        # Left panels
        self._tileset.draw(self._screen, self._tilesets,
                           active_brush=self._canvas.active_brush)
        self._attr.draw(self._screen)

        # Status bar
        self._draw_status()

        # pygame_gui on top
        self._ui.draw_ui(self._screen)

        pygame.display.flip()

    def _tint_view_buttons(self):
        """Draw a small indicator line under the active view-mode button."""
        mapping = {
            "visual":      self._btn_view_v,
            "attributes":  self._btn_view_a,
            "both":        self._btn_view_b,
        }
        active_btn = mapping.get(self._canvas.view_mode)
        for btn in mapping.values():
            r = btn.rect
            active = (btn is active_btn)
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

        # Tile position
        tile_txt = ""
        if self._canvas.hovered_tile is not None:
            c, r = self._canvas.hovered_tile
            attr_char = self._canvas.attribute_grid[r][c]
            from src.golf.terrain import CHAR_TO_TERRAIN, TERRAIN_PROPS
            terr  = CHAR_TO_TERRAIN.get(attr_char)
            tname = TERRAIN_PROPS[terr]["name"] if terr else "?"
            tile_txt = f"({c},{r})  {tname}"

        # Active brushes
        brush_txt = ""
        if self._canvas.active_brush:
            tid, sc, sr = self._canvas.active_brush
            brush_txt = f"Tile: {tid}({sc},{sr})"

        attr_txt  = f"Attr: {self._canvas.active_attribute.name}"
        zoom_txt  = f"{self._canvas.zoom:.1f}×"
        mode_txt  = self._canvas.view_mode.upper()
        file_name = os.path.basename(self._filepath) if self._filepath else "Untitled"
        dirty_sfx = " *" if self._dirty else ""

        parts = [p for p in [tile_txt, brush_txt, attr_txt, zoom_txt,
                              mode_txt, file_name + dirty_sfx] if p]
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

    # ── Commands ──────────────────────────────────────────────────────────────

    def _cmd_new(self):
        self._course   = make_empty_course()
        self._filepath = None
        self._dirty    = False
        self._canvas.reset()
        self._tileset.clear()
        self._tilesets.clear()
        self._tileset_paths.clear()
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
        if not self._filepath:
            path = ask_save_file(initial_dir="data/courses/development")
            if not path:
                return
            self._filepath = path

        try:
            save_course(
                self._course,
                self._filepath,
                self._canvas.visual_grid,
                self._canvas.attribute_grid,
                self._tileset_paths,
            )
            self._dirty = False
            self._show_msg("Saved.")
        except Exception as exc:
            self._show_msg(f"Save error: {exc}")

    def _cmd_open(self):
        path = ask_open_file(initial_dir="data/courses")
        if not path:
            return

        try:
            course_data, visual_grid, attribute_grid, tileset_specs = load_course(path)
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
                self._show_msg(f"Tileset load error: {exc}")

        self._course   = course_data
        self._filepath = path
        self._dirty    = False
        self._canvas.load_grids(visual_grid, attribute_grid)
        self._show_msg(f"Opened: {os.path.basename(path)}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _show_msg(self, text: str, duration: float = 3.0):
        self._status_msg = text
        self._msg_timer  = duration
