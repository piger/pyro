import inspect
import random
import re
import json
import pkg_resources
import tcod
import tcod.path
import tcod.map
from pyro.utils import Vector2, Direction, weighted_choice
from pyro import *
from pyro.gamedata import gamedata
from pyro.astar import astar
from pyro.potions import POTION_AVATAR, POTION_COLOR


# https://web.njit.edu/~kevin/rgb.txt.html
DEFAULT_ENTITY_COLOR = (255, 127, 36) # chocolate1


def parse_capability(line):
    if ':' not in line:
        return (line, [])
    name, line = line.split(':', 1)
    results = re.split(r'(?<!\\):', line)
    results = [x.replace('\\\\', '\\') for x in results]
    return (name, results)


class Component(object):

    NAME = 'component'
    kind = ComponentType.DUMB

    def config(self, values):
        raise NotImplementedError

    @property
    def name(self):
        return self.NAME


class HealthComponent(Component):

    NAME = 'health'
    kind = ComponentType.HEALTH

    def __init__(self):
        super(HealthComponent, self).__init__()
        self.health = 0

    def config(self, values):
        self.health = int(values[0])


class PotionComponent(Component):
    """Potions

    - they can be on the map or in the inventory (just delete from cell.entities? and store somewhere?)
    - the player can drink or throw them
    - they must have a random mapped color
    """

    NAME = 'potion'
    kind = ComponentType.POTION

    def __init__(self, potion_type):
        super(PotionComponent, self).__init__()
        self.potion_type = potion_type

    def config(self, values):
        return


class InventoryComponent(Component):
    NAME = 'inventory'
    kind = ComponentType.INVENTORY

    def __init__(self):
        super(InventoryComponent, self).__init__()
        self.items = []
        self.max_items = 10
        self.item_map = {}

    def config(self, values):
        return


class CombatComponent(Component):

    NAME = 'combat'
    kind = ComponentType.COMBAT

    def __init__(self, damage=0, defense=0, accuracy=0):
        super(CombatComponent, self).__init__()
        self.damage = damage
        self.defense = defense
        self.accuracy = accuracy

    def config(self, values):
        m = {
            'DAMAGE': 'damage',
            'DEFENSE': 'defense',
            'ACCURACY': 'accuracy',
        }
        for i in xrange(0, len(values), 2):
            name = values[i]
            value = values[i+1]
            setattr(self, m[name], int(value))


class DoorComponent(Component):

    NAME = 'door'
    kind = ComponentType.DOOR

    def __init__(self, initial_state=True):
        super(DoorComponent, self).__init__()
        self.state = initial_state

    def config(self, values):
        pass


class MonsterAIComponent(Component):
    """AI for monsters."""

    NAME = 'monster_ai'
    kind = ComponentType.MONSTER_AI

    def __init__(self):
        super(MonsterAIComponent, self).__init__()
        self.fov_map = None
        self.radius = 4
        self.can_move_diagonal = True
        self.aggressive = True

        self.chasing = False
        self.last_player_pos = None
        self.cur_direction = None

    def config(self, values):
        for i in xrange(0, len(values), 2):
            name = values[i]
            value = values[i+1]
            if name == 'FOV_RADIUS':
                self.radius = int(value)
            elif name == 'DIAGONAL':
                self.can_move_diagonal = bool(int(value))
            elif name == 'AGGRESSIVE':
                self.aggressive = bool(int(value))

    def setup(self, game):
        """Must be called during game initialization, after fov_map is computed"""

        self.fov_map = tcod.map.Map(width=game.game_width, height=game.game_height)
        for y in xrange(game.game_height):
            for x in xrange(game.game_width):
                self.fov_map.walkable[y,x] = game.fov_map.walkable[y,x]
                self.fov_map.transparent[y,x] = game.fov_map.transparent[y,x]

    def move_to(self, entity, cur_map, entity_manager, pos):
        """Move the entity to a pos, if possible"""

        new_cell = cur_map.get_at(pos)
        caller = inspect.stack()[1][3]

        if new_cell is None:
            print "move_to: %r is outside of map (caller: %s)" % (new_cell, caller)
            return False
        elif not new_cell.walkable:
            print "move_to: %r is not walkable (caller: %s)" % (new_cell, caller)
            return False

        for entity_id in new_cell.entities:
            if entity_id in entity_manager.monster_ai_components:
                # we can't move, there's another AI in that cell
                return False

        cur_map.move_entity(entity, pos)
        return True

    def wander(self, entity, game):
        """Wander around randomly"""

        candidates = []
        cur_map = game.world.get_current_map()
        for d in Direction.all():
            dest = entity.position + d
            cell = cur_map.get_at(dest)
            if not cell.walkable:
                continue
            for eid in cell.entities:
                e = game.world.entity_manager.get_entity(eid)
                if e in game.world.entity_manager.monster_ai_components:
                    continue
            candidates.append(dest)

        # chose a new random direction, with a preference on following the current direction, just to make it look
        # slightly less random.
        if self.cur_direction is not None and self.cur_direction in candidates:
            w = []
            for c in candidates:
                if c == self.cur_direction:
                    w.append((2.5, c))
                else:
                    w.append((1, c))
            winner = candidates[weighted_choice([x[0] for x in w])]
        else:
            winner = random.choice(candidates)

        if self.move_to(entity, cur_map, game.world.entity_manager, winner):
            self.cur_direction = winner.copy()

    def update(self, entity, game):
        """To be called every turn"""

        if not self.aggressive:
            if random.random() < 0.3:
                return
            self.wander(entity, game)
            return

        player = game.player
        cur_map = game.world.get_current_map()
        em = game.world.entity_manager

        if self.last_player_pos is not None and entity.position == self.last_player_pos:
            self.last_player_pos = None

        # check if the player is directly adjacent, so that we can skip calculating the FOV for this
        # monster.
        adjacent = False
        for d in Direction.all():
            pos = entity.position + d
            if pos == player.position:
                adjacent = True
                self.chasing = True

        if not adjacent:
            # update fov
            self.fov_map.compute_fov(entity.position.x, entity.position.y,
                                     radius=self.radius, algorithm=tcod.FOV_DIAMOND)
            # if the player position is "lit", then we see the player
            self.chasing = self.fov_map.fov[player.position.y, player.position.x]
        elif adjacent:
            print "attacking"
            game.enemy_fight_player(entity)
            return

        if self.chasing:
            path = astar(cur_map, entity.position, player.position, self.can_move_diagonal)
            if len(path) == 1:
                new_pos = path[0]
                if new_pos == player.position:
                    # attack
                    print "attacking"
                    game.enemy_fight_player(entity)
            elif path:
                print "chasing"
                self.last_player_pos = path[-1]

                new_pos = path[0]
                if not self.move_to(entity, cur_map, em, new_pos):
                    print "can't move, cell is busy"
            else:
                print "path is empty!?"
        else:
            if self.last_player_pos is not None:
                print "remembering the chase"
                path = astar(cur_map, entity.position, self.last_player_pos,
                             self.can_move_diagonal)
                self.move_to(entity, cur_map, em, path[0])
            else:
                # move randomly, but not all the times
                if random.random() < 0.3:
                    return
                self.wander(entity, game)


