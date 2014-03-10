import libtcodpy as tcod
from config import TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO, \
    DIAGONAL_MOVEMENT, VICTORY_DISTANCE
import render
import random
import mapgen
import mob
import item
import ui
import terrain

player = state = None
alive = False
current_turn = 0


def get_key(key):
    # TODO: move this to ui.py?
    # return either libtcod code or character that was pressed
    if key.vk == tcod.KEY_CHAR:
        return chr(key.c)
    else:
        return key.vk


def compute_fov():
    tcod.map_compute_fov(terrain.map.fov_map, player.x, player.y,
                         TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)


def handle_keys():  # controls
    tcod.sys_check_for_event(tcod.EVENT_KEY_PRESS | tcod.EVENT_MOUSE,
                             ui.key, ui.mouse)
    key = get_key(ui.key)

    action = None  # action that player takes, e.g. 'moved' or 'attacked'

    # movement keys
    if state == 'playing':
        if key in ui.direction_keys:
            (x, y) = ui.direction_keys[key]
            if DIAGONAL_MOVEMENT:
                action = player.move_or_attack(x, y)
            elif not (x != 0 and y != 0):
                action = player.move_or_attack(x, y)
            else:
                # player is trying to move diagonally
                # diagonal movement is disabled, though!
                return None
        elif key in ('.', tcod.KEY_KP5):
            action = 'pass'
        elif key in ('g', ','):
            # pick up an item
            # look for an item in player's tile
            for object in terrain.map.objects:
                if isinstance(object, item.Item):
                    if (object.x, object.y) == (player.x, player.y):
                        player.pick_up(object)
                        break
        # inventory menu
        elif key == 'z':
            #use player's first item
            i = player.inventory[0]
            action = player.use(i)
        elif key == 'x':
            #use player's 2nd item
            i = player.inventory[1]
            action = player.use(i)
        elif key == 'c':
            #use player's 3rd item
            i = player.inventory[2]
            action = player.use(i)

    if key == tcod.KEY_ENTER and ui.key.lalt:
        # Alt+Enter: toggle fullscreen
        tcod.console_set_fullscreen(not tcod.console_is_fullscreen())

    elif key == tcod.KEY_ESCAPE:
        ui.handle_escape_menu()

    if action == 'moved':
        if player.x > terrain.map.width / 2:
            terrain.map.scroll()
        # player moved, so we should recompute the fov map
        #terrain.map.init_fov_and_pathfinding()
        #terrain.map.update_fov_map()
        compute_fov()
        terrain.map.update_pathfinding()
        #also move render camera
        render.move_camera(player.x, player.y)
        # also update each tile on screen (different tiles will be lit)
        render.clear_all_tiles()
        render.draw_all_tiles()
    return action


def run():
    global current_turn
    while alive and not tcod.console_is_window_closed():
        action = handle_keys()
        if action:
            compute_fov()
            update_objects()
            randomly_spawn_enemies()
            current_turn += 1
            if player.x + terrain.map.scroll_amount >= VICTORY_DISTANCE:
                ui.message('Congratulations, you win! Press escape to exit.', tcod.cyan)
                global state
                state = 'dead'
        render.render_all()


def update_objects():
    # update all objects
    for object in terrain.map.objects[:]:
        #only update living objects
        if not object.dead:
            object.update()
        if player.dead:
            #if player dies, immediately end gameplay
            break
    #also update objects in player inventory
    #e.g. passive items may do stuff here
    if not player.dead:
        for object in player.inventory:
            object.update()
    purge_dead_objects()

def purge_dead_objects():
    # get rid of all dead objects
    for object in terrain.map.objects[:]:
        if object.dead:
            object.die()
            if object == player:
                ui.message('GAME OVER! Press escape to exit.')
                global state
                state = 'dead'
            else:
                terrain.map.objects.remove(object)


def get_names_under_mouse():
    # TODO: move this to ui.py
    # return a string with the names of all objects under the mouse
    (x, y) = (ui.mouse.cx, ui.mouse.cy)
    x += render.camera_x
    y += render.camera_y
    # create a list with the names of all objects at the mouse's coords
    # and in FOV
    if tcod.map_is_in_fov(terrain.map.fov_map, x, y):
        names = [obj.name for obj in terrain.map.objects
                 if (obj.x, obj.y) == (x, y)]
        # add the name of the map tile under any objects
        if x < terrain.map.width and y < terrain.map.height:
            names.insert(0, terrain.map[x][y].name)
        names = ', '.join(names)  # join the names, separated by commas
        return names.capitalize()
    else:
        return ''


def randomly_spawn_enemies():
    y = random.randint(0, terrain.map.height - 1)

    if random.randint(1, 3) == 1:
        f = 1
        x = 0
    else:
        f = 2
        x = terrain.map.width - 1

    obj = mob.get_random_mob(mob.moblist)((x, y), f)
    spawn_object(obj)

def spawn_enemies(x, map=None):
    if map == None:
        map = terrain.map
    #spawns enemies on random spot on top and bottom of map
    obj = mob.get_random_mob(mob.moblist)((x, 0), 1)
    obj.faction = 1
    spawn_object(obj, map)
    obj = mob.get_random_mob(mob.moblist)((x, map.height - 1), 2)
    obj.faction = 2
    spawn_object(obj, map)


def spawn_object(object, map=None):
    if map == None:
        map = terrain.map
    if not map.is_blocked(object.x, object.y):
        map.objects.append(object)


def new_game():
    global player, alive, state, current_turn
    starting_items = ui.item_choice_menu()
    if starting_items is None:
        #player closed window during starting item dialog
        return
    terrain.map = mapgen.generate_map()

    pos = terrain.map.player_start_pos
    player = mob.Player(pos)
    for i in starting_items:
        player.get(i((0, 0)))

    #terrain.map.init_fov_and_pathfinding()

    for i in range(50):
        update_objects()

    terrain.map.objects.append(player)
    ui.clear_messages()

    render.init()
    compute_fov()
    render.draw_all_tiles()

    alive = True
    state = 'playing'

    current_turn = 1

    ui.message('Good job! You managed to sneak into the fortress of the dwarves and nabbed a priceless artifact while the dwarves were busy repelling a seige. Unfortunately, your escape route is now encased in battle! Can you navigate 200 tiles of mayhem?')
