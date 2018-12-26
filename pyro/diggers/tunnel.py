import random
from ..gamemap import GameMap
from .. import WALL, ROOM


class TunnelingGameMap(GameMap):
    """Randomly places rooms into the map and the connected them. Very simple."""

    def generate(self, level, entity_manager):
        max_room_size = 16
        min_room_size = 5
        max_rooms = 30
        weird_done = False
        is_weird = False

        self._place_outer_walls()

        for _ in range(max_rooms):
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
                        if c == "#":
                            self.cells[room.x + x][room.y + y].kind = WALL
                is_weird = False

            if len(self.rooms) > 1:
                last_room = self.rooms.values()[-2]
                self._connect_rooms(room, last_room)
            else:
                self.start_room_id = room.rid

        self._tag_rooms()
        self._select_start_and_end(entity_manager)
        self._place_creatures_in_rooms(level, entity_manager)
        self._place_doors(entity_manager)
        self._add_features()
        self._place_items_in_rooms(entity_manager)
