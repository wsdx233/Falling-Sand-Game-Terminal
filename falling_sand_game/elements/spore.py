# -*- coding: utf-8 -*-
from .base import Powder, Element # Spores are light powders
import random
import curses

class Spore(Powder):
    key = ','
    name = '孢子'
    char = ','
    color = (curses.COLOR_GREEN, -1, curses.A_DIM) # Dim Green, like fungus parent
    density = 0.1 # Very light, should be easily displaced by air currents (if implemented) or fall slowly
    is_powder = True
    is_solid = True # Treat as solid particle
    dissipate_chance = 0.005 # Chance to disappear naturally
    grow_chance = 0.01 # Chance to grow into Fungus if conditions met

    # Coordinates for checking growth conditions
    GROW_CHECK = [(1, 0), (0, 1), (0, -1), (-1, 0)] # Check adjacent for growable surface

    def run_interactions(self, grid):
        """Spore tries to grow into Fungus or dissipates."""
        if self.processed: return

        # 1. Chance to dissipate
        if random.random() < self.dissipate_chance:
            grid.set_element(self.y, self.x, None)
            self.processed = True
            return

        # 2. Chance to grow
        can_grow_here = False
        for dy, dx in self.GROW_CHECK:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check if neighbor exists and is something fungus can grow on (e.g., Mud)
                if neighbor and neighbor.can_grow_on: # Check property
                     can_grow_here = True
                     break

        if can_grow_here and random.random() < self.grow_chance:
            # Turn into Fungus ('f')
            new_fungus = grid.create_element('f', self.y, self.x)
            if new_fungus:
                 new_fungus.tags = list(self.tags) # Copy tags
                 grid.set_element(self.y, self.x, new_fungus)
                 # Let new fungus run its update next frame
            self.processed = True # Spore is gone
            return

        # Base Powder update runs after interactions if nothing happened

