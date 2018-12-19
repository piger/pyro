import unittest
from pyro.utils import Rect, Vector2


class RectTest(unittest.TestCase):
    def test_center(self):
        x = Rect(5, 5, 10, 10)
        expected = Vector2(10, 10)
        center = x.center
        assert expected.x == center.x
        assert expected.y == center.y
