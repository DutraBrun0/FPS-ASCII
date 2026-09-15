

from __future__ import annotations

import math


DENSITY = " .:-=+*#%@"
WALL_HEIGHT = 2.0

_TERMINAL = (
    "+----------------------+",
    "| LAN HOUSE // SECTOR 7 |",
    "| +------------------+ |",
    "| | C:\\> CONNECT_    | |",
    "| | [########----]   | |",
    "| | TCP/IP  100 MBPS | |",
    "| | WINDOWS 2000    | |",
    "| +------------------+ |",
    "|      [ POWER ]       |",
    "+----------------------+",
    "   ___/________\\___    ",
    "===/__/__/__/__/__/=====",
)
_SERVER = (
    "+----------------------+",
    "| SYSTEM / MAINFRAME   |",
    "+----------------------+",
    "| [o] ::::::::::: [01] |",
    "| [o] ::::::::::: [02] |",
    "+----------------------+",
    "| [o] ::::::::::: [03] |",
    "| [o] ::::::::::: [04] |",
    "+----------------------+",
    "| /!\\  RESTRICTED     |",
    "| ==================== |",
    "+----------------------+",
)


class Raycaster:
    

    def __init__(self):
        self.scene_top = 8
        self.scene_bottom = 58
        self.horizon = 33.0
        self.zbuffer: list[float] = []
        self._projection_x = 1.0
        self._projection_y = 1.0
        self._eye = .55

    def render(self, buffer, world, player, enemies, projectiles, time, zoom=False) -> None:
        cols, rows = buffer.cols, buffer.rows
        self.scene_top = min(8, max(0, rows // 4))
        self.scene_bottom = max(self.scene_top + 1, rows - 14)
        self.scene_bottom = min(rows, self.scene_bottom)
        center = (self.scene_top + self.scene_bottom) / 2
        fov = .45 if zoom else float(getattr(player, "fov", math.radians(76)))
        fov = max(.25, min(1.95, fov))
        plane_scale = math.tan(fov * .5)
        self._projection_x = cols / (2 * plane_scale)
        self._projection_y = self._projection_x * getattr(buffer, "cell_aspect", .615)
        self._eye = float(getattr(player, "camera_height", .55 + getattr(player, "z", 0)))
        if getattr(player, "moving", False):
            self._eye += math.sin(getattr(player, "bob_phase", 0) * 2) * .012
        self._eye = max(.12, min(WALL_HEIGHT - .08, self._eye))
        self.horizon = center + math.tan(float(getattr(player, "pitch", 0))) * self._projection_y
        direction_x, direction_y = math.cos(player.angle), math.sin(player.angle)
        plane_x, plane_y = -direction_y * plane_scale, direction_x * plane_scale
        ray_x = [direction_x + plane_x * (2 * (x + .5) / cols - 1) for x in range(cols)]
        ray_y = [direction_y + plane_y * (2 * (x + .5) / cols - 1) for x in range(cols)]

        self.zbuffer = [40.0] * cols
        wall_starts = [self.scene_top] * cols
        wall_ends = [self.scene_top] * cols
        for column in range(cols):
            depth, side, map_x, map_y = world.raycast(
                player.x, player.y, ray_x[column], ray_y[column], max_distance=40.0
            )
            depth = max(.03, float(depth))
            self.zbuffer[column] = depth
            wall_top = self.horizon - (WALL_HEIGHT - self._eye) * self._projection_y / depth
            wall_bottom = self.horizon + self._eye * self._projection_y / depth
            first = max(self.scene_top, int(math.floor(wall_top)))
            last = min(self.scene_bottom, int(math.ceil(wall_bottom)) + 1)
            wall_starts[column], wall_ends[column] = first, last
            if first >= last:
                continue
            hit_position = player.x + ray_x[column] * depth if side else player.y + ray_y[column] * depth
            u = hit_position - math.floor(hit_position)
            if (not side and ray_x[column] < 0) or (side and ray_y[column] > 0):
                u = 1.0 - u
            tile = "#"
            if 0 <= map_y < world.height and 0 <= map_x < world.width:
                tile = world.grid[map_y][map_x]
            # Light and texture setup is per column, not per glyph.
            shade = max(1, min(9, int(9.5 - depth * .48 - side * .9)))
            dense, sparse = DENSITY[shade], DENSITY[max(1, shade - 1)]
            base_color = "normal" if depth < 7 else "muted" if depth < 14 else "dim"
            if side and depth > 5:
                base_color = "muted" if depth < 13 else "dim"
            pattern = (_TERMINAL if tile == "C" else _SERVER) if tile in ("C", "S") and depth < 18 else None
            texture_x = int(u * 24)
            texture_x = min(23, texture_x)
            hash_x = int(u * 16) * 13 + map_x * 3 + map_y
            terminal_color = "bright" if int(time * 6 + map_x) % 19 else "dim"
            server_color = "accent" if int(time * 4 + map_y) % 3 else "danger"
            v_step = depth / (self._projection_y * WALL_HEIGHT)
            v_start = (WALL_HEIGHT - self._eye) / WALL_HEIGHT - (self.horizon - first - .5) * v_step
            for row in range(first, last):
                v = v_start + (row - first) * v_step
                if v < 0:
                    v = 0.0
                elif v >= 1:
                    v = .9999
                texture_hash = (hash_x + int(v * 24) * 11) % 7
                char, color = (sparse if texture_hash == 0 else dense), base_color
                if pattern:
                    line = pattern[int(v * 12)]
                    char = line[texture_x] if texture_x < len(line) else " "
                    if tile == "C" and .23 < v < .64 and .12 < u < .88:
                        color = terminal_color
                    elif tile == "S" and char == "o":
                        color = server_color
                elif depth < 15:
                    if u < .023 or u > .977:
                        char = "|"
                    elif abs(v - .10) < .009 or abs(v - .89) < .009:
                        char, color = "=", "muted"
                    elif int(v * 12) % 4 == 0 and texture_hash < 3:
                        char = "-"
                buffer._chars[row][column] = char
                buffer._colors[row][column] = color

        self._draw_floor_and_ceiling(buffer, player, ray_x, ray_y, time, wall_starts, wall_ends)

        # Painter ordering handles sprite/sprite overlap. Wall depth remains per
        # column, including for each label/projectile character, so no wall leaks.
        objects = []
        for prop in getattr(world, "props", ()):
            dx, dy = prop.x - player.x, prop.y - player.y
            depth = dx * direction_x + dy * direction_y
            if depth > .07:
                objects.append((depth, False, prop))
        for enemy in enemies:
            if not getattr(enemy, "alive", True):
                continue
            dx, dy = enemy.x - player.x, enemy.y - player.y
            depth = dx * direction_x + dy * direction_y
            if depth > .07:
                objects.append((depth, True, enemy))
        for depth, hostile, obj in sorted(objects, key=lambda item: item[0], reverse=True):
            self._draw_sprite(buffer, player, obj, depth, hostile, direction_x, direction_y, time)
        for projectile in projectiles:
            self._draw_projectile(buffer, player, projectile, direction_x, direction_y, time)

    def _draw_floor_and_ceiling(self, buffer, player, rays_x, rays_y, time, wall_starts, wall_ends) -> None:
        """World-aligned tile seams, cables and fluorescent ceiling strips."""
        for y in range(self.scene_top, self.scene_bottom):
            delta = y + .5 - self.horizon
            if abs(delta) < .05:
                continue
            floor = delta > 0
            height = self._eye if floor else WALL_HEIGHT - self._eye
            distance = abs(height * self._projection_y / delta)
            if distance > 32:
                continue
            chars, colors = buffer._chars[y], buffer._colors[y]
            for x in range(buffer.cols):
                if wall_starts[x] <= y < wall_ends[x]:
                    continue
                wx = player.x + rays_x[x] * distance
                wy = player.y + rays_y[x] * distance
                ix, iy = math.floor(wx), math.floor(wy)
                fx, fy = wx - ix, wy - iy
                grain = (int(wx * 13) * 17 + int(wy * 13) * 31) & 15
                char, color = " ", "dim"
                if floor:
                    if fx < .035 or fy < .035:
                        char = "+" if fx < .035 and fy < .035 else ("|" if fx < .035 else "-")
                        color = "muted" if distance < 5 else "dim"
                    elif iy % 5 == 2 and abs(fy - (.45 + .1 * math.sin(wx * 3))) < .055:
                        char, color = "~", "muted"
                    elif grain < (4 if distance < 7 else 2):
                        char = "." if (ix + iy) % 2 else ":"
                else:
                    if ix % 4 == 1 and iy % 4 == 1 and .12 < fx < .88 and .36 < fy < .62:
                        char, color = "=", "bright" if int(time * 8 + ix) % 23 else "muted"
                    elif fx < .025 or fy < .025:
                        char = "-"
                    elif ix % 5 == 0 and .46 < fx < .53:
                        char = "|"
                    elif grain == 0:
                        char = "."
                chars[x], colors[x] = char, color

    def _draw_sprite(self, buffer, player, obj, depth, hostile, direction_x, direction_y, time):
        sprite = getattr(obj, "sprite", ())
        if not sprite:
            return
        sprite_height = len(sprite)
        sprite_width = max(map(len, sprite))
        if not sprite_width:
            return
        world_height = float(getattr(obj, "height", 1.0))
        # Sprite art is authored for classic narrow terminal cells (aspect .55).
        world_width = world_height * sprite_width / sprite_height * .55
        projected_height = self._projection_y * world_height / depth
        projected_width = self._projection_x * world_width / depth
        lateral = -(obj.x - player.x) * direction_y + (obj.y - player.y) * direction_x
        center_x = buffer.cols / 2 + lateral * self._projection_x / depth
        base_z = float(getattr(obj, "z", 0))
        # Slow hovering is limited to malware; decorative furniture stays grounded.
        if hostile and "ILOVE" in str(getattr(obj, "kind", "")).upper():
            base_z += .025 * math.sin(time * 7 + obj.x)
        top = self.horizon + (self._eye - world_height - base_z) * self._projection_y / depth
        left = center_x - projected_width / 2
        first_x, last_x = max(0, int(math.floor(left))), min(buffer.cols, int(math.ceil(left + projected_width)))
        first_y = max(self.scene_top, int(math.floor(top)))
        last_y = min(self.scene_bottom, int(math.ceil(top + projected_height)))
        if first_x >= last_x or first_y >= last_y:
            return
        hurt = float(getattr(obj, "hurt", 0)) > 0
        kind = str(getattr(obj, "kind", "")).lower()
        color = ("white" if hurt else "danger") if hostile else ("normal" if depth < 8 else "muted")
        for x in range(first_x, last_x):
            if depth >= self.zbuffer[x] - .01:
                continue
            sx = min(sprite_width - 1, max(0, int((x + .5 - left) / max(.01, projected_width) * sprite_width)))
            for y in range(first_y, last_y):
                sy = min(sprite_height - 1, max(0, int((y + .5 - top) / max(.01, projected_height) * sprite_height)))
                line = sprite[sy]
                char = line[sx] if sx < len(line) else " "
                if char == " ":
                    continue
                glyph_color = color
                if not hostile and any(token in kind for token in ("crt", "computer", "monitor", "terminal")):
                    if char in "01>_#":
                        glyph_color = "bright" if int(time * 4 + obj.x) % 13 else "muted"
                if hostile and char in "@OXx*":
                    glyph_color = "white" if hurt else "accent"
                buffer.put(x, y, char, glyph_color)
        if hostile and depth < 12 and projected_height >= 4 and top >= self.scene_top + 1:
            name = str(getattr(getattr(obj, "kind", "MALWARE"), "value", getattr(obj, "kind", "MALWARE"))).upper()
            if getattr(obj, "boss", False):
                name = "!! " + name + " !!"
            label_x = int(center_x - len(name) / 2)
            label_y = int(top) - 1
            for offset, char in enumerate(name):
                x = label_x + offset
                if 0 <= x < buffer.cols and depth < self.zbuffer[x]:
                    buffer.put(x, label_y, char, "white" if hurt else "danger")

    def _draw_projectile(self, buffer, player, projectile, direction_x, direction_y, time):
        dx, dy = projectile.x - player.x, projectile.y - player.y
        depth = dx * direction_x + dy * direction_y
        if depth <= .06:
            return
        lateral = -dx * direction_y + dy * direction_x
        x = int(buffer.cols / 2 + lateral * self._projection_x / depth)
        z = float(getattr(projectile, "z", .5))
        y = int(self.horizon + (self._eye - z) * self._projection_y / depth)
        radius = 1 if depth < 4 else 0
        for offset in range(-radius, radius + 1):
            sx = x + offset
            if 0 <= sx < buffer.cols and self.scene_top <= y < self.scene_bottom and depth < self.zbuffer[sx]:
                buffer.put(sx, y, "*" if offset == 0 else "-", "accent" if int(time * 12) % 2 else "danger")
