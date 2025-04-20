# -*- coding: utf-8 -*-
from .base import StaticSolid # Inherits from StaticSolid as it's immovable
import curses

class Glass(StaticSolid):
    key = 'X'
    name = '玻璃'
    char = '+'
    color = (curses.COLOR_CYAN, -1)
    density = 25 # Quite dense solid
    # is_static = True inherited
    # is_solid = True inherited
    # update is inherited from StaticSolid (does nothing)
    # Not flammable, not dissolvable by default
