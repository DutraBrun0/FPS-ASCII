from __future__ import annotations
from dataclasses import dataclass
import math
import random

SPRITES = {
    "ILOVEYOU": (r" \ V / ", r"  @ @  ", r"<[<3]> ", r" /   \ "),
    "WannaCry": (r" .---. ", r" |X X| ", r"/|###|\ ", r"  |_|  "),
    "Mydoom": (r" [===] ", r" |o o| ", r"<|###|>", r" /_|_\ "),
    "ROOTKIT.EXE": (
        r"   /\___/\   ", r"  [X#####X]  ", r" /|@@###@@|\ ",
        r"<<|###V###|>>", r"  |[#####]|  ", r" /|_______|\ ", r"//  || ||  \\",
    ),
}


@dataclass
class Enemy:
    kind: str
    x: float
    y: float
    hp: float
    max_hp: float
    speed: float
    radius: float = .26
    height: float = .90
    sprite: tuple[str, ...] = SPRITES["ILOVEYOU"]
    boss: bool = False
    hurt: float = 0.0
    z: float = 0.0
    generation: int = 0
    attack_timer: float = .7
    windup: float = 0.0
    path_timer: float = 0.0
    direction_x: float = 0.0
    direction_y: float = 0.0
    strafe_sign: int = 1
    wave: int = 1

    @property
    def alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        if self.alive and amount > 0:
            self.hp = max(0.0, self.hp - amount)
            self.hurt = .16


@dataclass
class Projectile:
    x: float
    y: float
    dx: float
    dy: float
    speed: float = 4.5
    damage: float = 9.0
    z: float = .50
    radius: float = .10
    height: float = .20
    sprite: tuple[str, ...] = (" * ", "<#>", " * ")
    ttl: float = 5.0
    alive: bool = True
    kind: str = "PACKET"
    boss: bool = False
    hurt: float = 0.0


