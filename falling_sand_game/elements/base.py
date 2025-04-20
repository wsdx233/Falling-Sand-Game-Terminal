# -*- coding: utf-8 -*-
import random
import curses

# --- Base Classes ---
class Element:
    """Base class for all elements in the simulation."""
    key = ' '  # Unique single character key identifying the element type
    name = "Element"
    char = ' ' # Character used for drawing
    color = (curses.COLOR_WHITE, -1) # Default: White foreground, default background
    color_pair_index = 0 # Assigned during curses initialization
    processed = False # Flag to prevent processing an element multiple times per frame
    density = 0 # Affects how elements displace each other. Higher sinks below lower.
    is_static = True # Does the element generally not move on its own?
    is_flammable = False
    is_liquid = False
    is_gas = False
    is_powder = False
    is_solid = True # Default assumption unless specified otherwise
    dissolvable_by_acid = False
    is_heat_source = False
    can_freeze = False # Can this element be frozen by CryoPowder?
    can_grow_on = False # Can plants/fungus grow on this? (e.g., Mud)

    # Property for light emission (used by Lamp)
    emits_light = False
    light_radius = 0

    # Property for light sensitivity (used by PhotosensitivePowder)
    is_light_sensitive = False


    def __init__(self, y, x):
        self.y = y
        self.x = x
        self.processed = False # Reset processed flag on creation
        self.tags: list[str] = [] # Initialize empty list for custom tags

    def update(self, grid):
        """
        The main update logic for the element.
        Should be overridden by subclasses.
        The base implementation does nothing but mark as processed.
        """
        # Ensure processed flag is set if not already done by subclass
        if not self.processed:
            self.processed = True

    def get_drawing_info(self):
        """Returns the character and color pair index for drawing."""
        # Subclasses might override this for dynamic appearances
        return self.char, self.color_pair_index

    def _can_displace(self, target_element):
        """
        Checks if this element can displace the target based on density.
        Type-specific displacement rules are handled within each element's update logic.
        """
        if target_element is None:
            return True # Can always move into empty space
        # Density check: Higher density displaces lower density.
        return self.density > target_element.density

    def _swap_with(self, grid, ny, nx):
        """Swaps this element's position with the target cell (ny, nx) on the grid."""
        target_element = grid.get_element(ny, nx)

        # Store current position before modifying grid
        old_y, old_x = self.y, self.x

        # Update grid state
        # Pass tags when setting elements? No, tags are per-instance.
        grid.set_element(old_y, old_x, target_element) # Put target where self was
        grid.set_element(ny, nx, self)               # Put self where target was

        # Update element positions and internal coordinates (including tags if they were swapped)
        if target_element:
            target_element.y, target_element.x = old_y, old_x
            # Swapping tags might be needed if tags define behavior/appearance
            # For now, assume tags stay with the original instance object.

        self.y, self.x = ny, nx
        self.processed = True # Mark self as processed *after* successfully moving/swapping


    def _move_to(self, grid, ny, nx):
        """Moves this element to the target cell (ny, nx), assuming it's empty."""
        if grid.get_element(ny, nx) is None:
            grid.set_element(self.y, self.x, None) # Clear old position
            # Update self position *before* placing in grid for consistency
            self.y, self.x = ny, nx
            grid.set_element(ny, nx, self) # Set new position (implicitly handles tags)
            self.processed = True # Mark self as processed after moving
            return True
        return False

    def check_neighbors(self, grid, check_coords, condition_func):
        """
        Helper to check neighbors at relative coordinates.
        Args:
            grid: The game grid.
            check_coords: List of (dy, dx) tuples for relative coordinates.
            condition_func: A function that takes an element (or None) and returns True if the condition is met.
        Returns:
            List of (y, x, element) tuples for neighbors meeting the condition.
        """
        found = []
        for dy, dx in check_coords:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                if condition_func(neighbor):
                    found.append((ny, nx, neighbor))
        return found


class Movable(Element):
    """Base class for elements that can move."""
    is_static = False
    is_solid = False # Movable things are usually not considered 'static solids'

