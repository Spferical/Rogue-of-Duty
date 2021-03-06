import libtcodpy as tcod
import mob
import ui
import game
import terrain
import textwrap
import effects
from config import SCREEN_WIDTH, SCREEN_HEIGHT, RIGHT_PANEL_WIDTH, \
    BAR_WIDTH, MAP_WIDTH, MAP_HEIGHT, BOTTOM_PANEL_WIDTH, \
    BOTTOM_PANEL_HEIGHT, MSG_X, MOUSE_HIGHLIGHT_COLOR, CAMERA_WIDTH, \
    CAMERA_HEIGHT, EFFECT_FADE_TIME


con = right_panel = bottom_panel = None
prev_mouse_pos = (0, 0)

(camera_x, camera_y) = (0, 0)

def move_camera(target_x, target_y):
	global camera_x, camera_y
 
	#new camera coordinates (top-left corner of the screen relative to the map)
	x = target_x - CAMERA_WIDTH / 2  #coordinates so that the target is at the center of the screen
	y = target_y - CAMERA_HEIGHT / 2
 
	#make sure the camera doesn't see outside the map
	if x > MAP_WIDTH - CAMERA_WIDTH - 1: x = MAP_WIDTH - CAMERA_WIDTH
	if y > MAP_HEIGHT - CAMERA_HEIGHT - 1: y = MAP_HEIGHT - CAMERA_HEIGHT
	if x < 0: x = 0
	if y < 0: y = 0
 
	(camera_x, camera_y) = (x, y)


def render_bottom_panel():
    # fill it with black
    tcod.console_set_default_background(bottom_panel, tcod.black)
    tcod.console_clear(bottom_panel)
    tcod.console_set_default_foreground(bottom_panel, tcod.white)
    # draw separating line
    for x in range(BOTTOM_PANEL_WIDTH):
        tcod.console_set_char(bottom_panel, x, 0, 205)
    #draw distance traveled
    tcod.console_print(bottom_panel, 1, 1, 'DISTANCE:' + 
                       str(terrain.map.scroll_amount + game.player.x))
    # render player stats
    tcod.console_print(bottom_panel, 1, 4, 'Strength: ' +
                       str(game.player.strength))
    tcod.console_print(bottom_panel, 1, 5, 'Defense: ' +
                       str(game.player.defense))
    tcod.console_print(bottom_panel, 1, 7, '[z]' + \
                       str(game.player.inventory[0].name))
    tcod.console_print(bottom_panel, 1, 9, '[x]' + \
                       str(game.player.inventory[1].name))
    tcod.console_print(bottom_panel, 1, 11, '[c]' + \
                       str(game.player.inventory[2].name))
    tcod.console_set_default_foreground(bottom_panel, tcod.cyan)
    tcod.console_print(bottom_panel, 4, 8, \
                       str(game.player.inventory[0].ammo) + ' ammo')
    tcod.console_print(bottom_panel, 4, 10, \
                       str(game.player.inventory[1].ammo) + ' ammo')
    tcod.console_print(bottom_panel, 4, 12, \
                       str(game.player.inventory[2].ammo) + ' ammo')
    tcod.console_set_alignment(bottom_panel, tcod.LEFT)
    # render game messages
    render_messages()
    # render object and tile names under mouse
    tcod.console_set_default_foreground(bottom_panel,
                                        tcod.light_gray)
    tcod.console_print(bottom_panel, 1, 0, game.get_names_under_mouse())
    tcod.console_blit(
        bottom_panel, 0, 0, BOTTOM_PANEL_WIDTH,
        BOTTOM_PANEL_HEIGHT, 0, 0, SCREEN_HEIGHT - BOTTOM_PANEL_HEIGHT)


def render_messages():
    # render all game messages
    y = 1
    messages = ui.messages[:]
    # messages.reverse()
    for (line, color, timestamp) in messages:
        # fade out old messages
        age = game.current_turn - timestamp
        color = color * (1.0 - min(age / 5.0, 3 / 5.0))

        tcod.console_set_default_foreground(bottom_panel,
                                            color)
        tcod.console_print_ex(bottom_panel, MSG_X, y, tcod.CENTER,
                              tcod.BKGND_NONE, line)
        y += 1


def get_closest_mobs_to_player():
    # gets 5 closest mobs to player
    mobs = terrain.map.mobs[:]
    mobs.sort(key=game.player.distance_to)
    for object in mobs[:]:
        if not tcod.map_is_in_fov(
                terrain.map.fov_map, object.x, object.y):
            mobs.remove(object)
    return mobs[:10]


def render_stats_of_mobs(mobs):
    y = 0
    for m in mobs:
        tcod.console_set_default_background(right_panel, tcod.black)
        tcod.console_set_default_foreground(right_panel, m.color)
        tcod.console_put_char(right_panel, 1, y, m.char)
        tcod.console_set_default_foreground(right_panel, tcod.white)
        tcod.console_print(right_panel, 3, y, m.name)
        y += 1
        for line in textwrap.wrap(m.description, RIGHT_PANEL_WIDTH - 1):
            tcod.console_print(right_panel, 1, y, line)
            y += 1
        #tcod.console_set_default_foreground(right_panel, tcod.red)
        if m.ai:
            tcod.console_print(right_panel, 1, y, 'Strength: ' + str(m.strength))
            y += 1

        render_bar(right_panel, 1, y, BAR_WIDTH, 'HP', m.hp,
                   m.max_hp, tcod.red, tcod.darker_red)
        y += 2


