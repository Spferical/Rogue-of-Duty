#!/usr/bin/python2
import libtcodpy as tcod
import ui
from config import SCREEN_WIDTH, SCREEN_HEIGHT, MAX_FPS, GAME_NAME

def main():
    tcod.console_set_custom_font(
            'terminal10x16_gs_ro.png',
            flags=tcod.FONT_LAYOUT_ASCII_INROW)
    tcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, GAME_NAME,
                        False)
    tcod.sys_set_fps(MAX_FPS)
    ui.handle_main_menu()

if __name__ == '__main__':
    main()
