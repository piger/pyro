from tcod.random import Random

class TcodRandom(object):
    """Helper class to be able to use a tcod.random.Random generator globally"""

    def __init__(self):
        self.seed = 0
        self._rng = None

    def init(self, seed):
        self.seed = seed

    @property
    def rng(self):
        assert self.seed != 0
        if self._rng is None:
            self._rng = Random(1, self.seed)
        return self._rng.random_c

tcod_random = TcodRandom()


def clamp(num, min_value, max_value):
    """Limit a number between a minimum and a maximum value"""

    return max(min(max_value, num), min_value)


# https://stackoverflow.com/questions/6615002/given-an-rgb-value-how-do-i-create-a-tint-or-shade
def darken_color(color, amount=0.50):
    red = color[0] * amount
    green = color[1] * amount
    blue = color[2] * amount
    return tuple([clamp(int(x), 0, 255) for x in (red, green, blue)])


def lighten_color(color, amount=0.50):
    red = color[0] + (amount * (255 - color[0]))
    green = color[1] + (amount * (255 - color[1]))
    blue = color[2] + (amount * (255 - color[2]))
    return tuple([clamp(int(x), 0, 255) for x in (red, green, blue)])


class Vector2(object):
    def __init__(self, x_, y_):
        self.x = x_
        self.y = y_

    def copy(self):
        return Vector2(self.x, self.y)

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __repr__(self):
        return 'Vector2(%d, %d)' % (self.x, self.y)


# Example:
# move(player_pos + NORTH)
NORTH = Vector2(0, -1)
SOUTH = Vector2(0, 1)
EAST = Vector2(1, 0)
WEST = Vector2(-1, 0)
NORTH_EAST = Vector2(1, -1)
NORTH_WEST = Vector2(-1, -1)
SOUTH_EAST = Vector2(1, 1)
SOUTH_WEST = Vector2(-1, 1)


class Rect(object):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.endX = self.x + self.width
        self.endY = self.y + self.height

    def __eq__(self, other):
        return (self.x == other.x and self.y == other.y and self.width == other.width and
                self.height == other.height)

    @property
    def center(self):
        center_x = int((self.x + self.endX) / 2)
        center_y = int((self.y + self.endY) / 2)
        return (center_x, center_y)

    def intersect(self, other):
        return (self.x <= other.endX and self.endX >= other.x and
                self.y <= other.endY and self.endY >= other.y)

    def __repr__(self):
        return 'Rect(x=%d, y=%d, width=%d, height=%d)' % (self.x, self.y, self.width, self.height)
