import tcod.bsp
from ..gamemap import GameMap, create_room_inside
from ..utils import Rect, tcod_random
from .. import ROOM, WALL


class BspGameMap(GameMap):
    """Pretty standard BSP based dungeon generation"""
    def __init__(self, *args, **kwargs):
        super(BspGameMap, self).__init__(*args, **kwargs)
        self.depth = 7

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

        for room in list(self.rooms.values()):
            if room.intersect(n1):
                room_a = room
                break

        for room in list(self.rooms.values()):
            if room.intersect(n2) and room != room_a:
                room_b = room
                break

        if room_a is None and room_b is None:
            print("both room_a and room_b are None")
            return
        elif room_a is None and room_b:
            print("room_a is None, room_b is OK")
            return
        elif room_a and room_b is None:
            print("room_a is OK, room_b is None")
            return
        elif node1.level != node2.level:
            print("node1 and node2 are different levels!")
            return

        self._connect_rooms(room_a, room_b)
        self.rooms[room_a.rid].connected = True
        self.rooms[room_b.rid].connected = True

    # NOTES:
    # if we store a rect for each room and then in connect_nodes() we create a new Rect for both
    # rooms and then we use Rect.intersect() to find the matching room.
    def generate(self, level, entity_manager):
        # place outer walls
        for x in range(self.width):
            self.cells[x][0].kind = WALL
            self.cells[x][self.height-1].kind = WALL

        for y in range(self.height):
            self.cells[0][y].kind = WALL
            self.cells[self.width-1][y].kind = WALL

        # split game map with BSP
        bsp = tcod.bsp.BSP(x=1, y=1, width=self.width-2, height=self.height-2)
        bsp.split_recursive(depth=self.depth, min_width=self.min_room_width + 1,
                            min_height=self.min_room_height + 1, max_horizontal_ratio=1.5,
                            max_vertical_ratio=1.5, seed=tcod_random.rng)

        # traverse all the nodes to place rooms and connect them
        self._traverse(bsp)

        # we're lazy and we just delete unconnected rooms
        unconnected_rooms = [room for room in list(self.rooms.values()) if not room.connected]
        print("%d unconnected rooms" % len(unconnected_rooms))
        for room in unconnected_rooms:
            self._cancel_room(room)

        # Convert 'tunnel' blocks inside rooms into room blocks
        for room in list(self.rooms.values()):
            for y in range(room.y+1, room.endY-1):
                for x in range(room.x+1, room.endX-1):
                    self.cells[x][y].kind = ROOM

        # select starting and ending rooms
        self._select_start_and_end(entity_manager)
        self._place_creatures_in_rooms(level, entity_manager)
        self._place_doors(entity_manager)
        self._add_features()
        self._place_items_in_rooms(entity_manager)
