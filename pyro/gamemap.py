import random
from pyro.entities import EntityManager


WALL = 0
FLOOR = 1

class GameCell(object):
    def __init__(self):
        self.kind = FLOOR
        self.entities = []


class GameMap(object):

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = [[GameCell() for y in xrange(self.height)] for x in xrange(self.width)]

    def generate(self, level, entity_manager):
        for x in xrange(self.width):
            self.cells[x][0].kind = WALL
            self.cells[x][self.height-1].kind = WALL

        for y in xrange(self.height):
            self.cells[0][y].kind = WALL
            self.cells[self.width-1][y].kind = WALL

        num_boars = level * 3
        for _ in xrange(num_boars):
            rx = random.randint(1, self.width-2)
            ry = random.randint(1, self.height-2)
            cell = self.get_at(rx, ry)
            if len(cell.entities):
                print "Cell already occupied"
                continue
            entity = entity_manager.create_entity('boar')
            cell.entities.append(entity.eid)

        for _ in xrange(3):
            rx = random.randint(1, self.width-2)
            ry = random.randint(1, self.height-2)
            cell = self.get_at(rx, ry)
            if len(cell.entities):
                print "Cell already occupied for fairy"
                continue
            entity = entity_manager.create_entity('fairy')
            cell.entities.append(entity.eid)

    def get_at(self, x, y):
        return self.cells[x][y]


class World(object):
    def __init__(self):
        self.maps = []
        self.current_map = 0
        self.entity_manager = EntityManager()
        self.entity_manager.load()

    def create_map(self, width, height, level):
        game_map = GameMap(width, height)
        game_map.generate(level, self.entity_manager)
        self.maps.append(game_map)

    def get_current_map(self):
        return self.maps[self.current_map]
