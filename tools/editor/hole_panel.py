"""
hole_panel.py — right-side panel for hole metadata and course info (Phase E3).

Layout (panel rect: x=1220, y=48, w=220, h=828)
────────────────────────────────────────────────
  HOLE INFO   : navigation, par, yds, SI, Set Tee / Set Pin
  COURSE INFO : name, tour dropdown, hole grid, add/delete hole
"""

import pygame
import pygame_gui

TOURS = ["amateur", "challenger", "development", "continental", "world", "grand"]

C_PANEL_BG    = (40, 40, 40)
C_SECTION_HDR = (50, 50, 50)
C_LABEL       = (155, 155, 155)
C_SEP         = (65, 65, 65)
C_HOLE_BTN    = (58, 58, 58)
C_HOLE_ACTIVE = (50, 120, 215)
C_HOLE_EMPTY  = (42, 42, 42)
C_HOLE_TEXT   = (210, 210, 210)
C_BORDER      = (70, 70, 70)
C_ARM_TEE     = (50, 190, 50)
C_ARM_PIN     = (215, 55, 55)


class HolePanel:
    """Right-panel widget: hole metadata editor + course management."""

    # ── Construction ──────────────────────────────────────────────────────────

    def __init__(self, rect: pygame.Rect, ui_manager):
        self.rect  = rect
        self._ui   = ui_manager
        self._font     = pygame.font.SysFont("monospace", 12)
        self._font_hdr = pygame.font.SysFont("monospace", 12, bold=True)

        self._hole_index  = 0
        self._total_holes = 1

        x = rect.x
        y = rect.y
        w = rect.width

        def btn(label, rx, ry, bw, bh=24):
            return pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x + rx, y + ry, bw, bh),
                text=label,
                manager=ui_manager,
            )

        def entry(rx, ry, ew, eh=24):
            e = pygame_gui.elements.UITextEntryLine(
                relative_rect=pygame.Rect(x + rx, y + ry, ew, eh),
                manager=ui_manager,
            )
            return e

        # ── Hole navigation ───────────────────────────────────────────────────
        # "Hole N/M" label is drawn manually between the buttons
        self._btn_prev = btn("◀", 6,     20, 26)
        self._btn_next = btn("▶", w - 32, 20, 26)

        # ── Hole metadata (par / yds / SI) ────────────────────────────────────
        # Labels drawn in draw(); entries positioned inline with labels
        self._par_entry = entry(60, 52, 100)
        self._par_entry.set_text("4")

        self._yds_entry = entry(60, 82, 100)
        self._yds_entry.set_text("0")
        self._btn_calc_yds = btn("Calc Yds", 6, 108, w - 12, 20)

        self._si_entry = entry(60, 136, 100)
        self._si_entry.set_text("1")

        # ── Set Tee / Set Pin ─────────────────────────────────────────────────
        self._btn_set_tee = btn("Set Tee", 6,   166, 95)
        self._btn_set_pin = btn("Set Pin", 113, 166, 95)

        # ── Course metadata ───────────────────────────────────────────────────
        # Name entry (full-width below label)
        self._name_entry = entry(52, 222, w - 58)
        self._name_entry.set_text("Untitled")

        # Tour dropdown — recreated in populate_course() when tour changes
        self._tour_dropdown: pygame_gui.elements.UIDropDownMenu | None = None
        self._tour_dropdown_rect = pygame.Rect(x + 52, y + 252, w - 58, 26)
        self._make_tour_dropdown("development")

        # ── Add / Delete hole ─────────────────────────────────────────────────
        self._btn_add_hole = btn("+ Hole", 6,   386, 95)
        self._btn_del_hole = btn("- Hole", 113, 386, 95)

        # ── Copy hole ─────────────────────────────────────────────────────────
        self._btn_copy_hole = btn("Copy Hole →", 6, 418, w - 12)

        # ── Grid size ─────────────────────────────────────────────────────────
        self._cols_entry = entry(52, 472, 60)
        self._cols_entry.set_text("48")
        self._rows_entry = entry(52, 500, 60)
        self._rows_entry.set_text("36")
        self._btn_resize = btn("Resize Grid", 6, 528, w - 12)

        # Pre-build the 18-slot hole-grid rects (constant positions)
        self._hole_btn_rects: list[pygame.Rect] = self._build_hole_rects()

    # ── Public API ────────────────────────────────────────────────────────────

    def populate_hole(self, hole_data: dict) -> None:
        """Fill hole metadata fields from a hole dict."""
        self._par_entry.set_text(str(hole_data.get("par", 4)))
        self._yds_entry.set_text(str(hole_data.get("yardage", 0)))
        self._si_entry.set_text(str(hole_data.get("stroke_index", 1)))
        self._cols_entry.set_text(str(hole_data.get("grid_cols", 48)))
        self._rows_entry.set_text(str(hole_data.get("grid_rows", 36)))

    def get_grid_size(self) -> tuple[int, int]:
        """Return (cols, rows) from the grid-size entry fields."""
        try:
            cols = max(8, min(200, int(self._cols_entry.get_text())))
        except ValueError:
            cols = 48
        try:
            rows = max(8, min(200, int(self._rows_entry.get_text())))
        except ValueError:
            rows = 36
        return cols, rows

    def populate_course(self, course_meta: dict, total_holes: int,
                        hole_index: int) -> None:
        """Fill course-level fields and update hole count/selection."""
        self._name_entry.set_text(course_meta.get("name", "Untitled"))
        tour = course_meta.get("tour", "development")
        if tour not in TOURS:
            tour = "development"
        self._make_tour_dropdown(tour)
        self._total_holes = total_holes
        self._hole_index  = hole_index

    def set_current_hole(self, index: int, total: int) -> None:
        self._hole_index  = index
        self._total_holes = total

    def get_hole_meta(self) -> tuple[int, int, int]:
        """Return (par, yardage, stroke_index)."""
        try:
            par = max(3, min(6, int(self._par_entry.get_text())))
        except ValueError:
            par = 4
        try:
            yds = max(0, int(self._yds_entry.get_text()))
        except ValueError:
            yds = 0
        try:
            si = max(1, min(18, int(self._si_entry.get_text())))
        except ValueError:
            si = 1
        return par, yds, si

    def get_course_meta(self) -> tuple[str, str]:
        """Return (name, tour)."""
        name = (self._name_entry.get_text() or "Untitled").strip()
        opt  = self._tour_dropdown.selected_option if self._tour_dropdown else "development"
        # pygame_gui may return a string, list, or tuple depending on version
        if isinstance(opt, (list, tuple)):
            tour = opt[0]
        else:
            tour = opt
        return name, tour

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event) -> str | None:
        """
        Returns an action string or None:
          'prev_hole', 'next_hole', 'add_hole', 'del_hole',
          'arm_tee', 'arm_pin', 'go_hole:<0-based index>',
          'copy_hole', 'resize_grid'
        """
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            elem = event.ui_element
            if elem == self._btn_prev:
                return "prev_hole"
            if elem == self._btn_next:
                return "next_hole"
            if elem == self._btn_calc_yds:
                return "calc_yds"
            if elem == self._btn_set_tee:
                return "arm_tee"
            if elem == self._btn_set_pin:
                return "arm_pin"
            if elem == self._btn_add_hole:
                return "add_hole"
            if elem == self._btn_del_hole:
                return "del_hole"
            if elem == self._btn_copy_hole:
                return "copy_hole"
            if elem == self._btn_resize:
                return "resize_grid"

        # Hole grid click (handled manually — not a pygame_gui element)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self._hole_btn_rects):
                if i >= self._total_holes:
                    break
                if r.collidepoint(event.pos):
                    return f"go_hole:{i}"

        return None

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, set_mode: str | None = None) -> None:
        r = self.rect

        # Panel background + left border
        pygame.draw.rect(surface, C_PANEL_BG, r)
        pygame.draw.line(surface, C_BORDER, (r.x, r.y), (r.x, r.bottom))

        # ── HOLE INFO ─────────────────────────────────────────────────────────
        self._section_header(surface, "HOLE INFO", r.y + 0)

        # Hole navigation label between ◀ / ▶ buttons
        nav   = f"Hole {self._hole_index + 1} / {self._total_holes}"
        ns    = self._font_hdr.render(nav, True, (215, 215, 215))
        surface.blit(ns, (r.x + (r.width - ns.get_width()) // 2, r.y + 26))

        # Par / Yds / SI row labels
        for label, entry_y in [("Par:", 52), ("Yds:", 82), ("SI:", 136)]:
            s  = self._font.render(label, True, C_LABEL)
            ly = r.y + entry_y + (24 - s.get_height()) // 2
            surface.blit(s, (r.x + 6, ly))

        # Arm highlight border around the active set-mode button
        if set_mode == "tee":
            pygame.draw.rect(surface, C_ARM_TEE,
                             pygame.Rect(r.x + 6, r.y + 166, 95, 24), 2)
        elif set_mode == "pin":
            pygame.draw.rect(surface, C_ARM_PIN,
                             pygame.Rect(r.x + 113, r.y + 166, 95, 24), 2)

        # Separator
        sep_y = r.y + 198
        pygame.draw.line(surface, C_SEP, (r.x, sep_y), (r.right, sep_y))

        # ── COURSE INFO ───────────────────────────────────────────────────────
        self._section_header(surface, "COURSE INFO", r.y + 200)

        # Name / Tour row labels
        for label, entry_y in [("Name:", 222), ("Tour:", 252)]:
            s  = self._font.render(label, True, C_LABEL)
            ly = r.y + entry_y + (24 - s.get_height()) // 2
            surface.blit(s, (r.x + 6, ly))

        # Separator above holes list
        sep2_y = r.y + 284
        pygame.draw.line(surface, C_SEP, (r.x, sep2_y), (r.right, sep2_y))

        # "Holes:" header
        hs = self._font_hdr.render("Holes:", True, C_LABEL)
        surface.blit(hs, (r.x + 6, r.y + 288))

        # Hole grid
        self._draw_hole_grid(surface)

        # ── COPY HOLE ─────────────────────────────────────────────────────────
        sep3_y = r.y + 414
        pygame.draw.line(surface, C_SEP, (r.x, sep3_y), (r.right, sep3_y))

        # ── GRID SIZE ─────────────────────────────────────────────────────────
        sep4_y = r.y + 446
        pygame.draw.line(surface, C_SEP, (r.x, sep4_y), (r.right, sep4_y))
        self._section_header(surface, "GRID SIZE", r.y + 448)

        for label, entry_y in [("Cols:", 472), ("Rows:", 500)]:
            s  = self._font.render(label, True, C_LABEL)
            ly = r.y + entry_y + (24 - s.get_height()) // 2
            surface.blit(s, (r.x + 6, ly))

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _section_header(self, surface: pygame.Surface,
                        label: str, abs_y: int) -> None:
        r = self.rect
        pygame.draw.rect(surface, C_SECTION_HDR,
                         pygame.Rect(r.x, abs_y, r.width, 18))
        s = self._font_hdr.render(label, True, (200, 200, 200))
        surface.blit(s, (r.x + 8, abs_y + 2))

    def _make_tour_dropdown(self, selected: str) -> None:
        if self._tour_dropdown is not None:
            self._tour_dropdown.kill()
        self._tour_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=TOURS,
            starting_option=selected if selected in TOURS else "development",
            relative_rect=self._tour_dropdown_rect,
            manager=self._ui,
        )

    def _build_hole_rects(self) -> list[pygame.Rect]:
        bw, bh = 30, 22
        gx, gy = 3, 4
        cols   = 6
        x0     = self.rect.x + 6
        y0     = self.rect.y + 306   # just below "Holes:" label
        rects  = []
        for i in range(18):
            col = i % cols
            row = i // cols
            rects.append(pygame.Rect(
                x0 + col * (bw + gx),
                y0 + row * (bh + gy),
                bw, bh,
            ))
        return rects

    def _draw_hole_grid(self, surface: pygame.Surface) -> None:
        for i, r in enumerate(self._hole_btn_rects):
            exists    = i < self._total_holes
            is_active = exists and (i == self._hole_index)

            bg = C_HOLE_ACTIVE if is_active else (C_HOLE_BTN if exists else C_HOLE_EMPTY)
            pygame.draw.rect(surface, bg, r)
            pygame.draw.rect(surface, (75, 75, 75), r, 1)

            if exists:
                label = str(i + 1)
                ts = self._font.render(label, True, C_HOLE_TEXT)
                surface.blit(ts, (
                    r.x + (r.width  - ts.get_width())  // 2,
                    r.y + (r.height - ts.get_height()) // 2,
                ))
