import random
import tcod.bsp
from pyro.entities import EntityManager
from pyro.math import Rect


WALL = 0
FLOOR = 1
ROOM = 2
CORRIDOR = 3


def create_rect_inside(x, y, min_width, min_height, max_width, max_height):
    width = random.randint(min_width, max_width)
    height = random.randint(min_height, max_height)
    pad_x = max_width - width
    pad_y = max_height - height

    if pad_x > 0:
        x += random.randint(0, pad_x)

    if pad_y > 0:
        y += random.randint(0, pad_y)

    return Rect(x, y, width, height)


class GameCell(object):
    def __init__(self):
        self.kind = FLOOR
        self.entities = []


class GameMap(object):

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = [[GameCell() for y in xrange(self.height)] for x in xrange(self.width)]

    # NOTES:
    # if we store a rect for each room and then in connect_rooms() we create a new Rect for both rooms
    # and then we use Rect.intersect() to find the matching room.
    def generate(self, level, entity_manager):
        min_room_width = 6
        min_room_height = 6

        # place outer walls
        for x in xrange(self.width):
            self.cells[x][0].kind = WALL
            self.cells[x][self.height-1].kind = WALL

        for y in xrange(self.height):
            self.cells[0][y].kind = WALL
            self.cells[self.width-1][y].kind = WALL

        # rooms
        bsp = tcod.bsp.BSP(x=1, y=1, width=self.width-2, height=self.height-2)
        bsp.split_recursive(depth=7, min_width=min_room_width + 1, min_height=min_room_height + 1,
                            max_horizontal_ratio=1.5,
                            max_vertical_ratio=1.5)

        rooms = []

        def create_room(node):
            room = create_rect_inside(node.x, node.y, min_room_width, min_room_height, node.width, node.height)
            rooms.append(room)

            # room outer walls (y)
            for y in xrange(room.y, room.endY):
                self.cells[room.x][y].kind = WALL
                self.cells[room.endX-1][y].kind = WALL

            # room outer walls (x)
            for x in xrange(room.x, room.endX):
                self.cells[x][room.y].kind = WALL
                self.cells[x][room.endY-1].kind = WALL

            # room interior
            for y in xrange(room.y+1, room.endY-1):
                for x in xrange(room.x+1, room.endX-1):
                    self.cells[x][y].kind = ROOM

        def draw_corridor(room1, room2):
            sx, sy = room1.center
            dx, dy = room2.center

            if random.randint(0, 1) == 0:
                self.create_horizontal_tunnel(sx, dx, sy)
                self.create_vertical_tunnel(sy, dy, dx)
            else:
                self.create_vertical_tunnel(sy, dy, sx)
                self.create_horizontal_tunnel(sx, dx, dy)

        def connect_rooms(node):
            room_a, room_b = None, None

            node1, node2 = node.children
            n1 = Rect(node1.x, node1.y, node1.width, node1.height)
            n2 = Rect(node2.x, node2.y, node2.width, node2.height)

            for room in rooms:
                if room.intersect(n1):
                    room_a = room
                    break

            for room in rooms:
                if room.intersect(n2) and room != room_a:
                    room_b = room
                    break

            if room_a is None and room_b is None:
                print "both room_a and room_b are None"
                return
            elif room_a is None and room_b:
                print "room_a is None, room_b is OK"
                return
            elif room_a and room_b is None:
                print "room_a is OK, room_b is None"
                return
            elif room_a == room_b:
                print "room_a and room_b are the SAME"
                return
            elif node1.level != node2.level:
                print "node1 and node2 are different levels!"
                return
            else:
                print "connect %r to %r" % (room_a, room_b)

            draw_corridor(room_a, room_b)

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

    def create_horizontal_tunnel(self, x1, x2, y):
        for x in xrange(min(x1, x2), max(x1, x2) + 1):
            if self.cells[x][y].kind != ROOM:
                self.cells[x][y].kind = CORRIDOR

    def create_vertical_tunnel(self, y1, y2, x):
        for y in xrange(min(y1, y2), max(y1, y2) + 1):
            if self.cells[x][y].kind != ROOM:
                self.cells[x][y].kind = CORRIDOR

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

    def destroy_entity(self, eid):
        entity = self.entity_manager.get_entity(eid)
        pos = entity.get_position()
        cell = self.maps[self.current_map].get_at(pos.x, pos.y)
        if eid not in cell.entities:
            print "BUGGONE"
        else:
            cell.entities.remove(eid)

        self.entity_manager.destroy_entity(eid)
