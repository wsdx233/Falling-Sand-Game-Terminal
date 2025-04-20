# -*- coding: utf-8 -*-
from .base import Powder, Element # Inherit from Powder structure, but reverse gravity
import random
import curses

class AntiGravityPowder(Powder):
    key = 'a'
    name = '反重力粉末'
    char = '^' # Use caret for visual cue
    color = (curses.COLOR_MAGENTA, -1) # Magenta color
    density = -2 # Very light, floats above gases/liquids? Or treat density normally but move up?
                 # Let's keep density somewhat normal (e.g., 3) but override movement logic.
    density = 3
    is_powder = True # Behaves structurally like powder
    is_solid = True

    def update(self, grid):
        """Overrides Powder update to move upwards instead of downwards."""
        if self.processed:
            return

        # Interactions first (if any defined for this element)
        self.run_interactions(grid)
        if self.processed:
            return

        # --- Movement Logic (Upwards) ---
        potential_y = self.y - 1 # Check UP instead of down
        moved = False

        # 1. Try moving straight up
        if grid.is_valid(potential_y, self.x):
            above_element = grid.get_element(potential_y, self.x)
            if above_element is None:
                if self._move_to(grid, potential_y, self.x): moved = True
            # Can it displace elements *above* it?
            # Let's say it displaces only Gases or lighter AntiGravityPowder
            elif above_element is not None:
                can_displace_target = False
                if above_element.is_gas:
                    # Compare density normally: if self is denser than gas, it pushes up.
                    can_displace_target = self._can_displace(above_element)
                elif isinstance(above_element, AntiGravityPowder):
                     # Lighter AntiGravity powder pushes up denser AntiGravity powder? Makes sense.
                     can_displace_target = self.density < above_element.density # Reversed check

                if can_displace_target:
                    self._swap_with(grid, potential_y, self.x)
                    moved = True
            if moved: return

        # 2. Try moving diagonally up (if couldn't move straight up)
        if not moved:
            possible_targets = []
            directions = [-1, 1]
            random.shuffle(directions)

            for dx in directions:
                diag_x = self.x + dx
                if grid.is_valid(potential_y, diag_x): # Check upper diagonal cell
                    # Check diagonal target first
                    diag_element = grid.get_element(potential_y, diag_x)
                    if diag_element is None:
                        # Check if path sideways is clear (empty or gas)
                        side_element = grid.get_element(self.y, diag_x)
                        can_pass_side = (side_element is None or side_element.is_gas)
                        if can_pass_side:
                             possible_targets.append((diag_x, False)) # Move diagonally up
                             break
                    elif diag_element is not None:
                        # Check if diagonal target is displaceable (Gas or lighter AGPowder)
                        can_displace_target = False
                        if diag_element.is_gas:
                            can_displace_target = self._can_displace(diag_element)
                        elif isinstance(diag_element, AntiGravityPowder):
                             can_displace_target = self.density < diag_element.density

                        if can_displace_target:
                             # Check if path sideways is clear
                             side_element = grid.get_element(self.y, diag_x)
                             can_pass_side = (side_element is None or side_element.is_gas)
                             if can_pass_side:
                                 possible_targets.append((diag_x, True)) # Swap diagonally up
                                 break

            if possible_targets:
                target_x, is_swap = possible_targets[0]
                if is_swap:
                    self._swap_with(grid, potential_y, target_x)
                else:
                    self._move_to(grid, potential_y, target_x)
                moved = True
            if moved: return

        # 3. Final Processing Flag
        if not self.processed:
            self.processed = True

    # Inherits run_interactions from base Powder (does nothing by default)
    # def run_interactions(self, grid):
    #     pass
