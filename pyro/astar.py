"""
http://code.activestate.com/recipes/578919-python-a-pathfinding-with-binary-heap/
"""
import heapq
from pyro.utils import Direction
from pyro import WALL, VOID


class PriorityQueue(object):
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]

    def contain(self, item):
        for _, i in self.elements:
            if i == item:
                return True
        return False


def heuristic(a, b):
    return abs(a.x - b.x) + abs(a.y - b.y)


def astar(dungeon, start, goal, diagonal=True):
    close_set = set()
    came_from = {}
    gscore = {
        start: 0
    }
    fscore = {
        start: heuristic(start, goal)
    }
    oheap = PriorityQueue()

    if diagonal:
        directions = Direction.all()
    else:
        directions = Direction.cardinal()

    oheap.put(start, fscore[start])

    while not oheap.empty():
        current = oheap.get()
        if current == goal:
            result = []
            while current in came_from:
                result.append(current)
                current = came_from[current]
            result.reverse()
            return result

        close_set.add(current)
        for d in directions:
            neighbor = current + d
            tentative_g_score = gscore[current] + heuristic(current, neighbor)
            cell = dungeon.get_at(neighbor)
            if cell is None or not cell.walkable:
                continue
            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, 0):
                continue

            if tentative_g_score < gscore.get(neighbor, 0) or not oheap.contain(neighbor):
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g_score
                fscore[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                oheap.put(neighbor, fscore[neighbor])
    return []
