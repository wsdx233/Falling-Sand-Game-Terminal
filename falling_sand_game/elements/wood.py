# -*- coding: utf-8 -*-
from .base import Solid # Wood is solid but flammable
import curses

class Wood(Solid):
    key = 'd' # Changed key from D to d
    name = '木头'
    char = 'd' # Changed char to match key
    # Use COLOR_RED as approximation for Brown in standard curses
    color = (curses.COLOR_RED, -1)
    density = 7 # Reasonably dense solid, lighter than stone/metal
    is_static = True # Doesn't move on its own
    is_solid = True
    is_flammable = True
    dissolvable_by_acid = True
    can_grow_on = True # Fungus can grow on wood

    # Wood itself doesn't have active interactions in its update.
    # It relies on Fire/Ember to burn it.
    # Inherited Solid update calls run_interactions, which is empty here.
    # If Wood had other reactions (e.g., rot), they'd go in run_interactions.