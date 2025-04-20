# -*- coding: utf-8 -*-
from ...base import Solid, Element  # Use Solid as the base class
import random
import curses
# Import the element manager singleton to get the list of placeable elements
from ....element_manager import element_manager
import math # Import math for distance calculation

class Emitter(Solid):
    key = 'Q'  # Assign a unique key (assuming 'Q' is available)
    name = '发射器'
    char = 'Q' # Character representation
    # Example color: Bright White on a Blue background
    color = (curses.COLOR_WHITE, curses.COLOR_BLUE, curses.A_BOLD)
    density = 15 # Typical solid density
    is_static = True # It doesn't move itself, it acts
    is_solid = True
    # Defaults from Solid: not flammable, not dissolvable etc.

    EMIT_CHANCE = 0.10 # 10% chance per frame to emit
    # Directions: Up, Down, Left, Right relative to the emitter
    DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def run_interactions(self, grid):
        """
        Emitter attempts to emit a random placeable element into an adjacent empty cell.
        This is called by the Solid base class's update method.
        """
        # Check the probability condition first
        if random.random() < self.EMIT_CHANCE:
            # Choose a random direction from the defined list
            dy, dx = random.choice(self.DIRECTIONS)
            ny, nx = self.y + dy, self.x + dx # Calculate neighbor coordinates

            # Check if the target cell is within grid bounds AND is currently empty
            if grid.is_valid(ny, nx) and grid.get_element(ny, nx) is None:
                # Get the list of currently known placeable element keys
                placeable_keys = element_manager.get_placeable_order()

                # Ensure there are elements available to emit
                if placeable_keys:
                    # Choose a random element key from the placeable list
                    emit_key = random.choice(placeable_keys)

                    # Use the grid's factory method to create an instance of the chosen element
                    # at the target neighbor coordinates (ny, nx)
                    new_element = grid.create_element(emit_key, ny, nx)

                    # If the element was successfully created, place it onto the grid
                    if new_element:
                        grid.set_element(ny, nx, new_element)
                        # The newly created element will run its own update in a later step/frame.
                        # We don't mark the new element as processed here.

                        # Mark the Emitter itself as processed for this frame because it performed its action.
                        self.processed = True
                        return # Exit after successful emission for this frame

        # If the emitter didn't emit (due to chance, blocked target, or no placeable elements found),
        # the base Solid.update method will eventually mark self.processed = True.
        # No need to set it here unless emission actually happened.

# 强效发射器
class PowerfulEmitter(Emitter):
    key = '%'  # Unique key for Powerful Emitter
    name = '强效发射器'
    char = '%' # Character representation
    # Example color: Bright Red on a Blue background
    color = (curses.COLOR_RED, curses.COLOR_BLUE, curses.A_BOLD)

    EMIT_CHANCE = 0.25 # 25% chance per frame to emit
    EMIT_RANGE = 5 # Emission range is a radius of 5 cells

    def run_interactions(self, grid):
        """
        Powerful Emitter attempts to emit a random placeable element within its range (radius 5)
        and will replace the content of the target cell.
        """
        if random.random() < self.EMIT_CHANCE:
            # Find a random target cell within the radius
            # We'll iterate through cells within the square bounding box of the circle and check distance
            max_offset = self.EMIT_RANGE
            possible_targets = []
            for dy in range(-max_offset, max_offset + 1):
                for dx in range(-max_offset, max_offset + 1):
                    # Calculate distance from the emitter
                    distance = math.sqrt(dx**2 + dy**2)
                    if distance <= self.EMIT_RANGE:
                        ny, nx = self.y + dy, self.x + dx
                        # Exclude the emitter's own cell and only consider valid grid cells
                        if grid.is_valid(ny, nx) and (ny, nx) != (self.y, self.x):
                            possible_targets.append((ny, nx))

            if possible_targets:
                # Choose a random target cell from the possible locations
                ny, nx = random.choice(possible_targets)

                # Get the list of currently known placeable element keys
                placeable_keys = element_manager.get_placeable_order()

                # Ensure there are elements available to emit
                if placeable_keys:
                    # Choose a random element key from the placeable list
                    emit_key = random.choice(placeable_keys)

                    # Use the grid's factory method to create an instance of the chosen element
                    # at the target coordinates (ny, nx)
                    new_element = grid.create_element(emit_key, ny, nx)

                    # If the element was successfully created, place it onto the grid, replacing existing content
                    if new_element:
                        grid.set_element(ny, nx, new_element)
                        # Mark the Powerful Emitter itself as processed
                        self.processed = True
                        return # Exit after successful emission

        # If no emission occurred, the base Solid.update will handle processed state

# 干净发射器
class CleanEmitter(Emitter):
    key = '&'  # Unique key for Clean Emitter
    name = '干净发射器'
    char = '&' # Character representation
    # Example color: Bright Cyan on a Blue background
    color = (curses.COLOR_CYAN, curses.COLOR_BLUE, curses.A_BOLD)

    # Inherits EMIT_CHANCE (0.10) and DIRECTIONS from Emitter
    # Inherits name, char, color, density, is_static, is_solid from Emitter

    def run_interactions(self, grid):
        """
        Clean Emitter attempts to emit a random placeable element (excluding 'v')
        into an adjacent empty cell.
        """
        if random.random() < self.EMIT_CHANCE:
            # Choose a random direction from the defined list
            dy, dx = random.choice(self.DIRECTIONS)
            ny, nx = self.y + dy, self.x + dx # Calculate neighbor coordinates

            # Check if the target cell is within grid bounds AND is currently empty
            if grid.is_valid(ny, nx) and grid.get_element(ny, nx) is None:
                # Get the list of currently known placeable element keys
                placeable_keys = element_manager.get_placeable_order()

                # Filter out the virus key ('v')
                clean_placeable_keys = [key for key in placeable_keys if key != 'v']

                # Ensure there are elements available to emit after filtering
                if clean_placeable_keys:
                    # Choose a random element key from the filtered list
                    emit_key = random.choice(clean_placeable_keys)

                    # Use the grid's factory method to create an instance of the chosen element
                    # at the target neighbor coordinates (ny, nx)
                    new_element = grid.create_element(emit_key, ny, nx)

                    # If the element was successfully created, place it onto the grid
                    if new_element:
                        grid.set_element(ny, nx, new_element)
                        # Mark the Clean Emitter itself as processed
                        self.processed = True
                        return # Exit after successful emission

        # If no emission occurred, the base Solid.update will handle processed state

