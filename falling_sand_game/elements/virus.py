# -*- coding: utf-8 -*-
from .base import Solid, Element # Treat as a non-falling solid that spreads
import random
import curses

class Virus(Solid):
    key = 'V'
    name = '病毒'
    char = 'v'
    color = (curses.COLOR_MAGENTA, -1, curses.A_BOLD) # Bright Magenta
    density = 1 # Doesn't really interact with density, but give it a value
    is_static = False # It spreads, so not static
    is_solid = True # Acts like a spreading solid block
    spread_chance = 0.02
    dissolvable_by_acid = True # Viruses can be killed by acid
    is_flammable = True

    # Define spread directions (orthogonal)
    SPREAD_DIRECTIONS = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    def run_interactions(self, grid):
        """Virus tries to spread to adjacent empty cells."""
        if self.processed: return

        # Check available empty neighbors
        possible_spread_spots = []
        for dy, dx in self.SPREAD_DIRECTIONS:
            ny, nx = self.y + dy, self.x + dx
            # Check if valid, empty, and target not processed
            if grid.is_valid(ny, nx) and grid.get_element(ny, nx) is None:
                 # Need a way to check if the target cell *will be* processed,
                 # or just accept potential simultaneous spread for now.
                 # Let's assume if it's None now, it's available.
                 possible_spread_spots.append((ny, nx))

        # Attempt to spread
        if possible_spread_spots and random.random() < self.spread_chance:
            gy, gx = random.choice(possible_spread_spots)
            new_virus = Virus(gy, gx)
            grid.set_element(gy, gx, new_virus)
            new_virus.processed = True # Mark the newly spread virus as processed

        # Mark the original virus as processed
        if not self.processed:
            self.processed = True
