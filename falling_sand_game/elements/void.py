# -*- coding: utf-8 -*-
from .base import StaticSolid, Element # Void doesn't move, it affects others
import random
import curses
# Import Wall explicitly if needed for checks
# from .wall import Wall

class Void(StaticSolid):
    key = '?'
    name = '虚空'
    char = '?'
    # Magenta foreground, Black background, Bold
    color = (curses.COLOR_MAGENTA, curses.COLOR_BLACK, curses.A_BOLD)
    density = 1000 # Infinitely dense? Doesn't matter much as it's static
    consume_chance = 0.15

    # Define coordinates to check for consumption (includes diagonals)
    CONSUME_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

    def update(self, grid):
        """Void overrides StaticSolid update to consume neighbors."""
        if self.processed: return

        consumable_neighbors = []
        for dy, dx in self.CONSUME_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check if neighbor exists, is not Wall ('#'), not Void ('?'), and not processed
                # Note: Use key check for Wall/Void as class might not be loaded yet? Safer.
                if neighbor and neighbor.key != '#' and neighbor.key != '?' and not neighbor.processed:
                    consumable_neighbors.append((ny, nx, neighbor))

        # Attempt to consume one neighbor
        if consumable_neighbors and random.random() < self.consume_chance:
            ny, nx, target_neighbor = random.choice(consumable_neighbors)
            grid.set_element(ny, nx, None) # Consume neighbor
            # Mark the consumed cell's *original* element? No, just remove it.

        # Mark the void itself as processed for this frame
        self.processed = True
