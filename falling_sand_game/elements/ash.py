# -*- coding: utf-8 -*-
from .base import Powder, Element
import curses
import random

class Ash(Powder):
    key = 'H'
    name = '灰烬'
    char = 'h'
    color = (curses.COLOR_WHITE, -1, curses.A_DIM) # Dim white -> Grey
    density = 4
    dissolvable_by_acid = True
    mud_formation_chance = 0.6 # Chance to turn into mud when touching water

    # Coordinates to check for interactions (orthogonal)
    INTERACTION_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def run_interactions(self, grid):
        """Ash checks for adjacent water to potentially turn into Mud."""
        if self.processed: return

        reacted = False
        for dy, dx in self.INTERACTION_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check if neighbor is Water ('W') by key and not processed
                if neighbor and neighbor.key == 'W' and not neighbor.processed:
                    if random.random() < self.mud_formation_chance:
                        # Turn self into Mud ('R') using grid factory
                        new_mud = grid.create_element('R', self.y, self.x)
                        if new_mud:
                            new_mud.tags = list(self.tags) # Copy tags
                            grid.set_element(self.y, self.x, new_mud)
                            # Mark self (ash) as processed because it transformed
                            self.processed = True
                            # Consume the water neighbor
                            grid.set_element(ny, nx, None)
                            reacted = True
                            break # One reaction is enough

        # Mark as processed if no reaction occurred but interaction phase completed
        if reacted and not self.processed:
            self.processed = True

