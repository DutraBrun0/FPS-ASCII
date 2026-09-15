"""A fixed character grid and cached, monospace terminal glyph renderer.

No graphical sprites or geometry are drawn: every visible mark is an ASCII
character.  Pygame is imported lazily so simulation/tests can run without SDL.
"""

from __future__ import annotations

import unicodedata


PALETTES = {
    "green": {
        "normal": (91, 208, 129), "dim": (28, 76, 52),
        "bright": (171, 255, 184), "accent": (235, 207, 117),
        "danger": (255, 101, 111), "muted": (48, 126, 82),
        "white": (224, 245, 228),
    },
    "amber": {
        "normal": (230, 173, 77), "dim": (83, 57, 27),
        "bright": (255, 217, 135), "accent": (255, 237, 190),
        "danger": (255, 105, 75), "muted": (132, 92, 40),
        "white": (255, 241, 210),
    },
    "ice": {
        "normal": (108, 199, 223), "dim": (28, 62, 84),
        "bright": (185, 241, 255), "accent": (248, 201, 119),
        "danger": (255, 115, 146), "muted": (57, 111, 140),
        "white": (228, 248, 255),
    },
}


class AsciiBuffer:
    """Clipped text drawing; cell dimensions adapt to the window at render time."""

    def __init__(self, cols: int = 144, rows: int = 72):
        self.cell_width = 8
        self.cell_height = 13
        self.cell_aspect = self.cell_width / self.cell_height
        self.offset = (0, 0)
        self.font_size = 13
        self._font = None
        self._font_key = None
        self._glyphs = {}
        self.resize(cols, rows)

    def resize(self, cols: int, rows: int) -> None:
        self.cols, self.rows = max(1, int(cols)), max(1, int(rows))
        self._chars = [[" "] * self.cols for _ in range(self.rows)]
        self._colors = [["normal"] * self.cols for _ in range(self.rows)]
        self._font_key = None
        self._glyphs.clear()
        self._row_keys = [None] * self.rows
        self._row_surfaces = [None] * self.rows

    def clear(self, char: str = " ", color: str = "normal") -> None:
        char = char[0] if char and 32 <= ord(char[0]) <= 126 else " "
        for y in range(self.rows):
            self._chars[y][:] = [char] * self.cols
            self._colors[y][:] = [color] * self.cols

    def put(self, x: int, y: int, char: str, color: str = "normal") -> None:
        x, y = int(x), int(y)
        if 0 <= x < self.cols and 0 <= y < self.rows and char:
            char = char[0]
            self._chars[y][x] = char if 32 <= ord(char) <= 126 else "?"
            self._colors[y][x] = color

    def text(self, x: int, y: int, text: str, color: str = "normal") -> None:
        # UI strings may be Portuguese, but the output always stays 7-bit ASCII.
        text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
        x, y = int(x), int(y)
        for offset, line in enumerate(text.split("\n")):
            row = y + offset
            if not 0 <= row < self.rows:
                continue
            start, end = max(0, x), min(self.cols, x + len(line))
            if start < end:
                visible = line[start - x:end - x]
                self._chars[row][start:end] = [c if 32 <= ord(c) <= 126 else " " for c in visible]
                self._colors[row][start:end] = [color] * len(visible)

    def center(self, y: int, text: str, color: str = "normal") -> None:
        for offset, line in enumerate(str(text).split("\n")):
            self.text((self.cols - len(line)) // 2, y + offset, line, color)

    def box(self, x: int, y: int, w: int, h: int, color: str = "dim") -> None:
        if w < 2 or h < 2:
            return
        self.text(x, y, "+" + "-" * (w - 2) + "+", color)
        self.text(x, y + h - 1, "+" + "-" * (w - 2) + "+", color)
        for row in range(y + 1, y + h - 1):
            self.put(x, row, "|", color)
            self.put(x + w - 1, row, "|", color)

    def fill(self, x: int, y: int, w: int, h: int, char: str = " ", color: str = "normal") -> None:
        """Clear or shade a rectangular area using characters (for modal panels)."""
        for row in range(max(0, y), min(self.rows, y + h)):
            self.text(x, row, char[:1] * max(0, w), color)

    def lines(self) -> list[str]:
        """Return the actual character output, useful for headless validation."""
        return ["".join(row) for row in self._chars]

    def _prepare_font(self, surface) -> None:
        import pygame

        width, height = surface.get_size()
        cell_width = max(1, width // self.cols)
        cell_height = max(1, height // self.rows)
        key = cell_width, cell_height
        self.offset = ((width - cell_width * self.cols) // 2,
                       (height - cell_height * self.rows) // 2)
        self.cell_width, self.cell_height = key
        self.cell_aspect = cell_width / cell_height
        if self._font_key == key:
            return
        if not pygame.font.get_init():
            pygame.font.init()
        self.font_size = max(6, cell_height)
        font_path = pygame.font.match_font("consolas,couriernew,dejavusansmono,liberationmono")
        self._font = pygame.font.Font(font_path, self.font_size)
        self._font_key = key
        self._glyphs.clear()
        self._row_keys = [None] * self.rows
        self._row_surfaces = [None] * self.rows

    def render(self, surface, palette: str = "green", scanlines: bool = True) -> None:
        """Blit cached glyphs in one batch; no text rasterization in the hot path.

        Scanlines are alternating glyph brightness, not a graphical overlay.
        The grid fills whole pixel cells and centers any leftover pixel margin.
        """
        import pygame

        self._prepare_font(surface)
        surface.fill((0, 0, 0))
        palette = palette if palette in PALETTES else "green"
        colors = PALETTES[palette]
        cell_width, cell_height = self.cell_width, self.cell_height
        ox, oy = self.offset
        jobs = []
        glyphs = self._glyphs
        for y, row in enumerate(self._chars):
            row_dim = bool(scanlines and y % 2)
            py = oy + y * cell_height
            # Static rows (menus, HUD and still camera) need one blit, not 160.
            row_key = "".join(row), tuple(self._colors[y]), palette, row_dim
            row_surface = self._row_surfaces[y]
            if self._row_keys[y] == row_key:
                jobs.append((row_surface, (ox, py)))
                continue
            if row_surface is None:
                row_surface = pygame.Surface((self.cols * cell_width, cell_height))
                self._row_surfaces[y] = row_surface
            row_surface.fill((0, 0, 0))
            row_jobs = []
            for x, char in enumerate(row):
                if char == " ":
                    continue
                color_name = self._colors[y][x]
                key = palette, color_name, row_dim, char
                glyph = glyphs.get(key)
                if glyph is None:
                    rgb = colors.get(color_name, colors["normal"])
                    if row_dim:
                        rgb = tuple(int(component * .84) for component in rgb)
                    glyph = self._font.render(char, True, rgb)
                    # Every glyph occupies the same cell, even on a fallback font.
                    if glyph.get_size() != (cell_width, cell_height):
                        glyph = pygame.transform.scale(glyph, (cell_width, cell_height))
                    glyphs[key] = glyph
                row_jobs.append((glyph, (x * cell_width, 0)))
            row_surface.blits(row_jobs, doreturn=False)
            self._row_keys[y] = row_key
            jobs.append((row_surface, (ox, py)))
        surface.blits(jobs, doreturn=False)
