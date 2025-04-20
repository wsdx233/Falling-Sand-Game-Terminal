# -*- coding: utf-8 -*-
from .base import Powder, Element # Let's make it a powder that falls
import random
import curses

class Radioactive(Powder):
    key = 'u'
    name = '放射物'
    char = 'u'
    color = (curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.A_BOLD) # Bright Green on Yellow
    density = 8 # Dense powder
    is_powder = True
    is_solid = True
    is_flammable = False # Doesn't burn easily
    dissolvable_by_acid = True # Acid might neutralize it?
    decay_chance = 0.001 # Chance per frame to decay into something else (e.g., Lead/Metal)
    mutation_chance = 0.005 # Chance per frame to mutate an adjacent non-static neighbor
    radiation_particle_chance = 0.01 # Chance to emit a short-lived particle effect

    # Coordinates for mutation check (orthogonal + diagonal)
    MUTATION_CHECKS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    def run_interactions(self, grid):
        """Radioactive material decays and mutates neighbors."""
        if self.processed: return

        # 1. Decay
        if random.random() < self.decay_chance:
            # Turn into Metal ('M') - assuming Metal represents a stable end product like lead
            new_stable = grid.create_element('M', self.y, self.x)
            if new_stable:
                 new_stable.tags = list(self.tags) # Copy tags
                 grid.set_element(self.y, self.x, new_stable)
                 # Don't mark new metal processed? Let it settle if needed.
            self.processed = True # Self is gone
            return

        # 2. Mutate Neighbor (if didn't decay)
        mutated_neighbor = False
        if random.random() < self.mutation_chance:
            possible_targets = []
            for dy, dx in self.MUTATION_CHECKS:
                ny, nx = self.y + dy, self.x + dx
                if grid.is_valid(ny, nx):
                    neighbor = grid.get_element(ny, nx)
                    # Can mutate non-static, non-radioactive elements that aren't processed
                    if neighbor and not neighbor.is_static and neighbor.key != 'u' and not neighbor.processed:
                        possible_targets.append((ny, nx, neighbor))

            if possible_targets:
                ny, nx, target_neighbor = random.choice(possible_targets)
                # Simple mutation: turn target into another random element? Risky.
                # Or turn into Virus ('V') or Fungus ('f')?
                mutated_key = random.choice(['V', 'f'])
                new_mutant = grid.create_element(mutated_key, ny, nx)
                if new_mutant:
                    new_mutant.tags = list(target_neighbor.tags) # Copy tags from original
                    grid.set_element(ny, nx, new_mutant)
                    new_mutant.processed = True # Mark mutant processed
                    mutated_neighbor = True

        # 3. Emit Radiation Particle (visual effect - hard in curses)
        # Instead, let's just have a small chance to turn an adjacent EMPTY cell into fire or acid temporarily?
        # if random.random() < self.radiation_particle_chance:
        #     empty_neighbors = []
        #     for dy, dx in self.MUTATION_CHECKS: # Reuse check coordinates
        #         ny, nx = self.y + dy, self.x + dx
        #         if grid.is_valid(ny, nx) and grid.get_element(ny, nx) is None:
        #             empty_neighbors.append((ny,nx))
        #     if empty_neighbors:
        #         py, px = random.choice(empty_neighbors)
        #         particle_key = random.choice(['F']) # Temp Fire particle?
        #         # Need a way for this particle to disappear quickly.
        #         # This adds complexity. Skip visual particle for now.

        # Base Powder update runs AFTER interactions in this setup
        # So, don't set processed = True here unless decay happened.

