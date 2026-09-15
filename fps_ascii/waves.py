"""Progressao de ondas e recompensas entre confrontos.

EnemyDirector atualiza mortes e cria clones antes deste gerenciador,
para que os descendentes de WannaCry contem como inimigos ativos.
"""


class WaveManager:
    INITIAL_DELAY = 2.0
    INTERMISSION = 4.5
    HEALTH_REWARD = 25
    ARMOR_REWARD = 15

    def __init__(self):
        self.wave = 0
        self.countdown = self.INITIAL_DELAY
        self.banner = "CONECTANDO A ARENA..."
        self.banner_timer = self.INITIAL_DELAY
        self.in_progress = False

    def update(self, dt, director, player, world, weapons):
        if dt <= 0 or not player.alive:
            return []
        self.banner_timer = max(0.0, self.banner_timer - dt)
        if self.in_progress:
            if any(enemy.alive for enemy in director.enemies):
                return []
            # Limpar a onda tambem neutraliza os projeteis restantes.
            director.projectiles.clear()
            self.in_progress = False
            self.countdown = self.INTERMISSION
            player.heal(self.HEALTH_REWARD)
            player.armor = min(100, player.armor + self.ARMOR_REWARD)
            weapons.refill()
            self.banner = f"WAVE {self.wave:02d} CONCLUIDA // REDE LIMPA"
            self.banner_timer = self.INTERMISSION
            return [self.banner, "Suprimentos recebidos: vida, armadura e municao."]
        self.countdown = max(0.0, self.countdown - dt)
        if self.countdown > 0:
            return []
        self.wave += 1
        director.spawn_wave(self.wave, player, world)
        self.in_progress = True
        self.banner_timer = 3.0
        if self.wave % 3 == 0:
            self.banner = f"WAVE {self.wave:02d} // CHEFE DETECTADO"
            return [self.banner, "ALERTA: processo critico infectado. Procure cobertura!"]
        self.banner = f"WAVE {self.wave:02d} // PROCESSOS HOSTIS"
        return [self.banner]

