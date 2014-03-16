import libtcodpy as tcod
import mob
import random
from config import ROOM_MIN_SIZE, ROOM_MAX_SIZE, MAX_ROOMS, \
    MAX_ROOM_MONSTERS, MAX_ROOM_ITEMS, MAP_WIDTH, MAP_HEIGHT, VICTORY_DISTANCE
import terrain
import game


class Structure:
    weight = 0
    tiles = ['.']


class Bunker(Structure):
    weight = 1
    tiles = ['##.##',
             '#*.*#',
             '.....',
             '#*.*#',
             '##.##']

class Wall(Structure):
    weight = 5
    tiles = ['#',
             '#',
             '#']


class Ruins(Structure):
    weight = 1
    tiles = ['*' * 5] * 5


structures = [Bunker, Wall, Ruins]


def get_tile(t):
    if t == '#': return terrain.Wall()
    if t == '.': return terrain.Floor()
    if t == '*': return random.choice((terrain.Wall, terrain.Floor))()


def generate_map():
    map = terrain.Map(MAP_WIDTH, MAP_HEIGHT)
    map.tiles = []
    map.scroll_amount = - map.width
    x = 0
    while x < map.width:
        generate_new_map_chunk(map)
        map.scroll_amount += 5
        x += 5
    map.update_fov_map()
    map.update_pathfinding()
    return map


def generate_new_map_chunk(map):
    columns = [[terrain.Tile() for y in range(map.height)]
               for x in range(5)]
    x = map.width + map.scroll_amount - 1
    if x < VICTORY_DISTANCE - map.width / 2:
        struct = get_random_structure()
        sh = len(struct.tiles)
        sw = len(struct.tiles[0])

        x = random.randint(0, 5 - sw)
        y = random.randint(0, map.height - sh)
        print x, y, struct.tiles

        for sx in range(0, sw):
            for sy in range(0, sh):
                columns[x + sx][y + sy] = get_tile(struct.tiles[sy][sx])

    map.tiles.extend(columns)


def get_random_structure():
    total = sum(s.weight for s in structures)
    r = random.uniform(0, total)
    upto = 0
    for s in structures:
        if upto + s.weight > r:
            return s
        upto += s.weight
