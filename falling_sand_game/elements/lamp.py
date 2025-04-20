# -*- coding: utf-8 -*-
from .base import StaticSolid, Element
import curses

class Lamp(StaticSolid):
    key = 'l'
    name = '灯'
    char = 'L'
    color = (curses.COLOR_YELLOW, -1, curses.A_BOLD) # Bright Yellow
    density = 20 # Solid object density
    is_static = True
    is_solid = True

    # Light properties
    emits_light = True
    light_radius = 5 # How far the light reaches

    # Lamp itself doesn't do anything in update/interactions
    # Other elements (like PhotosensitivePowder) will check for nearby lamps.
