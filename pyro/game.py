import random
import tdl
from pyro.gamemap import WALL, ROOM, CORRIDOR, World
from pyro.math import NORTH, SOUTH, EAST, WEST


SCREEN_WIDTH = 80
SCREEN_HEIGHT = 60
FONT = 'consolas10x10_gs_tc.png'

COLOR_FLOOR = (79, 79, 79)
COLOR_WALL = (205, 133, 63)
COLOR_ROOM = (255, 211, 155)


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

        self.init_random()

    def init_random(self):
        random.seed(self.seed)

    def init_game(self):
        # https://github.com/HexDecimal/python-tdl/tree/master/fonts/libtcod
        tdl.set_font(FONT, greyscale=True, altLayout=True)
        self.root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="PyRo", fullscreen=False)
        self.console = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
        # tdl.setFPS(20)

        self.world = World()
        self.world.create_map(self.game_width, self.game_height, 1)

        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.player = self.world.entity_manager.create_entity('player')
        self.player.set_position(self.game_width / 2, self.game_height / 2)

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
                cell = game_map.get_at(x, y)
                if cell.kind == WALL:
                    self.console.draw_char(xx, yy, '#', bg=None, fg=COLOR_WALL)
                elif cell.kind == ROOM:
                    self.console.draw_char(xx, yy, '*', bg=None, fg=COLOR_ROOM)
                elif cell.kind == CORRIDOR:
                    self.console.draw_char(xx, yy, '=', bg=None, fg=COLOR_ROOM)
                else:
                    self.console.draw_char(xx, yy, '.', bg=None, fg=COLOR_FLOOR)

                for eid in cell.entities:
                    entity = self.world.entity_manager.get_entity(eid)
                    self.console.draw_char(xx, yy, entity.avatar, bg=None, fg=entity.color)

        self.console.draw_char(player_pos.x - self.camera.x, player_pos.y - self.camera.y, '@', bg=None, fg=(255, 255, 255))
        self.root.blit(self.console, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)

    def attempt_move(self, dest_vec):
        game_map = self.world.get_current_map()
        dcell = game_map.get_at(dest_vec.x, dest_vec.y)
        if not dcell.entities:
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
