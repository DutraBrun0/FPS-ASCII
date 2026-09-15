"""Integration regressions for actual pygame input and application states.

SDL uses its dummy driver: these checks never open a visible window.
"""

from collections import defaultdict
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
try:
    import pygame
except ImportError:
    pygame = None

if pygame is not None:
    from fps_ascii.app import Application, parse_args


@unittest.skipIf(pygame is None, "Install requirements.txt for SDL integration tests")
class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.app = Application(parse_args(["--headless", "--no-audio", "--size", "800x600"]))
        self.addCleanup(pygame.quit)
        pygame.event.clear()
        self.keys = defaultdict(bool)
        self.mouse = [False, False, False]
        for name, callback in (
            ("pygame.key.get_pressed", lambda: self.keys),
            ("pygame.mouse.get_pressed", lambda: self.mouse),
        ):
            mock = patch(name, side_effect=callback)
            mock.start()
            self.addCleanup(mock.stop)

    def tick(self, frames=1):
        for _ in range(frames):
            self.app.update(1 / 60)

    def assert_screen_contains(self, text):
        self.app.render()
        self.assertIn(text, "\n".join(self.app.buffer.lines()))

    def test_menu_pause_resume_preserve_the_match(self):
        self.assertEqual(self.app.state, "menu")
        self.assert_screen_contains("INICIAR CONEXAO")
        self.app.handle_key(pygame.K_RETURN)
        self.assertEqual(self.app.state, "playing")
        game = self.app.game
        self.tick(6)
        before = (game.time, game.player.x, game.player.health, game.weapons.ammo)
        self.app.handle_key(pygame.K_ESCAPE)
        self.assertEqual(self.app.state, "paused")
        self.assert_screen_contains("RETOMAR CONEXAO")
        self.tick(90)
        self.assertEqual(before, (game.time, game.player.x, game.player.health, game.weapons.ammo))
        self.app.handle_key(pygame.K_ESCAPE)
        self.assertEqual(self.app.state, "playing")
        self.assertIs(self.app.game, game)
        self.tick()
        self.assertGreater(game.time, before[0])

    def test_help_from_game_returns_to_pause(self):
        self.app.start()
        game = self.app.game
        self.app.handle_key(pygame.K_F1)
        self.assertEqual(self.app.state, "help")
        self.assert_screen_contains("MANUAL.TXT")
        self.tick(30)
        self.assertEqual(game.time, 0.0)
        self.app.handle_key(pygame.K_RETURN)
        self.assertEqual(self.app.state, "paused")
        self.assertIs(self.app.game, game)
        self.app.handle_key(pygame.K_RETURN)
        self.assertEqual(self.app.state, "playing")

    def test_death_and_reconnect_reset_match_state(self):
        self.app.start()
        old_game = self.app.game
        self.app.handle_key(pygame.K_f)
        self.tick()
        self.assertEqual(old_game.shots, 1)
        old_game.player.health = 0
        self.tick()
        self.assertEqual(self.app.state, "dead")
        self.assert_screen_contains("FATAL EXCEPTION")
        self.app.handle_key(pygame.K_RETURN)
        self.assertEqual(self.app.state, "playing")
        self.assertIsNot(self.app.game, old_game)
        self.assertEqual(self.app.game.player.health, 100)
        self.assertEqual(self.app.game.shots, 0)
        self.assertEqual(self.app.game.time, 0.0)
        self.assertEqual(self.app.game.weapons.index, 0)

    def test_pending_actions_survive_short_frame_but_pause_discards_them(self):
        self.app.start()
        self.app.handle_key(pygame.K_SPACE)
        self.app.handle_key(pygame.K_f)
        self.app.update(1 / 480)
        self.assertEqual(self.app.game.shots, 0)
        self.assertEqual(self.app.game.player.z, 0)
        self.tick()
        self.assertEqual(self.app.game.shots, 1)
        self.assertGreater(self.app.game.player.z, 0)
        self.app.start()
        self.app.handle_key(pygame.K_SPACE)
        self.app.handle_key(pygame.K_f)
        self.app.handle_key(pygame.K_ESCAPE)
        self.app.handle_key(pygame.K_ESCAPE)
        self.tick()
        self.assertEqual(self.app.game.shots, 0)
        self.assertEqual(self.app.game.player.z, 0)

    def test_pistol_click_fires_once_even_with_mouse_and_key_held(self):
        self.app.start()
        ammo_before = self.app.game.weapons.ammo
        self.keys[pygame.K_f] = True
        self.mouse[0] = True
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1))
        self.app.events()
        self.tick(75)
        self.assertEqual(self.app.game.shots, 1)
        self.assertEqual(self.app.game.weapons.ammo, ammo_before - 1)

    def test_rifle_continues_firing_while_trigger_is_held(self):
        self.app.start()
        self.app.handle_key(pygame.K_2)
        ammo_before = self.app.game.weapons.ammo
        self.mouse[0] = True
        self.tick(60)
        self.assertGreater(self.app.game.shots, 3)
        self.assertEqual(self.app.game.weapons.ammo, ammo_before - self.app.game.shots)
        self.mouse[0] = False
        count = self.app.game.shots
        self.tick(30)
        self.assertEqual(self.app.game.shots, count)


if __name__ == "__main__":
    unittest.main()

