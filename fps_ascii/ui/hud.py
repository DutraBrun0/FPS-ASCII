import math

LOGO = (
    " ______ ____   _____      _    ____   ____ ___ ___ ",
    "|  ____|  _ \\ / ____|    / \\  / ___| / ___|_ _|_ _|",
    "| |__  | |_) | (___     / _ \\ \\___ \\| |    | | | | ",
    "|  __| |  __/ \\___ \\   / ___ \\ ___) | |___ | | | | ",
    "|_|    |_|    |_____/  /_/   \\_\\____/ \\____|___|___|",
)
PALETTE_NAMES = {"green": "FOSFORO VERDE", "amber": "AMBAR", "ice": "GELO"}


def bar(value, maximum=100, size=18):
    count = max(0, min(size, round(value / maximum * size)))
    return "[" + "#" * count + "." * (size - count) + "]"


def panel(buffer, x, y, width, height, title=""):
    for row in range(y, y + height):
        buffer.text(x, row, " " * width)
    buffer.box(x, y, width, height, "dim")
    if title:
        buffer.text(x + 3, y, "[ " + title + " ]", "accent")


def minimap(buffer, game):
    world, player = game.world, game.player
    size = 13
    left, top = buffer.cols - size - 5, 10
    panel(buffer, left - 1, top - 1, size + 2, size + 2, "LAN")
    ox, oy = int(player.x) - size // 2, int(player.y) - size // 2
    for row in range(size):
        for col in range(size):
            x, y = ox + col, oy + row
            if 0 <= x < world.width and 0 <= y < world.height:
                wall = world.grid[y][x]
                buffer.put(left + col, top + row,
                           "#" if wall != "." and world.is_wall(x + .5, y + .5) else ".",
                           "dim")
    for enemy in game.director.enemies:
        x, y = int(enemy.x) - ox, int(enemy.y) - oy
        if enemy.alive and 0 <= x < size and 0 <= y < size:
            buffer.put(left + x, top + y, "B" if enemy.boss else "x", "danger")
    direction = (">", "v", "<", "^")[round(player.angle / (math.pi / 2)) % 4]
    buffer.put(left + size // 2, top + size // 2, direction, "bright")


def draw_hud(buffer, game, fps=60, palette="green", show_map=True, zoom=False, muted=False):
    p, weapons, waves = game.player, game.weapons, game.waves
    w, h = buffer.cols, buffer.rows
    buffer.text(2, 0, "=" * (w - 4), "dim")
    buffer.text(3, 1, "FPS ASCII", "bright")
    buffer.text(15, 1, "// LAN HOUSE 2001", "accent")
    buffer.text(w - 45, 1, f"LOCALHOST:27015  |  {fps:05.1f} FPS", "normal")
    buffer.text(3, 3, "C:\\LAN\\ARENA> quarantine.exe --survive", "normal")
    buffer.text(w - 45, 3, f"PALETA {PALETTE_NAMES[palette]}  |  {'MUDO' if muted else 'SOM ON'}", "normal")
    alive = sum(e.alive for e in game.director.enemies)
    buffer.text(3, 5, f"WAVE {waves.wave:02d}  /  PROCESSOS HOSTIS {alive:02d}", "accent")
    buffer.text(w // 2 - 11, 5, f"FRAGS {game.director.kills:04d}", "normal")
    buffer.text(w - 33, 5, f"SCORE {game.director.score:07d}", "bright")
    buffer.text(2, 7, "-" * (w - 4), "dim")

    cx, cy = w // 2, (8 + h - 14) // 2
    if zoom:
        
        for offset in range(-12, 13):
            if abs(offset) > 2:
                buffer.put(cx + offset, cy, "-", "dim")
        for offset in range(-8, 9):
            if abs(offset) > 1:
                buffer.put(cx, cy + offset, "|", "dim")
        buffer.text(cx + 14, cy, "ZOOM", "accent")
        buffer.text(cx - 12, cy + 10, "[ OPTIC // CONNECTED ]", "dim")
    if weapons.hit_marker > 0:
        for dx, dy in ((-2, -1), (2, 1), (-2, 1), (2, -1)):
            buffer.put(cx + dx, cy + dy, "x", "danger")
    else:
        buffer.text(cx - 2, cy, "- + -", "bright")

    bottom = h - 14
    if not zoom:
        sprite = weapons.current.sprite
        recoil = int(min(2, weapons.recoil * 4))
        sway = int(math.sin(p.bob_phase) * 2) if p.moving else 0
        sx = cx + 9 + sway
        sy = bottom - len(sprite) - 1 + recoil
        for i, line in enumerate(sprite):
            buffer.text(sx - len(line) // 2, sy + i, line,
                        "bright" if weapons.flash > 0 else "normal")
        if weapons.flash > 0:
            for i, line in enumerate((" \\ | / ", "-- * --", " / | \\ ")):
                buffer.text(sx - 3, sy - 2 + i, line, "accent")

    bosses = [e for e in game.director.enemies if e.alive and e.boss]
    if bosses:
        boss = bosses[0]
        buffer.center(9, f"!! {boss.kind} {bar(boss.hp, boss.max_hp, 28)} !!", "danger")
    elif getattr(waves, "banner_timer", 0) > 0:
        buffer.center(10, f">>> {waves.banner} <<<", "accent")
    if not waves.in_progress and p.alive:
        buffer.center(12, f"PROXIMA WAVE EM {waves.countdown:.1f}s", "normal")
    if show_map and not zoom:
        minimap(buffer, game)
    if game.damage_flash > 0:
        buffer.text(2, 8, "!" * (w - 4), "danger")
        for y in range(9, bottom):
            buffer.put(2, y, "!", "danger")
            buffer.put(w - 3, y, "!", "danger")
        buffer.center(bottom - 2, "[ ! INTEGRIDADE COMPROMETIDA ! ]", "danger")

    buffer.text(2, bottom, "=" * (w - 4), "dim")
    tab_width = (w - 6) // 5
    for index, definition in enumerate(weapons.definitions):
        label = f" {index + 1} {definition.name.upper()} "
        if index == weapons.index:
            label = "[" + label + "]"
        buffer.text(3 + index * tab_width, bottom + 1, label,
                    "bright" if index == weapons.index else "normal")
    hp_color = "danger" if p.health < 30 else "bright"
    buffer.text(3, bottom + 3, f"VIDA {p.health:03.0f} {bar(p.health, size=15)}", hp_color)
    buffer.text(w // 3, bottom + 3, f"ARMADURA {p.armor:03.0f} {bar(p.armor, size=12)}", "normal")
    ammo_text = "INFINITA" if weapons.current.magazine == 0 else f"{weapons.ammo:02d} / {weapons.reserve:03d}"
    buffer.text(2 * w // 3, bottom + 3, f"AMMO {ammo_text}", "bright")
    stance = "SLIDE" if p.slide_timer > 0 else ("AGACHADO" if p.crouching else ("NO AR" if p.z > .05 else "ONLINE"))
    buffer.text(3, bottom + 5, f"ENERGIA {bar(p.stamina, size=14)}  {stance}", "normal")
    if weapons.reload_timer > 0:
        buffer.text(2 * w // 3, bottom + 5, f"RECARREGANDO... {weapons.reload_timer:.1f}s", "accent")
    elif weapons.current.magazine and weapons.ammo == 0:
        buffer.text(2 * w // 3, bottom + 5, "[ R ] RECARREGAR", "danger")
    else:
        buffer.text(2 * w // 3, bottom + 5, f"{weapons.current.name.upper()} // READY", "normal")
    for i, (at, message) in enumerate(list(game.messages)[-2:]):
        if game.time - at < 8:
            buffer.text(3, bottom + 7 + i, "> " + message[:w - 9], "accent" if i else "dim")
    buffer.text(2, h - 4, "-" * (w - 4), "dim")
    buffer.center(h - 3, "WASD mover   MOUSE mirar/atirar   1-5 armas   R recarregar   SHIFT correr   CTRL slide   ESPACO pular", "normal")
    buffer.center(h - 2, "TAB mapa   F1 ajuda   F2 paleta   F3 CRT   F4 som   F5 qualidade   F11 tela cheia   ESC pausa", "normal")


def draw_menu(buffer, selected, mode, game, palette="green"):
    w, h = buffer.cols, buffer.rows
    width, height = min(108, w - 8), min(40, h - 12)
    x, y = (w - width) // 2, (h - height) // 2
    title = {"menu": "BOOT SEQUENCE / 2001", "paused": "PROCESSO SUSPENSO", "dead": "FATAL EXCEPTION"}.get(mode, "AJUDA")
    panel(buffer, x, y, width, height, title)
    for i, line in enumerate(LOGO):
        buffer.center(y + 3 + i, line, "bright")
    buffer.center(y + 9, "FIRST PERSON SHOOTER // CADA PIXEL, UM CARACTERE.", "accent")
    buffer.center(y + 11, "[ LAN HOUSE 2001 ]  [ SURVIVAL MODE ]  [ OFFLINE ]", "dim")
    if mode == "dead":
        buffer.center(y + 14, "CONNECTION LOST. O FIREWALL CAIU.", "danger")
        buffer.center(y + 16, f"WAVE {game.waves.wave:02d}   FRAGS {game.director.kills:04d}   SCORE {game.director.score:07d}", "bright")
        choices = ["RECONECTAR / NOVA PARTIDA", "VOLTAR AO TERMINAL", "SAIR"]
    elif mode == "paused":
        buffer.center(y + 14, "SESSAO EM PAUSA // MOUSE LIBERADO", "accent")
        choices = ["RETOMAR CONEXAO", "REINICIAR PARTIDA", "CONTROLES", "VOLTAR AO TERMINAL"]
    else:
        buffer.center(y + 14, "VIRUS DETECTADOS: ILOVEYOU / WANNACRY / MYDOOM", "normal")
        choices = ["INICIAR CONEXAO", "CONTROLES", "SAIR"]
    for i, label in enumerate(choices):
        prefix = ">> " if i == selected else "   "
        buffer.center(y + 19 + i * 2, prefix + label + (" <" if i == selected else "  "),
                      "bright" if i == selected else "normal")
    buffer.center(y + height - 8, "CHEFE A CADA 3 WAVES. SOBREVIVA. LIMPE A REDE.", "accent")
    buffer.center(y + height - 6, "W/S ou SETAS selecionar  |  ENTER conectar", "normal")
    buffer.center(y + height - 4, f"F2: {PALETTE_NAMES[palette]}   /   F3: scanlines   /   F4: som", "normal")
    buffer.center(y + height - 2, "C:\\LAN> aguardando comando_", "normal")
    return choices


def draw_help(buffer):
    width, height = 116, 42
    x, y = (buffer.cols - width) // 2, (buffer.rows - height) // 2
    panel(buffer, x, y, width, height, "MANUAL.TXT")
    buffer.center(y + 3, "FPS ASCII / CONTROLES E PROTOCOLOS", "bright")
    lines = [
        ("W A S D / setas cima, baixo", "Andar; A/D deslocam de lado"),
        ("Mouse / setas esquerda, direita", "Olhar; Page Up/Down olham verticalmente"),
        ("Mouse esquerdo / F", "Atirar (segure para Rifle automatico)"),
        ("Mouse direito / Q", "Mira telescopica da Sniper"),
        ("1 2 3 4 5 / roda do mouse", "Pistol, Rifle, Shotgun, Sniper, Sword"),
        ("R", "Recarregar; a recarga pode ser interrompida trocando"),
        ("Shift", "Correr; consome energia e amplia o FOV"),
        ("Espaco", "Pular; pode evitar projeteis baixos"),
        ("Ctrl / C", "Agachar; em movimento inicia um slide"),
        ("Tab / Esc / F1", "Mapa / pausar e liberar mouse / ajuda"),
        ("F2 / F3 / F4 / F5 / F11", "Paleta / CRT / som / qualidade / tela cheia"),
        ("- / =", "Reduzir / aumentar sensibilidade do mouse"),
    ]
    for i, (key, description) in enumerate(lines):
        buffer.text(x + 4, y + 6 + i * 2, key, "accent")
        buffer.text(x + 48, y + 6 + i * 2, description, "normal")
    buffer.text(x + 4, y + 32, "ILOVEYOU: veloz.  WANNACRY: divide-se.  MYDOOM: ataques a distancia.", "normal")
    buffer.text(x + 4, y + 34, "Chefes anunciam ataques. Use os corredores e os PCs como cobertura.", "normal")
    buffer.text(x + 4, y + 36, "Entre ondas: recuperacao e municao. Sword funciona sem balas.", "normal")
    buffer.center(y + 39, "[ ENTER / ESC / F1 ] VOLTAR", "bright")


