# -*- coding: utf-8 -*-
from .base import Solid # Movable Solid? Or Static? Let's assume movable by gravity initially.
# If it should be completely static like Wall, change to StaticSolid
# Original code implies it falls if created mid-air, so use Solid or Powder?
# Let's try Powder, as it's created from powder/liquid interactions often.
from .base import Powder
import curses

class Stone(Solid): 
    key = 'O'
    name = '石头'
    char = 'O'
    color = (curses.COLOR_WHITE, -1) # Normal White
    density = 20 # Very dense powder/solid
    dissolvable_by_acid = True # Make stone dissolvable
    is_static = True

    # Stone uses standard Powder behavior but is very dense.
    # It won't be displaced easily and will fall.
