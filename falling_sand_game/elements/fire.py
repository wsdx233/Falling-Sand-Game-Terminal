# -*- coding: utf-8 -*-
from .base import Gas, Element
import random
import curses
# No top-level imports of Ash, Smoke, Ember

class Fire(Gas):
    key = 'F'
    name = '火'
    char = '*'
    # Bright Red foreground, Yellow background
    color = (curses.COLOR_RED, curses.COLOR_YELLOW, curses.A_BOLD)
    density = -4 # Lighter than most gases except maybe itself? Rises fast.
    rise_speed = 2
    spread_factor = 3
    is_heat_source = True
    burn_chance = 0.45 # Chance to ignite *one* neighbor per step
    burn_out_chance_fueled = 0.05
    burn_out_chance_idle = 0.15
    ash_on_burnout_chance = 0.4 # Chance to become Ash vs Smoke

    # Coordinates for spreading/burning (includes diagonals)
    BURN_CHECKS = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

    def run_interactions(self, grid):
        """Fire tries to burn neighbors and might burn out."""
        if self.processed: return

        fuel_consumed = False
        # 1. Try to burn ONE flammable neighbor
        flammable_neighbors = []
        for dy, dx in self.BURN_CHECKS:
            ny, nx = self.y + dy, self.x + dx
            if grid.is_valid(ny, nx):
                neighbor = grid.get_element(ny, nx)
                # Ensure neighbor exists, is flammable, not already burning/processed,
                # and not fire ('F') or ember ('B') by checking keys
                if neighbor and neighbor.is_flammable and not neighbor.processed \
                   and neighbor.key != 'F' and neighbor.key != 'B':
                    flammable_neighbors.append((ny, nx, neighbor))

        if flammable_neighbors and random.random() < self.burn_chance:
            ny, nx, target_neighbor = random.choice(flammable_neighbors)

            # Determine product key based on fuel key
            product_key = None
            if target_neighbor.key in ('D', 'P', 'R'): product_key = 'H' # Ash
            elif target_neighbor.key in ('I', 'J'): product_key = 'K' # Smoke
            elif target_neighbor.key == 'U': product_key = 'B' # Ember
            elif target_neighbor.key == 'N': product_key = 'F' # Fire (Explosion)
            else: product_key = 'B' # Default to Ember

            if product_key:
                # Create product using grid factory
                new_product = grid.create_element(product_key, ny, nx)
                grid.set_element(ny, nx, new_product)
                if new_product: new_product.processed = True # Mark product as processed
                fuel_consumed = True

        # 2. Chance to burn out
        current_burn_out_chance = self.burn_out_chance_fueled if fuel_consumed else self.burn_out_chance_idle
        if random.random() < current_burn_out_chance:
            # Turn into Smoke or Ash
            product_key = 'H' if random.random() < self.ash_on_burnout_chance else 'K'
            # Create product using grid factory
            new_product = grid.create_element(product_key, self.y, self.x)
            grid.set_element(self.y, self.x, new_product)
            # Don't mark the new product as processed
            self.processed = True # Mark the fire itself as processed (it's gone)
            return

        # Mark as processed if not already done
        if not self.processed:
            self.processed = True

    def check_boundary_dissipation(self, grid):
        """Fire doesn't dissipate at the boundary, it just stops rising."""
        pass # Override Gas behavior


