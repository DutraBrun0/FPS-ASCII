"""Simulacao independente da janela: facilita testes e novos frontends."""
from collections import deque
from .maps import WorldMap
from .player import Player
from .weapons import WeaponSystem
from .enemies import EnemyDirector
from .waves import WaveManager


class Game:
    def __init__(self, seed=2001):
        self.world = WorldMap()
        self.player = Player(*self.world.spawn)
        self.weapons = WeaponSystem()
        self.director = EnemyDirector(seed=seed)
        self.waves = WaveManager()
        self.time = 0.0
        self.damage_flash = 0.0
        self.shots = 0
        self.messages = deque(maxlen=4)
        self.message("CONEXAO ESTABELECIDA // localhost:27015")
        self.message("Firewall offline. Elimine os processos infectados.")

    def message(self, text):
        self.messages.append((self.time, str(text)))

    def update(self, dt, controls, trigger=False, zoom=False):
        if not self.player.alive:
            return
        self.time += dt
        self.damage_flash = max(0.0, self.damage_flash - dt)
        before = self.player.health + self.player.armor
        self.weapons.update(dt)
        self.player.update(dt, controls, self.world)
        fired = trigger and self.weapons.fire(
            self.player, self.director.enemies, self.world, zoom=zoom
        )
        if fired:
            self.shots += 1
        for message in self.director.update(dt, self.player, self.world, self.waves.wave):
            self.message(message)
        if self.player.health + self.player.armor < before:
            self.damage_flash = 0.3
        if self.player.alive:
            for message in self.waves.update(
                dt, self.director, self.player, self.world, self.weapons
            ):
                self.message(message)
        return bool(fired)

