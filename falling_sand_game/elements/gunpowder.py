# -*- coding: utf-8 -*-
from .base import Powder, Element
import random
import curses
# No top-level imports of Fire

class Gunpowder(Powder):
    key = 'N'
    name = '火药'
    char = 'n'
    # Black foreground, Yellow background
    color = (curses.COLOR_BLACK, curses.COLOR_YELLOW)
    density = 5.5
    is_flammable = True # Key property for Fire/Ember interaction
    dissolvable_by_acid = True
    explode_on_heat_chance = 0.9 # High chance to turn into fire when heated

    # Define coordinates to check for heat sources (includes diagonals)
    HEAT_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    # Define coordinates for explosion spread (orthogonal)
    EXPLOSION_SPREAD = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def run_interactions(self, grid):
        """Gunpowder checks if adjacent to a heat source to explode (turn into fire)."""
        if self.processed: return

        is_heated = False
        for dy, dx in self.HEAT_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check using property
                if neighbor and neighbor.is_heat_source:
                    is_heated = True
                    break

        if is_heated and random.random() < self.explode_on_heat_chance:
            # Turn self into Fire using grid factory
            new_fire = grid.create_element('F', self.y, self.x)
            grid.set_element(self.y, self.x, new_fire)
            if new_fire: new_fire.processed = True # Mark self-fire processed if created
            self.processed = True # Mark gunpowder as processed (it's gone)

            # Spread fire to adjacent flammable/empty cells (simple explosion)
            for dy, dx in self.EXPLOSION_SPREAD:
                 nny, nnx = self.y + dy, self.x + dx
                 if grid.is_valid(nny, nnx):
                     neighbor = grid.get_element(nny, nnx)
                     # Check using key for Fire
                     if neighbor is None or (neighbor.is_flammable and neighbor.key != 'F'):
                         # Check if the cell wasn't already processed (e.g., another explosion part)
                         if neighbor is None or not neighbor.processed:
                             # Create fire using grid factory
                             spread_fire = grid.create_element('F', nny, nnx)
                             grid.set_element(nny, nnx, spread_fire)
                             if spread_fire: spread_fire.processed = True # Mark spread fire processed too
            return # Explosion happened

        # Mark as processed if not already done
        if not self.processed:
            self.processed = True


