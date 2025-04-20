# -*- coding: utf-8 -*-
from .base import Solid, Element # Keep base import
import random
import curses
# No top-level imports of Water, Mud

class Plant(Solid):
    key = 'P'
    name = '植物'
    char = 'p'
    color = (curses.COLOR_GREEN, -1, curses.A_BOLD) # Bright Green
    density = 2 # Light solid
    is_static = False # Can grow
    is_solid = True
    is_flammable = True
    dissolvable_by_acid = True
    grow_chance = 0.003

    # Define potential growth directions (prefer up, then sides)
    GROW_DIRECTIONS = [(-1, 0), (0, -1), (0, 1)]
    # Define coordinates to check for source (below)
    SOURCE_CHECK = [(1, 0)]

    def run_interactions(self, grid):
        """Plant tries to grow into adjacent empty spaces if conditions are met."""
        if self.processed: return

        # 1. Check for growth conditions
        has_source = False
        for dy, dx in self.SOURCE_CHECK:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Needs Water ('W') or Mud ('R') below it (check keys)
                if neighbor and (neighbor.key == 'W' or neighbor.key == 'R'):
                    has_source = True
                    break

        if not has_source:
            if not self.processed: self.processed = True
            return

        # 2. Check available empty spaces for growth
        possible_grow_spots = []
        for dy, dx in self.GROW_DIRECTIONS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx) and grid.get_element(ny, nx) is None:
                 possible_grow_spots.append((ny, nx))

        # 3. Attempt growth
        if possible_grow_spots and random.random() < self.grow_chance:
            gy, gx = random.choice(possible_grow_spots)
            # Create another Plant instance using self.__class__
            new_plant = self.__class__(gy, gx) # Use own class to create more
            grid.set_element(gy, gx, new_plant)
            if new_plant: new_plant.processed = True # Mark the newly grown part as processed

        # Mark the original plant as processed
        if not self.processed:
            self.processed = True


