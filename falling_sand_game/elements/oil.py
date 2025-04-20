# -*- coding: utf-8 -*-
from .base import Liquid
import curses

class Oil(Liquid):
    key = 'I'
    name = '油'
    char = '%'
    color = (curses.COLOR_YELLOW, -1) # Yellow, distinct from sand
    density = 0.9 # Lighter than water, floats
    flow_speed = 2 # Flows slower than water/gasoline
    is_flammable = True
    dissolvable_by_acid = True

    # Oil uses standard liquid behavior + flammability property
