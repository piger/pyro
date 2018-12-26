from .diggers.bsp import BspGameMap
from .diggers.tunnel import TunnelingGameMap
from .entities import EntityManager


class World:
    def __init__(self):
        self.maps = []
        self.current_map = 0
        self.entity_manager = EntityManager()

    def create_map(self, width, height, level=1, dungeon_algorithm=None):
        if dungeon_algorithm in (None, "bsp"):
            MapClass = BspGameMap
        else:
            MapClass = TunnelingGameMap

        game_map = MapClass(width, height)
        game_map.generate(level, self.entity_manager)
        game_map.describe()

        self.maps.append(game_map)

    def get_current_map(self):
        return self.maps[self.current_map]

    def destroy_entity(self, eid):
        cur_map = self.get_current_map()
        entity = self.entity_manager.get_entity(eid)
        cell = cur_map.get_at(entity.get_position())
        if eid not in cell.entities:
            print("Entity %r not in cell %r" % (entity, cell))
        else:
            cell.remove_entity(entity)

        self.entity_manager.destroy_entity(eid)