class EnemyDirector:
    MAX_ENEMIES = 48
    MAX_PROJECTILES = 100

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.enemies = []
        self.projectiles = []
        self.score = 0
        self.kills = 0

    def _make_enemy(self, kind, x, y, wave, generation=0):
        scale = 1 + min(1.8, max(0, wave - 1) * .11)
        speed_scale = 1 + min(.65, max(0, wave - 1) * .035)
        hp, speed = {
            "ILOVEYOU": (48.0, 1.50), "WannaCry": (66.0, .95),
            "Mydoom": (100.0, .72), "ROOTKIT.EXE": (420.0 + wave * 40.0, .62),
        }[kind]
        boss = kind == "ROOTKIT.EXE"
        if not boss:
            hp *= scale
        if generation:
            hp *= .40
            speed *= 1.28
        return Enemy(
            kind=kind, x=x, y=y, hp=hp, max_hp=hp, speed=speed * speed_scale,
            radius=.43 if boss else (.18 if generation else .26),
            height=1.28 if boss else (.58 if generation else .90),
            sprite=SPRITES[kind], boss=boss, generation=generation,
            attack_timer=self.rng.uniform(.7, 1.6),
            strafe_sign=self.rng.choice((-1, 1)), wave=wave,
        )

    def spawn_wave(self, wave, player, world):
        self.enemies.clear()
        self.projectiles.clear()
        wave = max(1, int(wave))
        points = list(world.spawn_points) or [(world.spawn[0], world.spawn[1])]
        distant = [p for p in points if math.hypot(p[0] - player.x, p[1] - player.y) >= 5]
        if distant:
            points = distant
        else:
            points.sort(key=lambda p: math.hypot(p[0] - player.x, p[1] - player.y), reverse=True)
            points = points[:max(1, len(points) // 3)]
        self.rng.shuffle(points)
        count = min(32, 4 + wave * 2)
        roster = ("ILOVEYOU", "WannaCry", "Mydoom")
        for index in range(count):
            if wave == 1:
                kind = "ILOVEYOU" if index % 3 else "WannaCry"
            else:
              
                kind = roster[index] if index < 3 else self.rng.choices(roster, weights=[5, 3, 2])[0]
            x, y = points[index % len(points)]
            enemy = self._make_enemy(kind, x, y, wave)
            world.move(enemy, self.rng.uniform(-.18, .18), self.rng.uniform(-.18, .18), enemy.radius)
            self.enemies.append(enemy)
        if wave % 3 == 0:
            available = [p for p in points if all(math.hypot(e.x-p[0], e.y-p[1]) > 1 for e in self.enemies)]
            x, y = max(available or points, key=lambda p: math.hypot(p[0]-player.x, p[1]-player.y))
            self.enemies.append(self._make_enemy("ROOTKIT.EXE", x, y, wave))

    def _collect_dead(self, world):
        messages, survivors, children = [], [], []
        live_count = sum(e.alive for e in self.enemies)
        for enemy in self.enemies:
            if enemy.alive:
                survivors.append(enemy)
                continue
            self.kills += 1
            value = {"ILOVEYOU": 100, "WannaCry": 140, "Mydoom": 200, "ROOTKIT.EXE": 1500}[enemy.kind]
            self.score += value // 2 if enemy.generation else value
            if enemy.boss:
                messages.append("ROOTKIT.EXE eliminado. Acesso restaurado.")
            if enemy.kind == "WannaCry" and enemy.generation == 0:
               
                for side in (-1, 1):
                    if live_count + len(children) >= self.MAX_ENEMIES:
                        break
                    child = self._make_enemy("WannaCry", enemy.x, enemy.y, enemy.wave, generation=1)
                    world.move(child, side * .25, .12, child.radius)
                    children.append(child)
        self.enemies = survivors + children
        if children:
            messages.append("WannaCry replicou processos! Elimine as copias.")
        return messages

    def _launch(self, enemy, angle, *, speed=4.5, damage=9.0):
        if len(self.projectiles) < self.MAX_PROJECTILES:
            self.projectiles.append(Projectile(
                enemy.x, enemy.y, math.cos(angle), math.sin(angle),
                speed=speed, damage=damage, z=.52 if enemy.boss else .45, boss=enemy.boss,
            ))

    def _move_towards(self, enemy, player, world, dt):
        enemy.path_timer -= dt
        if enemy.path_timer <= 0:
            dx, dy = player.x-enemy.x, player.y-enemy.y
            distance = math.hypot(dx, dy)
            if world.line_of_sight(enemy.x, enemy.y, player.x, player.y):
                enemy.direction_x, enemy.direction_y = dx/max(distance, .001), dy/max(distance, .001)
            else:
                enemy.direction_x, enemy.direction_y = world.path_direction(enemy.x, enemy.y, player.x, player.y)
            enemy.path_timer = self.rng.uniform(.20, .38)
        world.move(enemy, enemy.direction_x * enemy.speed * dt, enemy.direction_y * enemy.speed * dt, enemy.radius)

    def _update_enemy(self, enemy, dt, player, world, wave):
        messages = []
        enemy.hurt = max(0.0, enemy.hurt - dt)
        enemy.attack_timer = max(0.0, enemy.attack_timer - dt)
        dx, dy = player.x-enemy.x, player.y-enemy.y
        distance = math.hypot(dx, dy)
        visible = world.line_of_sight(enemy.x, enemy.y, player.x, player.y)
        angle = math.atan2(dy, dx)
        if enemy.boss:
            if enemy.windup > 0:
                enemy.windup = max(0.0, enemy.windup - dt)
                if enemy.windup == 0:
                    for index in range(12):
                        self._launch(enemy, angle + index * math.tau / 12, speed=3.8, damage=12)
                    for offset in (-.10, 0, .10):
                        self._launch(enemy, angle + offset, speed=5.5, damage=11)
                    enemy.attack_timer = max(1.8, 3.2-wave*.035)
            elif enemy.attack_timer <= 0 and visible:
                enemy.windup = .80
                messages.append("ALERTA ROOTKIT: rajada em 0.8s! Mova-se!")
            elif distance > 3.2 or not visible:
                self._move_towards(enemy, player, world, dt)
            if distance < .85 and visible and enemy.attack_timer <= 0:
                if player.z < .65:
                    player.damage(20)
                enemy.attack_timer = 1.0
            return messages
        if enemy.kind == "Mydoom" and visible and distance < 12:
            if enemy.attack_timer <= 0:
                self._launch(enemy, angle, damage=9 + min(7, max(0, wave-1)*.5))
                enemy.attack_timer = max(1.0, 2.3-wave*.035)
            if distance < 3:
                world.move(enemy, -math.cos(angle)*enemy.speed*dt, -math.sin(angle)*enemy.speed*dt, enemy.radius)
            elif distance > 7:
                self._move_towards(enemy, player, world, dt)
            else:
                world.move(enemy, -math.sin(angle)*enemy.strafe_sign*dt*.30,
                           math.cos(angle)*enemy.strafe_sign*dt*.30, enemy.radius)
            return messages
        melee_range = enemy.radius + player.radius + .18
        if distance <= melee_range and visible:
            if enemy.attack_timer <= 0:
                if player.z < .60:
                    damage = 8 if enemy.kind == "ILOVEYOU" else 11
                    if enemy.generation:
                        damage = 5
                    player.damage(damage + min(6, max(0, wave-1)//3))
                enemy.attack_timer = .80 if enemy.kind == "ILOVEYOU" else 1.1
        else:
            self._move_towards(enemy, player, world, dt)
        return messages

    def _update_projectiles(self, dt, player, world):
        remaining = []
        for projectile in self.projectiles:
            projectile.ttl -= dt
            if not projectile.alive or projectile.ttl <= 0:
                continue
            travel = projectile.speed * dt
            limit = travel + projectile.radius
            wall = world.raycast(projectile.x, projectile.y, projectile.dx, projectile.dy,
                                 max_distance=limit + .001)[0]
            allowed = min(travel, max(0.0, wall-projectile.radius))
            end_x = projectile.x + projectile.dx*allowed
            end_y = projectile.y + projectile.dy*allowed
            sx, sy = end_x-projectile.x, end_y-projectile.y
            length_sq = sx*sx + sy*sy
            fraction = max(0.0, min(1.0, ((player.x-projectile.x)*sx + (player.y-projectile.y)*sy)/length_sq)) if length_sq else 0
            nearest_x, nearest_y = projectile.x+sx*fraction, projectile.y+sy*fraction
            hit_radius = projectile.radius + player.radius
            body_height = max(.30, (player.camera_height-player.z)*1.1)
            vertical_hit = player.z-projectile.radius <= projectile.z <= player.z+body_height+projectile.radius
            if (player.alive and vertical_hit
                    and math.hypot(player.x-nearest_x, player.y-nearest_y) <= hit_radius
                    and world.line_of_sight(nearest_x, nearest_y, player.x, player.y)):
                player.damage(projectile.damage)
                projectile.alive = False
                continue
            if wall <= limit:
                projectile.alive = False
                continue
            projectile.x, projectile.y = end_x, end_y
            remaining.append(projectile)
        self.projectiles = remaining

    def update(self, dt, player, world, wave):
        dt = max(0.0, min(float(dt), .25))
        messages = self._collect_dead(world)
        if not player.alive:
            return messages
        for enemy in self.enemies:
            if not player.alive:
                break
            messages.extend(self._update_enemy(enemy, dt, player, world, wave))
        self._update_projectiles(dt, player, world)
        return messages