class Powder(Movable):
    """
    Behavior for powder-like elements (Sand, Salt, Ash, etc.).
    Fall down, displacing lighter elements (liquids, gases, lighter powders).
    """
    is_powder = True
    is_solid = True # Treat powders as granular solids for some interactions
    density = 5 # Example default density
    can_freeze = True # Most powders can be 'frozen' into a solid block

    def update(self, grid):
        if self.processed:
            return

        # --- Interactions first? Or Movement first? ---
        # Let's try interactions *before* movement for powders, allows reactions before falling
        self.run_interactions(grid)
        if self.processed: # Interaction might have transformed or moved the element
            return

        # --- Movement Logic (if not processed by interaction) ---
        potential_y = self.y + 1
        moved = False

        # 1. Try moving straight down
        if grid.is_valid(potential_y, self.x):
            below_element = grid.get_element(potential_y, self.x)
            if below_element is None:
                if self._move_to(grid, potential_y, self.x): moved = True
            elif below_element is not None:
                # Powders displace liquids, gases, or OTHER powders if denser
                can_displace_target = False
                if below_element.is_liquid or below_element.is_gas:
                    can_displace_target = self._can_displace(below_element)
                elif below_element.is_powder:
                    can_displace_target = self._can_displace(below_element)

                if can_displace_target:
                    self._swap_with(grid, potential_y, self.x)
                    moved = True
            if moved: return

        # 2. Try moving diagonally down (if couldn't move straight down)
        if not moved:
            possible_targets = []
            directions = [-1, 1]
            random.shuffle(directions)

            for dx in directions:
                diag_x = self.x + dx
                if grid.is_valid(potential_y, diag_x):
                    # Check diagonal target first
                    diag_element = grid.get_element(potential_y, diag_x)
                    if diag_element is None:
                        # Check if path sideways is clear (empty, liquid, gas)
                        side_element = grid.get_element(self.y, diag_x)
                        can_pass_side = (side_element is None or side_element.is_liquid or side_element.is_gas)
                        if can_pass_side:
                             possible_targets.append((diag_x, False)) # Move diagonally
                             break
                    elif diag_element is not None:
                         # Check if diagonal target is displaceable
                        can_displace_target = False
                        if diag_element.is_liquid or diag_element.is_gas:
                            can_displace_target = self._can_displace(diag_element)
                        elif diag_element.is_powder:
                            can_displace_target = self._can_displace(diag_element)

                        if can_displace_target:
                             # Check if path sideways is clear
                             side_element = grid.get_element(self.y, diag_x)
                             can_pass_side = (side_element is None or side_element.is_liquid or side_element.is_gas)
                             if can_pass_side:
                                 possible_targets.append((diag_x, True)) # Swap diagonally
                                 break

            if possible_targets:
                target_x, is_swap = possible_targets[0]
                if is_swap:
                    self._swap_with(grid, potential_y, target_x)
                else:
                    self._move_to(grid, potential_y, target_x)
                moved = True
            if moved: return

        # 3. Final Processing Flag (if not processed by move or interaction)
        if not self.processed:
            self.processed = True

    def run_interactions(self, grid):
        """Placeholder for specific powder interactions, called BEFORE movement attempts."""
        pass # Base powder has no interactions


