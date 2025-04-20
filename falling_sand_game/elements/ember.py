# -*- coding: utf-8 -*-
from .base import Powder, Element
import random
import curses
# No top-level imports of Ash, Fire, Smoke

class Ember(Powder):
    key = 'B'
    name = '余烬'
    char = 'b'
    # Red foreground, Yellow background
    color = (curses.COLOR_RED, curses.COLOR_YELLOW)
    density = 4.5 # Similar to ash but maybe slightly denser
    is_heat_source = True
    ignite_chance = 0.25
    burn_out_chance_ignited = 0.04
    burn_out_chance_idle = 0.02
    dissolvable_by_acid = True

    # Coordinates to check for igniting neighbors (usually orthogonal)
    IGNITE_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def run_interactions(self, grid):
        """Ember tries to ignite flammable neighbors and might burn out."""
        if self.processed: return

        ignited_neighbor = False
        # 1. Try to ignite neighbors
        flammable_neighbors = []
        for dy, dx in self.IGNITE_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check if neighbor exists, is flammable, not processed,
                # and not Fire ('F') or Ember ('B') using keys
                if neighbor and neighbor.is_flammable and not neighbor.processed \
                   and neighbor.key != 'F' and neighbor.key != 'B':
                     flammable_neighbors.append((ny, nx, neighbor))

        if flammable_neighbors and random.random() < self.ignite_chance:
            ny, nx, target_neighbor = random.choice(flammable_neighbors)
            # Turn neighbor into Fire using grid factory
            new_fire = grid.create_element('F', ny, nx)
            grid.set_element(ny, nx, new_fire)
            if new_fire: new_fire.processed = True # Mark new fire as processed
            ignited_neighbor = True

        # 2. Chance to burn out
        current_burn_out_chance = self.burn_out_chance_ignited if ignited_neighbor else self.burn_out_chance_idle
        if random.random() < current_burn_out_chance:
            # Create Ash using grid factory
            new_ash = grid.create_element('H', self.y, self.x)
            grid.set_element(self.y, self.x, new_ash)
            # Don't mark new_ash as processed
            self.processed = True # Mark the ember as processed (it's gone)
            return # Stop further processing for this ember

        # Mark as processed if not already done
        if not self.processed:
            self.processed = True