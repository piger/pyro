import tdl
from enum import Enum
from pyro import SceneId


class Scene(object):
    def __init__(self):
        self.DEBUG = False

    def setup(self, game):
        pass

    def update(self, game):
        pass

    def keydown_event(self, event, game):
        pass


class StartScreen(Scene):
    def __init__(self):
        super(StartScreen, self).__init__()
        self.window = None

    def setup(self, game):
        self.window = tdl.Console(game.screen_width, game.screen_height)

    def keydown_event(self, event, game):
        game.next_scene = 'dungeon'

    def update(self, game):
        self.window.draw_str(0, 0, "pyro!", fg=(255, 255, 255))
        game.root.blit(self.window, 0, 0, game.screen_width, game.screen_height, 0, 0)
        tdl.flush()


class Fizzlefade(Scene):
    """Apply fizzlefade effect and return. Only works for window sizes up to 320x200
    and it's really just for fun.

    Stolen from http://fabiensanglard.net/fizzlefade/index.php
    """
    def __init__(self):
        super(Fizzlefade, self).__init__()
        self.window = None

    def setup(self, game):
        self.window = tdl.Console(game.screen_width, game.screen_height)

    def update(self, game):
        # NOTE: run everything in 1 update call, hijacking tdl.flush() from the game loop

        # copy the root content onto board
        self.window.blit(game.root, 0, 0, game.screen_width, game.screen_height, 0, 0)
        rndval = 1

        running = True
        i = 0

        while running:
            y = rndval & 0x000FF
            x = (rndval & 0x1FF00) >> 8
            lsb = rndval & 1
            rndval >>= 1
            if lsb != 0:
                rndval ^= 0x00012000
            if x < game.screen_width and y < game.screen_height:
                self.window.draw_char(x, y, ' ', fg=(205, 38, 38), bg=(205, 38, 38))
                i += 1
                if i >= 100:
                    i = 0
                    game.root.blit(self.window, 0, 0, game.screen_width, game.screen_height, 0, 0)
                    tdl.flush()

            if rndval == 1:
                running = False
