# -*- coding: utf-8 -*-
from .base import Powder, Element
import random
import curses

class CryoPowder(Powder):
    key = '<'
    name = '冷冻粉末'
    char = '<'
    color = (curses.COLOR_CYAN, -1, curses.A_BOLD) # Bright Cyan
    density = 5.1 # Slightly denser than standard powder
    freeze_chance = 0.35 # Chance to freeze an adjacent freezable neighbor
    self_consume_chance = 0.05 # Chance to disappear after freezing something

    # Coordinates to check for freezing (includes diagonals for wider effect?)
    FREEZE_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

    def run_interactions(self, grid):
        """CryoPowder attempts to freeze adjacent freezable elements."""
        if self.processed: return

        frozen_neighbor = False
        # 1. Find freezable neighbors
        freezable_neighbors = []
        for dy, dx in self.FREEZE_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Check if neighbor exists, can be frozen, and isn't already Ice ('C') or processed
                if neighbor and neighbor.can_freeze and neighbor.key != 'C' and not neighbor.processed:
                    freezable_neighbors.append((ny, nx, neighbor))

        # 2. Attempt to freeze one neighbor
        if freezable_neighbors and random.random() < self.freeze_chance:
            ny, nx, target_neighbor = random.choice(freezable_neighbors)

            # Turn the neighbor into Ice ('C') using grid factory
            # Preserve tags? Let's copy tags from original to new ice.
            new_ice = grid.create_element('C', ny, nx)
            if new_ice:
                new_ice.tags = list(target_neighbor.tags) # Copy tags
                grid.set_element(ny, nx, new_ice)
                # Mark the new ice as processed for this frame to prevent chain reactions
                new_ice.processed = True
                frozen_neighbor = True

                # 3. Chance to consume self after freezing
                if random.random() < self.self_consume_chance:
                    grid.set_element(self.y, self.x, None) # Remove self
                    self.processed = True # Mark self as processed (it's gone)
                    return # Exit early

        # Mark as processed if interaction finished but self wasn't consumed
        # Base Powder update logic will handle final processing if no interaction/move occurred
        # However, since interaction runs first, set processed if we attempted interactions.
        # if not self.processed:
        #      self.processed = True

