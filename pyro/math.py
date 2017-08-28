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



class Rect(object):
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.endX = self.x + self.width
        self.endY = self.y + self.height

    @property
    def center(self):
        center_x = int((self.x + self.endX) / 2)
        center_y = int((self.y + self.endY) / 2)
        return (center_x, center_y)

    def intersect(self, other):
        return (self.x <= other.endX and self.endX >= other.x and
                self.y <= other.endY and self.endY >= other.y)

    def __repr__(self):
        return 'Rect(x=%d, y=%d, width=%d, height=%d)' % (self.x, self.y, self.width, self.height)
