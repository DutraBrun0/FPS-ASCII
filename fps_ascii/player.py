from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .maps import WorldMap


@dataclass
class Player:
    x: float = 12.5
    y: float = 12.5
    angle: float = -math.pi / 2
    pitch: float = 0.0
    health: float = 100.0
    armor: float = 40.0
    z: float = 0.0
    stamina: float = 100.0
    radius: float = 0.22
    slide_timer: float = 0.0
    crouching: bool = False
    moving: bool = False
    bob_phase: float = 0.0
    sprinting: bool = False
    _vertical_velocity: float = field(default=0.0, repr=False)
    _crouch_held: bool = field(default=False, repr=False)
    _slide_direction: tuple[float, float] = field(default=(0.0, 0.0), repr=False)
    _slide_cooldown: float = field(default=0.0, repr=False)
    _fov: float = field(default=math.radians(70.0), repr=False)
    _stance_height: float = field(default=0.5, repr=False)

    @property
    def alive(self) -> bool:
        return self.health > 0

    @property
    def camera_height(self) -> float:
        return self._stance_height + self.z

    @property
    def fov(self) -> float:
        return self._fov

    def damage(self, amount: float) -> None:
        if amount <= 0 or not self.alive:
            return
        absorbed = min(self.armor, amount * 0.65)
        self.armor = max(0.0, self.armor - absorbed)
        self.health = max(0.0, self.health - (amount - absorbed))

    def heal(self, amount: float) -> None:
        if self.alive:
            self.health = min(100.0, self.health + max(0.0, amount))

    def update(self, dt: float, controls: dict, world: WorldMap) -> None:
    
        if dt <= 0:
            return
        if not self.alive:
            self.moving = self.sprinting = False
            return

        forward = max(-1.0, min(1.0, float(controls.get("forward", 0.0))))
        strafe = max(-1.0, min(1.0, float(controls.get("strafe", 0.0))))
        magnitude = math.hypot(forward, strafe)
        if magnitude > 1.0:
            forward /= magnitude
            strafe /= magnitude
        cos_a, sin_a = math.cos(self.angle), math.sin(self.angle)
        wish_x = cos_a * forward - sin_a * strafe
        wish_y = sin_a * forward + cos_a * strafe
        has_motion = magnitude > 1e-5
        crouch = bool(controls.get("crouch", False))
        grounded = self.z <= 1e-6 and self._vertical_velocity <= 0.0
        self._slide_cooldown = max(0.0, self._slide_cooldown - dt)

        if (
            crouch and not self._crouch_held and has_motion and grounded
            and self.stamina >= 20.0 and self._slide_cooldown <= 0.0
        ):
            length = math.hypot(wish_x, wish_y)
            self._slide_direction = (wish_x / length, wish_y / length)
            self.slide_timer = 0.65
            self._slide_cooldown = 1.0
            self.stamina -= 20.0
        self._crouch_held = crouch

        if controls.get("jump", False) and grounded and self.stamina >= 9.0:
            self._vertical_velocity = 3.5
            self.stamina -= 9.0
            self.slide_timer = 0.0
            grounded = False

        self.crouching = crouch or self.slide_timer > 0.0
        self.sprinting = bool(
            controls.get("run", False) and has_motion and not self.crouching
            and self.stamina > 1.0 and forward > 0.0
        )
        if self.slide_timer > 0:
          
            speed = 3.0 + 3.4 * (self.slide_timer / 0.65)
            move_x, move_y = self._slide_direction
            self.slide_timer = max(0.0, self.slide_timer - dt)
        else:
            speed = 1.55 if self.crouching else (4.6 if self.sprinting else 2.9)
            move_x, move_y = wish_x, wish_y

        old_x, old_y = self.x, self.y
        world.move(self, move_x * speed * dt, move_y * speed * dt, self.radius)
        travel = math.hypot(self.x - old_x, self.y - old_y)
        self.moving = travel > 1e-5
        if self.moving and grounded:
            self.bob_phase += travel * (8.5 if self.sprinting else 6.8)

        if self.sprinting and self.moving:
            self.stamina = max(0.0, self.stamina - 17.0 * dt)
        elif self.slide_timer <= 0.0 and grounded:
            self.stamina = min(100.0, self.stamina + 13.0 * dt)

     
        if self.z > 0.0 or self._vertical_velocity > 0.0:
            self._vertical_velocity -= 10.0 * dt
            self.z += self._vertical_velocity * dt
            if self.z <= 0.0:
                self.z = 0.0
                self._vertical_velocity = 0.0

        smooth = 1.0 - math.exp(-10.0 * dt)
        target_height = 0.29 if self.crouching else 0.5
        self._stance_height += (target_height - self._stance_height) * smooth
        target_fov = math.radians(77.0 if self.sprinting or self.slide_timer > 0 else 70.0)
        self._fov += (target_fov - self._fov) * smooth

