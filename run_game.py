#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to run the Falling Sand Game.
Ensures the game package is in the Python path if run from outside.
"""

import os
import sys

# Add the parent directory of 'falling_sand_game' to the Python path
# This allows running 'python run_game.py' from the project root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.dirname(script_dir) # If run_game.py is inside falling_sand_game dir
project_root = script_dir # If run_game.py is in the same dir as falling_sand_game dir
sys.path.insert(0, project_root)


# Now import the main entry point from the package
try:
    # Make sure the elements directory exists before trying to import main
    # main() will create it if needed, but good to check path logic here.
    element_path_check = os.path.join(project_root, "falling_sand_game", "elements")
    # print(f"Checking for elements at: {element_path_check}") # Debug print

    from falling_sand_game.main import main as run_main
except ImportError as e:
    print("Error: Could not import the game module.")
    print("Please ensure 'run_game.py' is in the project root directory")
    print(f" (the directory containing the 'falling_sand_game' folder),")
    print(f" or that the 'falling_sand_game' package is correctly installed.")
    print(f"Python Path: {sys.path}")
    print(f"Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred during import: {e}")
    sys.exit(1)


if __name__ == "__main__":
    print("Starting Falling Sand Game...")
    run_main()
    print("Game finished.")