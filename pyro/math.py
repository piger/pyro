class Vector2(object):
    def __init__(self, x_, y_):
        self.x = x_
        self.y = y_

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __repr__(self):
        return 'Vector2(%d, %d)' % (self.x, self.y)


# Example:
# move(player_pos + NORTH)
NORTH = Vector2(0, -1)
SOUTH = Vector2(0, 1)
EAST = Vector2(1, 0)
WEST = Vector2(-1, 0)
