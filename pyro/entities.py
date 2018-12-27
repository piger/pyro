import inspect
import random
import re
import json
import pkg_resources
import tcod
import tcod.path
import tcod.map
from .utils import Vector2, Direction, weighted_choice
from . import LAYER_CREATURES, LAYER_ITEMS
from .gamedata import gamedata
from .astar import astar
from .potions import POTION_AVATAR, POTION_COLOR
from .components import COMPONENT_CLASS, HealthComponent, PotionComponent


# https://web.njit.edu/~kevin/rgb.txt.html
DEFAULT_ENTITY_COLOR = (255, 127, 36)  # chocolate1


def parse_capability(line):
    """
    Parse a capability string.

    The format for a capability string is:

    <name>:[<ATTRIBUTE:VALUE>, ":", <ATTRIBUTE:VALUE>...]

    For example the string "combat:DAMAGE:2:ACCURACY:70" configure the 'combat' capability
    with values "2" for "DAMAGE" and "70" for "ACCURACY".
    """
    if ":" not in line:
        return (line, [])
    name, line = line.split(":", 1)
    results = re.split(r"(?<!\\):", line)
    results = [x.replace("\\\\", "\\") for x in results]
    return (name, results)


class Entity:
    def __init__(self, eid, name, avatar, color, layer=LAYER_CREATURES):
        self.eid = eid
        self.name = name
        self.display_name = None
        self.avatar = avatar
        self.color = color
        self.layer = layer
        self.position = Vector2(0, 0)
        self.always_visible = False
        self.description = ""
        self.components = {}

    def get_component(self, name):
        return self.components[name]

    def has_component(self, name):
        return name in self.components

    def add_component(self, component):
        self.components[component.name] = component

    def set_position(self, x_or_pos, y=None):
        if isinstance(x_or_pos, Vector2) and y is None:
            self.position.x = x_or_pos.x
            self.position.y = x_or_pos.y
        else:
            self.position.x = x_or_pos
            self.position.y = y

    def get_position(self):
        return self.position

    def is_monster(self):
        return any([c.name == "monster_ai" for c in self.components.values()])

    def is_potion(self):
        return any([c.name == "potion" for c in self.components.values()])

    def __repr__(self):
        return f"<Entity(eid={self.eid}, name={self.name} ({self.display_name}), pos={self.position})>"


class EntityManager:
    def __init__(self):
        # used to track the first free entity ID that can be assigned
        self._eid = 0

        # entity/component tables
        self.entities = {}

        # dictionary of dictionaries storing a map Entity ID -> Component instance
        # keys will be Component's names (e.g. "health").
        self.components = {}

    def next_eid(self):
        """Allocate and return new Entity ID"""

        rv = self._eid
        self._eid += 1
        return rv

    def register_component(self, entity, component):
        # print("registering %s for %s" % (component.name, entity))
        self.components.setdefault(component.name, {})
        self.components[component.name][entity.eid] = component

    def get_component_by_eid(self, eid, component_name):
        return self.components[component_name].get(eid)

    def create_entity(self, name, entity_data=None):
        """
        Create a new Entity from game data.

        `entity_data` is either a dictionary containing the configuration for the entity
        or `None` when the EntityManager should do the lookup by itself.

        """
        eid = self.next_eid()

        if entity_data is None:
            entity_data = gamedata.get_entity(name)
        assert entity_data is not None, "Entity data for %s is None" % name

        color = entity_data.get("color", DEFAULT_ENTITY_COLOR)
        entity = Entity(eid, name, entity_data["avatar"], color)
        entity.always_visible = entity_data.get("always_visible", False)
        entity.description = entity_data.get("description", "<MISSING DESCRIPTION>")
        entity.display_name = entity_data.get("display_name", "<MISSING DISPLAY_NAME>")

        # configure all the entity's capabilities.
        for cap in entity_data.get("can", []):
            name, values = parse_capability(cap)
            comp = COMPONENT_CLASS[name]()
            comp.config(values)

            # store the capability for this Entity in the db
            self.register_component(entity, comp)

            # print("Adding %r to %r" % (comp, entity))
            entity.add_component(comp)

        self.entities[entity.eid] = entity
        return entity

    def create_potion(self, potion_type):
        eid = self.next_eid()
        entity = Entity(eid, "potion", POTION_AVATAR, POTION_COLOR, layer=LAYER_ITEMS)
        pc = PotionComponent(potion_type)
        entity.add_component(pc)
        self.register_component(entity, pc)
        self.entities[entity.eid] = entity
        return entity

    def destroy_entity(self, eid):
        """Destroy and entity and unregister all its components"""

        for component_db in self.components.values():
            if eid in component_db:
                del component_db[eid]

        del self.entities[eid]

    def get_entity(self, eid):
        return self.entities[eid]
