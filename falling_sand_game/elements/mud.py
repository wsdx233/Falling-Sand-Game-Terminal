# -*- coding: utf-8 -*-
from .base import Powder # Mud behaves like a dense powder
import curses

class Mud(Powder): # Represents Dirt/Soil formed from Ash+Water
    key = 'R'
    name = '泥土'
    char = 'r'
    # Use COLOR_RED as approximation for Brown in standard curses
    color = (curses.COLOR_RED, -1)
    density = 5.5 # Similar to sand/gunpowder
    is_flammable = False # Less flammable than dry wood/plants, let's say false
    dissolvable_by_acid = True
    can_grow_on = True # Plants/Fungus can grow on mud

    # Mud uses standard powder behavior.
    # It serves as a substrate for Plant/Seed/Fungus growth.
    # No unique interactions defined here.
