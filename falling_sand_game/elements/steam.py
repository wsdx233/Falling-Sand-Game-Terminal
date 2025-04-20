# -*- coding: utf-8 -*-
from .base import Gas, Element
import random
import curses
# No top-level imports of Water, Ash

class Steam(Gas):
    key = 'G'
    name = '蒸汽'
    char = '^'
    color = (curses.COLOR_WHITE, -1, curses.A_DIM) # Dim White
    density = -5.5 # Slightly denser than smoke/base gas, lighter than fire
    rise_speed = 1
    spread_factor = 2
    condense_chance = 0.005
    cool_ember_chance = 0.05

    # Define coordinates for cooling check (orthogonal)
    COOL_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def run_interactions(self, grid):
        """Steam can condense back into water or cool embers."""
        if self.processed: return

        # 1. Chance to condense
        if random.random() < self.condense_chance:
            # Create Water using grid factory
            new_water = grid.create_element('W', self.y, self.x)
            grid.set_element(self.y, self.x, new_water)
            # Don't mark water processed, let it fall next frame
            self.processed = True # Steam is gone
            return

        # 2. Try to cool adjacent embers (if not condensed)
        cooled_neighbor = False
        for dy, dx in self.COOL_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check if neighbor is Ember ('B') by key and not processed
                if neighbor and neighbor.key == 'B' and not neighbor.processed:
                     if random.random() < self.cool_ember_chance:
                         # Create Ash using grid factory
                         new_ash = grid.create_element('H', ny, nx)
                         grid.set_element(ny, nx, new_ash)
                         if new_ash: new_ash.processed = True # Mark ash processed
                         cooled_neighbor = True
                         break # Cool only one ember per step

        # Mark as processed if not already done
        if not self.processed:
            self.processed = True

    def check_boundary_dissipation(self, grid):
        """Steam doesn't dissipate at boundary, it might condense."""
        pass # Override Gas behavior


