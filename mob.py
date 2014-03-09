from gobject import Object
import libtcodpy as tcod
import math
import ai
import ui
import copy
import item
import terrain
import random
from config import DIAGONAL_MOVEMENT, BULLET_LIFE, DAMAGE_EFFECT_FADE


class Mob(Object):
    max_hp = 10
    strength = 2
    defense = 0
    blocks = True
    ai = None
    description = 'this is a Mob'
    damaged = 0

    def __init__(self, pos):
        Object.__init__(self, pos)
        self.hp = self.max_hp
        # ai is defined in the individual mob type's class
        # we need a new instance of it for the object
        if self.ai:
            self.ai = copy.copy(self.ai)
            self.ai.owner = self

    def update(self):
        if self.ai:
            self.ai.update()

    def move_or_attack(self, dx, dy):
        x = self.x + dx
        y = self.y + dy

        target = None
        for object in terrain.map.objects:
            if isinstance(object, Mob) and (object.x, object.y) == (x, y):
                target = object
                break
        if target:
            self.attack(target)
            return 'attacked'
        else:
            return self.move(dx, dy)

    def attack(self, target):
        damage = target.take_damage(self.strength)
        if isinstance(self, Player) or isinstance(target, Player):
            color = tcod.red
        else:
            color = tcod.white
        if damage > 0:
            if target == self:
                ui.message(self.name.capitalize() + ' attacks itself for ' +
                           str(damage) + ' hit points', tcod.white)
            else:
                ui.message(self.name.capitalize() + ' attacks ' +
                           target.name +
                           ' for ' + str(damage) + ' hit points.',
                           color)
        else:
            ui.message(self.name.capitalize(
            ) + ' attacks ' + target.name + ' but it has no effect!')

    def take_damage(self, damage):
        damage -= self.defense
        if damage > 0:
            self.damaged = DAMAGE_EFFECT_FADE
            self.hp -= damage
            if self.hp <= 0:
                self.dead = True
        return damage

    def move(self, dx, dy):
        x = self.x + dx
        y = self.y + dy
        m = self.move_to(x, y)
        if m == 'blocked' and DIAGONAL_MOVEMENT:
            # smooth wall-hugging
            # the following code makes it so:
                # the player hugs the wall when walking into one at an angle
                # mobs walk around their allies

            # basically, if it is possible to move to a non-blocked spot via
            # changing either dx or dy by one, do it
            if dx == 0:
                possible_x_moves = [-1, 1]
            else:
                possible_x_moves = [0]
            if dy == 0:
                possible_y_moves = [-1, 1]
            else:
                possible_y_moves = [0]
            for ndx in possible_x_moves:
                m = self.move_to(self.x + ndx, y)
                if m != 'blocked':
                    return m
            for ndy in possible_y_moves:
                m = self.move_to(x, self.y + ndy)
                if m != 'blocked':
                    return m
            return 'blocked'
        else:
            return m

    def move_to(self, x, y):
        if not (x, y) == (self.x, self.y) and not terrain.map.is_blocked(x, y):
            self.x, self.y = x, y
            return 'moved'
        else:
            return 'blocked'

    def move_towards(self, target_x, target_y):
        #libtcod CANNOT path into a blocked tile.
        #this is bad because this game treats mobs as blocked.
        #this allows mobs to path around each other
        #so, we won't change it
        #we will temporarily make the target tile unblocked
        #JUST for this computation
        #this is a hack
        #but it works
        blocked = terrain.map.is_blocked(target_x, target_y)
        if blocked:
            tcod.map_set_properties (terrain.map.fov_map, target_x, target_y, 
                                     True, True)
        tcod.path_compute(terrain.map.path, self.x, self.y, target_x, target_y)
        if blocked:
            terrain.map.update_fov_tile(target_x, target_y)
        (x, y) = tcod.path_walk(terrain.map.path, True)
        if not (x, y) == (None, None):
            dx, dy = (x - self.x, y - self.y)
            self.move(dx, dy)

    def die(self):
        ui.message(self.name.capitalize() + ' dies!', tcod.red)
        terrain.map.objects.insert(0, Corpse(self))


