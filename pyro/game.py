import random
import tdl
import tcod.map
from pyro.gamemap import WALL, ROOM, CORRIDOR, VOID, FLOOR, World
from pyro.math import (NORTH, SOUTH, EAST, WEST, NORTH_EAST, NORTH_WEST,
                       SOUTH_EAST, SOUTH_WEST)
from pyro.utils import tcod_random, darken_color
from pyro.gamedata import gamedata


SYMBOLS = {
    'FLOOR': {
        'symbol': '.',
        'color': (79, 79, 79),
    },
    'WALL': {
        'symbol': '#',
        'color': (110, 110, 110),
    },
    'ROOM': {
        'symbol': '.',
        'color': (46, 46, 46),
    },
    'CORRIDOR': {
        'symbol': '.',
        # 'color': (238, 229, 222),
        'color': (79, 79, 79),
    },
    'VOID': {
        'symbol': ' ',
        'color': (0, 0, 0),
    },
    'PLAYER': {
        'symbol': '@',
        'color': (250, 128, 114),
    },
}

DARK_BACKGROUND = (8, 8, 8)


class Camera(object):
    def __init__(self, width, height):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height

    def center_on(self, x, y):
        self.x = x - (self.width / 2)
        self.y = y - (self.height / 2)

    def __repr__(self):
        return "Camera(x=%d, y=%d, w=%d, h=%d)" % (self.x, self.y, self.width, self.height)


