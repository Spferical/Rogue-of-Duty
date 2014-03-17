"""
Stores game map and classes like Tile, Map, etc.
The levels are set in game.py, generated in mapgen.py.
This file is imported by anything that needs to access the game's levels.
"""
import libtcodpy as tcod
from config import DIAGONAL_MOVEMENT, MAP_WIDTH, MAP_HEIGHT
import mapgen
import game


class Tile:
    """
    A tile of the map and its properties
    """
    blocked = False
    blocks_sight = False
    char = '.'
    fg_color = tcod.white
    bg_color = tcod.black
    # a tile starts unexplored
    explored = False
    name = 'floor'


class UpStairs(Tile):
    fg_color = tcod.black
    bg_color = tcod.white
    char = '<'
    name = 'upwards staircase'
    blocked = True


class DownStairs(Tile):
    fg_color = tcod.black
    bg_color = tcod.white
    char = '>'
    name = 'downwards staircase'
    blocked = True


class Floor(Tile):
    pass  # tile defaults are floor


class EndFloor(Tile):
    char = '>'


class Wall(Tile):
    blocked = True
    blocks_sight = True
    fg_color = tcod.black
    bg_color = tcod.white
    char = ' '
    name = 'wall'


class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.bullets = []
        self.mobs = []
        self.items = []
        # objects are anything not in the above lists
        self.objects = []
        self.objectlists = (self.objects, self.items, self.mobs, self.bullets)

        self.scroll_amount = 0

        # make a grid of generic floor tiles
        self.tiles = [[Floor()
                       for y in range(height)]
                      for x in range(width)]

        self.init_fov_and_pathfinding()
        self.player_start_pos = (0, height / 2)

    def init_fov_and_pathfinding(self):
        # init fov
        self.fov_map = tcod.map_new(self.width, self.height)
        self.update_fov_map()
        # init pathfinding
        self.path = tcod.path_new_using_map(self.fov_map, self.diagonal_cost)

    @property
    def diagonal_cost(self):
        if not DIAGONAL_MOVEMENT:
            # with a cost of 0, the pathfinding won't do diagonal movement
            return 0
        else:
            return 1.414

    def __getitem__(self, i):
        # Map[x][y] returns the tile at (x, y)
        return self.tiles[i]

    def update_fov_map(self):
        for x in range(self.width):
            for y in range(self.height):
                self.update_fov_tile(x, y)

    def update_fov_tile(self, x, y):
        tile = self[x][y]
        tcod.map_set_properties(self.fov_map, x, y,
                                not tile.blocks_sight,
                                not self[x][y].blocked)

    def update_pathfinding(self):
        tcod.path_delete(self.path)
        self.path = tcod.path_new_using_map(self.fov_map, self.diagonal_cost)

    def is_blocked(self, x, y):
        #return true if tile is outside of map
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return True
        # test the map tile
        if self[x][y].blocked:
            return True

        # now check for any blocking objects
        for list in self.objectlists:
            for object in list:
                if object.blocks and (object.x, object.y) == (x, y):
                    return True
        return False

    def scroll(self):
        #scrolls map by one column
        #scrolls all objects, too
        #deletes all objects on leftmost column
        for list in self.objectlists:
            for object in list:
                object.x -= 1
                if object.x < 0:
                    object.dead = True
        game.purge_dead_objects()

        self.tiles.pop(0)
        #generate new map column
        self.scroll_amount += 1
        if len(self.tiles) < MAP_WIDTH:
            mapgen.generate_new_map_chunk(self)
        self.update_fov_map()
        self.update_pathfinding()

map = Map(MAP_WIDTH, MAP_HEIGHT)
