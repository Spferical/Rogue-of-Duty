import libtcodpy as tcod
import mob
import random
from config import DIAGONAL_MOVEMENT, TORCH_RADIUS
import terrain
import math


class BasicMonster:
    # AI for a basic monster
    target = None
    state = 'resting'

    def update(self):
        # a basic monster takes its turn. If you can see it, it can see you
        if self.target:
            target_dist = self.owner.distance_to(self.target)
        for m in terrain.map.mobs:
            if m != self.target:
                if m.faction != self.owner.faction:
                    dist = self.owner.distance_to(m)
                    if dist < TORCH_RADIUS:
                        if not self.target or dist < target_dist:
                            self.target = m
                            self.state = 'chasing'
                            return

        # before chasing, make sure target is not dead
        if self.target:
            if self.target.dead:
                self.target = None
                self.state = 'resting'
            else:
                # move towards target if far away, or fire
                if self.owner.distance_to(self.target) >= 2:
                    if isinstance(self.owner, mob.RangedMob) and random.randint(0, 1) == 0:
                        self.fire_towards_target_if_clear()
                    else:
                        self.owner.move_towards(self.target.x, self.target.y)

                # close enough, attack!
                else:
                    self.owner.attack(self.target)

    def fire_towards_target_if_clear(self):
        #vector from this object to the target, and distance
        dx = self.target.x - self.owner.x
        dy = self.target.y - self.owner.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        #normalize it to length 1 (preserving direction), then round it and
        #convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        test_positions = []
        for i in range(1, 4):
            test_positions.append((self.owner.x + dx * i, self.owner.y + dy * i))

        for mob in terrain.map.mobs:
            for pos in test_positions:
                if mob.faction == self.owner.faction and (mob.x, mob.y) == pos:
                    return

        self.owner.fire_towards(self.target.x, self.target.y)


class ConfusedMob:
    confused_turns = 10
    state = 'confused'

    def __init__(self, old_ai):
        self.old_ai = old_ai
        self.owner = self.old_ai.owner

    def update(self):
        if DIAGONAL_MOVEMENT:
            (dx, dy) = (random.randint(-1, 1), random.randint(-1, 1))
        else:
            if random.randint(0, 1):
                (dx, dy) = (random.randint(-1, 1), 0)
            else:
                (dx, dy) = (0, random.randint(-1, 1))
        self.owner.move_or_attack(dx, dy)
        self.confused_turns -= 1
        if self.confused_turns <= 0:
            self.owner.ai = self.old_ai

class SoldierAI(BasicMonster):
    def update(self):
        if self.owner.x == 0:
            # we don't want soldiers to be scrolled off of the map
            # when the player moves
            self.move_towards_right()
        else:
            if self.owner.healer:
                for m in terrain.map.mobs:
                    if not m.dead and \
                            m.hp < m.max_hp and \
                            m.faction == self.owner.faction:
                        dist = self.owner.distance_to(m)
                        if dist == 1:
                            self.owner.heal(m)
                            self.state = 'healing'
                            break
                # no mobs found
                if self.state == 'healing':
                    self.state = 'resting'
            BasicMonster.update(self);
            if self.state == 'resting':
                self.state = 'advancing'

            if self.state == 'advancing':
                if self.owner.faction == 1:
                    self.move_towards_right()
                else:
                    self.move_towards_left()
    def move_towards_right(self):
        self.owner.move_or_get_mob(1, 0)
    def move_towards_left(self):
        self.owner.move_or_get_mob(-1, 0)

