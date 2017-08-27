import json
import pkg_resources


# https://web.njit.edu/~kevin/rgb.txt.html
DEFAULT_ENTITY_COLOR = (255, 127, 36) # chocolate1


class Position(object):
    def __init__(self, x_, y_):
        self.x = x_
        self.y = y_


class Component(object):
    def __init__(self, name):
        self.name = name


class HealthComponent(Component):

    NAME = 'health'

    def __init__(self, value):
        super(HealthComponent, self).__init__(self.NAME)
        self.value = value


class CombatComponent(Component):

    NAME = 'combat'

    def __init__(self, damage, armor):
        super(CombatComponent, self).__init__(self.NAME)
        self.damage = damage
        self.armor = armor


class Entity(object):
    def __init__(self, eid, name, avatar, color):
        self.eid = eid
        self.name = name
        self.avatar = avatar
        self.color = color
        self.position = Position(0, 0)
        self.components = {}

    def add_component(self, name, component):
        self.components[name] = component

    def get_component(self, name):
        return self.components[name]

    def set_position(self, x, y):
        self.position.x = x
        self.position.y = y

    def get_position(self):
        return self.position


class EntityManager(object):
    def __init__(self):
        self.entity_data = {}
        self.eid = 0
        self.entities = {}

        self.health_components = {}
        self.combat_components = {}

    def load(self):
        data = json.load(pkg_resources.resource_stream('pyro', 'data/entities.json'))
        for entity_data in data['entities']:
            name = entity_data['name']
            entity_data.setdefault('health', 0)
            entity_data.setdefault('damage', 0)
            entity_data.setdefault('armor', 0)
            self.entity_data[name] = entity_data

    def next_eid(self):
        rv = self.eid
        self.eid += 1
        return rv

    def create_entity(self, name):
        eid = self.next_eid()

        entity_data = self.entity_data.get(name)
        assert entity_data is not None, "Entity data for %s is None" % name

        color = entity_data.get('color', DEFAULT_ENTITY_COLOR)
        entity = Entity(eid, name, entity_data['avatar'], color)

        if entity_data['health'] > 0:
            hc = HealthComponent(entity_data['health'])
            self.health_components[entity.eid] = hc

        if entity_data['damage'] > 0:
            cc = CombatComponent(entity_data['damage'], entity_data['armor'])
            self.combat_components[entity.eid] = cc

        self.entities[entity.eid] = entity
        return entity

    def get_entity(self, eid):
        return self.entities[eid]
