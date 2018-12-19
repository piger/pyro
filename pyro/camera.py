import math
import logging
from .utils import Rect


logger = logging.getLogger(__name__)


class Camera(Rect):
    def __init__(self, width, height):
        x = y = 0
        super(Camera, self).__init__(x, y, width, height)

    def center_on(self, x, y):
        """Center the camera on a coordinate

        Center the camera on the given coordinate when the distance between the center of the camera
        (which is the center of the game "map" screen) and the target coordinate is more than
        roughly half the size of the camera.
        """
        # get our *absolute* center coordinates
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        max_distance = min([self.width // 2, self.height // 2])

        logger.debug("Center = %f/%f, center = %r", center_x, center_y, self.center)

        # distance between two points (pythagorean theorem)
        distance = math.sqrt((center_x - x) ** 2 + (center_y - y) ** 2)
        logger.debug("Distance between center of camera and target: %f", distance)

        # would be nice to use linear interpolation here
        # https://math.stackexchange.com/questions/1918743/how-to-interpolate-points-between-2-points

        if distance >= max_distance:
            self.x = x - (self.width // 2)
            self.y = y - (self.height // 2)

    def __repr__(self):
        return "Camera(x=%d, y=%d, w=%d, h=%d)" % (self.x, self.y, self.width, self.height)
