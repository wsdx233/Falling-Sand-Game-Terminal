# -*- coding: utf-8 -*-
from .base import Element
import curses

class EmptyElement(Element):
    """Represents an empty space. Not typically placed directly."""
    key = ' '
    name = '空'
    char = ' '
    color = (curses.COLOR_WHITE, -1) # Should match background
    density = -100 # Lightest possible, everything falls through/displaces it
    is_static = True
    is_solid = False

    def update(self, grid):
        # Empty space does nothing
        self.processed = True
