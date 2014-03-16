from config import EFFECT_FADE_TIME

import libtcodpy as tcod


fade_effects = []

bullet_effects = []


def add_bullet_effect(x, y, direction, frames, frametime=3):
    elapsed = 0
    bullet_effects.append([x, y, direction, frames, frametime, elapsed])


def add_fade_effect(x, y, color, time=EFFECT_FADE_TIME):
    fade_effects.append([x, y, color, time])


def apply_fade_effects(con):
    for e in fade_effects[:]:
        (x, y, color, time) = e

        e[3] -= 1
        if e[3] <= 0:
            fade_effects.remove(e)

        tcod.console_set_char_background(
            con, x, y,
            color * (float(time) / EFFECT_FADE_TIME))


def apply_bullet_effect(con):
    for e in bullet_effects[:]:
        (x, y, direction, frames, frametime, elapsed) = e
        elapsed += 1
        if elapsed >= frametime:
            elapsed = 0
            frames += 1
        (ex, ey) = (x + direction[0] * frames, y + direction[1] * frames)

        e[0] = x
        e[1] = y
        e[3] = frames
        e[4] = elapsed
