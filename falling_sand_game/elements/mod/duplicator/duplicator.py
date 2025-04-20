# -*- coding: utf-8 -*-
from ...base import StaticSolid, Element  # Use StaticSolid as it doesn't move
import random
import curses
# Import the element manager singleton (though not strictly needed here)
# from ....element_manager import element_manager

class Duplicator(StaticSolid):
    key = '*'  # Changed key from 'D' to '*' to avoid conflict with Wood ('d')
    name = '复制器'
    char = '*' # Character representation
    # Example color: Bright Yellow on a Blue background
    color = (curses.COLOR_YELLOW, curses.COLOR_BLUE, curses.A_BOLD)
    density = 20 # A bit denser than the emitter
    is_static = True # It doesn't move itself, it acts
    is_solid = True
    duplicate_chance = 0.2 # Chance to duplicate per frame if conditions met

    # Directions to attempt duplication: Down, Left, Right relative to the duplicator
    DUPLICATE_DIRECTIONS = [(1, 0), (0, -1), (0, 1)] # Down, Left, Right

    # Override update from StaticSolid
    def update(self, grid):
        """
        Duplicator checks the cell above it. If not empty and not another Duplicator,
        it attempts to duplicate that element into an adjacent empty cell (Down, Left, Right).
        """
        if self.processed:
             return

        # Check the cell directly above the duplicator
        above_y, above_x = self.y - 1, self.x
        above_element = None

        # Ensure the cell above is valid
        if grid.is_valid(above_y, above_x):
            above_element = grid.get_element(above_y, above_x)

        # Check if element above exists, is not None, and is not itself a Duplicator ('*')
        if above_element and above_element.key != '*':
            # Check duplication chance
            if random.random() < self.duplicate_chance:
                # Find available EMPTY target cells in the specified directions
                possible_targets = []
                for dy, dx in self.DUPLICATE_DIRECTIONS:
                    target_y, target_x = self.y + dy, self.x + dx
                    # Check if the target cell is valid AND empty
                    if grid.is_valid(target_y, target_x) and grid.get_element(target_y, target_x) is None:
                        possible_targets.append((target_y, target_x))

                # If there are valid, empty target cells, attempt duplication
                if possible_targets:
                    # Choose a random empty target cell
                    target_y, target_x = random.choice(possible_targets)

                    # Get the key of the element above to duplicate
                    element_to_duplicate_key = above_element.key

                    # Create a new instance of the element using the grid factory
                    # Copy tags from the source element to the new one
                    new_element = grid.create_element(element_to_duplicate_key, target_y, target_x)

                    if new_element:
                        new_element.tags = list(above_element.tags) # Copy tags
                        grid.set_element(target_y, target_x, new_element)
                        # Don't mark the new element processed, let it act next frame if needed
                        # Mark the Duplicator as processed since it acted
                        self.processed = True
                        return # Exit after successful duplication

        # If no duplication occurred, mark duplicator as processed
        if not self.processed:
            self.processed = True

    # No run_interactions needed, logic is in update
    # def run_interactions(self, grid):
    #    pass