class Liquid(Movable):
    """Behavior for liquid elements (Water, Lava, etc.)."""
    is_liquid = True
    density = 1
    flow_speed = 3
    can_freeze = True # Liquids can typically be frozen

    def update(self, grid):
        if self.processed:
            return

        # --- 1. Interactions First ---
        self.run_interactions(grid)
        if self.processed: # Return if interaction consumed/transformed self
            return

        # --- 2. Movement Logic (if not processed by interaction) ---
        moved = False
        potential_y = self.y + 1

        # Try moving straight down
        if grid.is_valid(potential_y, self.x):
            below_element = grid.get_element(potential_y, self.x)
            if below_element is None:
                if self._move_to(grid, potential_y, self.x): moved = True
            # Liquids displace gases or other liquids if denser
            elif (below_element.is_gas or below_element.is_liquid) and self._can_displace(below_element):
                 self._swap_with(grid, potential_y, self.x); moved = True
            if moved: return

        # Try moving diagonally down
        if not moved:
            possible_targets = []
            directions = [-1, 1]
            random.shuffle(directions)
            for dx in directions:
                diag_x = self.x + dx
                if grid.is_valid(potential_y, diag_x):
                    diag_element = grid.get_element(potential_y, diag_x)
                    if diag_element is None:
                         # Check side clearance (empty or gas)
                         side_element = grid.get_element(self.y, diag_x)
                         can_pass_side = (side_element is None or side_element.is_gas)
                         if can_pass_side:
                             possible_targets.append((diag_x, False)); break
                    # Displace gases/other liquids diagonally if denser
                    elif (diag_element.is_gas or diag_element.is_liquid) and self._can_displace(diag_element):
                         # Check side clearance (empty or gas)
                         side_element = grid.get_element(self.y, diag_x)
                         can_pass_side = (side_element is None or side_element.is_gas)
                         if can_pass_side:
                             possible_targets.append((diag_x, True)); break

            if possible_targets:
                target_x, is_swap = possible_targets[0]
                if is_swap: self._swap_with(grid, potential_y, target_x)
                else: self._move_to(grid, potential_y, target_x)
                moved = True; return

        # Try flowing horizontally
        if not moved:
            direction = random.choice([-1, 1])
            can_flow = False
            final_target_x = self.x
            is_swap_flow = False

            # Check preferred direction
            for i in range(1, self.flow_speed + 1):
                potential_flow_x = self.x + direction * i
                if not grid.is_valid(self.y, potential_flow_x): break
                check_element = grid.get_element(self.y, potential_flow_x)
                if check_element is None:
                    final_target_x = potential_flow_x; can_flow = True; is_swap_flow = False; continue # Keep searching further
                # Liquids displace gases/other liquids horizontally if denser
                elif (check_element.is_gas or check_element.is_liquid) and self._can_displace(check_element):
                    final_target_x = potential_flow_x; can_flow = True; is_swap_flow = True; break # Found displaceable, stop search
                else: break # Blocked

            # Check other direction if first was blocked/OOB *or* only found empty space (try for swap)
            if not is_swap_flow: # Only check other dir if no swap found yet
                 new_direction = -direction
                 for i in range(1, self.flow_speed + 1):
                     potential_flow_x = self.x + new_direction * i
                     if not grid.is_valid(self.y, potential_flow_x): break
                     check_element = grid.get_element(self.y, potential_flow_x)
                     # If this direction offers a swap, prioritize it
                     if (check_element and (check_element.is_gas or check_element.is_liquid) and self._can_displace(check_element)):
                          final_target_x = potential_flow_x; can_flow = True; is_swap_flow = True; break
                     # If this direction offers empty space and first dir didn't, take it
                     elif check_element is None and not can_flow:
                          final_target_x = potential_flow_x; can_flow = True; is_swap_flow = False; continue
                     # If blocked or worse than first dir found, stop checking this direction
                     elif check_element is not None:
                          break

            # Execute flow if a target was found
            if can_flow and final_target_x != self.x:
                 if is_swap_flow:
                      self._swap_with(grid, self.y, final_target_x); moved = True
                 else:
                      if self._move_to(grid, self.y, final_target_x): moved = True
            if moved: return

        # --- 3. Final Processing Flag ---
        if not self.processed:
            self.processed = True

    def run_interactions(self, grid):
        """Placeholder for specific liquid interactions. Called BEFORE movement."""
        pass