COMP_MAP = {
    'health': HealthComponent,
    'combat': CombatComponent,
    'door': DoorComponent,
    'monster_ai': MonsterAIComponent,
    'potion': PotionComponent,
}


class Entity(object):
    def __init__(self, eid, name, avatar, color, layer=LAYER_CREATURES):
        self.eid = eid
        self.name = name
        self.display_name = None
        self.avatar = avatar
        self.color = color
        self.layer = layer
        self.position = Vector2(0, 0)
        self.always_visible = False
        self.description = ''
        self.components = {}

    def get_component(self, name):
        return self.components[name]

    def has_component(self, name):
        return name in self.components

    def add_component(self, component):
        self.components[component.kind.name] = component

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
        return any([c.kind == ComponentType.MONSTER_AI for c in self.components.values()])

    def is_potion(self):
        return any([c.kind == ComponentType.POTION for c in self.components.values()])

    def __repr__(self):
        return "<Entity(eid=%d, name=%s, display_name=%s, position=%r, components=%r)>" % (
            self.eid, self.name, self.display_name, self.position, self.components)


class EntityManager(object):
    def __init__(self):
        self.eid = 0
        self.entities = {}
        self.health_components = {}
        self.combat_components = {}
        self.door_components = {}
        self.monster_ai_components = {}
        self.potion_components = {}

        self.comp_db = {
            'health': self.health_components,
            'combat': self.combat_components,
            'door': self.door_components,
            'monster_ai': self.monster_ai_components,
            'potion': self.potion_components,
        }

    def next_eid(self):
        rv = self.eid
        self.eid += 1
        return rv

    def create_entity(self, name, entity_data=None):
        eid = self.next_eid()

        if entity_data is None:
            entity_data = gamedata.get_entity(name)
        assert entity_data is not None, "Entity data for %s is None" % name

        color = entity_data.get('color', DEFAULT_ENTITY_COLOR)
        entity = Entity(eid, name, entity_data['avatar'], color)
        entity.always_visible = entity_data.get('always_visible', False)
        entity.description = entity_data.get('description', '')
        entity.display_name = entity_data.get('display_name', '')

        for cap in entity_data.get('can', []):
            name, values = parse_capability(cap)
            CompClass = COMP_MAP[name]
            comp = CompClass()
            comp.config(values)
            db = self.comp_db[name]
            db[entity.eid] = comp
            entity.add_component(comp)

        self.entities[entity.eid] = entity
        return entity

    def create_potion(self, potion_type):
        eid = self.next_eid()
        entity = Entity(eid, 'potion', POTION_AVATAR, POTION_COLOR, layer=LAYER_ITEMS)
        entity.add_component(PotionComponent(potion_type))
        self.entities[entity.eid] = entity
        return entity

    def destroy_entity(self, eid):
        for db in self.comp_db.itervalues():
            if eid in db:
                del db[eid]

        del self.entities[eid]

    def get_entity(self, eid):
        return self.entities[eid]
