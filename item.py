from gobject import Object
import libtcodpy as tcod
import mob
import ai
import ui
import effects
import terrain


class Item(Object):
    owner = None
    description = ''
    ammo = 6
    ammo_name = 'ammo'
    def use(self, user):
        self.ammo -= 1


class Heal(Item):
    char = '+'
    name = 'medkit'
    color = tcod.red
    heal_amount = 20
    ammo = 1
    ammo_name = 'medkits'
    description = 'Heals you completely. One-time use'

    def use(self, user):
        old_hp = user.hp
        user.hp = min(user.max_hp, user.hp + self.heal_amount)
        heal = user.hp - old_hp
        if heal == 0:
            # if player wasn't actually healed, don't cost him
            ui.message('You are already at full health!')
            return False
        ui.message('You recover ' + str(heal) + ' hp!', tcod.green)
        Item.use(self, user)
        return True  # player used a turn


class Grenade(Item):
    char = '*'
    name = 'grenade'
    ammo_name = 'grenades'
    color = tcod.green
    oneuse = True
    damage = 10
    radius = 4
    ammo = 5
    description = 'Thrown 7 tiles, explodes in a %d tile radius' \
            % (radius)

    def use(self, user, direction=None):
        if direction is None:
            direction = ui.pick_direction()
            #if player exitted out if pick_direction or something:
            #just quit
            if direction is None:
                return False
        (dx, dy) = direction
        pos = (user.x, user.y)
        grenade = ActiveGrenade(pos, self.damage, self.radius, dx, dy)
        terrain.map.bullets.append(grenade)
        Item.use(self, user)
        return True


class ActiveGrenade(Object):
    name = 'active grenade'
    char = '*'
    color = tcod.green
    blocks = False
    def __init__(self, pos, damage, radius, dx, dy):
        Object.__init__(self, pos)
        self.damage = damage
        self.radius = radius
        self.dx, self.dy = dx, dy
        self.life = 7

    def update(self):
        if self.life <= 0:
            self.dead = True
            ui.message("The grenade explodes!", tcod.light_red)
            explode(self.x, self.y, self.radius, self.damage)
            return
        self.life -= 1

        # grenades stop when hitting walls
        if terrain.map.is_blocked(self.x + self.dx, self.y + self.dy):
            self.dx = self.dy = 0

        self.x += self.dx
        self.y += self.dy


def explode(x, y, radius, damage):
    """Convenience function for all that explodes"""
    for obj in terrain.map.mobs:
        if obj.get_distance(x, y) <= radius:
            ui.message('The explosion damages the ' + obj.name, tcod.orange)
            obj.take_damage(damage)
    for ex in range(x - radius, x + radius + 1):
        for ey in range(y - radius, y + radius + 1):
            if not terrain.map.is_blocked(ex, ey):
                effects.add_fade_effect(ex, ey, tcod.orange)


class Gun(Item):
    ammo = 15
    damage = 5
    char = '/'
    color = tcod.gray
    bulletcolor = tcod.yellow
    name = 'rifle'
    ammo_name = 'rifle bullets'
    description = 'Fires a bullet. %d starting ammo, %d damage' % (ammo, damage)
    def use(self, user, direction=None):
        if direction is None:
            direction = ui.pick_direction()
            #if player exitted out if pick_direction or something:
            #just quit
            if direction is None:
                return False
        (dx, dy) = direction
        pos = (user.x, user.y)
        bullet = mob.Bullet(pos, self.damage, self.bulletcolor, dx, dy)
        terrain.map.bullets.append(bullet)
        Item.use(self, user)
        return True


itemlist = [Gun, Grenade, Heal]
