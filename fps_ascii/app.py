"""Janela, entrada e loop fixo de 120 Hz; renderizacao limitada a 60 FPS."""
import argparse
import math
import os
from pathlib import Path

import pygame

from .audio import Audio
from .engine.buffer import AsciiBuffer
from .engine.raycaster import Raycaster
from .game import Game
from .ui.hud import draw_help, draw_hud, draw_menu

QUALITY = {"low": (128, 48), "normal": (144, 54), "high": (160, 60)}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="FPS ASCII / LAN HOUSE 2001")
    parser.add_argument("--size", default="1280x800", help="Tamanho da janela, ex.: 1280x800")
    parser.add_argument("--palette", choices=("green", "amber", "ice"), default="green")
    parser.add_argument("--quality", choices=tuple(QUALITY), default="normal", help="Nivel de detalhe ASCII")
    parser.add_argument("--no-audio", action="store_true", help="Desativar audio sintetizado")
    parser.add_argument("--headless", action="store_true", help="SDL virtual para verificacao automatizada")
    parser.add_argument("--frames", type=int, default=0, help="Encerrar apos N frames (0: ilimitado)")
    parser.add_argument("--demo", action="store_true", help="Demonstracao automatica dos controles")
    parser.add_argument("--screenshot", type=Path, help="Salvar o ultimo frame em PNG")
    args = parser.parse_args(argv)
    try:
        args.size = tuple(int(n) for n in args.size.lower().split("x"))
        if len(args.size) != 2 or args.size[0] < 800 or args.size[1] < 600:
            raise ValueError
    except ValueError:
        parser.error("--size precisa ser LARGURAxALTURA, com minimo 800x600")
    if args.frames < 0:
        parser.error("--frames nao pode ser negativo")
    if args.headless and not args.frames:
        args.frames = 180
    return args