class Gas(Movable):
    """Behavior for gas elements (Steam, Smoke, Fire)."""
    is_gas = True
    density = -5
    rise_speed = 1
    spread_factor = 2
    can_freeze = False # Gases typically don't get frozen by cryo powder

    def update(self, grid):
        if self.processed:
            return

        # --- 1. Movement Logic First ---
        # Gases try to rise and spread before interacting
        moved = False
        current_y, current_x = self.y, self.x # Store initial position

        # A. Try Rising
        can_rise = False
        final_target_y = current_y
        is_swap_rise = False

        for i in range(1, self.rise_speed + 1):
            check_y = current_y - i
            if not grid.is_valid(check_y, current_x):
                self.check_boundary_dissipation(grid)
                if self.processed: return # Dissipated at boundary
                break # Hit boundary
            above_element = grid.get_element(check_y, current_x)
            if above_element is None:
                final_target_y = check_y; can_rise = True; is_swap_rise = False; continue # Keep checking higher
            # Gases displace other gases if denser (less negative density)
            elif above_element.is_gas and self._can_displace(above_element):
                final_target_y = check_y; can_rise = True; is_swap_rise = True; break # Found displaceable
            else:
                break # Blocked

        if can_rise and final_target_y != current_y:
            if is_swap_rise:
                self._swap_with(grid, final_target_y, current_x); moved = True
            else:
                if self._move_to(grid, final_target_y, current_x): moved = True
            # self.y might have changed if moved/swapped

        # B. Try Spreading (if not processed by rising or dissipation)
        # Use potentially updated position (self.y, self.x)
        if not self.processed:
            spread_y, spread_x = self.y, self.x # Position after potential rise
            direction = random.choice([-1, 1])
            can_spread = False
            final_target_x = spread_x
            is_swap_spread = False

            # Check preferred direction
            for i in range(1, self.spread_factor + 1):
                 potential_spread_x = spread_x + direction * i
                 if not grid.is_valid(spread_y, potential_spread_x): break
                 check_element = grid.get_element(spread_y, potential_spread_x)
                 if check_element is None:
                     final_target_x = potential_spread_x; can_spread = True; is_swap_spread = False; continue
                 elif check_element.is_gas and self._can_displace(check_element):
                      final_target_x = potential_spread_x; can_spread = True; is_swap_spread = True; break
                 else: break

            # Check other direction if no swap found yet
            if not is_swap_spread:
                 new_direction = -direction
                 for i in range(1, self.spread_factor + 1):
                     potential_spread_x = spread_x + new_direction * i
                     if not grid.is_valid(spread_y, potential_spread_x): break
                     check_element = grid.get_element(spread_y, potential_spread_x)
                     if (check_element and check_element.is_gas and self._can_displace(check_element)):
                         final_target_x = potential_spread_x; can_spread = True; is_swap_spread = True; break
                     elif check_element is None and not can_spread:
                         final_target_x = potential_spread_x; can_spread = True; is_swap_spread = False; continue
                     elif check_element is not None: break

            # Execute spread
            if can_spread and final_target_x != spread_x:
                 if is_swap_spread:
                     self._swap_with(grid, spread_y, final_target_x); moved = True
                 else:
                     if self._move_to(grid, spread_y, final_target_x): moved = True

        # --- 2. Interactions (only if not processed by movement/dissipation) ---
        if not self.processed:
             self.run_interactions(grid) # Interactions might set processed = True

        # --- 3. Final Processing Flag ---
        if not self.processed:
            self.processed = True

    def run_interactions(self, grid):
        """Placeholder for specific gas interactions. Called AFTER movement attempts."""
        pass # Base Gas doesn't interact beyond potential dissipation

    def check_boundary_dissipation(self, grid):
        """Check if gas should dissipate at the top boundary."""
        # Default: Low chance to dissipate at boundary
        if random.random() < 0.01:
            grid.set_element(self.y, self.x, None)
            self.processed = True


class Solid(Element):
    """
    Base class for solid elements that might react but generally don't move
    on their own unless gravity affects them (e.g., Stone if placed mid-air,
    which might better inherit Powder). Use StaticSolid for truly immovable ones.
    """
    is_static = True # Default solid behavior is static unless gravity applies
    is_solid = True
    density = 10
    can_freeze = False # Solids typically aren't frozen further

    def update(self, grid):
        if self.processed:
            return
        # Interactions first for static solids
        self.run_interactions(grid)
        # If interaction didn't process it, mark as processed
        if not self.processed:
            self.processed = True

    def run_interactions(self, grid):
        """Placeholder for solid interactions (melting, reacting, growing)."""
        pass

class StaticSolid(Solid):
    """
    Solids that absolutely never move or react on their own (e.g., Wall, Glass, Lamp).
    Inherits from Solid, confirms is_static = True.
    """
    is_static = True
    density = 100

    # Override update to do nothing but set processed flag
    def update(self, grid):
        if not self.processed:
             self.processed = True

    # Override run_interactions to be empty
    def run_interactions(self, grid):
        pass
