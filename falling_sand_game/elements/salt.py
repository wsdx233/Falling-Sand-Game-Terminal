# -*- coding: utf-8 -*-
from .base import Powder, Element
import random
import curses
# No top-level import of Water

class Salt(Powder):
    key = 't' # Changed key from T to t
    name = '盐'
    char = 't'
    color = (curses.COLOR_WHITE, -1, curses.A_DIM) # Dim White
    density = 5.2
    dissolve_chance = 0.5 # Chance to dissolve per adjacent water cell per step
    dissolvable_by_acid = True # Acid dissolves salt too

    # Define coordinates to check for water (orthogonal)
    WATER_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def run_interactions(self, grid):
        """Salt checks for adjacent water to dissolve."""
        if self.processed: return

        found_water = False
        for dy, dx in self.WATER_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check using key 'W' and ensure neighbor not processed
                if neighbor and neighbor.key == 'W' and not neighbor.processed:
                    found_water = True
                    break # Found one water source

        if found_water and random.random() < self.dissolve_chance:
            # Turn into Water using grid factory
            # Copy tags from salt to the new water? Maybe not, water is just water.
            new_water = grid.create_element('W', self.y, self.x)
            if new_water:
                 grid.set_element(self.y, self.x, new_water)
            # Don't mark the new water as processed, let it flow next frame
            self.processed = True # Mark the salt as processed (it's gone)
            return

        # Base Powder update handles final processing if no interaction
