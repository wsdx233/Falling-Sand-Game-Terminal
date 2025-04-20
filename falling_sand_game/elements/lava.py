# -*- coding: utf-8 -*-
from .base import Liquid, Element
import random
import curses
# No top-level imports of Water, Ice, Stone, Steam, Fire

class Lava(Liquid):
    key = 'L'
    name = '岩浆'
    char = 'L'
    color = (curses.COLOR_RED, -1, curses.A_BOLD) # Bright Red
    density = 3 # Denser than water/oil, less than powders/solids
    flow_speed = 1 # Flows slowly
    is_heat_source = True
    ignite_chance = 0.3 # Chance to ignite adjacent flammable material

    # Define interaction coordinates (orthogonal)
    INTERACTION_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def run_interactions(self, grid):
        """Lava interacts with neighbors: solidifies with water/ice, ignites flammable."""
        # This interaction runs *after* potential movement in Liquid.update
        if self.processed: return # Already moved or interacted

        reaction_occurred = False
        # Store original position in case lava turns into stone
        original_y, original_x = self.y, self.x

        for dy, dx in self.INTERACTION_CHECKS:
            ny, nx = original_y + dy, original_x + dx # Check relative to original position
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check neighbor exists and hasn't been processed this frame
                # Important: Check neighbor.processed because if Water/Ice moved
                # into this spot and got processed, we shouldn't react with it again.
                if neighbor and not neighbor.processed:
                    # 1. Reaction with Water (check key)
                    if neighbor.key == 'W':
                        # Lava turns to Stone (use factory) at its original position
                        new_stone = grid.create_element('O', original_y, original_x)
                        grid.set_element(original_y, original_x, new_stone)
                        # Don't mark stone as processed, let it fall/settle if needed
                        # Water turns to Steam (use factory) at neighbor's position
                        new_steam = grid.create_element('G', ny, nx)
                        grid.set_element(ny, nx, new_steam)
                        if new_steam: new_steam.processed = True # Mark steam processed immediately
                        self.processed = True # Lava is gone (already replaced by stone)
                        reaction_occurred = True
                        break # One reaction per step is enough

                    # 2. Reaction with Ice (check key)
                    elif neighbor.key == 'C':
                        # Lava turns to Stone (use factory)
                        new_stone = grid.create_element('O', original_y, original_x)
                        grid.set_element(original_y, original_x, new_stone)
                        # Don't mark stone processed
                        # Ice turns to Water (use factory)
                        new_water = grid.create_element('W', ny, nx)
                        grid.set_element(ny, nx, new_water)
                        # Don't process the new water this frame, let it flow next
                        self.processed = True # Lava is gone
                        reaction_occurred = True
                        break

                    # 3. Ignite Flammable (if no reaction yet)
                    # Check properties, ensure neighbor is flammable and not already a heat source
                    elif neighbor.is_flammable and not neighbor.is_heat_source and random.random() < self.ignite_chance:
                         # Turn neighbor into Fire (use factory)
                         new_fire = grid.create_element('F', ny, nx)
                         grid.set_element(ny, nx, new_fire)
                         if new_fire: new_fire.processed = True # Mark new fire processed
                         # Lava itself isn't consumed here, only the neighbor changes
                         reaction_occurred = True # Consider ignition a 'reaction' for loop break
                         break # Ignite only one neighbor per step

        # No return needed here, Liquid.update handles final processed=True if nothing happened

