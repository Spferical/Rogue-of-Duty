import libtcodpy as tcod
from config import INVENTORY_WIDTH, SCREEN_HEIGHT, SCREEN_WIDTH
import render
import textwrap
from config import MSG_WIDTH, MSG_HEIGHT
import game
import save
import item
import terrain

# mouse/key used for all keyboard and moust input
# used by tcod.sys_check_for_event(mask, key, mouse)
mouse = tcod.Mouse()
key = tcod.Key()

# dictionary of key:direction, used for movement
direction_keys = {
    # arrow keys
    tcod.KEY_UP: (0, -1),
    tcod.KEY_DOWN: (0, 1),
    tcod.KEY_LEFT: (-1, 0),
    tcod.KEY_RIGHT: (1, 0),
    # numpad keys
    tcod.KEY_KP1: (-1, 1),
    tcod.KEY_KP2: (0, 1),
    tcod.KEY_KP3: (1, 1),
    tcod.KEY_KP4: (-1, 0),
    tcod.KEY_KP6: (1, 0),
    tcod.KEY_KP7: (-1, -1),
    tcod.KEY_KP8: (0, -1),
    tcod.KEY_KP9: (1, -1),
    # vi keys
    'h': (-1, 0),
    'j': (0, 1),
    'k': (0, -1),
    'l': (1, 0),
    'y': (-1, -1),
    'u': (1, -1),
    'b': (-1, 1),
    'n': (1, 1)
}


def menu(header, options, width, highlighted=[]):
    """Basic, general-purpose menu.
    Allows the user to choose from up to 26 text options."""
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')
    # calculate total height for the header (after auto-wrap) and one line per
    # option
    if header == '':
        header_height = 0
    else:
        header_height = tcod.console_get_height_rect(0, 0, 0, width,
                                                     SCREEN_HEIGHT, header)
    height = len(options) + header_height
    # create an off-screen console that represents the menu's window
    window = tcod.console_new(width, height)

    # print the header, with auto-wrap
    tcod.console_set_default_foreground(window, tcod.white)
    tcod.console_print_rect(window, 0, 0, width, height, header)
    # print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        tcod.console_print(window, 0, y, text)
        y += 1
        letter_index += 1
    for index in highlighted:
        w = len(options[index]) + 4
        tcod.console_set_default_background(window, tcod.grey)
        y = index + header_height
        tcod.console_rect(window, 0, y, w, 1, False, flag=tcod.BKGND_SET)
    # blit the contents of "window" to the root console
    x = SCREEN_WIDTH / 2 - width / 2
    y = SCREEN_HEIGHT / 2 - height / 2
    tcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
    # present the root console to the player and wait for a key-press
    tcod.console_flush()
    tcod.sys_wait_for_event(tcod.EVENT_KEY_PRESS, key, mouse, True)

    # special case: changing to/from fullscreen
    if key.vk == tcod.KEY_F11:
        tcod.console_set_fullscreen(not tcod.console_is_fullscreen())
    elif key.vk == tcod.KEY_ESCAPE:
        return 'escape'
    else:
        # convert the ASCII code to an index; if it corresponds to an option,
        # return it
        index = key.c - ord('a')
        if index >= 0 and index < len(options):
            return index
        return None


def item_choice_menu():
    #player can choose three items
    chosen = []
    choices = [(i.name + ' - ' + i.description) for i in item.itemlist]
    while len(chosen) < 3:
        tcod.console_clear(0)
        choice = menu('CHOOSE THREE ITEMS', choices, SCREEN_WIDTH,
                      highlighted=[item.itemlist.index(i) for i in chosen])
        if choice is not None:
            if choice == 'escape':
                return None
            choice = item.itemlist[choice]
            if choice in chosen:
                chosen.remove(choice)
            else:
                chosen.append(choice)
        if tcod.console_is_window_closed():
            return None
    return chosen


def pick_direction():
    (w, h) = (20, 2)
    window = tcod.console_new(w, h)
    tcod.console_set_default_foreground(window, tcod.white)
    text = 'Pick a direction.'
    tcod.console_print_rect(window, 0, 0, w, h, text)
    x = SCREEN_WIDTH / 2 - w / 2
    y = SCREEN_HEIGHT / 2 - h / 2
    tcod.console_blit(window, 0, 0, w, h, 0, x, y, 1.0, 0.7)
    tcod.console_flush()
    global key
    tcod.sys_wait_for_event(tcod.EVENT_KEY_PRESS, key, mouse, True)
    # special case: changing to/from fullscreen
    if key.vk == tcod.KEY_F11:
        tcod.console_set_fullscreen(not tcod.console_is_fullscreen())
    else:
        key_pressed = game.get_key(key)
        if key_pressed in direction_keys:
            return direction_keys[key_pressed]
        elif key_pressed == tcod.KEY_ESCAPE or \
                tcod.console_is_window_closed():
            return None

def handle_main_menu():
    img = tcod.image_load('menu_background.png')

    while not tcod.console_is_window_closed():
        # show the background image, at twice the regular console resolution
        tcod.image_blit_2x(img, 0, 0, 0)

        # show the game's title, and some credits!
        tcod.console_set_default_foreground(0, tcod.white)
        tcod.console_print_ex(0, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 4,
                              tcod.BKGND_NONE, tcod.CENTER, 'Fleeing the Fray')
        tcod.console_print_ex(0, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 2,
                              tcod.BKGND_NONE, tcod.CENTER,
                              'By Spferical (Spferical@gmail.com)')

        # show options and wait for the player's choice
        choice = menu(
            '', ['Play a new game', 'Continue last game', 'Quit'], 24)

        if choice == 0:  # new game
            game.new_game()
            game.run()
        elif choice == 1:  # load last game
            try:
                save.load_game()
            except:
                msgbox('\n No saved game to load.\n', 24)
                continue
            game.run()
        elif choice == 2 or choice == 'escape':  # quit
            break


