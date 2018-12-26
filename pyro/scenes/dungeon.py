import textwrap
import logging
import tcod
import tdl
from . import Scene
from ..combat import roll_to_hit, chance_to_hit
from ..potions import PotionSystem
from ..world import World
from ..utils import darken_color, clamp, Direction, PopupWindow
from ..camera import Camera
from ..gamedata import gamedata
from .. import (
    MESSAGE_COLOR,
    DARK_BACKGROUND,
    PANEL_TEXT_COLOR,
    POPUP_BACKGROUND,
    POPUP_SIZE,
    WALL,
    ROOM,
    CORRIDOR,
    VOID,
    FLOOR,
)


logger = logging.getLogger(__name__)


class DungeonScene(Scene):
    def __init__(self):
        super(DungeonScene, self).__init__()
        self.fov_radius = 6

        self.game_width = 0
        self.game_height = 0

        # size of info panel
        self.panel_width = 0
        self.panel_height = 0

        # size of map area console
        self.display_width = 0
        self.display_height = 0

        # size of message log console
        self.log_width = 0
        self.log_height = 0

        # size of status bar console
        self.status_width = 0
        self.status_height = 0

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
        self.potion_system = PotionSystem()

        self.is_looking = False
        self.eye_position = None
        self.do_render = True

        self.message_log = []

        # devel options
        self.dungeon_algorithm = None

    def setup(self, game):
        self.DEBUG = game.DEBUG

        self.game_width = game.game_width
        self.game_height = game.game_height

        # size of info panel
        self.panel_width = 30
        self.panel_height = game.screen_height // 2

        # size of map area console
        self.display_width = game.screen_width - self.panel_width
        self.display_height = game.screen_height - 1  # -1 for status bar

        # size of message log console
        self.log_width = self.panel_width
        self.log_height = game.screen_height - self.panel_height

        # size of status bar console
        self.status_width = self.display_width
        self.status_height = 1

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
        self.panel.set_colors(PANEL_TEXT_COLOR, DARK_BACKGROUND)

        self.logpanel = tdl.Console(self.log_width, self.log_height)
        self.logpanel.set_colors(fg=MESSAGE_COLOR, bg=DARK_BACKGROUND)
        self.logpanel.clear()

        self.status = tdl.Console(self.status_width, self.status_height)

        # the popup must grow and shrink so the size of the console will be the same size as
        # the display (i.e. where we show the map); we'll render the popup based on the size
        # stored in self.info_popup_size.
        self.info_popup = PopupWindow(
            POPUP_SIZE[0],
            POPUP_SIZE[1],
            self.display_width,
            self.display_height,
            PANEL_TEXT_COLOR,
            POPUP_BACKGROUND,
        )

        # initialize the potion system
        self.potion_system.setup()

        # Initialize world and current dungeon
        self.world = World()
        self.world.create_map(
            self.game_width, self.game_height, level=1, dungeon_algorithm=self.dungeon_algorithm
        )
        cur_map = self.world.get_current_map()

        self.camera = Camera(self.display_width, self.display_height)
        logger.debug("Camera = %r" % self.camera)

        # setup FOV
        self.init_fov(cur_map)

        # setup player
        self.player = self.world.entity_manager.create_entity("player")
        cur_map.move_entity(self.player, cur_map.start_vec)
        self.fov_map.compute_fov(cur_map.start_vec.x, cur_map.start_vec.y, radius=6)

        # setup visited cells
        self.init_visited()

        # init AI
        for ai in self.world.entity_manager.components["monster_ai"].values():
            ai.setup(self)

    def init_fov(self, cur_map):
        """Initialize the Field of View handler

        NOTE: fov requires [y,x] addressing!
        """

        fov_map = tcod.map.Map(width=self.game_width, height=self.game_height)
        for y in range(self.game_height):
            for x in range(self.game_width):
                cell = cur_map.get_at(x, y)
                if cell.walkable:
                    fov_map.walkable[y, x] = True
                    fov_map.transparent[y, x] = True
                # doors will block sight
                for entity_id in cell.entities:
                    door_components_db = self.world.entity_manager.components["door"]
                    if entity_id in door_components_db:
                        fov_map.transparent[y, x] = False
        self.fov_map = fov_map

    def init_visited(self):
        cur_map = self.world.get_current_map()
        self.visited = [[False for y in range(self.game_height)] for x in range(self.game_width)]

        # the starting room is always entirely visited.
        start_cell = cur_map.get_at(cur_map.start_vec.x, cur_map.start_vec.y)
        logger.debug(
            "Start cell: %r at %dx%d", start_cell, cur_map.start_vec.x, cur_map.start_vec.y
        )
        start_room = cur_map.get_room(start_cell.room_id)
        logger.debug("Start room: %r", start_room)

        for y in range(start_room.y, start_room.y + start_room.height):
            for x in range(start_room.x, start_room.x + start_room.width):
                self.visited[x][y] = True

    def render_all(self, game):
        game_map = self.world.get_current_map()

        self.console.clear(bg=DARK_BACKGROUND)
        self.panel.clear(bg=DARK_BACKGROUND)
        self.status.clear(bg=DARK_BACKGROUND)

        player_pos = self.player.get_position()
        self.camera.center_on(player_pos.x, player_pos.y)

        # Print some stuff into the info panel
        self.panel.draw_str(0, 0, "You, the rogue.")
        self.panel.draw_str(0, 1, "Player position: %d/%d" % (player_pos.x, player_pos.y))

        for y in range(self.game_height):
            for x in range(self.game_width):
                # from camera coordinates to game world coordinates
                xx = x - self.camera.x
                yy = y - self.camera.y

                # skip rendering of cells out of the camera view
                if xx < 0 or xx > game.screen_width or yy < 0 or yy > game.screen_height:
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
                        self.console.draw_char(xx, yy, " ", bg=bg_color, fg=(0, 0, 0))
                    if not self.DEBUG:
                        continue
                elif is_visible and not is_visited:
                    # mark visible cells as visited
                    self.visited[x][y] = True

                cell = game_map.get_at(x, y)
                if cell.kind == WALL:
                    symbol = gamedata.get_feature("wall")
                elif cell.kind == VOID:
                    symbol = gamedata.get_feature("void")
                elif cell.kind == ROOM or cell.kind == FLOOR:
                    symbol = gamedata.get_feature("floor")
                elif cell.kind == CORRIDOR:
                    symbol = gamedata.get_feature("corridor")
                else:
                    print("unknown cell kind %r" % cell)

                if has_fog_of_war:
                    color = darken_color(symbol["color"])
                else:
                    color = symbol["color"]

                if self.DEBUG and cell.value is not None:
                    char = str(cell.value)
                else:
                    char = symbol["avatar"]
                    if cell.walkable and cell.feature in ("dirt", "grass", "water"):
                        feature = gamedata.get_feature(cell.feature)
                        char = feature["avatar"]
                        if has_fog_of_war:
                            color = darken_color(feature["color"])
                        else:
                            color = feature["color"]

                if (
                    cell.kind == WALL
                    and self.is_looking
                    and x == self.eye_position.x
                    and y == self.eye_position.y
                ):
                    color = (255, 255, 255)

                self.console.draw_char(xx, yy, char, bg=bg_color, fg=color)

                # do not paint entities if they are not visibles.
                # TODO: we must still paint items! or at least stairs!
                entities = []
                for eid in cell.entities:
                    entity = self.world.entity_manager.get_entity(eid)
                    entities.append(entity)
                entities.sort(key=lambda x: x.layer)
                for entity in entities:
                    if is_visible or entity.always_visible or self.DEBUG:
                        self.console.draw_char(xx, yy, entity.avatar, bg=None, fg=entity.color)

        player_symbol = gamedata.get_entity("player")
        self.console.draw_char(
            player_pos.x - self.camera.x,
            player_pos.y - self.camera.y,
            player_symbol["avatar"],
            bg=None,
            fg=player_symbol["color"],
        )

        # blit everything onto the root console
        game.root.blit(self.console, 0, 0, self.display_width, self.display_height, 0, 0)

        if self.is_looking:
            self.panel.draw_str(
                0, 2, "Eye position: %d/%d" % (self.eye_position.x, self.eye_position.y)
            )
            self.render_look_command(game)

        # info panel is a column on the right side of the screen, half the height of the window
        game.root.blit(self.panel, self.display_width, 0, 0, 0)
        # log panel is a column below info panel occupying the remaining half of the window
        game.root.blit(self.logpanel, self.display_width, self.panel_height, 0, 0)

        # status bar goes at the last line of the screen and it extends until the log panel
        game.root.blit(self.status, 0, self.display_height, 0, 0)
        self.do_render = False

    def render_look_command(self, game):
        """Display informations about what the cursor is looking at"""

        text = ""

        # render position
        x = 1
        y = 1

        # NOTE: right now 'eye_position' is relative to the game world, not the camera world.
        if self.eye_position.y - self.camera.y <= self.display_height // 2:
            # render on the second half of the screen and add 3 cells margin
            y = self.display_height // 2 + 3

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
                    if entity.is_potion():
                        name = self.potion_system.get_name_for_potion(entity)
                        d = "a %s potion" % name
                        descriptions.append(d)
                    elif entity.description:
                        descriptions.append(entity.description)
                if descriptions:
                    text += ", ".join(descriptions)

            if cell.feature is not None:
                feature = gamedata.get_feature(cell.feature)
                if feature is not None and len(feature["description"]):
                    if text != "":
                        text += "; "
                    text += "%s %s" % (prefix, feature["description"])

            if text:
                self.info_popup.draw(text)
                self.info_popup.blit(game.root, x, y)

    def attempt_move(self, dest_vec):
        """Return False to negate passage, True to allow it"""

        game_map = self.world.get_current_map()
        dcell = game_map.get_at(dest_vec.x, dest_vec.y)
        if not dcell.walkable:
            return False

        if not dcell.entities:
            return True

        em = self.world.entity_manager
        entities = [em.get_entity(eid) for eid in dcell.entities]

        is_fight = False
        for entity in entities:
            cc = em.get_component_by_eid(entity.eid, "combat")
            if cc is not None:
                self.player_fight(entity, cc, em)
                is_fight = True
                break
            ai = em.get_component_by_eid(entity.eid, "monster_ai")
            if ai is not None:
                return False

        if is_fight:
            return False

        return True

    def player_fight(self, entity, entity_cc, em):
        player_cc = em.get_component_by_eid(self.player.eid, "combat")
        enemy_hc = em.get_component_by_eid(entity.eid, "health")

        print(
            "fight between player (%d/%d/%d) and %r (%d/%d/%d)"
            % (
                player_cc.damage,
                player_cc.accuracy,
                player_cc.defense,
                entity.name,
                entity_cc.damage,
                entity_cc.accuracy,
                entity_cc.defense,
            )
        )

        if roll_to_hit(player_cc.accuracy, entity_cc.defense):
            enemy_hc.health -= player_cc.damage
            self.post_message(
                "You hit the %s for %d damage (%d left)"
                % (entity.name, player_cc.damage, enemy_hc.health)
            )
        else:
            # show some details about the chance to hit
            chance = chance_to_hit(player_cc.accuracy, entity_cc.defense)
            self.post_message("You miss the %s (%d%%)" % (entity.name, chance))

        if enemy_hc.health <= 0:
            self.post_message("%s is dead" % entity.name)
            self.world.destroy_entity(entity.eid)

    def enemy_fight_player(self, entity):
        em = self.world.entity_manager
        entity_cc = em.get_component_by_eid(entity.eid, "combat")
        player_cc = em.get_component_by_eid(self.player.eid, "combat")
        player_hc = em.get_component_by_eid(self.player.eid, "health")
        self.enemy_fight(entity, entity_cc, self.player, player_cc, player_hc)

    def enemy_fight(self, entity, entity_cc, other, other_cc, other_hc):
        victim = other.name
        if other.name == "player":
            victim = "you"
        if roll_to_hit(entity_cc.accuracy, other_cc.defense):
            self.post_message(
                "the %s hits %s for %d damage" % (entity.name, victim, entity_cc.damage)
            )
            other_hc.health -= entity_cc.damage
        else:
            self.post_message("the %s miss %s" % (entity.name, victim))

        if other_hc.health <= 0:
            if other.name == "player":
                self.post_message("You are dead!")
                self.player_is_dead = True
            else:
                self.world.destroy_entity(entity.eid)

    def move_enemies(self):
        self.do_render = True
        em = self.world.entity_manager
        for entity_id, ai_cc in em.components["monster_ai"].items():
            entity = em.get_entity(entity_id)
            ai_cc.update(entity, self)

        self.enemies_turn = False

    def move_player(self, direction):
        dest_vec = self.player.get_position() + direction
        can = self.attempt_move(dest_vec)
        if can:
            game_map = self.world.get_current_map()
            game_map.move_entity(self.player, dest_vec)
            self.fov_map.compute_fov(
                dest_vec.x, dest_vec.y, radius=self.fov_radius, algorithm=tcod.FOV_DIAMOND
            )
            self.visited[dest_vec.x][dest_vec.y] = True
            self.enemies_turn = True

    def move_eye(self, direction):
        dest_vec = self.eye_position + direction
        dest_vec.x = clamp(dest_vec.x, 0, self.game_width - 1)
        dest_vec.y = clamp(dest_vec.y, 0, self.game_height - 1)
        self.eye_position.x = dest_vec.x
        self.eye_position.y = dest_vec.y

    def player_take_item(self):
        cur_map = self.world.get_current_map()
        em = self.world.entity_manager
        ic = self.player.get_component("inventory")
        cell = cur_map.get_at(self.player.get_position())
        if not cell.entities:
            return False

        to_remove = []
        for entity_id in cell.entities:
            entity = em.get_entity(entity_id)
            if entity.is_potion():
                ic.take_item(entity)
                to_remove.append(entity.eid)
                name = self.potion_system.get_name_for_potion(entity)
                self.post_message("You took a %s potion" % name)

        if not to_remove:
            return False
        for entity_id in to_remove:
            cell.entities.remove(entity_id)
        self.enemies_turn = True
        return True

    def post_message(self, message):
        lines = textwrap.wrap(message, width=self.log_width)
        self.logpanel.scroll(0, len(lines) * -1)
        self.logpanel.draw_str(0, self.log_height - len(lines), message)

    def is_visible(self, x, y):
        return self.fov_map.fov[y, x]

    def is_visited(self, x, y):
        return self.visited[x][y]

    def update(self, game):
        if self.enemies_turn:
            self.move_enemies()

        if self.do_render:
            self.render_all(game)
        tdl.flush()

    def keydown_event(self, event, game):
        self.do_render = True
        direction = None

        if event.key == "ESCAPE":
            game.next_scene = "quit"
            return
        elif event.char == "q":
            self.player_is_dead = True
            game.next_scene = "quit"
            return
        elif event.key == "ENTER":
            self.is_looking = not (self.is_looking)
            if self.is_looking is True:
                self.eye_position = self.player.get_position().copy()
            return
        elif event.key == "UP" or event.char == "k":
            direction = Direction.NORTH
        elif event.char == "y":
            direction = Direction.NORTH_WEST
        elif event.char == "u":
            direction = Direction.NORTH_EAST
        elif event.key == "DOWN" or event.char == "j":
            direction = Direction.SOUTH
        elif event.key == "LEFT" or event.char == "h":
            direction = Direction.WEST
        elif event.key == "RIGHT" or event.char == "l":
            direction = Direction.EAST
        elif event.char == "b":
            direction = Direction.SOUTH_WEST
        elif event.char == "n":
            direction = Direction.SOUTH_EAST
        elif event.char == ";" or event.char == "g":
            self.player_take_item()
            return
        elif event.key == "SPACE" or event.char == "z":
            self.enemies_turn = True
            return

        if direction is not None:
            if self.is_looking:
                self.move_eye(direction)
            else:
                self.move_player(direction)
