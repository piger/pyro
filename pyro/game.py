import random
import tdl
import tcod.map
from pyro.gamemap import WALL, ROOM, CORRIDOR, VOID, FLOOR, World
from pyro.math import NORTH, SOUTH, EAST, WEST


SCREEN_WIDTH = 80
SCREEN_HEIGHT = 60
FONT = 'consolas10x10_gs_tc.png'

COLOR_FLOOR = (79, 79, 79)
COLOR_WALL = (110, 110, 110)
COLOR_ROOM = (46, 46, 46)
COLOR_CORRIDOR = (238, 229, 222)


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
    def __init__(self, seed, game_width=SCREEN_WIDTH, game_height=SCREEN_HEIGHT):
        self.seed = seed
        self.game_width = game_width
        self.game_height = game_height
        self.DEBUG = False

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

    def init_game(self):
        # https://github.com/HexDecimal/python-tdl/tree/master/fonts/libtcod
        tdl.set_font(FONT, greyscale=True, altLayout=True)
        self.root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="PyRo", fullscreen=False)
        self.console = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
        # tdl.setFPS(20)

        self.world = World()
        self.world.create_map(self.game_width, self.game_height, 1)
        cur_map = self.world.get_current_map()

        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        fov_map = tcod.map.Map(width=self.game_width, height=self.game_height)
        for y in xrange(self.game_height):
            for x in xrange(self.game_width):
                cell = cur_map.get_at(x, y)
                if cell.kind in (FLOOR, ROOM, CORRIDOR):
                    fov_map.walkable[y,x] = True
                    fov_map.transparent[y,x] = True
        self.fov_map = fov_map

        self.player = self.world.entity_manager.create_entity('player')
        self.player.set_position(cur_map.start_vec.x, cur_map.start_vec.y)
        self.fov_map.compute_fov(cur_map.start_vec.x, cur_map.start_vec.y, radius=6)

        self.init_visited()

    def init_visited(self):
        cur_map = self.world.get_current_map()
        self.visited = [[False for y in xrange(self.game_height)] for x in xrange(self.game_width)]
        start_cell = cur_map.get_at(cur_map.start_vec.x, cur_map.start_vec.y)
        start_room = cur_map.get_room(start_cell.room_id)

        for y in xrange(start_room.y, start_room.y + start_room.height):
            for x in xrange(start_room.x, start_room.x + start_room.width):
                self.visited[x][y] = True

    def game_loop(self):
        assert self.world is not None

        while not tdl.event.is_window_closed():
            self.render_all()
            tdl.flush()

            exit_game = self.handle_keys()
            if exit_game:
                break

    def render_all(self):
        game_map = self.world.get_current_map()

        self.console.clear()
        player_pos = self.player.get_position()
        self.camera.center_on(player_pos.x, player_pos.y)

        for y in xrange(self.game_height):
            for x in range(self.game_width):
                xx = x - self.camera.x
                yy = y - self.camera.y
                if xx < 0:
                    continue
                if xx >= self.game_width:
                    continue
                if yy < 0:
                    continue
                if yy >= self.game_height:
                    continue

                bg_color = None

                # do not print if not on FOV
                is_visible = self.fov_map.fov[y,x]
                is_visited = self.visited[x][y]

                if not is_visible and not is_visited:
                    continue
                elif not is_visible and is_visited:
                    # gray out visited but not currently visible cells
                    bg_color = (20, 20, 20)
                elif is_visible and not is_visited:
                    # mark visible cells as visited
                    self.visited[x][y] = True

                cell = game_map.get_at(x, y)
                if cell.kind == WALL:
                    self.console.draw_char(xx, yy, '#', bg=bg_color, fg=COLOR_WALL)
                elif cell.kind == VOID:
                    self.console.draw_char(xx, yy, ' ', bg=None, fg=(0, 0, 0))
                elif cell.kind == ROOM or cell.kind == FLOOR:
                    self.console.draw_char(xx, yy, '.', bg=bg_color, fg=COLOR_FLOOR)
                elif cell.kind == CORRIDOR:
                    self.console.draw_char(xx, yy, '=', bg=bg_color, fg=COLOR_CORRIDOR)
                else:
                    print "unknown cell kind %r" % cell

                for eid in cell.entities:
                    entity = self.world.entity_manager.get_entity(eid)
                    self.console.draw_char(xx, yy, entity.avatar, bg=None, fg=entity.color)

        self.console.draw_char(player_pos.x - self.camera.x, player_pos.y - self.camera.y, '@', bg=None, fg=(255, 255, 255))
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
