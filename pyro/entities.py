import json
import pkg_resources
from pyro.utils import Vector2
from pyro.gamedata import gamedata


# https://web.njit.edu/~kevin/rgb.txt.html
DEFAULT_ENTITY_COLOR = (255, 127, 36) # chocolate1


class Component(object):
    def __init__(self, name):
        self.name = name


class HealthComponent(Component):

    NAME = 'health'

    def __init__(self, value):
        super(HealthComponent, self).__init__(self.NAME)
        self.health = value


class CombatComponent(Component):

    NAME = 'combat'

    def __init__(self, damage, armor):
        super(CombatComponent, self).__init__(self.NAME)
        self.damage = damage
        self.armor = armor


class DoorComponent(Component):

    NAME = 'door'

    def __init__(self, initial_state=True):
        super(DoorComponent, self).__init__(self.NAME)
        self.state = initial_state


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

        if entity_data['health'] > 0:
            hc = HealthComponent(entity_data['health'])
            self.health_components[entity.eid] = hc

        if entity_data['damage'] > 0:
            cc = CombatComponent(entity_data['damage'], entity_data['armor'])
            self.combat_components[entity.eid] = cc

        self.entities[entity.eid] = entity
        return entity

    def create_door(self, x, y):
        entity = self.create_entity('door')
        dc = DoorComponent()
        self.door_components[entity.eid] = dc
        entity.always_visible = True
        entity.set_position(x, y)
        return entity

    def destroy_entity(self, eid):
        if eid in self.health_components:
            del self.health_components[eid]

        if eid in self.combat_components:
            del self.combat_components[eid]

        del self.entities[eid]

    def get_entity(self, eid):
        return self.entities[eid]
