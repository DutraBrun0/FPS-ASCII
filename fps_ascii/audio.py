from array import array
import math
import random


class Audio:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.sounds = {}
        if not enabled:
            return
        import pygame
        self.pygame = pygame
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            if pygame.mixer.get_init() != (22050, -16, 1):
                pygame.mixer.quit()
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            specs = {"pistol": (130, .12), "rifle": (170, .07), "shotgun": (65, .26),
                     "sniper": (80, .35), "sword": (480, .14), "hurt": (100, .13),
                     "hit": (900, .04), "wave": (650, .25)}
            rng = random.Random(2001)
            for name, (frequency, duration) in specs.items():
                values = array("h")
                for i in range(int(22050 * duration)):
                    t = i / 22050
                    envelope = (1 - t / duration) ** 2
                    tone = math.sin(2 * math.pi * frequency * (t - t*t))
                    noise = rng.uniform(-1, 1) if name not in ("wave", "hit") else 0
                    values.append(int((tone * .45 + noise * .55) * envelope * 6500))
                self.sounds[name] = pygame.mixer.Sound(buffer=values)
        except pygame.error:
            self.enabled = False

    def play(self, name):
        if self.enabled and name.lower() in self.sounds:
            self.sounds[name.lower()].play()

