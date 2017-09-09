import random
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

    @classmethod
    def random(cls, min_x, max_x, min_y, max_y):
        return cls(random.randint(min_x, max_x),
                   random.randint(min_y, max_y))

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __mul__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return Vector2(other * self.x, other * self.y)
        else:
            return Vector2(self.x * other.x, self.y * other.y)

    def __eq__(self, other):
        if isinstance(other, Vector2):
            return self.x == other.x and self.y == other.y
        elif other is None:
            return False
        else:
            raise NotImplementedError("eq not impelemented for type %s" % type(other))

    def __repr__(self):
        return 'Vector2(%d, %d)' % (self.x, self.y)


class Direction(object):
    NORTH = Vector2(0, -1)
    SOUTH = Vector2(0, 1)
    EAST = Vector2(1, 0)
    WEST = Vector2(-1, 0)
    NORTH_EAST = Vector2(1, -1)
    NORTH_WEST = Vector2(-1, -1)
    SOUTH_EAST = Vector2(1, 1)
    SOUTH_WEST = Vector2(-1, 1)

    @classmethod
    def all(cls):
        return (cls.NORTH_WEST, cls.NORTH, cls.NORTH_EAST,
                cls.WEST, cls.EAST,
                cls.SOUTH_WEST, cls.SOUTH, cls.SOUTH_EAST)

    @classmethod
    def cardinal(cls):
        return (cls.NORTH, cls.EAST, cls.SOUTH, cls.WEST)

    @classmethod
    def intercardinal(cls):
        return (cls.NORTH_EAST, cls.SOUTH_EAST, cls.SOUTH_WEST, cls.NORTH_WEST)


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

    def contains(self, other):
        if other.x < self.x:
            return False
        if other.x > self.endX:
            return False
        if other.y < self.y:
            return False
        if other.y > self.endY:
            return False
        return True

    def inflate(self, distance):
        return Rect(self.x - distance, self.y - distance,
                    self.width + (distance * 2), self.height + (distance * 2))

    def collidepoint(self, x, y):
        return x >= self.x and x <= self.endX and y >= self.y and y <= self.endY

    def __repr__(self):
        return 'Rect(x=%d, y=%d, width=%d, height=%d)' % (self.x, self.y, self.width, self.height)
