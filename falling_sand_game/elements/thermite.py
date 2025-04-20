# -*- coding: utf-8 -*-
from .base import Powder, Element
import random
import curses

class Thermite(Powder):
    key = 'T' # New key T (Salt is 't')
    name = '铝热剂'
    char = 'T'
    color = (curses.COLOR_WHITE, curses.COLOR_RED) # White on Red background
    density = 5.8 # Similar density to Cement/Gunpowder
    is_powder = True
    is_solid = True
    dissolvable_by_acid = True # Strong acid might react
    # Thermite needs strong heat to ignite
    ignition_threshold_temp = 2 # Needs adjacent Fire or Lava (count as temp 2), Ember is 1?
    ignition_chance = 0.6 # Chance to ignite if threshold met
    burn_duration = 5 # How many frames it burns for (simple counter)
    burn_temp = 3 # Burns hotter than Fire/Lava

    # State variables
    is_burning = False
    burn_timer = 0
    is_heat_source = False # Only a heat source when burning

    def __init__(self, y, x):
        super().__init__(y, x)
        self.is_burning = False
        self.burn_timer = 0
        self.is_heat_source = False

    # Coordinates for checking ignition sources
    HEAT_CHECKS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def run_interactions(self, grid):
        """Thermite checks for ignition or continues burning."""
        if self.processed: return

        if self.is_burning:
            # --- Burning Logic ---
            self.burn_timer -= 1
            if self.burn_timer <= 0:
                # Burnout: Turn into Metal ('M')
                new_metal = grid.create_element('M', self.y, self.x)
                if new_metal:
                     new_metal.tags = list(self.tags) # Copy tags
                     grid.set_element(self.y, self.x, new_metal)
                     # Let metal settle/interact next frame
                self.processed = True # Thermite is gone
                return
            else:
                # Continue burning: Act as a strong heat source
                self.is_heat_source = True
                # Maybe melt adjacent metal? Or just ignite flammable things intensely?
                # Keep it simple: it just acts as a heat source while burning.
                # Fire/Ember/etc. interactions are handled by those elements checking `is_heat_source`.
                pass # Continue burning

        else:
            # --- Ignition Check ---
            current_heat = 0
            for dy, dx in self.HEAT_CHECKS:
                ny, nx = self.y + dy, self.x + dx
                if grid.is_valid(ny, nx):
                    neighbor = grid.get_element(ny, nx)
                    if neighbor and neighbor.is_heat_source:
                        if neighbor.key in ('F', 'L'): # Fire, Lava
                             current_heat = max(current_heat, 2)
                        elif neighbor.key == 'B': # Ember
                             current_heat = max(current_heat, 1)
                        # Add check for burning Thermite? Temp 3?
                        elif neighbor.key == 'T' and getattr(neighbor, 'is_burning', False):
                             current_heat = max(current_heat, 3) # Use max heat from neighbor

            if current_heat >= self.ignition_threshold_temp:
                if random.random() < self.ignition_chance:
                    self.is_burning = True
                    self.burn_timer = self.burn_duration
                    self.is_heat_source = True # Becomes heat source immediately
                    # Change appearance? Maybe make brighter? Hard with current colors.
                    # Use a tag?
                    self.tags.append("burning") # Add a tag to indicate state visually if needed

        # Base Powder update runs after interactions if not burning/ignited this frame


    # Override drawing info if burning?
    def get_drawing_info(self):
        if self.is_burning:
             # Blinking bright red?
             # Need a dedicated color pair for burning thermite
             # Fallback: just return normal char/color but maybe add blink via tag check in Game.draw
             return self.char, self.color_pair_index # Add A_BLINK via tag check?
        else:
             return self.char, self.color_pair_index

