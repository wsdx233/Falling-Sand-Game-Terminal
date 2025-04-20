# -*- coding: utf-8 -*-
from .base import Gas
import random
import curses

class Smoke(Gas):
    key = 'K'
    name = '烟'
    # Using '.' like original, maybe 'k' is better? Sticking to '.' for now.
    char = '.'
    color = (curses.COLOR_WHITE, -1, curses.A_DIM) # Dim White -> Grey
    density = -6 # Slightly denser than base gas, lighter than steam/fire
    rise_speed = 1
    spread_factor = 2
    dissipate_chance = 0.02

    def run_interactions(self, grid):
        """Smoke has a chance to dissipate."""
        if self.processed: return

        if random.random() < self.dissipate_chance:
            grid.set_element(self.y, self.x, None)
            self.processed = True
            return

        # Mark as processed if not already done
        # Note: Gas movement might already mark it processed
        if not self.processed:
            self.processed = True

    def check_boundary_dissipation(self, grid):
        """Smoke has a higher chance to dissipate at the top boundary."""
        # Inherited Gas checks if self.y == 0 basically
        if random.random() < self.dissipate_chance * 2.5: # Increased chance at boundary
             grid.set_element(self.y, self.x, None)
             self.processed = True
