# -*- coding: utf-8 -*-
from .base import Liquid, Element
import random
import curses
# No top-level imports of Steam, Ash, Smoke, CementPowder, Stone

class Water(Liquid):
    key = 'W'
    name = '水'
    char = '~'
    color = (curses.COLOR_BLUE, -1)
    density = 1.0 # Base density for liquids
    flow_speed = 3
    vaporize_chance = 0.05
    cool_ember_chance = 0.6
    cool_fire_chance = 0.1

    # Define interaction coordinates (orthogonal)
    INTERACTION_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def run_interactions(self, grid):
        """Water interacts with heat sources (vaporize)."""
        # Cement interaction is handled by CementPowder
        # This interaction runs *after* potential movement in Liquid.update
        if self.processed: return # Already moved or interacted

        interaction_done = False
        original_y, original_x = self.y, self.x # Store current pos before potential change

        # 1. Check for heat sources nearby
        heat_source_found = False
        heat_source_coord = None
        heat_source_element = None
        for dy, dx in self.INTERACTION_CHECKS:
            ny, nx = original_y + dy, original_x + dx # Check relative to original position
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check if neighbor exists, is heat source, and not processed
                if neighbor and neighbor.is_heat_source and not neighbor.processed:
                    heat_source_found = True
                    heat_source_coord = (ny, nx)
                    heat_source_element = neighbor
                    break # Found one

        if heat_source_found and random.random() < self.vaporize_chance:
            # Turn into Steam using grid factory at original position
            new_steam = grid.create_element('G', original_y, original_x)
            grid.set_element(original_y, original_x, new_steam)
            if new_steam: new_steam.processed = True # Mark steam processed immediately
            self.processed = True # Water is gone (replaced by steam)
            interaction_done = True

            # Try to cool the heat source that caused vaporization
            if heat_source_element and not heat_source_element.processed:
                ny, nx = heat_source_coord
                cooled_product = None
                # Check key for type of heat source
                if heat_source_element.key == 'B': # Ember
                    if random.random() < self.cool_ember_chance:
                        cooled_product = grid.create_element('H', ny, nx) # Ash
                elif heat_source_element.key == 'F': # Fire
                    if random.random() < self.cool_fire_chance:
                         cooled_product = grid.create_element('K', ny, nx) # Smoke
                elif heat_source_element.key == 'L': # Lava - Water doesn't cool lava typically
                    pass

                # If a cooled product was created, place it and mark processed
                if cooled_product:
                    grid.set_element(ny, nx, cooled_product)
                    cooled_product.processed = True # Mark cooled product processed

            return # Vaporized and potentially cooled neighbor

        # No return needed here, Liquid.update handles final processed=True