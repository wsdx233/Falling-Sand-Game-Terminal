# -*- coding: utf-8 -*-
from .base import Powder
import curses

class Sand(Powder):
    key = 'S'
    name = '沙子'
    char = 'S'
    color = (curses.COLOR_YELLOW, -1)
    density = 6 # Denser than default powder/salt
    is_flammable = False # Default Sand is not flammable (can be changed)
    dissolvable_by_acid = True

    # Sand uses standard Powder behavior.
    # No unique interactions defined in the original code.
    # Override run_interactions if needed.
    # def run_interactions(self, grid):
    #     super().run_interactions(grid) # Call parent if extending
    #     # Add sand-specific logic here
    #     pass
