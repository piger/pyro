import random
import tcod.bsp
from pyro.entities import EntityManager


WALL = 0
FLOOR = 1
ROOM = 2

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
        # place outer walls
        for x in xrange(self.width):
            self.cells[x][0].kind = WALL
            self.cells[x][self.height-1].kind = WALL

        for y in xrange(self.height):
            self.cells[0][y].kind = WALL
            self.cells[self.width-1][y].kind = WALL

        # rooms
        bsp = tcod.bsp.BSP(x=1, y=1, width=self.width-2, height=self.height-2)
        bsp.split_recursive(depth=5, min_width=4, min_height=4,
                            max_horizontal_ratio=1.5,
                            max_vertical_ratio=1.5)

        def create_room(node):
            # TODO: add a chance to NOT generate a room
            if random.randint(0, 100) > 85:
                print "randomly skipping room"
                return
            print "Create a room in: %d %d (%d %d)" % (node.x, node.y, node.width, node.height)

            rx = node.x + 1
            rxx = node.x + node.width - 1
            ry = node.y + 1
            ryy = node.y + node.height - 1

            for y in xrange(ry, ryy+1):
                for x in xrange(rx, rxx+1):
                    self.cells[x][y].kind = ROOM

        def connect_rooms(node):
            node1, node2 = node.children
            # print "Connect %r and %r" % (node1, node2)

        def traverse(node):
            for child in node.children:
                traverse(child)

            if node.children:
                connect_rooms(node)
            else:
                create_room(node)

        traverse(bsp)
            
        num_boars = level * 3
        for _ in xrange(num_boars):
            rx = random.randint(1, self.width-2)
            ry = random.randint(1, self.height-2)
            cell = self.get_at(rx, ry)
            if len(cell.entities):
                print "Cell already occupied"
                continue
            entity = entity_manager.create_entity('boar')
            entity.set_position(rx, ry)
            cell.entities.append(entity.eid)

        for _ in xrange(3):
            rx = random.randint(1, self.width-2)
            ry = random.randint(1, self.height-2)
            cell = self.get_at(rx, ry)
            if len(cell.entities):
                print "Cell already occupied for fairy"
                continue
            entity = entity_manager.create_entity('fairy')
            entity.set_position(rx, ry)
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
