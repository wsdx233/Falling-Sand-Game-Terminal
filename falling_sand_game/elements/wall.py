# -*- coding: utf-8 -*-
from .base import StaticSolid # Inherits from StaticSolid
import curses

class Wall(StaticSolid):
    key = '#'
    name = '墙壁'
    char = '#'
    color = (curses.COLOR_WHITE, -1, curses.A_BOLD) # Bold White
    density = 100 # Very dense, immovable
    # Properties like is_static=True, is_solid=True inherited
    # update method inherited from StaticSolid does nothing.
    # Not flammable, not dissolvable by default.
