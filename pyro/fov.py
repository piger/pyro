# http://www.roguebasin.com/index.php?title=PythonShadowcastingImplementation

multipliers = [
    (1, 0, 0, -1, -1, 0, 0, 1),
    (0, 1, -1, 0, 0, -1, 1, 0),
    (0, 1, 1, 0, 0, -1, -1, 0),
    (1, 0, 0, 1, -1, 0, 0, -1),
]
# which gives
# 1, 0, 0, 1 -> E-NE
# 0, 1, 1, 0 -> NE-N
# 0, -1, 1, 0 -> N-NW
# -1, 0, 0, 1 -> NW-W
# -1, 0, 0, -1 -> W-SW
# 0, -1, -1, 0 -> SW-S
# 0, 1, -1, 0 -> S-SE
# 1, 0, 0, -1 -> SE-E


class Fov:
    def __init__(self, radius=6):
        self.radius = radius
        self.mapdata = None
        self.width = 0
        self.height = 0
        self.fovmap = None
        self.los_cache = None

    def setup(self, mapdata):
        self.width = len(mapdata.cells)
        self.height = len(mapdata.cells[0])

        self.mapdata = [[False for y in range(self.height)] for x in range(self.width)]
        self.fovmap = [[False for y in range(self.height)] for x in range(self.width)]

        for x in range(self.width):
            for y in range(self.height):
                cell = mapdata.get_at(x, y)
                if not cell.blocking:
                    self.mapdata[x][y] = True

    def calculate(self, x, y):
        self.los_cache = set()
        self._reset_fovmap()
        row = 1
        start = 1.0
        end = 0.0
        for octant in range(8):
            self._cast_light(
                x,
                y,
                row,
                start,
                end,
                multipliers[0][octant],
                multipliers[1][octant],
                multipliers[2][octant],
                multipliers[3][octant],
            )
        return self.los_cache

    def _cast_light(self, start_x, start_y, row, start, end, xx, xy, yx, yy):
        if start < end:
            return

        radius_squared = self.radius * self.radius
        new_start = None

        # j is distance
        # dx and dy are deltas
        for j in range(row, self.radius + 1):
            dx, dy = -j - 1, -j
            blocked = False

            while dx <= 0:
                dx += 1
                x = start_x + dx * xx + dy * xy
                y = start_y + dx * yx + dy * yy

                l_slope = (dx - 0.5) / (dy + 0.5)
                r_slope = (dx + 0.5) / (dy - 0.5)

                if start < r_slope:
                    continue
                elif end > l_slope:
                    break
                else:
                    # light a square
                    if dx * dx + dy * dy < radius_squared:
                        self._light_cell(x, y)

                    if blocked:
                        if self._is_blocked(x, y):
                            new_start = r_slope
                            continue
                        else:
                            blocked = False
                            start = new_start
                    else:
                        if self._is_blocked(x, y) and j < self.radius:
                            blocked = True
                            self._cast_light(
                                start_x, start_y, j + 1, start, l_slope, xx, xy, yx, yy
                            )
                            new_start = r_slope
            if blocked:
                break

    def _is_blocked(self, x, y):
        return self.mapdata[x][y] is False

    def _reset_fovmap(self):
        for x in range(self.width):
            for y in range(self.height):
                self.fovmap[x][y] = False

    def _light_cell(self, x, y):
        self.fovmap[x][y] = True
        self.los_cache.add((x, y))