def render_right_panel():
    # clear panel
    tcod.console_set_default_background(right_panel, tcod.black)
    tcod.console_clear(right_panel)
    # drawl separating line
    for y in range(SCREEN_HEIGHT):
        tcod.console_set_char(right_panel, 0, y, 186)
    # show stats for the closest mobs to player
    # note: this includes the player
    render_stats_of_mobs(get_closest_mobs_to_player())
    # show player's stats
    # blit to root console
    tcod.console_blit(
        right_panel, 0, 0, RIGHT_PANEL_WIDTH, SCREEN_HEIGHT, 0, CAMERA_WIDTH, 0)


def draw_tile(x, y):
    tile = terrain.map[x][y]
    screen_x = x - camera_x
    screen_y = y - camera_y

    # if player cannot see tile, make it darker
    visible = tcod.map_is_in_fov(terrain.map.fov_map, x, y)
    if visible or tile.explored:
        if visible:
            fg_color = tile.fg_color
            bg_color = tile.bg_color
            # set tile to explored for future rendering when not seen
            tile.explored = True
        elif tile.explored:
            fg_color = tile.fg_color * 0.5  # tcod.dark_grey
            bg_color = tile.bg_color * 0.5  # tcod.dark_grey

        tcod.console_put_char_ex(con, screen_x, screen_y,
                                 tile.char, fg_color, bg_color)


def draw_object(object):
    # sets color and draws the character that represents the object
    x = object.x - camera_x
    y = object.y - camera_y
    if isinstance(object, mob.Mob) or isinstance(object, mob.Corpse):
        if object.damaged > 0:
            tcod.console_put_char_ex(con, x, y, object.char, object.color,
                                tcod.red * (object.damaged / float(EFFECT_FADE_TIME)))
            object.damaged -= 1
            return
    tcod.console_set_default_foreground(con, object.color)
    tcod.console_put_char(con, x, y, object.char, tcod.BKGND_NONE)


def clear_object(object):
    # erases the character that represents this object,
    # drawing the tile at that position on top of it
    draw_tile(object.x, object.y)


def clear_tile(x, y):
    x = x - camera_x
    y = y - camera_y
    tcod.console_put_char_ex(con, x, y, ' ', tcod.white, tcod.black)


def clear_all_tiles():
    # draw each tile in map
    for x in range(MAP_WIDTH):
        for y in range(MAP_HEIGHT):
            clear_tile(x, y)


def draw_all_tiles():
    # draw each tile in map
    for x in range(MAP_WIDTH):
        for y in range(MAP_HEIGHT):
            draw_tile(x, y)


def highlight_mouse_position():
    # mouse is updated in game.handle_keys, so we don't need to update it
    (x, y) = (ui.mouse.cx, ui.mouse.cy)
    if x < MAP_WIDTH and y < MAP_HEIGHT:
        map_x = x + camera_x
        map_y = y + camera_y
        if tcod.map_is_in_fov(terrain.map.fov_map, map_x, map_y):
            global prev_mouse_pos
            prev_mouse_pos = (x, y)
            tcod.console_set_char_background(con, x, y, MOUSE_HIGHLIGHT_COLOR)


def dehilight_old_mouse_position():
    (x, y) = prev_mouse_pos
    color = terrain.map[x][y].bg_color
    tcod.console_set_char_background(con, x, y, color)


def render_all():
    # draw each object
    for list in terrain.map.objectlists:
        for object in list:
            if tcod.map_is_in_fov(terrain.map.fov_map, object.x, object.y):
                draw_object(object)
    dehilight_old_mouse_position()
    highlight_mouse_position()
    effects.apply_fade_effects(con)
    # blit renderer main (map) console to tcod's main console
    tcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
    # render panel on right
    render_right_panel()
    # render panel on bottom
    render_bottom_panel()
    # update the display that the player sees
    tcod.console_flush()

    # clear all objects for the next frame
    for list in terrain.map.objectlists:
        for object in list:
            clear_object(object)


def render_bar(panel, x, y, total_width, name, value, maximum, bar_color,
               back_color):
    "renders a bar (HP, experience, etc). "
    # first calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)

    # render the background first
    tcod.console_set_default_background(panel, back_color)
    tcod.console_rect(panel, x, y, total_width, 1, False, tcod.BKGND_SET)

    # now render the bar on top
    tcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        tcod.console_rect(panel, x, y, bar_width, 1, False, tcod.BKGND_SET)
    # finally, some centered text with the values
    tcod.console_set_default_foreground(panel, tcod.white)
    tcod.console_print_ex(
        panel, x + total_width // 2, y, tcod.BKGND_NONE, tcod.CENTER,
        bytes(name + ': ' + str(value) + '/' + str(maximum), 'utf-8'))


def init():
    global con, right_panel, bottom_panel, prev_mouse_pos
    con = tcod.console_new(MAP_WIDTH, MAP_HEIGHT)
    right_panel = tcod.console_new(RIGHT_PANEL_WIDTH,
                                   SCREEN_HEIGHT)
    bottom_panel = tcod.console_new(BOTTOM_PANEL_WIDTH,
                                    BOTTOM_PANEL_HEIGHT)
