from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Prop:
    x: float
    y: float
    kind: str
    sprite: tuple[str, ...]
    height: float = 0.9


class WorldMap:
    def __init__(self) -> None:
        size = 25
        cells = [["." for _ in range(size)] for _ in range(size)]
        for i in range(size):
            cells[0][i] = cells[-1][i] = "#"
            cells[i][0] = cells[i][-1] = "#"

      
        for x in (8, 16):
            for y in range(2, 22):
                if y not in (5, 6, 11, 12, 18, 19):
                    cells[y][x] = "#"
        for y in (8, 16):
            for x in range(2, 23):
                if x not in (4, 5, 11, 12, 19, 20):
                    cells[y][x] = "#"

      
        for start_x in (2, 10, 18):
            for y in (3, 5, 19, 21):
                for x in range(start_x, start_x + 4):
                    cells[y][x] = "C"
        for start_x in (2, 18):
            for y in (11, 13):
                for x in range(start_x, start_x + 4):
                    cells[y][x] = "C"
        for y in (10, 11, 13, 14):
            cells[y][22] = "S"

        self.grid = tuple("".join(row) for row in cells)
        self.width = self.height = size
        self.spawn = (12.5, 12.5, -math.pi / 2)
        self._path_target: tuple[int, int] | None = None
        self._path_distances: dict[tuple[int, int], int] = {}

        crt = (
            " .--------. ",
            " | C:>_   | ",
            " | [2000] | ",
            " '--------' ",
            "    |__|    ",
            "  /______\\  ",
        )
        chair = ("  .----.  ", "  |::::|  ", "  '----'  ", "  /____\\  ", "    ||    ", "  _/  \\_  ")
        server = (" .------. ", " |[::] *| ", " |[::] o| ", " |[::] *| ", " |[::] o| ", " '------' ")
        self.props = [
            Prop(3.5, 2.5, "crt", crt, 0.9),
            Prop(11.5, 2.5, "crt", crt, 0.9),
            Prop(19.5, 2.5, "crt", crt, 0.9),
            Prop(3.5, 10.5, "crt", crt, 0.9),
            Prop(19.5, 10.5, "crt", crt, 0.9),
            Prop(3.5, 18.5, "crt", crt, 0.9),
            Prop(11.5, 18.5, "crt", crt, 0.9),
            Prop(19.5, 18.5, "crt", crt, 0.9),
            Prop(6.4, 3.6, "chair", chair, 0.72),
            Prop(14.4, 3.6, "chair", chair, 0.72),
            Prop(6.4, 19.6, "chair", chair, 0.72),
            Prop(21.5, 14.5, "server", server, 1.15),
            Prop(12.5, 23.4, "sign", ("+---------------+", "| LAN HOUSE.EXE |", "|  OPEN 24/7    |", "+---------------+"), 0.85),
        ]
    
        self.spawn_points = [
            (x + 0.5, y + 0.5)
            for y in range(1, size - 1, 2)
            for x in range(1, size - 1, 2)
            if not self.collides(x + 0.5, y + 0.5, 0.42)
            and math.hypot(x + 0.5 - self.spawn[0], y + 0.5 - self.spawn[1]) >= 6.0
        ]

    def is_wall(self, x: float, y: float) -> bool:
        if not math.isfinite(x) or not math.isfinite(y):
            return True
        cx, cy = math.floor(x), math.floor(y)
        return (
            cx < 0 or cy < 0 or cx >= self.width or cy >= self.height
            or self.grid[cy][cx] not in ". "
        )

    def collides(self, x: float, y: float, radius: float = 0.22) -> bool:
       
        if not math.isfinite(x) or not math.isfinite(y):
            return True
        radius = max(0.0, radius)
        if radius == 0:
            return self.is_wall(x, y)
        for cy in range(math.floor(y - radius), math.floor(y + radius) + 1):
            for cx in range(math.floor(x - radius), math.floor(x + radius) + 1):
                if self.is_wall(cx, cy):
                    nearest_x = max(cx, min(x, cx + 1))
                    nearest_y = max(cy, min(y, cy + 1))
                    if (x - nearest_x) ** 2 + (y - nearest_y) ** 2 < radius ** 2:
                        return True
        return False

    def move(self, entity: object, dx: float, dy: float, radius: float = 0.22) -> None:
      
        steps = max(1, math.ceil(max(abs(dx), abs(dy)) / max(radius * 0.6, 0.04)))
        step_x, step_y = dx / steps, dy / steps
        for _ in range(steps):
            if not self.collides(entity.x + step_x, entity.y, radius):
                entity.x += step_x
            if not self.collides(entity.x, entity.y + step_y, radius):
                entity.y += step_y

    def raycast(
        self, ox: float, oy: float, dx: float, dy: float, max_distance: float = 40.0
    ) -> tuple[float, int, int, int]:
      
        cx, cy = math.floor(ox), math.floor(oy)
        if self.is_wall(ox, oy):
            return 0.0, 0, cx, cy
        if abs(dx) + abs(dy) < 1e-12:
            return max_distance, 0, cx, cy
        delta_x = abs(1.0 / dx) if dx else math.inf
        delta_y = abs(1.0 / dy) if dy else math.inf
        step_x, step_y = (-1 if dx < 0 else 1), (-1 if dy < 0 else 1)
        side_x = ((ox - cx) if dx < 0 else (cx + 1 - ox)) * delta_x
        side_y = ((oy - cy) if dy < 0 else (cy + 1 - oy)) * delta_y
        while True:
            if side_x < side_y:
                distance, side = side_x, 0
                side_x += delta_x
                cx += step_x
            else:
                distance, side = side_y, 1
                side_y += delta_y
                cy += step_y
            if distance > max_distance:
                return max_distance, side, cx, cy
            if self.is_wall(cx, cy):
                return distance, side, cx, cy

    def line_of_sight(self, ax: float, ay: float, bx: float, by: float) -> bool:
        if self.is_wall(ax, ay) or self.is_wall(bx, by):
            return False
        if math.hypot(bx - ax, by - ay) < 1e-8:
            return True
        distance, _, _, _ = self.raycast(ax, ay, bx - ax, by - ay, 1.0)
        return distance >= 1.0 - 1e-8

    def path_direction(self, x: float, y: float, tx: float, ty: float) -> tuple[float, float]:
       
        target = (math.floor(tx), math.floor(ty))
        start = (math.floor(x), math.floor(y))
        if self.is_wall(*target) or self.is_wall(*start):
            return 0.0, 0.0
        if target != self._path_target:
            self._path_target = target
            self._path_distances = {target: 0}
            frontier = deque([target])
            while frontier:
                cx, cy = frontier.popleft()
                for neighbor in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if neighbor not in self._path_distances and not self.is_wall(*neighbor):
                        self._path_distances[neighbor] = self._path_distances[(cx, cy)] + 1
                        frontier.append(neighbor)
        if start == target:
            vx, vy = tx - x, ty - y
        else:
            cx, cy = start
            distance = self._path_distances.get(start, math.inf)
            candidates = [
                cell for cell in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1))
                if self._path_distances.get(cell, math.inf) < distance
            ]
            if not candidates:
                return 0.0, 0.0
         
            nx, ny = min(candidates, key=lambda cell: (cell[0] + 0.5 - tx) ** 2 + (cell[1] + 0.5 - ty) ** 2)
            vx, vy = nx + 0.5 - x, ny + 0.5 - y
        length = math.hypot(vx, vy)
        return (vx / length, vy / length) if length > 1e-8 else (0.0, 0.0)

