# -*- coding: utf-8 -*-
from .base import StaticSolid, Element
import random
import curses
import math

class Singularity(StaticSolid):
    key = '@'
    name = '奇点'
    char = '@'
    color = (curses.COLOR_MAGENTA, curses.COLOR_BLACK, curses.A_BOLD | curses.A_BLINK) # Blinking Magenta on Black
    density = 10000 # Extremely dense conceptually
    is_static = True # Doesn't move
    is_solid = True
    pull_radius = 7 # Radius within which it pulls elements
    pull_strength = 0.4 # Chance per frame for an element within radius to be pulled closer
    consume_radius = 1 # Radius within which it consumes elements directly (orthogonal+diagonal)
    consume_chance = 0.8 # High chance to consume elements very close

    # Override update from StaticSolid
    def update(self, grid):
        if self.processed:
            return

        # --- Consumption Phase (inner radius) ---
        consumed_something = False
        for dy in range(-self.consume_radius, self.consume_radius + 1):
            for dx in range(-self.consume_radius, self.consume_radius + 1):
                if dy == 0 and dx == 0: continue # Skip self
                ny, nx = self.y + dy, self.x + dx
                if grid.is_valid(ny, nx):
                    neighbor = grid.get_element(ny, nx)
                    # Consume any non-static, non-singularity neighbor if chance passes
                    if neighbor and not neighbor.is_static and neighbor.key != '@' and not neighbor.processed:
                        if random.random() < self.consume_chance:
                            grid.set_element(ny, nx, None) # Consume
                            consumed_something = True
                            # Don't mark neighbor processed, it's gone.

        # --- Pulling Phase (outer radius) ---
        pulled_something = False
        if not consumed_something: # Maybe only pull if not consuming? Or always pull? Let's always try pulling.
            for r in range(max(0, self.y - self.pull_radius), min(grid.height, self.y + self.pull_radius + 1)):
                for c in range(max(0, self.x - self.pull_radius), min(grid.width, self.x + self.pull_radius + 1)):
                    # Skip self and inner consume radius
                    if abs(r - self.y) <= self.consume_radius and abs(c - self.x) <= self.consume_radius:
                        continue

                    dist = math.sqrt((self.x - c)**2 + (self.y - r)**2)
                    if dist <= self.pull_radius:
                        element = grid.get_element(r, c)
                        # Pull non-static, non-singularity elements if chance passes
                        if element and not element.is_static and element.key != '@' and not element.processed:
                            if random.random() < self.pull_strength:
                                # Calculate direction towards singularity
                                move_dy = 0
                                if r < self.y: move_dy = 1
                                elif r > self.y: move_dy = -1

                                move_dx = 0
                                if c < self.x: move_dx = 1
                                elif c > self.x: move_dx = -1

                                target_y, target_x = r + move_dy, c + move_dx

                                # Check if target cell is valid and closer/valid move
                                if grid.is_valid(target_y, target_x):
                                    target_element = grid.get_element(target_y, target_x)

                                    # Can move if target is empty or singularity itself (gets consumed next step)
                                    # Or if target is gas/liquid/lighter powder that element can displace? Complex.
                                    # Simple pull: only move if target is empty or singularity.
                                    if target_element is None or target_element.key == '@':
                                         # Move the element
                                         grid.set_element(r, c, None) # Clear original pos
                                         element.y, element.x = target_y, target_x # Update element coords
                                         grid.set_element(target_y, target_x, element) # Place in new pos
                                         # Mark the moved element as processed FOR THIS FRAME
                                         element.processed = True
                                         pulled_something = True
                                         # Don't break, try pulling multiple elements per frame? Yes.


        # Mark the singularity as processed
        if not self.processed:
            self.processed = True

    # No run_interactions needed
    # def run_interactions(self, grid):
    #    pass
