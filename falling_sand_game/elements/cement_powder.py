# -*- coding: utf-8 -*-
from .base import Powder, Element
import random
import curses
# No top-level imports of Water, Stone

class CementPowder(Powder):
    key = 'Y'
    name = '水泥粉末'
    char = 'y'
    color = (curses.COLOR_WHITE, -1) # White, maybe slightly dim?
    density = 5.8
    solidify_chance = 0.8 # High chance to solidify per adjacent water
    dissolvable_by_acid = True

    # Define coordinates to check for water (orthogonal)
    WATER_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def run_interactions(self, grid):
        """Cement powder checks for adjacent water to solidify into stone."""
        if self.processed: return

        water_neighbor_coord = None
        found_water = False

        for dy, dx in self.WATER_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check if neighbor is Water ('W') by key and not processed
                if neighbor and neighbor.key == 'W' and not neighbor.processed:
                    found_water = True
                    water_neighbor_coord = (ny, nx)
                    break # Found one water source

        if found_water and random.random() < self.solidify_chance:
            # Turn self into Stone using grid factory
            new_stone = grid.create_element('O', self.y, self.x)
            grid.set_element(self.y, self.x, new_stone)
            self.processed = True # Cement is gone

            # Consume the water neighbor
            if water_neighbor_coord:
                ny, nx = water_neighbor_coord
                # Ensure water is still there before removing (check key)
                neighbor = grid.get_element(ny, nx)
                if neighbor and neighbor.key == 'W':
                    grid.set_element(ny, nx, None) # Remove water

            return # Solidified

        # # Mark as processed if not already done
        # if not self.processed:
        #     self.processed = True


