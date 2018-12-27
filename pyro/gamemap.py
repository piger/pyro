import logging
import random
from collections import OrderedDict
import noise
from .utils import Rect, Vector2, Direction
from .gamedata import gamedata
from . import CORRIDOR, VOID, WALKABLE, BLOCKING, WALL, ROOM, PotionType


logger = logging.getLogger(__name__)


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

    def __repr__(self):
        return (
            f"<Room(x={self.x}, y={self.y}, width={self.width}, height={self.height}, "
            f"id={self.rid}, connected={self.connected})>"
        )


class SpecialRoom:
    def __init__(self, source):
        lines = source.split("\n")
        self.width = max([len(line) for line in lines]) + 1
        self.height = len(lines) + 1
        self.cells = [[False for _ in range(self.height)] for _ in range(self.width)]

        for y, line in enumerate(lines):
            for x, char in enumerate(list(line)):
                if 0 in [x, y] or char == "#":
                    # outer wall
                    self.cells[x][y] = True


class GameCell:
    """A single dungeon cell"""

    def __init__(self):
        self.kind = VOID
        self.entities = set()
        self.room_id = None
        self.feature = None
        # a debug value
        self.value = None

    def add_entity(self, entity):
        self.entities.add(entity.eid)

    def remove_entity(self, entity):
        self.entities.remove(entity.eid)

    def remove_entity_by_id(self, entity_id):
        self.entities.remove(entity_id)

    def has_entities(self):
        return bool(len(self.entities))

    @property
    def walkable(self):
        return self.kind in WALKABLE

    @property
    def blocking(self):
        return self.kind in BLOCKING

    def __repr__(self):
        return "<GameCell(kind=%r, entities=%r, room_id=%r, feature=%r)>" % (
            self.kind,
            self.entities,
            self.room_id,
            self.feature,
        )


