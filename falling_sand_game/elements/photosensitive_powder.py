# -*- coding: utf-8 -*-
from .base import Powder, Element, Solid # Can be Powder or Solid depending on state
import random
import curses
import math
from ..element_manager import element_manager # Import singleton directly

class PhotosensitivePowder(Powder):
    key = '='
    name = '感光粉末'
    char = '='
    color = (curses.COLOR_BLUE, -1, curses.A_DIM) # Dim Blue when powder
    density = 4.5 # Powder density
    is_powder = True
    is_solid = True
    is_light_sensitive = True
    solidification_threshold = 3 # Needs light from >= this many sources or distance? Let's use distance.
    solidification_range = 6 # Max distance from a Lamp to solidify
    solidified_char = 'H' # Character when solidified ('#' might be confusing)
    solidified_color = (curses.COLOR_BLUE, -1, curses.A_BOLD) # Bright Blue when solid
    solidified_density = 100 # Make it dense like a wall when solid
    solidified_key = '#' # Pretend to be Wall ('#') when solid for interaction simplicity? Maybe not.

    # Store solidified state
    is_solidified = False

    def __init__(self, y, x):
        super().__init__(y, x)
        self.is_solidified = False # Start as powder

    def check_light(self, grid):
        """Checks for nearby light sources (Lamps)."""
        for r in range(max(0, self.y - self.solidification_range), min(grid.height, self.y + self.solidification_range + 1)):
            for c in range(max(0, self.x - self.solidification_range), min(grid.width, self.x + self.solidification_range + 1)):
                element = grid.get_element(r, c)
                if element and element.emits_light:
                    dist = math.sqrt((self.x - c)**2 + (self.y - r)**2)
                    if dist <= element.light_radius and dist <= self.solidification_range:
                        return True # Found a sufficient light source
        return False

    def update(self, grid):
        if self.processed:
            return

        is_lit = self.check_light(grid)

        if is_lit:
            # --- Solidify ---
            if not self.is_solidified:
                self.is_solidified = True
                self.is_powder = False # Becomes a static solid-like entity
                self.is_static = True
                self.char = self.solidified_char
                self.density = self.solidified_density # Increase density
                # Color change is handled by get_drawing_info

            # Act like a StaticSolid when lit
            self.processed = True # Mark as processed, does nothing else

        else:
            # --- Revert to Powder ---
            if self.is_solidified:
                self.is_solidified = False
                self.is_powder = True # Becomes powder again
                self.is_static = False
                self.char = '=' # Revert character
                self.density = 4.5 # Revert density
                # Color change handled by get_drawing_info

            # Act like Powder when not lit
            # Call Powder's update logic directly using super()
            # Need to ensure Powder's update is called correctly
            # super(PhotosensitivePowder, self).update(grid)
            # Let's restructure slightly: Powder movement happens if not solidified.
            if not self.is_static: # If it's powder state
                 # Copy relevant parts of Powder.update logic here or call super().update()
                 # Calling super().update might double-process if not careful.
                 # Let's re-implement the powder fall logic here for clarity when not solidified.

                 potential_y = self.y + 1
                 moved = False

                 # 1. Try moving straight down
                 if grid.is_valid(potential_y, self.x):
                     below_element = grid.get_element(potential_y, self.x)
                     if below_element is None:
                         if self._move_to(grid, potential_y, self.x): moved = True
                     elif below_element is not None:
                         can_displace_target = False
                         if below_element.is_liquid or below_element.is_gas or below_element.is_powder:
                             can_displace_target = self._can_displace(below_element)
                         if can_displace_target:
                             self._swap_with(grid, potential_y, self.x); moved = True
                     if moved: self.processed = True; return

                 # 2. Try moving diagonally down
                 if not moved:
                     possible_targets = []
                     directions = [-1, 1]; random.shuffle(directions)
                     for dx in directions:
                         diag_x = self.x + dx
                         if grid.is_valid(potential_y, diag_x):
                             diag_element = grid.get_element(potential_y, diag_x)
                             if diag_element is None:
                                 side_element = grid.get_element(self.y, diag_x)
                                 if side_element is None or side_element.is_liquid or side_element.is_gas:
                                     possible_targets.append((diag_x, False)); break
                             elif diag_element is not None:
                                 can_displace_target = False
                                 if diag_element.is_liquid or diag_element.is_gas or diag_element.is_powder:
                                     can_displace_target = self._can_displace(diag_element)
                                 if can_displace_target:
                                     side_element = grid.get_element(self.y, diag_x)
                                     if side_element is None or side_element.is_liquid or side_element.is_gas:
                                         possible_targets.append((diag_x, True)); break
                     if possible_targets:
                         target_x, is_swap = possible_targets[0]
                         if is_swap: self._swap_with(grid, potential_y, target_x)
                         else: self._move_to(grid, potential_y, target_x)
                         moved = True; self.processed = True; return


            # Mark as processed if it didn't move (and wasn't already processed)
            if not self.processed:
                 self.processed = True

        # Final check (should normally be processed by now)
        if not self.processed:
            self.processed = True

    # Override drawing info based on state
    def get_drawing_info(self):
        if self.is_solidified:
             # Try to find a predefined color pair for the solid appearance
             # This relies on setup_colors pre-calculating pairs
             # For simplicity, let's hardcode a request for Bright Blue on Default BG
             # A better way needs dynamic pair creation or guaranteed pair IDs.
             # We'll return the intended color tuple, main setup needs to handle pair creation.
             # Let's find the element_manager's default background color if possible.
             solid_pair_idx = self.color_pair_index # Default to own pair if solid pair fails
             try:
                  # Attempt to get the color pair index dynamically? Too complex here.
                  # Hardcode: Assume Pair 1 is White/Default, Pair 2 Blue/Default, etc.
                  # This is fragile. Let's just use the bold blue color.
                  # The color pair index itself doesn't change unless we re-init colors.
                  # We rely on the character change and maybe tags for visual difference.
                  # Revisit color pair switching if essential.
                  pass # Keep original color pair index for now
             except Exception:
                  pass # Ignore errors finding color pair
             return self.solidified_char, self.color_pair_index # Return solidified char, same pair index
        else:
             # Return normal powder appearance
             return self.char, self.color_pair_index