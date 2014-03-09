from gobject import Object
import libtcodpy as tcod
import mob
import ai
import ui
import terrain


class Item(Object):
    owner = None
    description = ''
    def use(self, user):
        pass


class Heal(Item):
    char = '!'
    name = 'heal'
    color = tcod.red
    mana_use = 30
    heal_amount = 20
    description = 'Heals you completely using %d mana' % mana_use

    def use(self, user):
        old_hp = user.hp
        user.hp = min(user.max_hp, user.hp + self.heal_amount)
        heal = user.hp - old_hp
        if heal == 0:
            # if player wasn't actually healed, don't cost him
            ui.message('You are already at full health!')
            return False
        ui.message('You recover ' + str(heal) + ' hp!', tcod.green)
        user.mana -= self.mana_use
        return True  # player used a turn


class Regeneration(Item):
    char = '?'
    name = 'regen amulet'
    color = tcod.red
    mana_use = 0
    heal_interval = 4
    heal_time_elapsed = 0
    description = 'Passively heals you 1 hp every %d turns' % heal_interval

    def update(self):
        self.heal_time_elapsed += 1
        if self.heal_time_elapsed >= self.heal_interval:
            self.heal_time_elapsed = 0
            self.owner.hp = min(self.owner.hp + 1, self.owner.max_hp)

    def use(self, user):
        ui.message('This is a passive item!')


class Confuse(Item):
    char = '?'
    name = 'scroll of confusion'
    color = tcod.purple
    mana_use = 20
    description = 'Confuses an enemy for 10 turns using %d mana' \
            % mana_use

    def use(self, user):
        pos = ui.target_tile()
        if pos == (None, None):
            return False
        for object in terrain.map.objects:
            if (object.x, object.y) == pos and isinstance(object, mob.Mob):
                if object.ai:
                    object.ai = ai.ConfusedMob(object.ai)
                    ui.message(
                        'The ' + object.name + ' is confused!', tcod.blue)
                    user.mana -= self.mana_use
                    return True
        # if code hasn't returned yet, no mob is at the position
        ui.message('There is no being there!')


class Fireball(Item):
    char = '*'
    name = 'fireball'
    color = tcod.green
    mana_use = 50
    damage = 10
    radius = 2
    description = 'Explodes in a %d tile radius dealing %d damage using %d mana; targetable.' \
            % (radius, damage, mana_use)

    def use(self, user):
        (x, y) = ui.target_tile()
        if (x, y) == (None, None):
            return False
        explode(x, y, self.radius, self.damage)
        user.mana -= self.mana_use
        return True


def explode(x, y, radius, damage):
    """Convenience function for all that explodes"""
    for obj in terrain.map.objects:
        if isinstance(obj, mob.Mob) and \
                obj.get_distance(x, y) <= radius:
            ui.message('The ' + obj.name + ' gets burned for ' +
                       str(damage) + ' hit points.', tcod.orange)
            obj.take_damage(damage)


class Crossbow(Item):
    mana_use = 5
    damage = 5
    color = tcod.yellow
    name = 'crossbow'
    description = 'Fires a bolt, dealing %d damage using %d mana' % (damage, mana_use)

    def use(self, user, direction=None):
        if direction is None:
            direction = ui.pick_direction()
            #if player exitted out if pick_direction or something:
            #just quit
            if direction is None:
                return False
        user.mana -= self.mana_use
        (dx, dy) = direction
        pos = (user.x, user.y)
        bullet = mob.Bullet(pos, self.damage, self.color, dx, dy)
        terrain.map.objects.append(bullet)
        return True


class SelfDestruct(Item):
    mana_use = 50
    damage = 10
    radius = 10
    color = tcod.cyan
    name = 'self-destruct package'
    description = 'Explodes, dealing %d damage to all near you AND you, using %d mana.' % (damage, mana_use)
    def use(self, user):
        user.mana -= self.mana_use
        explode(user.x, user.y, self.radius, self.damage)
        return True


itemlist = [Crossbow, Heal, Regeneration, Fireball, Confuse, SelfDestruct]
