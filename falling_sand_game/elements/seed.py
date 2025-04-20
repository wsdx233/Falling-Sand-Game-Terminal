# -*- coding: utf-8 -*-
from .base import Powder, Element
import random
import curses
# No top-level imports of Water, Mud, Plant

class Seed(Powder):
    key = 'E'
    name = '种子'
    char = '.'
    color = (curses.COLOR_YELLOW, -1, curses.A_DIM) # Dim Yellow
    density = 2 # Seeds are light
    grow_chance = 0.008
    is_flammable = True
    dissolvable_by_acid = True

    # Define coordinates for checking conditions
    SOURCE_CHECK = [(1, 0)] # Check below for Water or Mud
    SPACE_CHECK = [(-1, 0)] # Check above for empty space

    def run_interactions(self, grid):
        """Seed tries to grow into a Plant if conditions are met."""
        if self.processed: return

        has_source = False
        has_space = False

        # Check below for Water ('W') or Mud ('R') using keys
        for dy, dx in self.SOURCE_CHECK:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                if neighbor and (neighbor.key == 'W' or neighbor.key == 'R'):
                    has_source = True
                    break

        # Check above for Empty Space
        for dy, dx in self.SPACE_CHECK:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                if neighbor is None:
                    has_space = True
                    break
            elif dy == -1 and ny < 0: # Special case: at the top edge counts as space
                 has_space = True
                 break


        # Attempt to grow if conditions met
        if has_source and has_space and random.random() < self.grow_chance:
            # Turn into Plant using grid factory
            new_plant = grid.create_element('P', self.y, self.x)
            grid.set_element(self.y, self.x, new_plant)
            # Let the new plant run its own update/interaction next frame if needed
            # Mark the seed as processed (it's gone)
            self.processed = True
            return

        # Mark as processed if not already done
        if not self.processed:
            self.processed = True