class Bullet(Object):
    name = 'crossbow bolt'
    faction = -1
    blocks = False
    #dict of ascii chars that will be used with different bullet velocities
    chars = {
        (1, 0) : '-',
        (-1, 0) : '-',
        (1, 1) : '\\',
        (-1, -1) : '\\',
        (0, 1) : '|',
        (0, -1) : '|',
        (-1, 1) : '/',
        (1, -1) : '/',
    }
    def __init__(self, pos, damage, color, dx, dy):
        Object.__init__(self, pos)
        self.damage = damage
        self.color = color
        self.dx = dx
        self.dy = dy
        self.char = self.chars[(self.dx, self.dy)]
        self.life = BULLET_LIFE
        #on creation, check for anyone directly in its way
        #so that if player fires a bullet at something adjacent to him,
        #it doesn't get a blow in before it dies
        #it feels better this way when playing
        #hackish way of doing it though: update, then roll back updates
        self.update()
        if not self.dead:
            self.x -= self.dx
            self.y -= self.dy
            self.life += 1


    def update(self):
        if self.life <= 0:
            self.dead = True
            return
        self.life -= 1
        self.x += self.dx
        self.y += self.dy
        if terrain.map.is_blocked(self.x, self.y):
            self.dead = True
        for object in terrain.map.objects:
            if object.x == self.x and object.y == self.y and \
                    isinstance(object, Mob):
                object.take_damage(self.damage - object.defense)
                ui.message(object.name.capitalize() + 
                        ' is hit by a ' + self.name + ', ' +
                        'taking ' + str(self.damage - object.defense) +
                        ' damage')
                self.dead = True
                break


class RangedMob(Mob):
    can_fire = True
    bullet_damage = 5
    bullet_color = tcod.yellow

    def fire_towards(self, target_x, target_y):
        #vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        #normalize it to length 1 (preserving direction), then round it and
        #convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.fire(dx, dy)

    def fire(self, dx, dy):
        bullet = Bullet((self.x, self.y), self.bullet_damage, self.bullet_color,
                        dx, dy)
        bullet.update()
        terrain.map.objects.append(bullet)



class Player(Mob):
    char = '@'
    faction = 1
    name = 'player'
    max_hp = 15
    strength = 6
    defense = 0
    faction = 1
    description = 'a stinking human thief'
    blocks = False
    def __init__(self, pos):
        Mob.__init__(self, pos)
        self.color = factions[self.faction]
        #if we don't create a new list every game stary, the player's inventory
        #would carry over each game... which we don't want
        self.inventory = []

    def use(self, item):
        if item.ammo <= 0:
            ui.message("You don't have enough ammo!")
            return False
        else:
            return item.use(self)

    def get(self, item):
        self.inventory.append(item)
        item.owner = self

    def drop(self, dropped_item):
        # remove from the player's inventory and add to the map
        self.inventory.remove(dropped_item)
        dropped_item.owner = None
        ui.message('You drop the ' + dropped_item.name)
        # if there is an item on the square the player is standing on,
        # pick it up
        for object in terrain.map.objects:
            if isinstance(object, item.Item) and \
                    (object.x, object.y) == (self.x, self.y):
                self.pick_up(object)
                # there shouldn't be more than one item on a square
                break
        # set item position to player's
        (dropped_item.x, dropped_item.y) = (self.x, self.y)
        # insert item to front of list so it is drawn in the back
        terrain.map.objects.insert(0, dropped_item)

    def die(self):
        ui.message(self.name.capitalize() + ' dies!', tcod.red)
        self.char = '%'
        self.color = tcod.dark_red
        self.name = 'remains of ' + self.name

    def move_to(self, x, y):
        m = Mob.move_to(self, x, y)
        if m == 'moved':
            # pick up any ammo from weapons we have on the ground
            for o in terrain.map.objects:
                if (o.x == self.x and o.y == self.y) and\
                        isinstance(o, item.Item):

                    for i in self.inventory:
                        if o.name == i.name:
                            o.dead = True
                            i.ammo += o.ammo
                            ui.message("You pick up %d %s!"
                                       % (o.ammo, i.ammo_name))
                            break
        return m



class Corpse(Object):
    char = '%'
    color = tcod.dark_red
    damaged = DAMAGE_EFFECT_FADE

    def __init__(self, mob):
        Object.__init__(self, (mob.x, mob.y))
        self.name = 'remains of ' + mob.name

    def update(self):
        pass


class Infantry(RangedMob):
    def __init__(self, pos, faction):
        self.color = factions[faction]
        self.faction = faction
        RangedMob.__init__(self, pos)

    def die(self):
        RangedMob.die(self)
        if random.randint(0, 1) == 1:
            drop = item.Gun((self.x, self.y))
            drop.ammo = random.randint(1, 10)
            terrain.map.objects.append(drop)

    char = 'I'
    name = 'infantry'
    description = 'a standard soldier'
    max_hp = 10
    strength = 4
    ai = ai.BasicMonster()

moblist = [Infantry]
factions = {
    1 : tcod.cyan,
    2 : tcod.red,
}