class Game(object):
    def __init__(self, seed, game_width, game_height, font, screen_width, screen_height):
        self.seed = seed
        self.game_width = game_width
        self.game_height = game_height
        self.DEBUG = False
        self.font = font
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.fov_radius = 6

        self.root = None
        self.console = None
        self.player = None
        self.world = None
        self.game_map = None
        self.camera = None
        self.fov_map = None
        self.visited = None
        self.enemies_turn = False

        self.is_looking = False
        self.eye_position = None

        # devel options
        self.dungeon_algorithm = None

        self.init_random()

    def init_random(self):
        print "SEED = %r" % self.seed
        random.seed(self.seed)
        tcod_random.init(self.seed)

    def init_game(self):
        # https://github.com/HexDecimal/python-tdl/tree/master/fonts/libtcod
        tdl.set_font(self.font, greyscale=True, altLayout=True)
        self.root = tdl.init(self.screen_width, self.screen_height, title="PyRo", fullscreen=False)
        tdl.set_fps(30)
        self.console = tdl.Console(self.screen_width, self.screen_height)

        # load game data
        gamedata.load()

        self.world = World()
        self.world.create_map(self.game_width, self.game_height, level=1,
                              dungeon_algorithm=self.dungeon_algorithm)
        cur_map = self.world.get_current_map()

        self.camera = Camera(self.screen_width, self.screen_height)

        # setup FOV
        self.init_fov(cur_map)

        # setup player
        self.player = self.world.entity_manager.create_entity('player')
        self.player.set_position(cur_map.start_vec.x, cur_map.start_vec.y)
        self.fov_map.compute_fov(cur_map.start_vec.x, cur_map.start_vec.y, radius=6)

        # setup visited cells
        self.init_visited()

    def init_fov(self, cur_map):
        """Initialize the Field of View handler

        NOTE: fov requires [y,x] addressing!
        """

        fov_map = tcod.map.Map(width=self.game_width, height=self.game_height)
        for y in xrange(self.game_height):
            for x in xrange(self.game_width):
                cell = cur_map.get_at(x, y)
                if cell.kind in (FLOOR, ROOM, CORRIDOR):
                    fov_map.walkable[y,x] = True
                    fov_map.transparent[y,x] = True
        self.fov_map = fov_map

    def init_visited(self):
        cur_map = self.world.get_current_map()
        self.visited = [[False for y in xrange(self.game_height)] for x in xrange(self.game_width)]
        start_cell = cur_map.get_at(cur_map.start_vec.x, cur_map.start_vec.y)
        start_room = cur_map.get_room(start_cell.room_id)

        for y in xrange(start_room.y, start_room.y + start_room.height):
            for x in xrange(start_room.x, start_room.x + start_room.width):
                self.visited[x][y] = True

    def render_all(self):
        game_map = self.world.get_current_map()

        self.console.clear(bg=DARK_BACKGROUND)
        player_pos = self.player.get_position()
        self.camera.center_on(player_pos.x, player_pos.y)

        for y in xrange(self.game_height):
            for x in range(self.game_width):
                # from camera coordinates to game world coordinates
                xx = x - self.camera.x
                yy = y - self.camera.y

                # skip rendering of cells out of the camera view
                if xx < 0 or xx >= self.game_width or yy < 0 or yy >= self.game_height:
                    continue

                if self.is_looking and x == self.eye_position.x and y == self.eye_position.y:
                    bg_color = (194, 194, 194)
                else:
                    bg_color = DARK_BACKGROUND

                # do not print if not on FOV
                is_visible = self.fov_map.fov[y,x]
                is_visited = self.visited[x][y]
                has_fog_of_war = not is_visible and is_visited

                if not is_visible and not is_visited:
                    if self.is_looking:
                        self.console.draw_char(xx, yy, ' ', bg=bg_color, fg=(0, 0, 0))
                    if not self.DEBUG:
                        continue
                elif is_visible and not is_visited:
                    # mark visible cells as visited
                    self.visited[x][y] = True

                cell = game_map.get_at(x, y)
                if cell.kind == WALL:
                    symbol = SYMBOLS['WALL']
                elif cell.kind == VOID:
                    symbol = SYMBOLS['VOID']
                elif cell.kind == ROOM or cell.kind == FLOOR:
                    symbol = SYMBOLS['FLOOR']
                elif cell.kind == CORRIDOR:
                    symbol = SYMBOLS['CORRIDOR']
                else:
                    print "unknown cell kind %r" % cell

                if has_fog_of_war:
                    color = darken_color(symbol['color'])
                else:
                    color = symbol['color']

                if self.DEBUG and cell.value is not None:
                    char = str(cell.value)
                else:
                    char = symbol['symbol']
                    if cell.kind in (ROOM, FLOOR, CORRIDOR) and cell.feature in ('dirt', 'grass', 'water'):
                        feature = gamedata.get_feature(cell.feature)
                        char = feature['avatar']
                        color = feature['color']
                self.console.draw_char(xx, yy, char, bg=bg_color, fg=color)

                # do not paint entities if they are not visibles.
                # TODO: we must still paint items! or at least stairs!
                for eid in cell.entities:
                    entity = self.world.entity_manager.get_entity(eid)
                    if is_visible or entity.always_visible or self.DEBUG:
                        self.console.draw_char(xx, yy, entity.avatar, bg=None, fg=entity.color)

        self.console.draw_char(player_pos.x - self.camera.x, player_pos.y - self.camera.y,
                               SYMBOLS['PLAYER']['symbol'], bg=None, fg=SYMBOLS['PLAYER']['color'])
        self.root.blit(self.console, 0, 0, self.screen_width, self.screen_height, 0, 0)
        tdl.flush()

    def attempt_move(self, dest_vec):
        game_map = self.world.get_current_map()
        dcell = game_map.get_at(dest_vec.x, dest_vec.y)
        if not dcell.entities and dcell.kind not in (VOID, WALL):
            return True

        em = self.world.entity_manager
        can_fight = []
        for eid in dcell.entities:
            # get entity
            entity = em.get_entity(eid)
            # get combat component, if any
            cc = em.combat_components.get(entity.eid)
            if cc is not None:
                can_fight.append((entity, cc))

        player_cc = em.combat_components.get(self.player.eid)
        player_hc = em.health_components.get(self.player.eid)

        for entity, cc in can_fight:
            print "fight between player and %r (%d/%d)" % (entity.name, cc.damage, cc.armor)
            enemy_hc = em.health_components.get(entity.eid)
            enemy_hc.health -= player_cc.damage
            if enemy_hc.health <= 0:
                print "enemy morto"
                self.world.destroy_entity(entity.eid)
            else:
                player_hc.health -= cc.damage
                if player_hc.health <= 0:
                    print "player morto!"

    def move_enemies(self):
        self.enemies_turn = False

    def game_loop(self):
        """Game loop, 1 frame for keypress"""

        assert self.world is not None

        running = True
        while running:
            self.render_all()
            exit_game = self.handle_events()
            if exit_game:
                running = False
                break

            if self.enemies_turn:
                self.move_enemies()

    def handle_events(self):
        result = False
        for event in tdl.event.get():
            if event.type == 'KEYDOWN':
                result = self.handle_keys(event)
                if result:
                    break

        return result

    def handle_keys(self, user_input):
        direction = None

        if user_input.key == 'ESCAPE':
            return True
        elif user_input.key == 'ENTER':
            if self.is_looking is True:
                self.is_looking = False
            else:
                self.eye_position = self.player.get_position().copy()
                self.is_looking = True
            return
        elif user_input.key == 'UP' or user_input.char == 'k':
            direction = NORTH
        elif user_input.char == 'y':
            direction = NORTH_WEST
        elif user_input.char == 'u':
            direction = NORTH_EAST
        elif user_input.key == 'DOWN' or user_input.char == 'j':
           direction = SOUTH
        elif user_input.key == 'LEFT' or user_input.char == 'h':
            direction = WEST
        elif user_input.key == 'RIGHT' or user_input.char == 'l':
            direction = EAST
        elif user_input.char == 'b':
            direction = SOUTH_WEST
        elif user_input.char == 'n':
            direction = SOUTH_EAST

        if direction is not None:
            if self.is_looking:
                self.move_eye(direction)
            else:
                self.move_player(direction)

    def move_player(self, direction):
        dest_vec = self.player.get_position() + direction
        can = self.attempt_move(dest_vec)
        if can:
            self.player.set_position(dest_vec.x, dest_vec.y)
            self.fov_map.compute_fov(dest_vec.x, dest_vec.y, radius=self.fov_radius,
                                     algorithm=tcod.FOV_DIAMOND)
            self.visited[dest_vec.x][dest_vec.y] = True
            self.enemies_turn = True

    def move_eye(self, direction):
        dest_vec = self.eye_position + direction
        self.eye_position.x = dest_vec.x
        self.eye_position.y = dest_vec.y
