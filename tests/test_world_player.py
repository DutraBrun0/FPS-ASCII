"""Headless regression checks: geometry, navigation and player physics."""

import math
from types import SimpleNamespace
import unittest

from fps_ascii.maps import WorldMap
from fps_ascii.player import Player


class WorldTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldMap()

    def test_every_floor_and_spawn_is_reachable(self):
        sx, sy, _ = self.world.spawn
        self.assertFalse(self.world.collides(sx, sy, 0.42))
        self.world.path_direction(1.5, 1.5, sx, sy)
        floor_count = sum(row.count(".") for row in self.world.grid)
        self.assertEqual(len(self.world._path_distances), floor_count)
        self.assertGreater(len(self.world.spawn_points), 15)
        for x, y in self.world.spawn_points:
            self.assertIn((math.floor(x), math.floor(y)), self.world._path_distances)
            self.assertFalse(self.world.collides(x, y, 0.42))

    def test_outside_map_is_solid(self):
        for x, y in ((-0.1, 5), (25, 5), (5, -0.1), (5, 25)):
            self.assertTrue(self.world.is_wall(x, y))
            self.assertTrue(self.world.collides(x, y, 0.22))
        self.assertTrue(self.world.collides(1.1, 1.5, 0.22))
        self.assertFalse(self.world.collides(1.3, 1.5, 0.22))

    def test_movement_cannot_tunnel_and_slides_along_walls(self):
        entity = SimpleNamespace(x=1.5, y=1.5)
        self.world.move(entity, -30.0, 3.0, 0.22)
        self.assertGreaterEqual(entity.x, 1.22)
        self.assertGreater(entity.y, 4.4)
        self.assertFalse(self.world.collides(entity.x, entity.y, 0.22))

    def test_raycast_uses_ray_parameter_and_los_stops_at_wall(self):
        distance, side, cx, cy = self.world.raycast(1.5, 1.5, -2.0, 0.0)
        self.assertAlmostEqual(distance, 0.25)
        self.assertEqual((side, cx, cy), (0, 0, 1))
        self.assertTrue(self.world.line_of_sight(1.5, 1.5, 7.5, 1.5))
        self.assertFalse(self.world.line_of_sight(7.5, 3.5, 9.5, 3.5))
        self.assertFalse(self.world.line_of_sight(1.5, 1.5, -1.5, 1.5))

    def test_navigation_routes_around_desk(self):
        entity = SimpleNamespace(x=3.5, y=2.5)
        target = (3.5, 6.5)
        for _ in range(800):
            dx, dy = self.world.path_direction(entity.x, entity.y, *target)
            self.world.move(entity, dx * 0.05, dy * 0.05, 0.22)
            if math.hypot(entity.x - target[0], entity.y - target[1]) < 0.1:
                break
        self.assertLess(math.hypot(entity.x - target[0], entity.y - target[1]), 0.15)


class PlayerTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldMap()

    def player(self):
        return Player(12.5, 12.5, 0.0)

    def test_diagonal_movement_has_same_speed(self):
        straight, diagonal = self.player(), self.player()
        straight.update(0.1, {"forward": 1}, self.world)
        diagonal.update(0.1, {"forward": 1, "strafe": 1}, self.world)
        straight_distance = math.hypot(straight.x - 12.5, straight.y - 12.5)
        diagonal_distance = math.hypot(diagonal.x - 12.5, diagonal.y - 12.5)
        self.assertAlmostEqual(straight_distance, diagonal_distance)
        self.assertAlmostEqual(straight_distance, 0.29)

    def test_jump_lands_and_does_not_repeat_without_new_input(self):
        player = self.player()
        player.update(1 / 120, {"jump": True}, self.world)
        max_z = player.z
        for _ in range(180):
            player.update(1 / 120, {}, self.world)
            max_z = max(max_z, player.z)
        self.assertGreater(max_z, 0.5)
        self.assertEqual(player.z, 0.0)
        self.assertEqual(player._vertical_velocity, 0.0)
        self.assertAlmostEqual(player.camera_height, 0.5)

    def test_run_consumes_and_idle_restores_stamina(self):
        player = self.player()
        player.update(0.1, {"forward": 1, "run": True}, self.world)
        self.assertLess(player.stamina, 100.0)
        self.assertGreater(player.fov, math.radians(70))
        for _ in range(60):
            player.update(1 / 60, {}, self.world)
        self.assertEqual(player.stamina, 100.0)

    def test_slide_boost_is_finite_and_requires_a_new_crouch_press(self):
        player = self.player()
        player.update(0.1, {"forward": 1, "crouch": True}, self.world)
        self.assertGreater(player.x - 12.5, 0.4)
        self.assertGreater(player.slide_timer, 0.0)
        self.assertLess(player.stamina, 85.0)
        for _ in range(120):
            player.update(1 / 60, {"crouch": True}, self.world)
        self.assertEqual(player.slide_timer, 0.0)
        self.assertTrue(player.crouching)
        self.assertLess(player.camera_height, 0.31)

    def test_damage_spends_armor_and_dead_player_cannot_move(self):
        player = self.player()
        player.damage(20)
        self.assertEqual(player.armor, 27.0)
        self.assertEqual(player.health, 93.0)
        player.heal(50)
        self.assertEqual(player.health, 100.0)
        player.damage(1000)
        player.update(0.1, {"forward": 1, "jump": True}, self.world)
        self.assertFalse(player.alive)
        self.assertEqual((player.x, player.y, player.z), (12.5, 12.5, 0.0))


if __name__ == "__main__":
    unittest.main()

