from dataclasses import dataclass
import math
import random


@dataclass(frozen=True)
class WeaponDefinition:
    name: str
    damage: float
    interval: float
    range: float
    spread: float
    pellets: int
    magazine: int
    reload_time: float
    automatic: bool
    sprite: tuple[str, ...]


DEFINITIONS = (
    WeaponDefinition("Pistol", 28, .28, 22, .010, 1, 18, 1.15, False, (
        "       .----.       ",
        "       | :: |       ",
        "   .===|====|===.   ",
        "   |   |____|   |   ",
        "   '===|::::|==='   ",
        "       |::::|      ",
        "      /|____|\\     ",
        "     /________\\    ",
    )),
    WeaponDefinition("Rifle", 19, .095, 28, .026, 1, 30, 1.7, True, (
        "         []         ",
        "        |::|        ",
        "        |::|        ",
        "    .===|==|===.    ",
        "   / [==|__|==] \\   ",
        "  | .---|::|---. |  ",
        "  | |___|::|___| |  ",
        "   \\____|__|____/   ",
        "      /______\\     ",
    )),
    WeaponDefinition("Shotgun", 13, .85, 8, .13, 8, 8, 2.2, False, (
        "     .--. .--.      ",
        "     |::| |::|      ",
        "     |::| |::|      ",
        "    /|==|=|==|\\     ",
        "   / |__|_|__| \\    ",
        "  | [#########] |   ",
        "   \\[#########]/    ",
        "     |:::::::|      ",
        "      \\_____/       ",
    )),
    WeaponDefinition("Sniper", 155, 1.45, 40, .032, 1, 5, 2.5, False, (
        "          ||         ",
        "          ||         ",
        "       .--||--.      ",
        "      / ( + )  \\     ",
        "      '---||---'     ",
        "      .===||===.     ",
        "     / [==||==] \\    ",
        "    |_____|_|____|   ",
        "       /____\\        ",
    )),
    WeaponDefinition("Sword", 65, .48, 1.35, .45, 1, 0, 0, False, (
        "             /|      ",
        "            /:|      ",
        "           /:/       ",
        "          /:/        ",
        "         /:/         ",
        "      __/:/__        ",
        "      \\=|=|=/        ",
        "        |#|          ",
        "        |_|          ",
    )),
)


@dataclass
class WeaponState:
    ammo: int
    reserve: int


class WeaponSystem:
    definitions = DEFINITIONS

    def __init__(self, seed=2001):
        self.states = [WeaponState(d.magazine, reserve)
                       for d, reserve in zip(self.definitions, (180, 90, 24, 15, 0))]
        self.index = 0
        self.reload_timer = self.cooldown = self.flash = self.recoil = self.hit_marker = 0.0
        self._reload_index = None
        self.rng = random.Random(seed)

    @property
    def current(self):
        return self.definitions[self.index]

    @property
    def ammo(self):
        return self.states[self.index].ammo

    @property
    def reserve(self):
        return self.states[self.index].reserve

    def select(self, index):
        if 0 <= index < len(self.definitions) and index != self.index:
            self.index = index
            self.reload_timer = 0.0
            self._reload_index = None
            self.flash = self.recoil = 0.0

    def cycle(self, delta):
        self.select((self.index + delta) % len(self.definitions))

    def reload(self):
        if (not self.current.magazine or self.reload_timer > 0
                or self.ammo >= self.current.magazine or self.reserve <= 0):
            return False
        self.reload_timer = self.current.reload_time
        self._reload_index = self.index
        return True

    def refill(self):
       
        for definition, state, supply, cap in zip(
                self.definitions, self.states, (54, 45, 12, 6, 0), (240, 180, 48, 30, 0)):
            state.ammo = definition.magazine
            state.reserve = min(cap, state.reserve + supply)
        self.reload_timer = 0.0
        self._reload_index = None

    def update(self, dt):
        dt = max(0.0, dt)
        for attr in ("cooldown", "flash", "hit_marker"):
            setattr(self, attr, max(0.0, getattr(self, attr) - dt))
        self.recoil = max(0.0, self.recoil - dt * 6)
        if self.reload_timer > 0:
            self.reload_timer = max(0.0, self.reload_timer - dt)
            if self.reload_timer == 0 and self._reload_index == self.index:
                state = self.states[self.index]
                transferred = min(self.current.magazine - state.ammo, state.reserve)
                state.ammo += transferred
                state.reserve -= transferred
                self._reload_index = None

    def fire(self, player, enemies, world, zoom=False):
        if (not player.alive or self.cooldown > 0 or self.reload_timer > 0
                or (self.current.magazine and self.ammo <= 0)):
            return False
        weapon = self.current
        if weapon.magazine:
            self.states[self.index].ammo -= 1
        self.cooldown = weapon.interval
        self.flash = .10 if self.index == 4 else .075
        self.recoil = 1.0
        self.hit_marker = 0.0
        if not weapon.magazine:
            self._melee(player, enemies, world)
            return True
        spread = .001 if self.index == 3 and zoom else weapon.spread
        for _ in range(weapon.pellets):
            angle = player.angle + self.rng.uniform(-spread, spread)
            pitch = player.pitch + self.rng.uniform(-spread * .5, spread * .5)
            dx, dy = math.cos(angle), math.sin(angle)
            wall, _, _, _ = world.raycast(player.x, player.y, dx, dy, weapon.range)
            nearest, distance = None, min(weapon.range, wall)
            for enemy in enemies:
                if not enemy.alive:
                    continue
                hit = self._intersection(player, enemy, dx, dy, pitch, distance)
                if hit is not None and hit < distance:
                    nearest, distance = enemy, hit
            if nearest is not None:
                falloff = max(.25, 1 - .65 * distance / weapon.range) if self.index == 2 else 1
                nearest.take_damage(weapon.damage * falloff)
                self.hit_marker = .14
        return True

    @staticmethod
    def _intersection(player, enemy, dx, dy, pitch, limit):
        
        ex, ey = enemy.x - player.x, enemy.y - player.y
        along = ex * dx + ey * dy
        sideways = ex * dy - ey * dx
        radius = enemy.radius
        discriminant = radius * radius - sideways * sideways
        if discriminant < 0:
            return None
        half = math.sqrt(discriminant)
        enter, leave = max(0.0, along - half), min(limit, along + half)
        if enter > leave:
            return None
        eye, slope = player.camera_height, math.tan(pitch)
        base = getattr(enemy, "z", 0.0)
        if abs(slope) < 1e-9:
            if not base <= eye <= base + enemy.height:
                return None
        else:
            low, high = sorted(((base - eye) / slope, (base + enemy.height - eye) / slope))
            enter, leave = max(enter, low), min(leave, high)
        return enter if enter <= leave else None

    def _melee(self, player, enemies, world):
        candidates = []
        for enemy in enemies:
            if not enemy.alive:
                continue
            dx, dy = enemy.x - player.x, enemy.y - player.y
            distance = math.hypot(dx, dy)
            offset = (math.atan2(dy, dx) - player.angle + math.pi) % math.tau - math.pi
            apparent_radius = math.asin(min(1, enemy.radius / max(distance, .001)))
            if distance - enemy.radius > self.current.range:
                continue
            if abs(offset) > self.current.spread + apparent_radius:
                continue
            height = player.camera_height + math.tan(player.pitch) * distance
            if not -.15 <= height <= enemy.height + .15:
                continue
            if world.line_of_sight(player.x, player.y, enemy.x, enemy.y):
                candidates.append((distance, enemy))
        if candidates:
            min(candidates, key=lambda item: item[0])[1].take_damage(self.current.damage)
            self.hit_marker = .14

