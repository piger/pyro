from enum import Enum


class ComponentType(Enum):
    DUMB = 0
    COMBAT = 1
    HEALTH = 2
    POTION = 3
    INVENTORY = 4
    DOOR = 5
    MONSTER_AI = 6


class Component:
    NAME = 'component'
    kind = ComponentType.DUMB

    def config(self, values):
        raise NotImplementedError

    @property
    def name(self):
        return self.NAME
