import time
import random
from optparse import OptionParser
import tdl
from pyro.gamemap import GameMap, WALL, FLOOR, World


SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50


class Player(object):
    def __init__(self):
        self.x = 0
        self.y = 0


class Game(object):
    def __init__(self, seed):
        self.seed = seed
        self.root = None
        self.console = None
        self.player = Player()
        self.game_width = 80
        self.game_height = 50
        self.world = None
        self.game_map = None

        self.init_random()

    def init_random(self):
        random.seed(self.seed)

    def init_game(self):
        # https://github.com/HexDecimal/python-tdl/tree/master/fonts/libtcod
        tdl.set_font('arial10x10.png', greyscale=True, altLayout=True)
        self.root = tdl.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="PyRo", fullscreen=False)
        self.console = tdl.Console(SCREEN_WIDTH, SCREEN_HEIGHT)
        tdl.setFPS(20)

        self.world = World()
        self.world.create_map(self.game_width, self.game_height, 1)

        self.player.x = SCREEN_WIDTH // 2
        self.player.y = SCREEN_HEIGHT // 2        

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
                    self.console.draw_char(x, y, '#', bg=None, fg=(255, 255, 255))
                else:
                    self.console.draw_char(x, y, '.', bg=None, fg=(255, 255, 255))

                for eid in cell.entities:
                    entity = self.world.entity_manager.get_entity(eid)
                    self.console.draw_char(x, y, entity.avatar, bg=None, fg=entity.color)

        self.console.draw_char(self.player.x, self.player.y, '@', bg=None, fg=(255, 255, 255))
        self.root.blit(self.console, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0)

    def handle_keys(self):
        user_input = tdl.event.key_wait()

        if user_input.key == 'UP':
            self.player.y -= 1
        elif user_input.key == 'DOWN':
            self.player.y += 1
        elif user_input.key == 'LEFT':
            self.player.x -= 1
        elif user_input.key == 'RIGHT':
            self.player.x += 1
        elif user_input.key == 'ESCAPE':
            return True


def main():
    parser = OptionParser()
    parser.add_option('--seed', '-s')
    opts, args = parser.parse_args()
    if opts.seed is None:
        seed = int(time.time())
    else:
        seed = opts.seed

    game = Game(seed)
    game.init_game()
    game.game_loop()


if __name__ == '__main__':
    main()
