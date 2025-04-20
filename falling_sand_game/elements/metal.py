# -*- coding: utf-8 -*-
from .base import StaticSolid # Immovable solid
import curses

class Metal(StaticSolid):
    key = 'M'
    name = '金属'
    char = 'M'
    color = (curses.COLOR_CYAN, -1, curses.A_BOLD) # Bright Cyan
    density = 70 # Very dense
    dissolvable_by_acid = True # Make metal dissolvable
