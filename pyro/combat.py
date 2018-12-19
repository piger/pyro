import random
from .utils import clamp


def roll_to_hit(accuracy, defense):
    to_hit = chance_to_hit(accuracy, defense)
    if random.randint(0, 99) <= to_hit:
        return True
    return False


def chance_to_hit(accuracy, defense):
    return clamp(accuracy * pow(0.987, defense), 0, 100)
