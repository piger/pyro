from enum import Enum


LAYER_FLOOR = 0
LAYER_ITEMS = 1
LAYER_CREATURES = 2


VOID = 0
WALL = 1
FLOOR = 2
ROOM = 3
CORRIDOR = 4

BLOCKING = (WALL, VOID)
WALKABLE = (ROOM, FLOOR, CORRIDOR)


class PotionType(Enum):
    HEALTH = 0
    POISON = 1
    CONFUSION = 2


class ComponentType(Enum):
    DUMB = 0
    COMBAT = 1
    HEALTH = 2
    POTION = 3
    INVENTORY = 4
    COMBAT = 5
    DOOR = 6
    MONSTER_AI = 7


class EntityType(Enum):
    PLAYER = 0
    MONSTER = 1
    POTION = 2
    SCROLL = 3
    WEAPON = 4
    TRAP = 5
    DOOR = 6
    NPC = 7
