# -*- coding: utf-8 -*-
from .base import Liquid, Element
import random
import curses

class Acid(Liquid):
    key = 'A'
    name = '酸'
    char = 'a'
    color = (curses.COLOR_GREEN, -1)
    density = 1.1 # Slightly denser than water
    flow_speed = 3
    dissolve_chance = 0.15
    self_consume_chance = 0.05

    # Define coordinates to check for dissolving (includes diagonals)
    DISSOLVE_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

    def run_interactions(self, grid):
        """Acid tries to dissolve neighbors."""
        # Interaction logic runs *before* movement in Liquid.update

        dissolvable_neighbors = []
        for dy, dx in self.DISSOLVE_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check if neighbor exists, is not already processed, and is dissolvable
                # Check neighbor.processed is important if the neighbor moved into place this frame
                if neighbor and not neighbor.processed and neighbor.dissolvable_by_acid:
                    dissolvable_neighbors.append((ny, nx, neighbor))

        if dissolvable_neighbors and random.random() < self.dissolve_chance:
            ny, nx, target_neighbor = random.choice(dissolvable_neighbors)
            # Dissolve the neighbor
            grid.set_element(ny, nx, None) # Neighbor is gone
            # Mark the dissolved neighbor's original object as processed? No, it's just gone.

            # Chance to consume the acid itself AFTER dissolving something
            if random.random() < self.self_consume_chance:
                grid.set_element(self.y, self.x, None) # Remove self from grid
                self.processed = True # Mark self as processed because it's gone
                return # Exit interaction logic early if self-consumed

        # --- REMOVED ---
        # The problematic block that always set processed=True was here.
        # We removed it. The base Liquid.update will handle setting processed=True
        # at the very end if neither interaction nor movement occurred.
        # --- /REMOVED ---

# Add elements that can be dissolved by acid to their respective classes
# Example (in sand.py):
# class Sand(Powder):
#     ...
#     dissolvable_by_acid = True