def handle_escape_menu():
    choices = ['Save and exit to main menu',
               'Back']
    choice = menu('Escape Menu', choices, 30)
    if choice == 0:
        save.save_game()
        game.alive = False


def msgbox(text, width=50):
    menu(text, [], width)  # use menu() as a sort of "message box"


def handle_inventory_menu(player):
    # show a menu with each item of the inventory as an option
    header = 'INVENTORY'
    if len(player.inventory) == 0:
        options = ['Inventory is empty.']
    else:
        # in the inventory, we want the player's items AND equipment
        options = [item.name for item in player.inventory]
        # equipment:
        for item in player.get_equipped():
            if item:
                # tell player item is being equipped
                options[options.index(item.name)] = item.name + \
                    ' (equipped on ' + item.slot + ')'

    index = menu(header, options, INVENTORY_WIDTH)
    if index is None or len(player.inventory) == 0:
        return None
    return player.inventory[index]


def target_tile(max_range=None):
    # TODO: replace this completely with the target_tile function below
    message('Use the mouse or the keyboard to select a tile...', tcod.blue)
    # return the position of a tile left-clicked in player's FOV (optionally
    # in a range), or (None,None) if right-clicked.
    while True:
        # render the screen. this erases the inventory and shows the names of
        # objects under the mouse.
        render.render_all()
        tcod.console_flush()

        tcod.sys_check_for_event(tcod.EVENT_MOUSE | tcod.EVENT_KEY_PRESS,
                                 key, mouse)
        (x, y) = (mouse.cx, mouse.cy)
        x += render.camera_width
        y += render.camera_height

        # accept the target if the player clicked in FOV, and in case a range
        # is specified, if it's in that range
        if (mouse.lbutton_pressed and tcod.map_is_in_fov(terain.map.fov_map, x, y) and
                (max_range is None or player.distance(x, y) <= max_range)):
            return (x, y)
        elif mouse.rbutton_pressed or key.vk == tcod.KEY_ESCAPE:
            message('Targetting cancelled')
            return (None, None)  # cancel if the player right-clicked or pressed Escape

global messages
messages = []


def message(new_message, color=tcod.white):
    global messages
    # split message, if necessary, among multiple lines
    lines = textwrap.wrap(new_message, MSG_WIDTH)
    # add each line to messages
    # order is reversed because the latest message is on top
    for line in lines:
        # if buffer is full, remove first line to make room for the new
        if len(messages) == MSG_HEIGHT:
            del messages[0]
        timestamp = game.current_turn
        messages.append((line, color, timestamp))


def target_tile(max_range=None):
    # return the position of a tile left-clicked in player's FOV (optionally
    # in a range), or (None,None) if right-clicked.
    message('Use the mouse or the keyboard to select a tile...', tcod.blue)
    prevcolor = tcod.black
    mouse_lastx, mouse_lasty = (x, y) = render.prev_mouse_pos

    while True:
        # render the screen. this erases the inventory and shows the names of
        # objects under the mouse.
        render.render_all()
        tcod.console_flush()

        tcod.console_set_char_background(
            render.con, x, y, prevcolor, tcod.BKGND_SET)  # set last tile's bg color to normal

        tcod.sys_check_for_event(tcod.EVENT_MOUSE | tcod.EVENT_KEY_PRESS,
                                 key, mouse)

        if mouse.dx or mouse.dy:
            (mouse_lastx, mouse_lasty) = (x, y) = (mouse.cx, mouse.cy)
            x = mouse.cx
            y = mouse.cy
            x = x + render.camera_x
            y = y + render.camera_y

        key_pressed = game.get_key(key)
        if key_pressed in direction_keys:
            direction = direction_keys[key_pressed]
            x += direction[0]
            y += direction[1]
        if tcod.map_is_in_fov(terrain.map.fov_map, x, y):
            prevcolor = tcod.console_get_char_background(
                render.con, x, y)  # for resetting the color later
            tcod.console_set_char_background(
                render.con, x, y, tcod.sky, tcod.BKGND_SET)  # visualising the target tile
        else:
            x, y = game.player.x, game.player.y  # if not in fov, reset it to the player coords

        if mouse.rbutton_pressed or key.vk == tcod.KEY_ESCAPE:
            tcod.console_set_char_background(
                render.con, x, y, prevcolor, tcod.BKGND_SET)
            return (None, None)  # cancel if the player right-clicked or pressed Escape

        # accept the target if the player clicked in FOV, and in case a range
        # is specified, if it's in that range
        if ((mouse.lbutton_pressed or key.vk == tcod.KEY_ENTER) and tcod.map_is_in_fov(terrain.map.fov_map, x, y) and
                (max_range is None or game.player.distance(x, y) <= max_range)):
            tcod.console_set_char_background(
                render.con, x, y, prevcolor, tcod.BKGND_SET)
            return (x, y)


def clear_messages():
    global messages
    messages = []
