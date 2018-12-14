import math
import textwrap
import tdl
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


# http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python
def weighted_choice(weights):
    totals = []
    running_total = 0

    for w in weights:
        running_total += w
        totals.append(running_total)

    rnd = random.random() * running_total
    for i, total in enumerate(totals):
        if rnd < total:
            return i


def center_text(text, width):
    t = math.ceil(len(text) / 2.0)
    w = math.ceil(width / 2.0)
    return w - t


class Vector2(object):
    def __init__(self, x_or_tuple, maybe_y=None):
        if maybe_y is None and isinstance(x_or_tuple, tuple):
            self.x, self.y = x_or_tuple
        else:
            self.x = x_or_tuple
            self.y = maybe_y

    def copy(self):
        return Vector2(self.x, self.y)

    def distance(self, other):
        return math.sqrt((other.x - self.x) ** 2 + (other.y - self.y) ** 2)

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
        return Vector2(center_x, center_y)

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


class PopupWindow(object):
    """A popup window to display variable length text.

    The width of this window is fixed while the height is resized based on the length
    of the message to be displayed.
    """

    # IBM code page 437 symbols (based on a 16x16 grid):
    # 10, 13
    TOP_LEFT = 201
    # 12, 12
    TOP_RIGHT = 187
    # 9, 13
    BOTTOM_LEFT = 200
    # 13, 12
    BOTTOM_RIGHT = 188
    # 14, 13
    HLINE = 205
    # 11, 12
    VLINE = 186

    def __init__(self, width, height, max_width, max_height, fg, bg):
        self.width = width
        self.height = height
        self.max_width = max_width
        self.max_height = max_height
        self.console = tdl.Console(self.max_width, self.max_height)
        self.console.set_colors(fg=fg, bg=bg)

    @property
    def max_text_width(self):
        # 1 for the frame on each side + 1 padding
        return self.width - 4

    def draw(self, message):
        lines = textwrap.wrap(message, width=self.max_text_width)
        self.height = clamp(len(lines) + 4, 0, self.max_height)

        c = self.console
        c.clear()
        # draw the corners
        c.draw_char(0, 0, self.TOP_LEFT)
        c.draw_char(self.width-1, 0, self.TOP_RIGHT)
        c.draw_char(0, self.height-1, self.BOTTOM_LEFT)
        c.draw_char(self.width-1, self.height-1, self.BOTTOM_RIGHT)

        # draw the rest of the frame
        for x in range(1, self.width - 1):
            c.draw_char(x, 0, self.HLINE)
            c.draw_char(x, self.height - 1, self.HLINE)

        for y in range(1, self.height - 1):
            c.draw_char(0, y, self.VLINE)
            c.draw_char(self.width - 1, y, self.VLINE)

        # draw the message, one line at a time
        y = 2
        x = 2
        for line in lines:
            c.draw_str(x, y, line)
            y += 1
            if y >= self.height - 2:
                break

    def blit(self, surface, x, y):
        """Blit this popup onto another surface"""

        surface.blit(self.console, x, y, self.width, self.height, 0, 0)


class Camera(Rect):
    def __init__(self, width, height):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height

    def center_on(self, x, y):
        d = math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        print(d)
        print("x=%r, y=%r; xx=%r, yy=%r; self.x=%r, self.y=%r" % (
            x, y, x + self.x, y + self.y, self.x, self.y))
        if d >= 50:
            self.x = x - (self.width / 2)
            self.y = y - (self.height / 2)

    def __repr__(self):
        return "Camera(x=%d, y=%d, w=%d, h=%d)" % (self.x, self.y, self.width, self.height)
