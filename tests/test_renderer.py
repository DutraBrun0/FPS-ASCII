"""Rendering contracts: ASCII output, perspective, occlusion and SDL surfaces."""

import math
import os
from types import SimpleNamespace
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from fps_ascii.engine import AsciiBuffer, Raycaster
from fps_ascii.maps import WorldMap
from fps_ascii.player import Player


class RendererTests(unittest.TestCase):
    def setUp(self):
        self.buffer = AsciiBuffer(160, 60)
        self.renderer = Raycaster()
        self.world = WorldMap()
        self.world.grid = ("#########",) + ("#.......#",) * 7 + ("#########",)
        self.world.width = self.world.height = 9
        self.world.props = []
        self.player = Player(4.5, 4.5, 0.0)

    def enemy(self, x=6.5, y=4.5):
        return SimpleNamespace(x=x, y=y, height=1.0, sprite=("$$$", "$$$", "$$$"),
                               hurt=0.0, alive=True, kind="TEST", boss=False)

    def render(self, enemies=(), zoom=False):
        self.buffer.clear()
        self.renderer.render(self.buffer, self.world, self.player, enemies, (), 1.0, zoom)
        return self.buffer.lines()

    def test_buffer_clips_and_normalizes_portuguese_to_ascii(self):
        self.buffer.text(-2, 0, "ABMUNICAO")
        self.buffer.text(0, 1, "sa\u00fade / muni\u00e7\u00e3o")
        self.buffer.put(999, 999, "x")
        self.assertTrue(self.buffer.lines()[0].startswith("MUNICAO"))
        self.assertTrue(self.buffer.lines()[1].startswith("saude / municao"))
        self.assertTrue(all(32 <= ord(c) <= 126 for line in self.buffer.lines() for c in line))

    def test_scene_does_not_overwrite_header_or_footer(self):
        self.buffer.text(0, 1, "HEADER")
        self.buffer.text(0, 55, "FOOTER")
        self.renderer.render(self.buffer, self.world, self.player, (), (), 0)
        self.assertTrue(self.buffer.lines()[1].startswith("HEADER"))
        self.assertTrue(self.buffer.lines()[55].startswith("FOOTER"))
        self.assertEqual((self.renderer.scene_top, self.renderer.scene_bottom), (8, 46))

    def test_camera_plane_ray_depth_has_no_fisheye(self):
        self.render()
        self.assertAlmostEqual(self.renderer.zbuffer[80], 3.5)
        self.assertAlmostEqual(self.renderer.zbuffer[30], 3.5)
        self.assertAlmostEqual(self.renderer.zbuffer[130], 3.5)

    def test_walls_occlude_enemy_glyphs(self):
        hidden = "\n".join(self.render([self.enemy(9.5)]))
        self.assertNotIn("$", hidden)
        visible = "\n".join(self.render([self.enemy()]))
        self.assertIn("$", visible)

    def test_zoom_enlarges_enemy_projection(self):
        regular = "".join(self.render([self.enemy()])).count("$")
        zoomed = "".join(self.render([self.enemy()], zoom=True)).count("$")
        self.assertGreater(zoomed, regular)

    def test_positive_pitch_moves_horizon_down(self):
        self.render()
        horizon = self.renderer.horizon
        self.player.pitch = .15
        self.render()
        self.assertGreater(self.renderer.horizon, horizon)

    def test_jump_changes_enemy_vertical_projection(self):
        grounded = self.render([self.enemy()])
        ground_top = next(i for i, line in enumerate(grounded) if "$" in line)
        self.player.z = .3
        jumping = self.render([self.enemy()])
        jump_top = next(i for i, line in enumerate(jumping) if "$" in line)
        self.assertGreater(jump_top, ground_top)

    def test_resize_updates_grid_and_clears_contents(self):
        self.buffer.text(0, 0, "OLD")
        self.buffer.resize(80, 30)
        self.assertEqual(len(self.buffer.lines()), 30)
        self.assertTrue(all(len(line) == 80 and not line.strip() for line in self.buffer.lines()))

    def test_scene_output_is_all_printable_ascii(self):
        for angle in (0, math.pi / 2, math.pi, -math.pi / 2):
            self.player.angle = angle
            for line in self.render([self.enemy()]):
                self.assertTrue(all(32 <= ord(char) <= 126 for char in line))


class SurfaceRenderingTests(unittest.TestCase):
    def test_atlas_is_reused_and_surface_has_glyphs(self):
        try:
            import pygame
        except ImportError:
            self.skipTest("pygame-ce unavailable; simulation rendering remains testable")
        pygame.font.init()
        surface = pygame.Surface((640, 400))
        buffer = AsciiBuffer(80, 30)
        buffer.center(8, "FPS ASCII", "bright")
        buffer.box(2, 2, 76, 25)
        buffer.render(surface, "amber", True)
        first = pygame.image.tobytes(surface, "RGB")
        glyph_count = len(buffer._glyphs)
        self.assertGreater(glyph_count, 0)
        self.assertTrue(any(first))
        buffer.render(surface, "amber", True)
        self.assertEqual(first, pygame.image.tobytes(surface, "RGB"))
        self.assertEqual(glyph_count, len(buffer._glyphs))
        buffer.render(surface, "ice", False)
        self.assertNotEqual(first, pygame.image.tobytes(surface, "RGB"))


if __name__ == "__main__":
    unittest.main()
