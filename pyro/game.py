import random
import tdl
from pyro.gamemap import WALL, World


SCREEN_WIDTH = 80
SCREEN_HEIGHT = 60
FONT = 'consolas10x10_gs_tc.png'

COLOR_FLOOR = (79, 79, 79)
COLOR_WALL = (205, 133, 63)


class Game(object):
    def __init__(self, seed, game_width=SCREEN_WIDTH, game_height=SCREEN_HEIGHT):
        self.seed = seed
        self.game_width = game_width
        self.game_height = game_height

        self.root = None
        self.console = None
        self.player = None
        self.world = None
        self.game_map = None

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

        self.player = self.world.entity_manager.create_entity('player')
        self.player.set_position(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    def game_loop(self):
        while not tdl.event.is_window_closed():
            self.render_all()
            tdl.flush()

            exit_game = self.handle_keys()
            if exit_game:
                break

    def render_all(self):
        game_map = self.world.get_current_map()

        for y in xrange(self.game_height):
            for x in range(self.game_width):
                cell = game_map.get_at(x, y)
                if cell.kind == WALL:
                    self.console.draw_char(x, y, '#', bg=None, fg=COLOR_WALL)
                else:
                    self.console.draw_char(x, y, '.', bg=None, fg=COLOR_FLOOR)

                for eid in cell.entities:
                    entity = self.world.entity_manager.get_entity(eid)
                    self.console.draw_char(x, y, entity.avatar, bg=None, fg=entity.color)

        player_pos = self.player.get_position()
        self.console.draw_char(player_pos.x, player_pos.y, '@', bg=None, fg=(255, 255, 255))
        self.root.blit(self.console, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)

    def handle_keys(self):
        user_input = tdl.event.key_wait()

        player_pos = self.player.get_position()
        if user_input.key == 'UP':
            player_pos.y -= 1
        elif user_input.key == 'DOWN':
            player_pos.y += 1
        elif user_input.key == 'LEFT':
            player_pos.x -= 1
        elif user_input.key == 'RIGHT':
            player_pos.x += 1
        elif user_input.key == 'ESCAPE':
            return True
