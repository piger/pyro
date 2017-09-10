import math
import random
import tdl
import tcod.map
import tcod.path
from pyro.gamemap import WALL, ROOM, CORRIDOR, VOID, FLOOR, World
from pyro.utils import tcod_random, darken_color, clamp, Direction, PopupWindow
from pyro.gamedata import gamedata
from pyro.combat import roll_to_hit, chance_to_hit


SYMBOLS = {
    'FLOOR': {
        'symbol': '.',
        'color': (79, 79, 79),
    },
    'WALL': {
        'symbol': 219,
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

MESSAGE_COLOR = (224, 224, 224)
DARK_BACKGROUND = (8, 8, 8)
PANEL_TEXT_COLOR = (224, 224, 224)
POPUP_BACKGROUND = (23, 23, 23)
POPUP_SIZE = (43, 17)


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

        # size of info panel
        self.panel_width = 30
        self.panel_height = self.screen_height / 2

        # size of map area console
        self.display_width = self.screen_width - self.panel_width
        self.display_height = self.screen_height - 1 # -1 for status bar

        # size of message log console
        self.log_width = self.panel_width
        self.log_height = self.screen_height - self.panel_height

        # size of status bar console
        self.status_width = self.display_width
        self.status_height = 1

        self.root = None
        self.console = None
        self.panel = None
        self.logpanel = None
        self.status = None
        self.player = None
        self.world = None
        self.game_map = None
        self.camera = None
        self.fov_map = None
        self.visited = None
        self.enemies_turn = False
        self.player_is_dead = False
        self.info_popup = None

        self.is_looking = False
        self.eye_position = None

        self.message_log = []

        # devel options
        self.dungeon_algorithm = None

        self.init_random()

    def init_random(self):
        print "SEED = %r" % self.seed
        random.seed(self.seed)
        tcod_random.init(self.seed)

    def init_game(self):
        # Other fonts: https://github.com/HexDecimal/python-tdl/tree/master/fonts/libtcod
        tdl.set_font(self.font, columns=16, rows=16, greyscale=True, altLayout=False)
        self.root = tdl.init(self.screen_width, self.screen_height, title="PyRo", fullscreen=False)
        tdl.set_fps(20)

        # setup all the consoles
        # +-------------+---+
        # |A            |B  |  A = console (where you see the actual game)
        # |             |   |  B = info panel
        # |             +---+  C = status bar (for 'look' command)
        # |             |D  |  D = log panel
        # +-------------|   |
        # |C____________|___|

        self.console = tdl.Console(self.display_width, self.display_height)
        self.panel = tdl.Console(self.panel_width, self.panel_height)

        self.logpanel = tdl.Console(self.log_width, self.log_height)
        self.logpanel.clear(bg=DARK_BACKGROUND)
        self.logpanel.set_colors(fg=MESSAGE_COLOR, bg=DARK_BACKGROUND)

        self.status = tdl.Console(self.status_width, self.status_height)

        # the popup must grow and shrink so the size of the console will be the same size as
        # the display (i.e. where we show the map); we'll render the popup based on the size
        # stored in self.info_popup_size.
        self.info_popup = PopupWindow(POPUP_SIZE[0], POPUP_SIZE[1], self.display_width, self.display_height,
                                      PANEL_TEXT_COLOR, POPUP_BACKGROUND)

        # load game data
        gamedata.load()

        # Initialize world and current dungeon
        self.world = World()
        self.world.create_map(self.game_width, self.game_height, level=1,
                              dungeon_algorithm=self.dungeon_algorithm)
        cur_map = self.world.get_current_map()

        self.camera = Camera(self.display_width, self.display_height)

        # setup FOV
        self.init_fov(cur_map)

        # setup player
        self.player = self.world.entity_manager.create_entity('player', cur_map.start_vec)
        self.fov_map.compute_fov(cur_map.start_vec.x, cur_map.start_vec.y, radius=6)
        cell = cur_map.get_at(self.player.position)
        cell.entities.append(self.player.eid)

        # setup visited cells
        self.init_visited()

        # init AI
        for ai in self.world.entity_manager.monster_ai_components.values():
            ai.setup(self)

    def init_fov(self, cur_map):
        """Initialize the Field of View handler

        NOTE: fov requires [y,x] addressing!
        """

        fov_map = tcod.map.Map(width=self.game_width, height=self.game_height)
        for y in xrange(self.game_height):
            for x in xrange(self.game_width):
                cell = cur_map.get_at(x, y)
                if cell.kind in (FLOOR, ROOM, CORRIDOR):
                    fov_map.walkable[y, x] = True
                    fov_map.transparent[y, x] = True
                # doors will block sight
                for entity_id in cell.entities:
                    if entity_id in self.world.entity_manager.door_components:
                        fov_map.transparent[y, x] = False
        self.fov_map = fov_map

    def init_visited(self):
        cur_map = self.world.get_current_map()
        self.visited = [[False for y in xrange(self.game_height)] for x in xrange(self.game_width)]

        # the starting room is always entirely visited.
        start_cell = cur_map.get_at(cur_map.start_vec.x, cur_map.start_vec.y)
        start_room = cur_map.get_room(start_cell.room_id)

        for y in xrange(start_room.y, start_room.y + start_room.height):
            for x in xrange(start_room.x, start_room.x + start_room.width):
                self.visited[x][y] = True

    def render_all(self):
        game_map = self.world.get_current_map()

        self.console.clear(bg=DARK_BACKGROUND)
        self.panel.clear(bg=DARK_BACKGROUND)
        self.status.clear(bg=DARK_BACKGROUND)

        player_pos = self.player.get_position()
        self.camera.center_on(player_pos.x, player_pos.y)

        # Print some stuff into the info panel
        self.panel.draw_str(0, 0, "You, the rogue.", fg=PANEL_TEXT_COLOR)
        self.panel.draw_str(0, 1, "Player position: %d/%d" % (player_pos.x, player_pos.y),
                            fg=PANEL_TEXT_COLOR)

        for y in xrange(self.game_height):
            for x in range(self.game_width):
                # from camera coordinates to game world coordinates
                xx = x - self.camera.x
                yy = y - self.camera.y

                # skip rendering of cells out of the camera view
                if xx < 0 or xx > self.screen_width or yy < 0 or yy > self.screen_height:
                    continue

                if self.is_looking and x == self.eye_position.x and y == self.eye_position.y:
                    bg_color = (194, 194, 194)
                else:
                    bg_color = DARK_BACKGROUND

                # do not print if not on FOV
                is_visible = self.is_visible(x, y)
                is_visited = self.is_visited(x, y)
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
                    if (cell.kind in (ROOM, FLOOR, CORRIDOR) and
                        cell.feature in ('dirt', 'grass', 'water')):
                        feature = gamedata.get_feature(cell.feature)
                        char = feature['avatar']
                        if has_fog_of_war:
                            color = darken_color(feature['color'])
                        else:
                            color = feature['color']
                if (cell.kind == WALL and self.is_looking and x == self.eye_position.x
                    and y == self.eye_position.y):
                    color = (255, 255, 255)
                self.console.draw_char(xx, yy, char, bg=bg_color, fg=color)

                # do not paint entities if they are not visibles.
                # TODO: we must still paint items! or at least stairs!
                for eid in cell.entities:
                    entity = self.world.entity_manager.get_entity(eid)
                    if is_visible or entity.always_visible or self.DEBUG:
                        self.console.draw_char(xx, yy, entity.avatar, bg=None, fg=entity.color)

        self.console.draw_char(player_pos.x - self.camera.x, player_pos.y - self.camera.y,
                               SYMBOLS['PLAYER']['symbol'], bg=None, fg=SYMBOLS['PLAYER']['color'])

        # blit everything onto the root console
        self.root.blit(self.console, 0, 0, self.display_width, self.display_height, 0, 0)

        # info panel is a column on the right side of the screen, half the height of the window
        self.root.blit(self.panel, self.display_width, 0, 0, 0)
        # log panel is a column below info panel occupying the remaining half of the window
        self.root.blit(self.logpanel, self.display_width, self.panel_height, 0, 0)

        # status bar goes at the last line of the screen and it extends until the log panel
        self.root.blit(self.status, 0, self.display_height, 0, 0)

        # popup test
        if self.is_looking:
            self.panel.draw_str(0, 2, "Eye position: %d/%d" % (self.eye_position.x,
                                                               self.eye_position.y))
            self.render_look_command()

        tdl.flush()

    def render_look_command(self):
        """Display informations about what the cursor is looking at"""

        text = ""

        game_map = self.world.get_current_map()
        cell = game_map.get_at(self.eye_position.x, self.eye_position.y)
        if self.is_visited(self.eye_position.x, self.eye_position.y):
            if self.is_visible(self.eye_position.x, self.eye_position.y):
                prefix = "You see"
            else:
                prefix = "You remember seeing"

            if cell.entities:
                descriptions = []
                for entity_id in cell.entities:
                    entity = self.world.entity_manager.get_entity(entity_id)
                    if entity.description:
                        descriptions.append(entity.description)
                if descriptions:
                    text += ", ".join(descriptions)

            if cell.feature is not None:
                feature = gamedata.get_feature(cell.feature)
                if feature is not None and len(feature['description']):
                    if text != "":
                        text += "; "
                    text += "%s %s" % (prefix, feature['description'])

            if text:
                self.info_popup.draw(text)
                self.info_popup.blit(self.root, 1, 1)

    def attempt_move(self, dest_vec):
        """Return False to negate passage, True to allow it"""

        game_map = self.world.get_current_map()
        dcell = game_map.get_at(dest_vec.x, dest_vec.y)
        if dcell.kind in (VOID, WALL):
            return False

        if not dcell.entities:
            return True

        em = self.world.entity_manager
        entities = [em.get_entity(eid) for eid in dcell.entities]

        is_fight = False
        for entity in entities:
            cc = em.combat_components.get(entity.eid)
            if cc is not None:
                self.player_fight(entity, cc, em)
                is_fight = True
                break

        if is_fight:
            return False

        return True

    def player_fight(self, entity, entity_cc, em):
        player_cc = em.combat_components.get(self.player.eid)
        enemy_hc = em.health_components.get(entity.eid)

        print "fight between player (%d/%d/%d) and %r (%d/%d/%d)" % (
            player_cc.damage, player_cc.accuracy, player_cc.defense,
            entity.name, entity_cc.damage, entity_cc.accuracy, entity_cc.defense)

        if roll_to_hit(player_cc.accuracy, entity_cc.defense):
            enemy_hc.health -= player_cc.damage
            self.post_message("You hit the %s for %d damage (%d left)" % (
                entity.name, player_cc.damage, enemy_hc.health))
        else:
            # show some details about the chance to hit
            chance = chance_to_hit(player_cc.accuracy, entity_cc.defense)
            self.post_message("You miss the %s (%d%%)" % (entity.name, chance))

        if enemy_hc.health <= 0:
            self.post_message("%s is dead" % entity.name)
            self.world.destroy_entity(entity.eid)

    def enemy_fight_player(self, entity):
        em = self.world.entity_manager
        entity_cc = em.combat_components.get(entity.eid)
        player_cc = em.combat_components.get(self.player.eid)
        player_hc = em.health_components.get(self.player.eid)
        self.enemy_fight(entity, entity_cc, self.player, player_cc, player_hc)

    def enemy_fight(self, entity, entity_cc, other, other_cc, other_hc):
        victim = other.name
        if other.name == 'player':
            victim = "you"
        if roll_to_hit(entity_cc.accuracy, other_cc.defense):
            self.post_message("the %s hits %s for %d damage" % (entity.name, victim, entity_cc.damage))
            other_hc.health -= entity_cc.damage
        else:
            self.post_message("the %s miss %s" % (entity.name, victim))

        if other_hc.health <= 0:
            if other.name == 'player':
                self.post_message("You are dead!")
                self.player_is_dead = True
            else:
                self.world.destroy_entity(entity.eid)

    def move_enemies(self):
        em = self.world.entity_manager
        for entity_id, ai_cc in em.monster_ai_components.iteritems():
            entity = em.get_entity(entity_id)
            ai_cc.update(entity, self)

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

            if self.player_is_dead:
                self.fizzlefade()
                running = False

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
        elif user_input.char == 'q':
            self.player_is_dead = True
            return
        elif user_input.key == 'ENTER':
            self.is_looking = not(self.is_looking)
            if self.is_looking is True:
                self.eye_position = self.player.get_position().copy()
            return
        elif user_input.key == 'UP' or user_input.char == 'k':
            direction = Direction.NORTH
        elif user_input.char == 'y':
            direction = Direction.NORTH_WEST
        elif user_input.char == 'u':
            direction = Direction.NORTH_EAST
        elif user_input.key == 'DOWN' or user_input.char == 'j':
            direction = Direction.SOUTH
        elif user_input.key == 'LEFT' or user_input.char == 'h':
            direction = Direction.WEST
        elif user_input.key == 'RIGHT' or user_input.char == 'l':
            direction = Direction.EAST
        elif user_input.char == 'b':
            direction = Direction.SOUTH_WEST
        elif user_input.char == 'n':
            direction = Direction.SOUTH_EAST
        elif user_input.key == 'SPACE' or user_input.char == 'z':
            self.enemies_turn = True
            return

        if direction is not None:
            if self.is_looking:
                self.move_eye(direction)
            else:
                self.move_player(direction)

    def move_player(self, direction):
        dest_vec = self.player.get_position() + direction
        can = self.attempt_move(dest_vec)
        if can:
            game_map = self.world.get_current_map()
            cell = game_map.get_at(dest_vec)
            old_cell = game_map.get_at(self.player.position)
            old_cell.entities.remove(self.player.eid)
            cell.entities.append(self.player.eid)
            self.player.set_position(dest_vec)
            self.fov_map.compute_fov(dest_vec.x, dest_vec.y, radius=self.fov_radius,
                                     algorithm=tcod.FOV_DIAMOND)
            self.visited[dest_vec.x][dest_vec.y] = True
            self.enemies_turn = True

    def move_eye(self, direction):
        dest_vec = self.eye_position + direction
        dest_vec.x = clamp(dest_vec.x, 0, self.game_width - 1)
        dest_vec.y = clamp(dest_vec.y, 0, self.game_height - 1)
        self.eye_position.x = dest_vec.x
        self.eye_position.y = dest_vec.y

        # debug
        # game_map = self.world.get_current_map()
        # print "Looking at cell: %r" % game_map.get_at(dest_vec.x, dest_vec.y)

    def post_message(self, message):
        n_lines = int(math.ceil(float(len(message)) / float(self.log_width)))
        if n_lines < 1:
            n_lines = 1
        self.logpanel.scroll(0, n_lines)
        self.logpanel.draw_str(0, 0, message)

    def is_visible(self, x, y):
        return self.fov_map.fov[y, x]

    def is_visited(self, x, y):
        return self.visited[x][y]

    def fizzlefade(self):
        """Apply fizzlefade effect and return. Only works for window sizes up to 320x200
        and it's really just for fun.

        Stolen from http://fabiensanglard.net/fizzlefade/index.php
        """

        board = tdl.Console(self.screen_width, self.screen_height)
        # copy the root content onto board
        board.blit(self.root, 0, 0, self.screen_width, self.screen_height, 0, 0)
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
            if x < self.screen_width and y < self.screen_height:
                board.draw_char(x, y, ' ', fg=(205, 38, 38), bg=(205, 38, 38))
                i += 1
                if i >= 100:
                    i = 0
                    self.root.blit(board, 0, 0, self.screen_width, self.screen_height, 0, 0)
                    tdl.flush()

            if rndval == 1:
                running = False

        tdl.flush()
