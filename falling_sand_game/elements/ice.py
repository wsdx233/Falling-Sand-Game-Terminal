# -*- coding: utf-8 -*-
from .base import Solid, Element
import random
import curses
# No top-level imports of Water, Ash, Smoke

class Ice(Solid):
    key = 'C'
    name = '冰'
    char = 'c'
    color = (curses.COLOR_CYAN, -1, curses.A_DIM) # Dim cyan
    density = 9 # Solid, but less dense than rock/metal
    is_static = False # Can melt, so not truly static
    melt_chance = 0.1
    cool_ember_chance = 0.7
    cool_fire_chance = 0.1
    dissolvable_by_acid = True

    # Define coordinates to check for heat sources (orthogonal)
    HEAT_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def run_interactions(self, grid):
        """Ice checks if adjacent to a heat source to melt."""
        if self.processed: return

        heated = False
        heat_source_coord = None
        heat_source_element = None

        for dy, dx in self.HEAT_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check using property
                if neighbor and neighbor.is_heat_source:
                    heated = True
                    heat_source_coord = (ny, nx)
                    heat_source_element = neighbor
                    break # Found one heat source

        if heated and random.random() < self.melt_chance:
            # Turn into Water using grid factory
            new_water = grid.create_element('W', self.y, self.x)
            grid.set_element(self.y, self.x, new_water)
            # Don't mark new water as processed, let it flow next frame
            self.processed = True # Mark the ice as processed (it's gone)

            # Try to cool the heat source that melted it
            if heat_source_element and not heat_source_element.processed:
                ny, nx = heat_source_coord
                # Check heat source type by key
                if heat_source_element.key == 'B': # Ember
                     if random.random() < self.cool_ember_chance:
                         # Create Ash using grid factory
                         cooled_product = grid.create_element('H', ny, nx)
                         grid.set_element(ny, nx, cooled_product)
                         if cooled_product: cooled_product.processed = True # Mark cooled product
                elif heat_source_element.key == 'F': # Fire
                     if random.random() < self.cool_fire_chance:
                          # Create Smoke using grid factory
                          cooled_product = grid.create_element('K', ny, nx)
                          grid.set_element(ny, nx, cooled_product)
                          if cooled_product: cooled_product.processed = True # Mark cooled product
            return # Melted and potentially cooled

        # Mark as processed if not already done
        if not self.processed:
            self.processed = True


