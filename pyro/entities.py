import random
import re
import json
import pkg_resources
from pyro.utils import Vector2, Direction
from pyro import *
from pyro.gamedata import gamedata


# https://web.njit.edu/~kevin/rgb.txt.html
DEFAULT_ENTITY_COLOR = (255, 127, 36) # chocolate1


def parse_capability(line):
    name, line = line.split(':', 1)
    results = re.split(r'(?<!\\):', line)
    results = [x.replace('\\\\', '\\') for x in results]
    return (name, results)


class Component(object):

    NAME = 'component'

    def config(self, values):
        raise NotImplementedError

    @property
    def name(self):
        return self.NAME


class HealthComponent(Component):

    NAME = 'health'

    def __init__(self):
        super(HealthComponent, self).__init__()
        self.health = 0

    def config(self, values):
        self.health = int(values[0])


class CombatComponent(Component):

    NAME = 'combat'

    def __init__(self, damage=0, defense=0, accuracy=0):
        super(CombatComponent, self).__init__()
        self.damage = damage
        self.defense = defense
        self.accuracy = accuracy

    def config(self, values):
        self.damage, self.defense, self.accuracy = [int(x) for x in values]


class DoorComponent(Component):

    NAME = 'door'

    def __init__(self, initial_state=True):
        super(DoorComponent, self).__init__()
        self.state = initial_state

    def config(self, values):
        pass


class MonsterAIComponent(Component):
    """AI for monsters."""

    NAME = 'monster_ai'

    def __init__(self):
        super(MonsterAIComponent, self).__init__()

    def config(self, values):
        pass

    def update(self, entity, game):
        print "Moving %s" % entity.name
        cur_map = game.world.get_current_map()
        d = random.choice(Direction.all())
        dest = entity.position + d
        old_cell = cur_map.get_at(entity.position)
        cell = cur_map.get_at(dest)
        if cell.kind in (ROOM, CORRIDOR, FLOOR) and not cell.entities:
            entity.position = dest
            old_cell.entities.remove(entity.eid)
            cell.entities.append(entity.eid)


COMP_MAP = {
    'health': HealthComponent,
    'combat': CombatComponent,
    'door': DoorComponent,
    'life': HealthComponent,
    'monster_ai': MonsterAIComponent,
}


class Entity(object):
    def __init__(self, eid, name, avatar, color):
        self.eid = eid
        self.name = name
        self.avatar = avatar
        self.color = color
        self.position = Vector2(0, 0)
        self.always_visible = False

    def set_position(self, x, y):
        self.position.x = x
        self.position.y = y

    def get_position(self):
        return self.position


class EntityManager(object):
    def __init__(self):
        self.eid = 0
        self.entities = {}
        self.health_components = {}
        self.combat_components = {}
        self.door_components = {}
        self.monster_ai_components = {}

        self.comp_db = {
            'health': self.health_components,
            'combat': self.combat_components,
            'door': self.door_components,
            'monster_ai': self.monster_ai_components,
        }

    def next_eid(self):
        rv = self.eid
        self.eid += 1
        return rv

    def create_entity(self, name):
        eid = self.next_eid()

        entity_data = gamedata.get_entity(name)
        assert entity_data is not None, "Entity data for %s is None" % name

        color = entity_data.get('color', DEFAULT_ENTITY_COLOR)
        entity = Entity(eid, name, entity_data['avatar'], color)
        entity.always_visible = entity_data.get('always_visible', False)

        for cap in entity_data.get('can', []):
            name, values = parse_capability(cap)
            CompClass = COMP_MAP[name]
            comp = CompClass()
            comp.config(values)
            db = self.comp_db[name]
            db[entity.eid] = comp

        self.entities[entity.eid] = entity
        return entity

    def destroy_entity(self, eid):
        for db in self.comp_db.itervalues():
            if eid in db:
                del db[eid]

        del self.entities[eid]

    def get_entity(self, eid):
        return self.entities[eid]
