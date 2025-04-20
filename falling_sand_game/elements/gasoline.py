# -*- coding: utf-8 -*-
from .base import Liquid
import curses

class Gasoline(Liquid):
    key = 'J'
    name = '汽油'
    char = 'j'
    color = (curses.COLOR_MAGENTA, -1)
    density = 0.7 # Lighter than water, floats on it
    flow_speed = 4 # Flows faster than water
    is_flammable = True
    dissolvable_by_acid = True

    # Gasoline uses standard liquid behavior + flammability property
    # No unique interactions defined here, burning is handled by Fire/Ember
