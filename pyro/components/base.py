import re
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

    @classmethod
    def name(cls):
        words = re.findall(r'[A-Z][^A-Z]*', cls.__name__)
        return "_".join([word.lower() for word in words])

    @classmethod
    def class_name(cls):
        return cls.__name__
