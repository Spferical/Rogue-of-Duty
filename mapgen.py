import libtcodpy as tcod
import mob
import random
from config import ROOM_MIN_SIZE, ROOM_MAX_SIZE, MAX_ROOMS, \
    MAX_ROOM_MONSTERS, MAX_ROOM_ITEMS, MAP_WIDTH, MAP_HEIGHT, VICTORY_DISTANCE
import terrain
import game


def generate_map():
    map = terrain.Map(MAP_WIDTH, MAP_HEIGHT)
    map.tiles = []
    map.scroll_amount = - map.width
    for x in range(0, map.width):
        generate_new_map_column(map)
        map.scroll_amount += 1
    map.update_fov_map()
    map.update_pathfinding()
    return map

def generate_new_map_column(map):
    column = [terrain.Tile() for x in range(map.height)]
    x = map.width + map.scroll_amount - 1
    if x < VICTORY_DISTANCE - map.width / 2:
        if random.randint(0, 1) == 0:
            wall_y = random.randint(1, map.height - 2)
            column[wall_y] = terrain.Wall()
        if x % 3 == 0 and x != -map.width:
            x = len(map.tiles) - 1
            game.spawn_enemies(x, map=map)

    map.tiles.append(column)
