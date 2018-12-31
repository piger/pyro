import random
import inspect
import logging
import tcod
from . import Component
from ..astar import astar
from ..utils import Direction, weighted_choice, probability


logger = logging.getLogger(__name__)


class MonsterAiComponent(Component):
    """AI for monsters."""

    def __init__(self):
        super(MonsterAiComponent, self).__init__()
        self.radius = 4
        self.can_move_diagonal = True
        self.aggressive = True

        self.chasing = False
        self.last_player_pos = None
        self.cur_direction = None

    def setup(self, config):
        if "FOV_RADIUS" in config:
            self.radius = int(config["FOV_RADIUS"])
        if "DIAGONAL" in config:
            self.can_move_diagonal = bool(int(config["DIAGONAL"]))
        if "AGGRESSIVE" in config:
            self.aggressive = bool(int(config["AGGRESSIVE"]))

    def move_to(self, monster, cur_map, entity_manager, pos):
        """Move the entity to a pos, if possible"""

        new_cell = cur_map.get_at(pos)
        caller = inspect.stack()[1][3]

        if new_cell is None:
            print("move_to: %r is outside of map (caller: %s)" % (new_cell, caller))
            return False
        elif not new_cell.walkable:
            print("move_to: %r is not walkable (caller: %s)" % (new_cell, caller))
            return False

        for entity_id in new_cell.entities:
            if entity_id in entity_manager.components["monster_ai"]:
                # we can't move, there's another AI in that cell
                return False

        cur_map.move_entity(monster, pos)
        return True

    def wander(self, monster, game):
        """Wander around randomly"""

        candidates = []
        cur_map = game.world.get_current_map()
        for d in Direction.all():
            dest = monster.position + d
            cell = cur_map.get_at(dest)
            if not cell.walkable:
                continue
            for eid in cell.entities:
                e = game.world.entity_manager.get_entity(eid)
                if e in game.world.entity_manager.components["monster_ai"]:
                    continue
            candidates.append(dest)

        # chose a new random direction, with a preference on following the current direction, just
        # to make it look slightly less random.
        if self.cur_direction is not None and self.cur_direction in candidates:
            w = []
            for c in candidates:
                if c == self.cur_direction:
                    w.append((2.5, c))
                else:
                    w.append((1, c))
            winner = candidates[weighted_choice([x[0] for x in w])]
        else:
            winner = random.choice(candidates)

        if self.move_to(monster, cur_map, game.world.entity_manager, winner):
            self.cur_direction = winner.copy()

    def maybe_move(self, monster, game):
        if probability("70%"):
            self.wander(monster, game)

    def update(self, monster, game):
        """To be called every turn"""

        if not self.aggressive:
            self.maybe_move(monster, game)
            return

        player = game.player
        cur_map = game.world.get_current_map()
        em = game.world.entity_manager
        fov_map = game.fov_map

        if self.last_player_pos is not None and monster.position == self.last_player_pos:
            self.last_player_pos = None
            logger.debug(f"{monster} stopping chase, reached last player position")
            self.chasing = False

        # check if the player is directly adjacent, so that we can skip calculating the FOV for this
        # monster.
        for d in Direction.all():
            pos = monster.position + d
            if pos == player.position:
                self.last_player_pos = player.position.copy()
                logger.debug(f"{monster} attacking {player}")
                self.chasing = True
                game.fight(monster, player)
                return

        # update fov
        fov_map.compute_fov(
            monster.position.x, monster.position.y, radius=self.radius, algorithm=tcod.FOV_DIAMOND
        )
        # if the player position is "lit", then we see the player.
        # if we're already chasing (going to lasy_player_pos) we skip this check.
        if fov_map.fov[player.position.y, player.position.x]:
            self.chasing = True
            self.last_player_pos = player.position.copy()
            logger.debug(f"{monster} can see the player")

        if self.chasing:
            path = astar(cur_map, monster.position, self.last_player_pos, self.can_move_diagonal)
            if path:
                logger.debug(f"{monster} chasing the player to {self.last_player_pos}")
                if not self.move_to(monster, cur_map, em, path[0]):
                    logger.warning(f"{monster} can't move to {path[0]}: cell is busy")
            else:
                logger.warning("A* Path for {monster} is empty")
        else:
            self.maybe_move(monster, game)
