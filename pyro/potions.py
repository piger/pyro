import random
from . import PotionType


POTION_AVATAR = 173

POTION_COLOR = [72, 209, 204]

POTION_COLORS = [
    "blue",
    "yellow",
    "cyan",
    "black",
    "white",
    "red",
    "green",
    "magenta",
    "brown",
    "orange",
]

POTIONS_MAPPING = {}


class PotionSystem:
    def __init__(self):
        self.potions_colors = {}
        self.potions_quaff = {}
        self.potions_throw = {}
        self.discovered_potions = {}

    def setup(self):
        colors = POTION_COLORS[:]
        random.shuffle(colors)

        for potion_type, quaff_fn, throw_fn in POTIONS:
            color = colors.pop()
            self.potions_colors[potion_type] = color
            self.potions_quaff[potion_type] = quaff_fn
            self.potions_throw[potion_type] = throw_fn
            self.discovered_potions[potion_type] = False

    def get_name_for_potion(self, potion):
        pc = potion.get_component("potion")
        if self.discovered_potions[pc.potion_type]:
            return pc.display_name
        return self.potions_colors[pc.potion_type]

    def set_discovered(self, potion):
        pc = potion.get_component("potion")
        self.discovered_potions[pc.potion_type] = True

    def is_discovered(self, potion):
        pc = potion.get_component("potion")
        return self.discovered_potions[pc.potion_type]


def quaff_health():
    pass


def throw_health():
    pass


def quaff_poison():
    pass


def throw_poison():
    pass


def quaff_confusion():
    pass


def throw_confusion():
    pass


POTIONS = [
    (PotionType.HEALTH, quaff_health, throw_health),
    (PotionType.POISON, quaff_poison, throw_poison),
]
