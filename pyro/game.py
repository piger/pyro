import random
import tdl
from pyro.utils import tcod_random
from pyro.gamedata import gamedata
from pyro.dungeon_scene import DungeonScene
from pyro.scene import StartScreen


class Game(object):
    def __init__(self, seed, game_width, game_height, font, screen_width, screen_height):
        self.seed = seed
        self.game_width = game_width
        self.game_height = game_height
        self.DEBUG = False
        self.font = font
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.running = True
        self.current_scene = None
        self.next_scene = None
        self.scenes = {}

        self.root = None
        self.init_random()

    def init_random(self):
        print("SEED = %r" % self.seed)
        random.seed(self.seed)
        tcod_random.init(self.seed)

    def init_game(self):
        # Other fonts: https://github.com/HexDecimal/python-tdl/tree/master/fonts/libtcod
        tdl.set_font(self.font, columns=16, rows=16, greyscale=True, altLayout=False)
        self.root = tdl.init(self.screen_width, self.screen_height, title="PyRo", fullscreen=False)
        tdl.set_fps(20)

        # load game data
        gamedata.load()

        self.current_scene = StartScreen()
        self.current_scene.setup(self)

    def change_scene(self):
        new_scene_name = self.next_scene
        self.next_scene = None

        if new_scene_name in self.scenes:
            self.current_scene = self.scenes[new_scene_name]
        elif new_scene_name == 'dungeon':
            self.current_scene = DungeonScene()
            self.current_scene.setup(self)
        elif new_scene_name == 'quit':
            self.running = False

    def game_loop(self):
        while self.running:
            updated = False

            for event in tdl.event.get():
                if event.type == 'KEYDOWN':
                    self.current_scene.keydown_event(event, self)
                    self.current_scene.update(self)
                    if self.next_scene:
                        self.change_scene()
                    updated = True
                    break
                elif event.type == 'QUIT':
                    self.running = False
                    break

            if not updated and self.running:
                self.current_scene.update(self)
