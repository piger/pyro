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
    red = int(color[0] * amount)
    green = int(color[1] * amount)
    blue = int(color[2] * amount)
    return tuple([clamp(x, 0, 255) for x in (red, green, blue)])
