import random
import inspect
import tcod
from . import Component
from ..astar import astar
from ..utils import Direction, weighted_choice


class MonsterAiComponent(Component):
    """AI for monsters."""

    def __init__(self):
        super(MonsterAiComponent, self).__init__()
        self.fov_map = None
        self.radius = 4
        self.can_move_diagonal = True
        self.aggressive = True

        self.chasing = False
        self.last_player_pos = None
        self.cur_direction = None

    def config(self, values):
        for i in range(0, len(values), 2):
            name = values[i]
            value = values[i + 1]
            if name == "FOV_RADIUS":
                self.radius = int(value)
            elif name == "DIAGONAL":
                self.can_move_diagonal = bool(int(value))
            elif name == "AGGRESSIVE":
                self.aggressive = bool(int(value))

    def setup(self, game):
        """Must be called during game initialization, after fov_map is computed"""

        self.fov_map = tcod.map.Map(width=game.game_width, height=game.game_height)
        for y in range(game.game_height):
            for x in range(game.game_width):
                self.fov_map.walkable[y, x] = game.fov_map.walkable[y, x]
                self.fov_map.transparent[y, x] = game.fov_map.transparent[y, x]

    def move_to(self, entity, cur_map, entity_manager, pos):
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

        cur_map.move_entity(entity, pos)
        return True

    def wander(self, entity, game):
        """Wander around randomly"""

        candidates = []
        cur_map = game.world.get_current_map()
        for d in Direction.all():
            dest = entity.position + d
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

        if self.move_to(entity, cur_map, game.world.entity_manager, winner):
            self.cur_direction = winner.copy()

    def update(self, entity, game):
        """To be called every turn"""

        if not self.aggressive:
            if random.random() < 0.3:
                return
            self.wander(entity, game)
            return

        player = game.player
        cur_map = game.world.get_current_map()
        em = game.world.entity_manager

        if self.last_player_pos is not None and entity.position == self.last_player_pos:
            self.last_player_pos = None

        # check if the player is directly adjacent, so that we can skip calculating the FOV for this
        # monster.
        adjacent = False
        for d in Direction.all():
            pos = entity.position + d
            if pos == player.position:
                adjacent = True
                self.chasing = True

        if not adjacent:
            # update fov
            self.fov_map.compute_fov(
                entity.position.x, entity.position.y, radius=self.radius, algorithm=tcod.FOV_DIAMOND
            )
            # if the player position is "lit", then we see the player
            self.chasing = self.fov_map.fov[player.position.y, player.position.x]
        elif adjacent:
            print("attacking")
            game.enemy_fight_player(entity)
            return

        if self.chasing:
            path = astar(cur_map, entity.position, player.position, self.can_move_diagonal)
            if len(path) == 1:
                new_pos = path[0]
                if new_pos == player.position:
                    # attack
                    print("attacking")
                    game.enemy_fight_player(entity)
            elif path:
                print("chasing")
                self.last_player_pos = path[-1]

                new_pos = path[0]
                if not self.move_to(entity, cur_map, em, new_pos):
                    print("can't move, cell is busy")
            else:
                print("path is empty!?")
        else:
            if self.last_player_pos is not None:
                print("remembering the chase")
                path = astar(cur_map, entity.position, self.last_player_pos, self.can_move_diagonal)
                self.move_to(entity, cur_map, em, path[0])
            else:
                # move randomly, but not all the times
                if random.random() < 0.3:
                    return
                self.wander(entity, game)
