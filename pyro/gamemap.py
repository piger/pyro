import random
import tcod.bsp
import noise
from collections import OrderedDict
from pyro.entities import EntityManager
from pyro.utils import Rect, Vector2, tcod_random, NORTH, SOUTH, EAST, WEST
from pyro.rooms import room_1


VOID = 0
WALL = 1
FLOOR = 2
ROOM = 3
CORRIDOR = 4


def create_room_inside(x, y, min_width, min_height, max_width, max_height):
    """Place a Rect inside another Rect, with random padding"""

    width = random.randint(min_width, max_width)
    height = random.randint(min_height, max_height)
    pad_x = max_width - width
    pad_y = max_height - height

    if pad_x > 0:
        x += random.randint(0, pad_x)

    if pad_y > 0:
        y += random.randint(0, pad_y)

    return Room(x, y, width, height)


class Room(Rect):
    """Holds coordinates for a Room"""

    LAST_ID = 0

    def __init__(self, x, y, width, height):
        super(Room, self).__init__(x, y, width, height)
        self.connected = False
        self.rid = Room.next_id()

    @classmethod
    def next_id(cls):
        rv = cls.LAST_ID
        cls.LAST_ID += 1
        return rv


class GameCell(object):
    """A single dungeon cell"""

    def __init__(self):
        self.kind = VOID
        self.entities = []
        self.room_id = None
        self.feature = None
        # a debug value
        self.value = None

    def __repr__(self):
        return "GameCell(kind=%r, entities=%r, room_id=%r, feature=%r)" % (
            self.kind, self.entities, self.room_id, self.feature)


