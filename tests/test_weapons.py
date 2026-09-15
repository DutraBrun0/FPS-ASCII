"""Regressoes de regras de combate: alcance, paredes, altura e municao."""
from dataclasses import dataclass
import math
import unittest

from fps_ascii.maps import WorldMap
from fps_ascii.player import Player
from fps_ascii.weapons import WeaponSystem


@dataclass
class Target:
    x: float
    y: float
    hp: float = 500
    radius: float = .3
    height: float = 1.1

    @property
    def alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)


class WeaponsTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldMap()
        self.world.grid = ("#" * 32,) + ("#" + "." * 30 + "#",) * 7 + ("#" * 32,)
        self.world.width, self.world.height = 32, 9
        self.player = Player(2.5, 4.5, 0)
        self.weapons = WeaponSystem(seed=123)

    def wall_at(self, x, y):
        rows = [list(row) for row in self.world.grid]
        rows[y][x] = "#"
        self.world.grid = tuple("".join(row) for row in rows)

    def test_nearest_enemy_absorbs_bullet(self):
        near, far = Target(4.5, 4.5), Target(6.5, 4.5)
        self.assertTrue(self.weapons.fire(self.player, [far, near], self.world))
        self.assertLess(near.hp, 500)
        self.assertEqual(far.hp, 500)
        self.assertGreater(self.weapons.hit_marker, 0)

    def test_bullets_and_sword_do_not_hit_through_walls(self):
        self.wall_at(4, 4)
        target = Target(5.5, 4.5)
        self.weapons.fire(self.player, [target], self.world)
        self.assertEqual(target.hp, 500)
        self.player.x = 3.75
        target.x = 5.1
        self.weapons.update(1)
        self.weapons.select(4)
        self.weapons.fire(self.player, [target], self.world)
        self.assertEqual(target.hp, 500)

    def test_vertical_aim_can_miss_and_then_hit(self):
        target = Target(8.5, 4.5)
        self.player.pitch = .5
        self.weapons.fire(self.player, [target], self.world)
        self.assertEqual(target.hp, 500)
        self.weapons.update(1)
        self.player.pitch = 0
        self.weapons.fire(self.player, [target], self.world)
        self.assertLess(target.hp, 500)

    def test_reload_transfers_only_available_ammunition(self):
        state = self.weapons.states[0]
        state.ammo, state.reserve = 0, 3
        self.assertFalse(self.weapons.fire(self.player, [], self.world))
        self.assertTrue(self.weapons.reload())
        self.assertFalse(self.weapons.reload())
        self.assertFalse(self.weapons.fire(self.player, [], self.world))
        self.weapons.update(2)
        self.assertEqual((self.weapons.ammo, self.weapons.reserve), (3, 0))
        self.assertFalse(self.weapons.reload())

    def test_switching_cancels_reload_and_preserves_shot_cooldown(self):
        self.weapons.states[0].ammo = 0
        self.weapons.reload()
        self.weapons.select(1)
        self.weapons.update(3)
        self.assertEqual(self.weapons.states[0].ammo, 0)
        self.weapons.fire(self.player, [], self.world)
        self.weapons.select(3)
        self.assertFalse(self.weapons.fire(self.player, [], self.world))
        self.weapons.update(.2)
        self.assertTrue(self.weapons.fire(self.player, [], self.world))

    def test_sniper_scope_reduces_dispersion(self):
        class OuterSpread:
            def uniform(self, low, high):
                return high
        self.weapons.rng = OuterSpread()
        self.weapons.select(3)
        target = Target(24.5, 4.5, radius=.2)
        self.weapons.fire(self.player, [target], self.world, zoom=False)
        self.assertEqual(target.hp, 500)
        self.weapons.update(2)
        self.weapons.fire(self.player, [target], self.world, zoom=True)
        self.assertLess(target.hp, 500)

    def test_shotgun_is_stronger_up_close(self):
        close = Target(4.5, 4.5)
        far = Target(9.5, 4.5)
        self.weapons.select(2)
        self.weapons.fire(self.player, [close], self.world)
        self.weapons.update(1)
        self.weapons.fire(self.player, [far], self.world)
        self.assertLess(close.hp, far.hp)
        self.assertEqual(self.weapons.ammo, 6)

    def test_sword_needs_range_and_facing_but_no_ammo(self):
        self.weapons.select(4)
        target = Target(1.5, 4.5)
        self.weapons.fire(self.player, [target], self.world)
        self.assertEqual(target.hp, 500)
        self.weapons.update(1)
        target.x = 4.5
        self.weapons.fire(self.player, [target], self.world)
        self.assertEqual(target.hp, 500)
        self.weapons.update(1)
        target.x = 3.5
        self.weapons.fire(self.player, [target], self.world)
        self.assertLess(target.hp, 500)
        self.assertEqual((self.weapons.ammo, self.weapons.reserve), (0, 0))

    def test_jump_changes_bullet_origin(self):
        target = Target(8.5, 4.5, height=.7)
        self.player.z = .6
        self.weapons.fire(self.player, [target], self.world)
        self.assertEqual(target.hp, 500)
        self.weapons.update(1)
        self.player.pitch = math.atan2(.35 - self.player.camera_height, 6)
        self.weapons.fire(self.player, [target], self.world)
        self.assertLess(target.hp, 500)


if __name__ == "__main__":
    unittest.main()

