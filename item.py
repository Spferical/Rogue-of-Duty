from gobject import Object
import libtcodpy as tcod
import mob
import ai
import ui
import terrain


class Item(Object):
    owner = None
    description = ''
    ammo = 6
    def use(self, user):
        self.ammo -= 1


class Heal(Item):
    char = '+'
    name = 'medkit'
    color = tcod.red
    heal_amount = 20
    ammo = 1
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
    color = tcod.green
    oneuse = True
    damage = 10
    radius = 2
    ammo = 2
    description = 'Explodes in a %d tile radius dealing %d damage; thrown.' \
            % (radius, damage)

    def use(self, user):
        (x, y) = ui.target_tile()
        if (x, y) == (None, None):
            return False
        explode(x, y, self.radius, self.damage)
        Item.use(self, user)
        return True


def explode(x, y, radius, damage):
    """Convenience function for all that explodes"""
    for obj in terrain.map.objects:
        if isinstance(obj, mob.Mob) and \
                obj.get_distance(x, y) <= radius:
            ui.message('The ' + obj.name + ' gets burned for ' +
                       str(damage) + ' hit points.', tcod.orange)
            obj.take_damage(damage)


class Gun(Item):
    ammo = 5
    damage = 5
    char = '/'
    color = tcod.gray
    name = 'rifle'
    description = 'Fires a bullet. %d ammo, %d damage' % (ammo, damage)
    def use(self, user, direction=None):
        if direction is None:
            direction = ui.pick_direction()
            #if player exitted out if pick_direction or something:
            #just quit
            if direction is None:
                return False
        (dx, dy) = direction
        pos = (user.x, user.y)
        bullet = mob.Bullet(pos, self.damage, self.color, dx, dy)
        terrain.map.objects.append(bullet)
        Item.use(self, user)
        return True


itemlist = [Gun, Grenade, Heal]