class GameMap(object):
    """The dungeon"""

    def __init__(self, width, height, min_room_width=6, min_room_height=6):
        self.width = width
        self.height = height
        self.min_room_width = min_room_width
        self.min_room_height = min_room_height

        self.cells = [[GameCell() for y in xrange(self.height)] for x in xrange(self.width)]
        self.rooms = OrderedDict()
        self.start_vec = None
        self.end_vec = None
        self.start_room_id = None
        self.end_room_id = None
        self.tunnel_id = '0' # note: it's a str!

    def _traverse(self, node):
        for child in node.children:
            self._traverse(child)

        if node.children:
            self._connect_nodes(node)
        else:
            room = create_room_inside(node.x, node.y, self.min_room_width, self.min_room_height,
                                      node.width, node.height)
            self.rooms[room.rid] = room
            self._dig_room(room)

    def _connect_nodes(self, node):
        """Creates two Rooms from two BSP nodes and connect them with a corridor"""

        room_a, room_b = None, None

        node1, node2 = node.children
        n1 = Rect(node1.x, node1.y, node1.width, node1.height)
        n2 = Rect(node2.x, node2.y, node2.width, node2.height)

        for room in self.rooms.values():
            if room.intersect(n1):
                room_a = room
                break

        for room in self.rooms.values():
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
        elif node1.level != node2.level:
            print "node1 and node2 are different levels!"
            return

        self._connect_rooms(room_a, room_b)
        self.rooms[room_a.rid].connected = True
        self.rooms[room_b.rid].connected = True

    def _connect_rooms(self, room1, room2):
        """Connects two rooms with a corridor"""

        sx, sy = room1.center
        dx, dy = room2.center

        v = self.tunnel_id
        self.tunnel_id = chr(ord(self.tunnel_id) + 1)
        if random.random() < 0.5:
            self._create_horizontal_tunnel(sx, dx, sy, v)
            self._create_vertical_tunnel(sy, dy, dx, v)
        else:
            self._create_vertical_tunnel(sy, dy, sx, v)
            self._create_horizontal_tunnel(sx, dx, dy, v)

    def _create_horizontal_tunnel(self, x1, x2, y, v=None):
        for x in xrange(min(x1, x2), max(x1, x2) + 1):
            self._create_tunnel(x, y, v)

    def _create_vertical_tunnel(self, y1, y2, x, v=None):
        for y in xrange(min(y1, y2), max(y1, y2) + 1):
            self._create_tunnel(x, y, v)

    def _create_tunnel(self, x, y, value=None):
        """Create a single corridor tile and perform some checks"""

        # if this tunnel touches a room, tell it that it is connected now
        room_id = self.cells[x][y].room_id
        if room_id:
            self.rooms[room_id].connected = True

        self.cells[x][y].kind = CORRIDOR

        # set up DEBUG value
        if value is not None:
            self.cells[x][y].value = value

        # fill cells around this corridor cell if they are void
        for c in self.get_cells_around(x, y):
            if c.kind == VOID:
                c.kind = WALL

    def _cancel_room(self, room):
        """Remove a room from the map. Used by BSP.

        To avoid deleting pieces of other rooms or corridors don't delete
        the outer walls of this room."""

        for y in xrange(room.y + 1, room.endY - 1):
            for x in xrange(room.x + 1, room.endX - 1):
                self.cells[x][y].kind = VOID
                self.cells[x][y].room_id = None
        del self.rooms[room.rid]

    def _place_creatures_in_rooms(self, level, entity_manager):
        rooms = [room for room in self.rooms.values() if room.rid != self.start_room_id]
        creatures = [('boar', level * 20), ('fairy', 3)]
        for creature_name, amount in creatures:
            for _ in xrange(amount):
                for j in xrange(5):
                    # retries 5 times
                    room = random.choice(rooms)
                    if len(self.get_entities_in_room(room.rid)) > 4:
                        continue
                    x = random.randint(room.x + 1, room.endX - 2)
                    y = random.randint(room.y + 1, room.endY - 2)
                    cell = self.get_at(x, y)
                    if cell.kind not in (ROOM, CORRIDOR) and len(cell.entities) > 0:
                        continue
                    entity = entity_manager.create_entity(creature_name)
                    entity.set_position(x, y)
                    cell.entities.append(entity.eid)
                    break

    def _place_items_in_rooms(self):
        pass

    def _select_start_and_end(self, entity_manager):
        """Place stairs up and stairs down"""

        rooms = self.rooms.values()
        if self.start_room_id is None:
            start_room = random.choice(rooms)
        else:
            start_room = self.get_room(self.start_room_id)
        rooms.remove(start_room)
        end_room = random.choice(rooms)

        self.start_room_id = start_room.rid
        self.end_room_id = end_room.rid

        start_x, start_y = start_room.center
        self.start_vec = Vector2(start_x, start_y)
        start_cell = self.get_at(start_x, start_y)

        entity = entity_manager.create_entity('stairs_up')
        entity.always_visible = True
        entity.set_position(start_x, start_y)
        start_cell.entities.append(entity.eid)

        end_x, end_y = end_room.center
        self.end_vec = Vector2(end_x, end_y)
        end_cell = self.get_at(end_x, end_y)

        entity = entity_manager.create_entity('stairs_down')
        entity.always_visible = True
        entity.set_position(end_x, end_y)
        end_cell.entities.append(entity.eid)

    # NOTES:
    # if we store a rect for each room and then in connect_nodes() we create a new Rect for both rooms
    # and then we use Rect.intersect() to find the matching room.
    def generate_bsp(self, level, entity_manager):
        # place outer walls
        for x in xrange(self.width):
            self.cells[x][0].kind = WALL
            self.cells[x][self.height-1].kind = WALL

        for y in xrange(self.height):
            self.cells[0][y].kind = WALL
            self.cells[self.width-1][y].kind = WALL

        # rooms
        bsp = tcod.bsp.BSP(x=1, y=1, width=self.width-2, height=self.height-2)
        bsp.split_recursive(depth=7, min_width=self.min_room_width + 1, min_height=self.min_room_height + 1,
                            max_horizontal_ratio=1.5, max_vertical_ratio=1.5, seed=tcod_random.rng)

        self._traverse(bsp)

        # we're lazy and we just delete unconnected rooms
        unconnected_rooms = [room for room in self.rooms.values() if not room.connected]
        print "%d unconnected rooms" % len(unconnected_rooms)
        for room in unconnected_rooms:
            self._cancel_room(room)

        # Convert 'tunnel' blocks inside rooms into room blocks
        for room in self.rooms.values():
            for y in xrange(room.y+1, room.endY-1):
                for x in xrange(room.x+1, room.endX-1):
                    self.cells[x][y].kind = ROOM

        # select starting and ending rooms
        self._select_start_and_end(entity_manager)
        self._place_creatures_in_rooms(level, entity_manager)
        self._add_features()

    def generate_tunneling(self, level, entity_manager):
        max_room_size = 16
        min_room_size = 5
        max_rooms = 30
        weird_done = False
        is_weird = False

        for _ in xrange(max_rooms):
            lines = []
            if random.random() > 0.8 and not weird_done:
                template = room_1.strip()
                lines = template.split("\n")
                width = len(lines[0])
                height = len(lines)
                weird_done = True
                is_weird = True
            else:
                width = random.randint(min_room_size, max_room_size)
                height = random.randint(min_room_size, max_room_size)

            x = random.randint(0, self.width - width - 1)
            y = random.randint(0, self.height - height - 1)
            room = Room(x, y, width, height)

            failed = False
            for other_room in self.rooms.values():
                if room.intersect(other_room):
                    failed = True
                    break

            if failed:
                continue

            self.rooms[room.rid] = room
            self._dig_room(room)

            # special case for creating prefab rooms
            if is_weird:
                for y, line in enumerate(lines):
                    for x, c in enumerate(line):
                        if c == '#':
                            self.cells[room.x + x][room.y + y].kind = WALL
                is_weird = False

            if len(self.rooms) > 1:
                last_room = self.rooms.values()[-2]
                self._connect_rooms(room, last_room)
            else:
                self.start_room_id = room.rid

        self._select_start_and_end(entity_manager)
        self._place_creatures_in_rooms(level, entity_manager)
        self._place_doors(entity_manager)

    def _dig_room(self, room):
        # room outer walls (y) - do not overwrite existing tunnel tho!
        for y in xrange(room.y, room.endY):
            if self.cells[room.x][y].kind == VOID:
                self.cells[room.x][y].kind = WALL
            self.cells[room.x][y].room_id = room.rid
            if self.cells[room.endX-1][y].kind == VOID:
                self.cells[room.endX-1][y].kind = WALL
            self.cells[room.endX-1][y].room_id = room.rid

        # room outer walls (x)
        for x in xrange(room.x, room.endX):
            if self.cells[x][room.y].kind == VOID:
                self.cells[x][room.y].kind = WALL
            self.cells[x][room.y].room_id = room.rid
            if self.cells[x][room.endY-1].kind == VOID:
                self.cells[x][room.endY-1].kind = WALL
            self.cells[x][room.endY-1].room_id = room.rid

        # room interior
        for y in xrange(room.y+1, room.endY-1):
            for x in xrange(room.x+1, room.endX-1):
                # detect when a room is digged over an existing corridor.
                if self.cells[x][y].kind == CORRIDOR:
                    room.connected = True
                self.cells[x][y].kind = ROOM
                self.cells[x][y].room_id = room.rid

    def _add_features(self):
        frequency = 8.0
        fx = float(self.width) / frequency
        fy = float(self.height) / frequency

        # thresholds
        # t1 = 0.2
        # t2 = 0.4
        # t3 = 0.5
        t1 = random.uniform(0.2, 0.4)
        t2 = t1 + random.uniform(0.1, 0.2)
        t3 = t2 + 0.1

        for y in xrange(1, self.height - 1):
            for x in xrange(1, self.width - 1):
                if self.cells[x][y].kind not in (ROOM, CORRIDOR, FLOOR):
                    continue
                # get noise and transform to a value between 1 and 0
                n = noise.pnoise2(x / fx, y / fy) * 0.5 + 0.5
                if n <= t1:
                    self.cells[x][y].feature = "water"
                elif n <= t2:
                    self.cells[x][y].feature = "grass"
                elif n <= t3:
                    self.cells[x][y].feature = "dirt"
                else:
                    self.cells[x][y].feature = "floor"

    def _place_doors(self, entity_manager):
        for room in self.rooms.values():
            # openings = []

            # inspect room sides, except corners
            for y in xrange(room.y + 1, room.endY - 1):
                for i in (room.x, room.endX - 1):
                    pos = Vector2(i, y)
                    # a room can only be placed between two walls
                    if (self.get_at(pos + NORTH).kind == WALL and
                        self.get_at(pos + SOUTH).kind == WALL):
                        self._maybe_place_door(entity_manager, i, y)

            for x in xrange(room.x + 1, room.endX - 1):
                for i in (room.y, room.endY - 1):
                    pos = Vector2(x, i)
                    if (self.get_at(pos + EAST).kind == WALL and
                        self.get_at(pos + WEST).kind == WALL):
                        self._maybe_place_door(entity_manager, x, i)

    def _maybe_place_door(self, entity_manager, x ,y):
        cell = self.get_at(x, y)
        if cell.kind == CORRIDOR:
            if random.random() > 0.3:
                entity = entity_manager.create_entity('door')
                entity.always_visible = True
                entity.set_position(x, y)
                cell.entities.append(entity.eid)

    def get_at(self, x_or_pos, y=None):
        if y is None and isinstance(x_or_pos, Vector2):
            return self.cells[x_or_pos.x][x_or_pos.y]
        return self.cells[x_or_pos][y]

    def get_cells_around(self, x, y):
        """Get cells around x, y, EXCEPT x,y!"""

        cells = []
        for dx, dy in ((-1, -1), (0, -1), (1, -1),
                       (-1, 0), (1, 0),
                       (-1, 1), (0, 1), (1, 1)):
            cells.append(self.get_at(x + dx, y + dy))
        return cells

    def get_room(self, room_id):
        return self.rooms[room_id]

    def get_entities_in_room(self, room_id):
        """Get all the entities ID for the entities in a room"""

        room = self.get_room(room_id)
        result = []
        for x in xrange(room.x, room.endX):
            for y in xrange(room.y, room.endY):
                cell = self.get_at(x, y)
                result.extend(cell.entities)
        return result


class World(object):
    def __init__(self):
        self.maps = []
        self.current_map = 0
        self.entity_manager = EntityManager()
        self.entity_manager.load()

    def create_map(self, width, height, level=1, dungeon_algorithm=None):
        game_map = GameMap(width, height)

        if dungeon_algorithm is None or dungeon_algorithm == 'bsp':
            game_map.generate_bsp(level, self.entity_manager)
        elif dungeon_algorithm == 'tunneling':
            game_map.generate_tunneling(level, self.entity_manager)
        else:
            raise Exception("Dungeon algorithm %s do not exists" % dungeon_algorithm)

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
