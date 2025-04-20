# -*- coding: utf-8 -*-
from .base import StaticSolid, Element
import curses
import random

class ConveyorBelt(StaticSolid):
    key = '>'
    name = '传送带 (右)' # Name indicates direction for now
    char = '>' # Char indicates direction
    color = (curses.COLOR_YELLOW, curses.COLOR_RED) # Yellow on Red
    density = 30 # Fairly dense static solid
    is_static = False # It causes movement, so not truly static in effect
    is_solid = True
    push_force = 1 # How many cells sideways it tries to push per frame

    # Direction is implicit in the key/char/name for this simple version
    # A more complex version might store direction as state.
    direction_dx = 1 # Pushes right

    # Override update from StaticSolid
    def update(self, grid):
        if self.processed:
            return

        # --- Interaction: Push element above ---
        above_y, above_x = self.y - 1, self.x
        if grid.is_valid(above_y, above_x):
            element_above = grid.get_element(above_y, above_x)

            # Check if there's a movable element directly above and not processed
            if element_above and not element_above.is_static and not element_above.processed:
                # Determine target position based on direction and force
                target_x = above_x + self.direction_dx * self.push_force
                target_y = above_y # Push horizontally

                # Check if the target cell is valid
                if grid.is_valid(target_y, target_x):
                    target_element = grid.get_element(target_y, target_x)

                    # Can only push if the target cell is empty OR contains a gas/liquid that can be displaced
                    can_push = False
                    is_swap = False
                    if target_element is None:
                        can_push = True
                        is_swap = False
                    elif target_element.is_gas or target_element.is_liquid:
                        # Check if element_above can displace target_element based on density
                        if element_above._can_displace(target_element):
                            can_push = True
                            is_swap = True
                        # Special case: If element_above is also AGPowder, maybe density check is reversed?
                        # Keep it simple for now: only density matters for displacement.

                    if can_push:
                        # We need to move/swap the element *above* the belt
                        # This is tricky as element_above handles its own movement.
                        # Let's try directly manipulating the grid here.

                        # Store original position of element_above
                        original_above_y, original_above_x = element_above.y, element_above.x

                        if is_swap:
                            # Swap element_above with target_element
                            grid.set_element(original_above_y, original_above_x, target_element)
                            grid.set_element(target_y, target_x, element_above) # element_above moves here
                            if target_element: # Update target's coords if it exists
                                target_element.y, target_element.x = original_above_y, original_above_x
                            element_above.y, element_above.x = target_y, target_x
                            # Mark the moved element as processed THIS FRAME because the belt moved it
                            element_above.processed = True
                        else:
                            # Move element_above to target (empty) cell
                            grid.set_element(original_above_y, original_above_x, None) # Clear original pos
                            grid.set_element(target_y, target_x, element_above) # element_above moves here
                            element_above.y, element_above.x = target_y, target_x
                            # Mark the moved element as processed
                            element_above.processed = True

                        # Mark the conveyor belt itself as processed since it acted
                        self.processed = True
                        return # Belt action complete

        # If no action taken, mark belt as processed
        if not self.processed:
            self.processed = True

    # No run_interactions needed as the logic is in update
    # def run_interactions(self, grid):
    #     pass

# TODO: Could add Left '<', Up '^', Down 'v' variants or a single element storing direction state.
