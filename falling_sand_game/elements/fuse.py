# -*- coding: utf-8 -*-
from .base import Solid, Element
import random
import curses
# No top-level imports of other elements (like Ember)

class Fuse(Solid):
    key = 'U'
    name = '导火索'
    char = '-'
    color = (curses.COLOR_RED, -1)
    density = 9 # Relatively dense solid
    is_static = False # Can change state, so not truly static
    is_flammable = True # Can be ignited
    dissolvable_by_acid = True

    # Define coordinates to check for ignition sources (orthogonal)
    HEAT_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def run_interactions(self, grid):
        """Fuse checks if adjacent to a heat source to ignite."""
        if self.processed: return

        is_lit = False
        for dy, dx in self.HEAT_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check using property, not class type
                if neighbor and neighbor.is_heat_source:
                    is_lit = True
                    break

        if is_lit:
            # Turn into Ember using grid factory method
            new_ember = grid.create_element('B', self.y, self.x)
            grid.set_element(self.y, self.x, new_ember)
            # Don't mark the new ember as processed, let it fall/interact next frame
            self.processed = True # Mark the fuse as processed (it's gone)
            return

        # Mark as processed if not already done
        if not self.processed:
            self.processed = True



