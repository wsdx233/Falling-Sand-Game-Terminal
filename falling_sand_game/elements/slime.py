# -*- coding: utf-8 -*-
from .base import Liquid
import curses

class Slime(Liquid):
    key = 'Z'
    name = '史莱姆'
    char = 'z'
    color = (curses.COLOR_GREEN, -1, curses.A_DIM) # Dim Green
    density = 1.5 # Denser than water/oil, lighter than lava
    flow_speed = 1 # Flows very slowly
    dissolvable_by_acid = True

    # Slime uses standard liquid behavior with adjusted parameters.