class GameMap:
    """The dungeon"""

    def __init__(self, width, height, min_room_width=6, min_room_height=6):
        self.width = width
        self.height = height
        self.min_room_width = min_room_width
        self.min_room_height = min_room_height

        self.cells = [[GameCell() for y in range(self.height)] for x in range(self.width)]
        self.rooms = OrderedDict()
        self.start_vec = None
        self.end_vec = None
        self.start_room_id = None
        self.end_room_id = None
        # tunnel_id is just used to debug corridors
        self._tunnel_id = 0

    def generate(self, level, entity_manager):
        raise NotImplementedError

    def describe(self):
        """Describe a Game Map"""

        logger.info("Map dimension: %dx%d", self.width, self.height)
        logger.info("Rooms count: %d", len(self.rooms))

        biggest_room = None
        for room in self.rooms.values():
            if biggest_room is None:
                biggest_room = room
            else:
                if room.width > biggest_room.width and room.height > biggest_room.height:
                    biggest_room = room

        logger.info("The biggest room is %dx%d", biggest_room.width, biggest_room.height)

    def _connect_rooms(self, room1, room2):
        """Connects two rooms with a corridor"""

        start = room1.center
        end = room2.center

        # assign and increment the tunnel ID
        v = self._tunnel_id
        self._tunnel_id += 1

        if random.random() < 0.5:
            self._create_horizontal_tunnel(start.x, end.x, start.y, v)
            self._create_vertical_tunnel(start.y, end.y, end.x, v)
        else:
            self._create_vertical_tunnel(start.y, end.y, start.x, v)
            self._create_horizontal_tunnel(start.x, end.x, end.y, v)

    def _create_horizontal_tunnel(self, x1, x2, y, v=None):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self._create_tunnel(x, y, v)

    def _create_vertical_tunnel(self, y1, y2, x, v=None):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self._create_tunnel(x, y, v)

    def _create_tunnel(self, x, y, value=None):
        """Create a single corridor tile and perform some checks"""

        # if this tunnel touches a room, tell it that it is connected now
        room_id = self.cells[x][y].room_id
        if room_id:
            self.rooms[room_id].connected = True

        self.cells[x][y].kind = CORRIDOR

        # set up DEBUG value (the string representation of the tunnel ID)
        if value is not None:
            self.cells[x][y].value = str(value)

        # fill cells around this corridor cell if they are void
        for c in [cell for cell in self.get_cells_around(x, y) if cell.kind == VOID]:
            c.kind = WALL

    def _cancel_room(self, room):
        """Remove a room from the map. Used by BSP.

        To avoid deleting pieces of other rooms or corridors don't delete
        the outer walls of this room."""

        for y in range(room.y + 1, room.endY - 1):
            for x in range(room.x + 1, room.endX - 1):
                self.cells[x][y].kind = VOID
                self.cells[x][y].room_id = None
        del self.rooms[room.rid]

    def _place_creatures_in_rooms(self, level, entity_manager):
        rooms = [room for room in self.rooms.values() if room.rid != self.start_room_id]
        floors_data = gamedata.get("floors")
        # floors arrays starts from 0, levels starts from 1.
        this_floor = floors_data[level-1]

        for creature_name, amount in this_floor["monsters"].items():
            for _ in range(amount):
                for j in range(5):
                    # retries 5 times
                    room = random.choice(rooms)
                    # if more than 4 enemies in the room, skip it and remove it from the pool
                    if len(self.get_entities_in_room(room.rid)) > 4:
                        rooms.remove(room)
                        continue
                    pos = Vector2.random(room.x + 1, room.endX - 2, room.y + 1, room.endY - 2)
                    cell = self.get_at(pos)
                    if not cell.walkable or cell.has_entities():
                        continue
                    entity = entity_manager.create_entity(creature_name)
                    self.move_entity(entity, pos)
                    break

    def _place_items_in_rooms(self, entity_manager):
        pos = self.start_vec.copy()
        pos.x += 1
        potion = entity_manager.create_potion(PotionType.HEALTH)
        self.move_entity(potion, pos)

    def _select_start_and_end(self, entity_manager):
        """Place stairs up and stairs down.

        NOTE: the current algorithm will pick up the "end room" between the 3 rooms with the
        most distance from the start room.
        """

        rooms = list(self.rooms.values())
        if self.start_room_id is None:
            start_room = random.choice(rooms)
        else:
            start_room = self.get_room(self.start_room_id)
        rooms.remove(start_room)

        # for each remaining room calculate the distance from the starting room
        distances = [(start_room.center.distance(room.center), room) for room in rooms]

        # pick a random rom between the 3 more far from the starting room
        distances.sort(key=lambda x: x[0])
        end_room = random.choice([x[1] for x in distances[-3:]])

        logger.debug("Start room: %r", start_room)
        logger.debug("End room: %r", end_room)

        self.start_room_id = start_room.rid
        self.end_room_id = end_room.rid

        self.start_vec = start_room.center
        self._place_stairs(self.start_vec, "stairs_up", entity_manager)

        self.end_vec = end_room.center
        self._place_stairs(self.end_vec, "stairs_down", entity_manager)

    def _place_stairs(self, pos, kind, entity_manager):
        entity = entity_manager.create_entity(kind)
        self.move_entity(entity, pos)

    def _put_wall_for_room(self, x, y, room):
        if self.cells[x][y].kind == VOID:
            self.cells[x][y].kind = WALL
        self.cells[x][y].room_id = room.rid

    def _dig_room(self, room):
        # room outer walls (y) - do not overwrite existing tunnel tho!
        for y in range(room.y, room.endY):
            self._put_wall_for_room(room.x, y, room)
            self._put_wall_for_room(room.endX - 1, y, room)

        # room outer walls (x)
        for x in range(room.x, room.endX):
            self._put_wall_for_room(x, room.y, room)
            self._put_wall_for_room(x, room.endY - 1, room)

        # room interior
        for y in range(room.y + 1, room.endY - 1):
            for x in range(room.x + 1, room.endX - 1):
                # detect when a room is digged over an existing corridor.
                if self.cells[x][y].kind == CORRIDOR:
                    room.connected = True
                self.cells[x][y].kind = ROOM
                self.cells[x][y].room_id = room.rid

    def _tag_rooms(self):
        """Set the kind of each room cell to ROOM"""

        for room in self.rooms.values():
            for y in range(room.y + 1, room.endY - 1):
                for x in range(room.x + 1, room.endX - 1):
                    if self.cells[x][y].kind not in (ROOM, WALL):
                        self.cells[x][y].kind = ROOM

    def _add_features(self):
        frequency = 8.0
        fx = self.width / frequency
        fy = self.height / frequency

        # thresholds
        # t1 = 0.2
        # t2 = 0.4
        # t3 = 0.5
        t1 = random.uniform(0.2, 0.4)
        t2 = t1 + random.uniform(0.1, 0.2)
        t3 = t2 + 0.1

        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if not self.cells[x][y].walkable:
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
            self._place_doors_axis(room, entity_manager, "x")
            self._place_doors_axis(room, entity_manager, "y")

    def _place_doors_axis(self, room, entity_manager, axis):
        """Place doors on walls

        Inspect the sides of a room (either on the X or the Y axis) and try to place a door on each
        corridor cell found, but only when it's surrounded by walls and not in a corner.
        """
        if axis == "x":
            wall_start = room.x + 1
            wall_end = room.endX - 1
            sides = (room.y, room.endY - 1)
            # for a door on the X axis walls must be on the left and right sides.
            directions = (Direction.EAST, Direction.WEST)
        else:
            wall_start = room.y + 1
            wall_end = room.endY - 1
            sides = (room.x, room.endX - 1)
            # for a door on the Y axis walls must be on the top and bottom sides.
            directions = (Direction.NORTH, Direction.SOUTH)

        for v in range(wall_start, wall_end):
            for i in sides:
                if axis == "x":
                    pos = Vector2(v, i)
                else:
                    pos = Vector2(i, v)
                cell = self.get_at(pos)
                if cell.kind != CORRIDOR:
                    continue

                cell_one = self.get_at(pos + directions[0])
                cell_two = self.get_at(pos + directions[1])
                if cell_one.kind == WALL and cell_two.kind == WALL:
                    self._maybe_place_door(entity_manager, pos)

    def _place_outer_walls(self):
        for x in range(self.width):
            self.cells[x][0].kind = WALL
            self.cells[x][self.height - 1].kind = WALL

        for y in range(self.height):
            self.cells[0][y].kind = WALL
            self.cells[self.width - 1][y].kind = WALL

    def _maybe_place_door(self, entity_manager, pos):
        # check adjacent cells for already existing corridors
        for d in Direction.cardinal():
            a_cell = self.get_at(pos + d)
            for entity_id in a_cell.entities:
                entity = entity_manager.get_entity(entity_id)
                if entity.name == "door":
                    return

        if random.random() > 0.3:
            door = entity_manager.create_entity("door")
            self.move_entity(door, pos)

    def move_entity(self, entity, pos):
        if entity.position is not None:
            old_cell = self.get_at(entity.position)
            if entity.eid in old_cell.entities:
                old_cell.remove_entity(entity)
        cell = self.get_at(pos)
        cell.add_entity(entity)
        entity.set_position(pos)

    def get_at(self, x_or_pos, y=None):
        if y is None and isinstance(x_or_pos, Vector2):
            if 0 <= x_or_pos.x < self.width and 0 <= x_or_pos.y < self.height:
                return self.cells[x_or_pos.x][x_or_pos.y]
            return None
        if 0 <= x_or_pos < self.width and 0 <= y < self.height:
            return self.cells[x_or_pos][y]
        return None

    def get_cells_around(self, x, y):
        """Get cells around x, y, EXCEPT x,y!"""

        cells = []
        center = Vector2(x, y)
        for d in Direction.all():
            dest = center + d
            if 0 <= dest.x < self.width and 0 <= dest.y < self.height:
                cells.append(self.get_at(dest))
        return cells

    def get_room(self, room_id):
        return self.rooms[room_id]

    def get_entities_in_room(self, room_id):
        """Get all the entities ID for the entities in a room"""

        room = self.get_room(room_id)
        result = []
        for x in range(room.x, room.endX):
            for y in range(room.y, room.endY):
                cell = self.get_at(x, y)
                result.extend(cell.entities)
        return result
