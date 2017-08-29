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