class Application:
    def __init__(self, args):
        self.args = args
        if args.headless:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            os.environ["SDL_AUDIODRIVER"] = "dummy"
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_caption("FPS ASCII // LAN HOUSE 2001")
        self.windowed_size = args.size
        self.screen = pygame.display.set_mode(args.size, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.quality = args.quality
        self.buffer = AsciiBuffer(*QUALITY[self.quality])
        self.raycaster = Raycaster()
        self.audio = Audio(not args.no_audio)
        self.palette = args.palette
        self.scanlines = True
        self.show_map = True
        self.fullscreen = False
        self.sensitivity = .0024
        self.game = Game()
        self.state = "menu"
        self.help_return = "menu"
        self.selected = 0
        self.running = True
        self.jump_pending = False
        self.shot_pending = False
        self.zoom = False
        self.accumulator = 0.0
        self.frame = 0
        self.render_time = 0.0
        if args.demo:
            self.start()

    def capture(self, active):
        if self.args.headless:
            return
        pygame.event.set_grab(active)
        pygame.mouse.set_visible(not active)
        pygame.mouse.get_rel()

    def transition(self, state):
        self.state = state
        self.selected = 0
        self.jump_pending = self.shot_pending = False
        self.zoom = False
        self.accumulator = 0.0
        self.capture(state == "playing")

    def start(self):
        self.game = Game()
        self.transition("playing")

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self.capture(self.state == "playing")

    def activate(self):
        if self.state == "menu":
            if self.selected == 0:
                self.start()
            elif self.selected == 1:
                self.help_return = "menu"
                self.transition("help")
            else:
                self.running = False
        elif self.state == "paused":
            if self.selected == 0:
                self.transition("playing")
            elif self.selected == 1:
                self.start()
            elif self.selected == 2:
                self.help_return = "paused"
                self.transition("help")
            else:
                self.transition("menu")
        elif self.state == "dead":
            if self.selected == 0:
                self.start()
            elif self.selected == 1:
                self.transition("menu")
            else:
                self.running = False

    def handle_key(self, key):
        if key == pygame.K_F2:
            palettes = ("green", "amber", "ice")
            self.palette = palettes[(palettes.index(self.palette) + 1) % len(palettes)]
            return
        if key == pygame.K_F3:
            self.scanlines = not self.scanlines
            return
        if key == pygame.K_F4:
            if not self.audio.sounds:
                self.audio = Audio(True)
            else:
                self.audio.enabled = not self.audio.enabled
            return
        if key == pygame.K_F5:
            levels = tuple(QUALITY)
            self.quality = levels[(levels.index(self.quality) + 1) % len(levels)]
            self.buffer.resize(*QUALITY[self.quality])
            label = {"low": "LEVE", "normal": "PADRAO", "high": "DETALHADA"}[self.quality]
            self.game.message(f"Qualidade: {label}")
            return
        if key == pygame.K_F11:
            self.toggle_fullscreen()
            return
        if self.state == "help":
            if key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_F1):
                self.transition(self.help_return)
            return
        if key == pygame.K_F1:
            self.help_return = "paused" if self.state == "playing" else self.state
            self.transition("help")
            return
        if self.state != "playing":
            if key == pygame.K_ESCAPE:
                if self.state == "paused":
                    self.transition("playing")
                elif self.state == "dead":
                    self.transition("menu")
                else:
                    self.running = False
            elif key in (pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN):
                delta = 1 if key in (pygame.K_s, pygame.K_DOWN) else -1
                self.selected = (self.selected + delta) % (4 if self.state == "paused" else 3)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.activate()
            return
        if key == pygame.K_ESCAPE:
            self.transition("paused")
        elif key == pygame.K_TAB:
            self.show_map = not self.show_map
        elif key == pygame.K_SPACE:
            self.jump_pending = True
        elif key == pygame.K_f:
            self.shot_pending = True
        elif pygame.K_1 <= key <= pygame.K_5:
            self.game.weapons.select(key - pygame.K_1)
        elif key == pygame.K_r:
            self.game.weapons.reload()
        elif key in (pygame.K_MINUS, pygame.K_EQUALS):
            multiplier = 1.15 if key == pygame.K_EQUALS else 1 / 1.15
            self.sensitivity = max(.0005, min(.009, self.sensitivity * multiplier))
            self.game.message(f"Sensibilidade: {self.sensitivity * 1000:.2f}")

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.WINDOWFOCUSLOST and self.state == "playing" and not self.args.headless:
                self.transition("paused")
            elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                size = max(800, event.w), max(600, event.h)
                self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
                self.windowed_size = size
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)
            elif event.type == pygame.MOUSEWHEEL and self.state == "playing":
                self.game.weapons.cycle(-event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN and self.state == "playing":
                if event.button == 1:
                    self.shot_pending = True
            elif event.type == pygame.MOUSEMOTION and self.state == "playing":
                factor = self.sensitivity * (.42 if self.zoom else 1)
                self.game.player.angle = (self.game.player.angle + event.rel[0] * factor) % math.tau
                self.game.player.pitch = max(-.65, min(.65, self.game.player.pitch - event.rel[1] * factor))

    def controls(self, dt):
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()
        player, weapons = self.game.player, self.game.weapons
        player.angle = (player.angle + (int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])) * dt * 1.8) % math.tau
        player.pitch = max(-.65, min(.65, player.pitch + (int(keys[pygame.K_PAGEUP]) - int(keys[pygame.K_PAGEDOWN])) * dt))
        self.zoom = weapons.index == 3 and bool(mouse[2] or keys[pygame.K_q])
        controls = {
            "forward": int(keys[pygame.K_w] or keys[pygame.K_UP]) - int(keys[pygame.K_s] or keys[pygame.K_DOWN]),
            "strafe": int(keys[pygame.K_d]) - int(keys[pygame.K_a]),
            "run": bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]),
            "crouch": bool(keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL] or keys[pygame.K_c]),
            "jump": self.jump_pending,
        }
        trigger = self.shot_pending or (weapons.current.automatic and bool(mouse[0] or keys[pygame.K_f]))
        if self.args.demo:
            targets = [enemy for enemy in self.game.director.enemies if enemy.alive]
            controls.update(forward=.35 if not targets else 0, strafe=0, run=False)
            if targets:
                world = self.game.world
                visible = [e for e in targets if world.line_of_sight(player.x, player.y, e.x, e.y)]
                target = min(visible or targets, key=lambda e: math.hypot(e.x-player.x, e.y-player.y))
                distance = math.hypot(target.x-player.x, target.y-player.y)
                if visible:
                    player.angle = math.atan2(target.y-player.y, target.x-player.x)
                    trigger = distance <= weapons.current.range
                    controls["forward"] = -.35 if distance < 2 else (.4 if distance > 6 else 0)
                else:
                    dx, dy = world.path_direction(player.x, player.y, target.x, target.y)
                    player.angle = math.atan2(dy, dx)
                    controls["forward"] = .65
                    trigger = False
                player.pitch = 0
                if weapons.ammo == 0:
                    weapons.reload()
            player.health = 100
        return controls, trigger

    def update(self, dt):
        if self.state != "playing":
            self.accumulator = 0
            return
        self.accumulator += dt
        step = 1 / 120
        while self.accumulator >= step and self.state == "playing":
            controls, trigger = self.controls(step)
            previous_wave = self.game.waves.wave
            previous_damage = self.game.damage_flash
            fired = self.game.update(step, controls, trigger, self.zoom)
            self.jump_pending = self.shot_pending = False
            if fired:
                self.audio.play(self.game.weapons.current.name)
                if self.game.weapons.hit_marker > 0:
                    self.audio.play("hit")
            if self.game.damage_flash > previous_damage:
                self.audio.play("hurt")
            if self.game.waves.wave > previous_wave:
                self.audio.play("wave")
            self.accumulator -= step
            if not self.game.player.alive:
                self.transition("dead")

    def render(self):
        self.buffer.clear()
        self.raycaster.render(self.buffer, self.game.world, self.game.player,
                              self.game.director.enemies, self.game.director.projectiles,
                              self.game.time if self.state != "menu" else self.render_time,
                              zoom=self.zoom)
        draw_hud(self.buffer, self.game, self.clock.get_fps(), self.palette,
                 self.show_map, self.zoom, not self.audio.enabled)
        if self.state == "help":
            draw_help(self.buffer)
        elif self.state != "playing":
            draw_menu(self.buffer, self.selected, self.state, self.game, self.palette)
        self.buffer.render(self.screen, palette=self.palette, scanlines=self.scanlines)
        pygame.display.flip()

    def run(self):
        try:
            while self.running:
                elapsed = self.clock.tick(60) / 1000
                dt = 1 / 60 if self.args.headless else min(.1, elapsed)
                self.render_time += dt
                self.events()
                if not self.running:
                    break
                self.update(dt)
                self.render()
                self.frame += 1
                if self.args.frames and self.frame >= self.args.frames:
                    break
            if self.args.screenshot:
                self.args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                pygame.image.save(self.screen, str(self.args.screenshot))
            if self.args.headless:
                print(f"FPS ASCII OK: {self.frame} frames; wave={self.game.waves.wave}; "
                      f"inimigos={len(self.game.director.enemies)}; "
                      f"frags={self.game.director.kills}; fps={self.clock.get_fps():.1f}")
            return 0
        finally:
            self.capture(False)
            pygame.quit()


def main(argv=None):
    return Application(parse_args(argv)).run()

