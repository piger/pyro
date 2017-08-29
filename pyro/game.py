import random
import tdl
import tcod.map
from pyro.gamemap import WALL, ROOM, CORRIDOR, VOID, FLOOR, World
from pyro.math import NORTH, SOUTH, EAST, WEST
from pyro.utils import tcod_random


SCREEN_WIDTH = 80
SCREEN_HEIGHT = 60

COLOR_FLOOR = (79, 79, 79)
COLOR_WALL = (110, 110, 110)
COLOR_ROOM = (46, 46, 46)
COLOR_CORRIDOR = (238, 229, 222)
COLOR_PLAYER = (250, 128, 114)


# https://stackoverflow.com/questions/6615002/given-an-rgb-value-how-do-i-create-a-tint-or-shade
def darken_color(color, amount=0.50):
    red = int(color[0] * amount)
    green = int(color[1] * amount)
    blue = int(color[2] * amount)
    return (red, green, blue)


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
    def __init__(self, seed, game_width, game_height, font):
        self.seed = seed
        self.game_width = game_width
        self.game_height = game_height
        self.DEBUG = False
        self.font = font

        self.root = None
        self.console = None
        self.player = None
        self.world = None
        self.game_map = None
        self.camera = None
        self.fov_map = None
        self.visited = None

        self.init_random()

    def init_random(self):
        print "SEED = %r" % self.seed
        random.seed(self.seed)
        tcod_random.init(self.seed)

    def init_game(self):
        # https://github.com/HexDecimal/python-tdl/tree/master/fonts/libtcod
        tdl.set_font(self.font, greyscale=True, altLayout=True)
        self.root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="PyRo", fullscreen=False)
        self.console = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.world = World()
        self.world.create_map(self.game_width, self.game_height, 1)
        cur_map = self.world.get_current_map()

        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

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

        self.console.clear()
        player_pos = self.player.get_position()
        self.camera.center_on(player_pos.x, player_pos.y)

        for y in xrange(self.game_height):
            for x in range(self.game_width):
                # from camera coordinates to game world coordinates
                xx = x - self.camera.x
                yy = y - self.camera.y

                if xx < 0 or xx >= self.game_width or yy < 0 or yy >= self.game_height:
                    continue

                bg_color = None

                # do not print if not on FOV
                is_visible = self.fov_map.fov[y,x]
                is_visited = self.visited[x][y]
                has_fog_of_war = not is_visible and is_visited

                if not is_visible and not is_visited:
                    continue
                elif is_visible and not is_visited:
                    # mark visible cells as visited
                    self.visited[x][y] = True

                cell = game_map.get_at(x, y)
                if cell.kind == WALL:
                    if has_fog_of_war:
                        color = darken_color(COLOR_WALL)
                    else:
                        color = COLOR_WALL
                    self.console.draw_char(xx, yy, '#', bg=bg_color, fg=color)
                elif cell.kind == VOID:
                    self.console.draw_char(xx, yy, ' ', bg=None, fg=(0, 0, 0))
                elif cell.kind == ROOM or cell.kind == FLOOR:
                    if has_fog_of_war:
                        color = darken_color(COLOR_FLOOR)
                    else:
                        color = COLOR_FLOOR
                    self.console.draw_char(xx, yy, '.', bg=bg_color, fg=color)
                elif cell.kind == CORRIDOR:
                    if has_fog_of_war:
                        color = darken_color(COLOR_CORRIDOR)
                    else:
                        color = COLOR_CORRIDOR
                    self.console.draw_char(xx, yy, '=', bg=bg_color, fg=color)
                else:
                    print "unknown cell kind %r" % cell

                # do not paint entities if they are not visibles.
                # TODO: we must still paint items! or at least stairs!
                for eid in cell.entities:
                    entity = self.world.entity_manager.get_entity(eid)
                    if is_visible or entity.always_visible:
                        self.console.draw_char(xx, yy, entity.avatar, bg=None, fg=entity.color)

        self.console.draw_char(player_pos.x - self.camera.x, player_pos.y - self.camera.y, '@',
                               bg=None, fg=COLOR_PLAYER)
        self.root.blit(self.console, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)

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

    def game_loop(self):
        """Game loop, 1 frame for keypress"""

        assert self.world is not None

        while not tdl.event.is_window_closed():
            self.render_all()
            tdl.flush()

            exit_game = self.handle_keys()
            if exit_game:
                break

    def handle_keys(self):
        # this is for turn based rendering!
        user_input = tdl.event.key_wait()

        player_pos = self.player.get_position()

        if user_input.key == 'ESCAPE':
            return True
        elif user_input.key == 'UP':
            direction = NORTH
        elif user_input.key == 'DOWN':
           direction = SOUTH
        elif user_input.key == 'LEFT':
            direction = WEST
        elif user_input.key == 'RIGHT':
            direction = EAST
        else:
            direction = None

        if direction is not None:
            dest_vec = player_pos + direction
            can = self.attempt_move(dest_vec)
            if can:
                self.player.set_position(dest_vec.x, dest_vec.y)
                self.fov_map.compute_fov(dest_vec.x, dest_vec.y, radius=6)
                # self.set_visited_room(dest_vec.x, dest_vec.y)
                self.visited[dest_vec.x][dest_vec.y] = True
