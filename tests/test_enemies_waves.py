import math
import unittest

from fps_ascii.enemies import Enemy, EnemyDirector, Projectile, SPRITES
from fps_ascii.game import Game
from fps_ascii.maps import WorldMap
from fps_ascii.player import Player


class EnemyTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldMap()
        self.world.grid = ("#"*20,) + ("#"+"."*18+"#",)*10 + ("#"*20,)
        self.world.width, self.world.height = 20, 12
        self.player = Player(5.5, 5.5, 0)
        self.director = EnemyDirector(seed=2001)

    def projectile(self, **kwargs):
        values = dict(x=1.5, y=5.5, dx=1, dy=0, z=.45)
        values.update(kwargs)
        bullet = Projectile(**values)
        self.director.projectiles = [bullet]
        return bullet

    def test_projectile_survives_free_space(self):
        bullet = self.projectile()
        self.director.update(.1, self.player, self.world, 1)
        self.assertEqual(len(self.director.projectiles), 1)
        self.assertAlmostEqual(bullet.x, 1.95)

    def test_projectile_hits_player_without_tunnelling(self):
        self.projectile(speed=30)
        self.director.update(.25, self.player, self.world, 1)
        self.assertLess(self.player.health, 100)
        self.assertEqual(self.director.projectiles, [])

    def test_wall_stops_fast_projectile_before_player(self):
        rows = list(self.world.grid)
        rows[5] = rows[5][:3] + "#" + rows[5][4:]
        self.world.grid = tuple(rows)
        self.projectile(speed=30)
        self.director.update(.25, self.player, self.world, 1)
        self.assertEqual(self.player.health, 100)
        self.assertEqual(self.director.projectiles, [])

    def test_jump_and_crouch_can_avoid_projectiles(self):
        self.player.z = .60
        self.projectile(speed=30)
        self.director.update(.25, self.player, self.world, 1)
        self.assertEqual(self.player.health, 100)
        self.player.z = 0
        for _ in range(60):
            self.player.update(1/120, {"crouch": True}, self.world)
        self.projectile(speed=30, z=.52)
        self.director.update(.25, self.player, self.world, 1)
        self.assertEqual(self.player.health, 100)

    def test_iloveyou_pursues_and_damages_player(self):
        enemy = Enemy("ILOVEYOU", 9.5, 5.5, 48, 48, 1.5)
        self.director.enemies = [enemy]
        for _ in range(360):
            self.director.update(1/60, self.player, self.world, 1)
        self.assertLess(self.player.health, 100)
        self.assertLess(math.hypot(enemy.x-self.player.x, enemy.y-self.player.y), .8)

    def test_wannacry_splits_once_and_awards_each_kill_once(self):
        parent = Enemy("WannaCry", 10.5, 5.5, 66, 66, .95)
        self.director.enemies = [parent]
        parent.take_damage(1000)
        self.director.update(.01, self.player, self.world, 1)
        self.assertEqual(len(self.director.enemies), 2)
        self.assertTrue(all(e.generation == 1 for e in self.director.enemies))
        self.assertEqual(self.director.kills, 1)
        for child in self.director.enemies:
            child.take_damage(1000)
        self.director.update(.01, self.player, self.world, 1)
        self.assertEqual(self.director.enemies, [])
        self.assertEqual((self.director.kills, self.director.score), (3, 280))
        self.director.update(.01, self.player, self.world, 1)
        self.assertEqual(self.director.kills, 3)

    def test_mydoom_fires_at_range(self):
        enemy = Enemy("Mydoom", 11.5, 5.5, 100, 100, .72, attack_timer=0)
        self.director.enemies = [enemy]
        self.director.update(.01, self.player, self.world, 2)
        self.assertEqual(len(self.director.projectiles), 1)
        self.assertLess(self.director.projectiles[0].dx, 0)

    def test_boss_announces_attack_before_radial_burst(self):
        boss = Enemy("ROOTKIT.EXE", 12.5, 5.5, 540, 540, .62,
                     boss=True, attack_timer=0, sprite=SPRITES["ROOTKIT.EXE"])
        self.director.enemies = [boss]
        messages = self.director.update(.01, self.player, self.world, 3)
        self.assertTrue(any("ALERTA" in message for message in messages))
        self.assertEqual(self.director.projectiles, [])
        for _ in range(3):
            self.director.update(.25, self.player, self.world, 3)
        self.assertEqual(self.director.projectiles, [])
        self.director.update(.06, self.player, self.world, 3)
        self.assertEqual(len(self.director.projectiles), 15)
        angles = {(round(p.dx, 3), round(p.dy, 3)) for p in self.director.projectiles}
        self.assertGreaterEqual(len(angles), 12)

    def test_real_map_spawns_are_clear_and_population_is_bounded(self):
        world = WorldMap()
        player = Player(*world.spawn)
        for wave in (1, 2, 3, 6, 30):
            self.director.spawn_wave(wave, player, world)
            self.assertEqual(sum(e.boss for e in self.director.enemies), int(wave % 3 == 0))
            self.assertLessEqual(len(self.director.enemies), self.director.MAX_ENEMIES)
            self.assertTrue(all(not world.collides(e.x, e.y, e.radius) for e in self.director.enemies))
            if wave >= 2:
                self.assertTrue({"ILOVEYOU", "WannaCry", "Mydoom"}.issubset({e.kind for e in self.director.enemies}))
            for enemy in self.director.enemies:
                if enemy.kind == "WannaCry":
                    enemy.take_damage(100000)
            self.director.update(.01, player, world, wave)
            self.assertLessEqual(len(self.director.enemies), self.director.MAX_ENEMIES)


class ProgressionTests(unittest.TestCase):
    def test_six_waves_finish_with_clones_bosses_and_single_rewards(self):
        game = Game()
        bosses = []
        for wave in range(1, 7):
            for _ in range(60):
                if game.waves.in_progress:
                    break
                game.update(.1, {})
            self.assertEqual(game.waves.wave, wave)
            self.assertTrue(game.waves.in_progress)
            if any(e.boss for e in game.director.enemies):
                bosses.append(wave)
            game.player.health, game.player.armor = 55, 10
            game.weapons.states[0].ammo = 0
            for _ in range(4):
                for enemy in game.director.enemies:
                    enemy.take_damage(100000)
                game.update(.01, {})
                if not game.waves.in_progress:
                    break
            self.assertFalse(game.waves.in_progress)
            self.assertEqual((game.player.health, game.player.armor), (80, 25))
            self.assertEqual(game.weapons.ammo, game.weapons.current.magazine)
            snapshot = game.player.health, game.player.armor, game.weapons.reserve
            game.update(.1, {})
            self.assertEqual(snapshot, (game.player.health, game.player.armor, game.weapons.reserve))
            self.assertEqual(game.director.projectiles, [])
        self.assertEqual(bosses, [3, 6])
        self.assertGreater(game.director.kills, 60)
        self.assertGreater(game.director.score, 6000)


if __name__ == "__main__":
    unittest.main()

