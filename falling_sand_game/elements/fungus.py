# -*- coding: utf-8 -*-
from .base import Solid, Element # Fungus is a solid that spreads
import random
import curses

class Fungus(Solid):
    key = 'f'
    name = '真菌'
    char = 'f'
    color = (curses.COLOR_GREEN, curses.COLOR_RED) # Green on Red/Brown bg
    density = 1.5 # Light solid
    is_static = False # It grows/spreads
    is_solid = True
    is_flammable = True # Organic
    dissolvable_by_acid = True
    spread_chance = 0.005 # Chance to spread to an adjacent valid spot
    spore_release_chance = 0.001 # Chance to release a spore into adjacent empty space
    max_neighbors_to_spread = 2 # Limit spread if too crowded

    # Directions for spreading and spore release (orthogonal + diagonal)
    SPREAD_DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    def run_interactions(self, grid):
        """Fungus tries to spread to adjacent growable surfaces or release spores."""
        if self.processed: return

        neighbor_count = 0
        possible_spread_spots = []
        possible_spore_spots = []

        for dy, dx in self.SPREAD_DIRECTIONS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                if neighbor:
                    # Count existing fungus neighbors
                    if isinstance(neighbor, Fungus):
                         neighbor_count += 1
                    # Check if neighbor is something Fungus can grow over/consume (e.g., Mud, Plant, Wood)
                    if neighbor.key in ('R', 'P', 'd') and not neighbor.processed: # Mud, Plant, Wood (key 'd')
                        possible_spread_spots.append((ny, nx, neighbor))
                else: # Empty space is potential spore spot
                    possible_spore_spots.append((ny, nx))

        # 1. Attempt to Spread (if not too crowded)
        spread_occurred = False
        if neighbor_count < self.max_neighbors_to_spread and \
           possible_spread_spots and random.random() < self.spread_chance:

            target_y, target_x, target_element = random.choice(possible_spread_spots)
            # Replace the target element with new Fungus
            new_fungus = Fungus(target_y, target_x)
            new_fungus.tags = list(self.tags) # Copy tags
            grid.set_element(target_y, target_x, new_fungus)
            new_fungus.processed = True # Mark new growth as processed
            spread_occurred = True

        # 2. Attempt to Release Spore (only if didn't spread)
        if not spread_occurred and possible_spore_spots and random.random() < self.spore_release_chance:
            spore_y, spore_x = random.choice(possible_spore_spots)
            # Create a Spore element (key ',')
            new_spore = grid.create_element(',', spore_y, spore_x)
            if new_spore:
                 new_spore.tags = list(self.tags) # Copy tags
                 grid.set_element(spore_y, spore_x, new_spore)
                 # Don't mark spore as processed, let it fall/drift

        # Mark the original fungus as processed for this frame
        if not self.processed:
            self.processed = True
