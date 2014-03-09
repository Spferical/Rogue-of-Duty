import libtcodpy as tcod
from config import DIAGONAL_MOVEMENT


class Object:
    char = '@'
    name = 'object'
    color = tcod.white
    dead = False
    blocks = False

    def __init__(self, pos):
        (self.x, self.y) = pos

    def update(self):
        pass

    def distance_to(self, other):
        # return the distance to another object
        return self.get_distance(other.x, other.y)

    def die(self):
        pass

    def get_distance(self, x, y):
        # return the distance to some coordinates
        dx = abs(x - self.x)
        dy = abs(y - self.y)
        if DIAGONAL_MOVEMENT:
            return max(dx, dy)
        else:
            return dx + dy
