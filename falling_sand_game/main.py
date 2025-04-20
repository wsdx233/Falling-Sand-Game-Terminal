# -*- coding: utf-8 -*-
import curses
import time
import sys
import traceback
import math
import os # Import os for path checking

# Import game components
from .config import DEFAULT_TARGET_FPS, GAME_AREA_RATIO, ELEMENT_DIR, DEFAULT_COLOR_PAIR_INDEX
# Import the element manager instance
from .element_manager import element_manager
from .game import Game
# Import the command processor
from .command import CommandProcessor, CommandError

def setup_colors():
    """Initializes curses color pairs based on loaded element definitions from the manager."""
    # Get registry from the manager
    registry = element_manager.get_registry()

    if not curses.has_colors():
        print("Warning: Terminal does not support colors.")
        # Assign default pair index to all elements if no colors
        for element_class in registry.values():
             try:
                 element_class.color_pair_index = DEFAULT_COLOR_PAIR_INDEX
             except AttributeError:
                 print(f"Error: Cannot set color_pair_index for {element_class}")
        return False

    curses.start_color()
    bg_color = curses.COLOR_BLACK # Default background
    try:
        # Try using terminal's default background if possible
        curses.use_default_colors()
        bg_color = -1 # Use terminal's default background
        # print("Using default terminal background color.")
    except curses.error:
        # Fallback if default colors aren't supported
        # print("Warning: Cannot use default colors. Falling back to black background.")
        try:
            # Initialize pair 0 as white on black if not using default
            curses.init_pair(DEFAULT_COLOR_PAIR_INDEX, curses.COLOR_WHITE, curses.COLOR_BLACK)
        except curses.error as e:
             print(f"Error initializing default color pair 0: {e}")
             return False # Cannot proceed without default pair

    pair_id_counter = 1 # Start assigning from pair 1 (pair 0 is default/fallback)

    # Iterate through the registry obtained from the manager
    # Sort by key for consistent pair assignment order? Optional.
    sorted_registry = sorted(registry.items())

    for key, element_class in sorted_registry:
        if pair_id_counter >= curses.COLOR_PAIRS:
            print(f"Warning: Ran out of color pairs ({curses.COLOR_PAIRS}). Element '{key}' will use default.")
            try:
                element_class.color_pair_index = DEFAULT_COLOR_PAIR_INDEX
            except AttributeError: pass
            continue

        try:
            # Get color definition from the class attribute 'color'
            # Default: White foreground, default background
            color_def = getattr(element_class, 'color', (curses.COLOR_WHITE, bg_color))
            fg = color_def[0]
            # Use element's specific bg or the determined default bg
            bg = color_def[1] if len(color_def) > 1 and color_def[1] is not None else bg_color
            # Attributes are handled separately now (e.g., via tags or drawing logic)

            # Validate color numbers
            valid_fg = fg if 0 <= fg < curses.COLORS else curses.COLOR_WHITE
            # Use default bg (-1) or validate explicit bg
            valid_bg = bg if bg == -1 or (0 <= bg < curses.COLORS) else bg_color

            if valid_fg != fg or valid_bg != bg:
                print(f"Warning: Invalid color value for element '{key}'. Using defaults ({valid_fg}, {valid_bg}).")

            curses.init_pair(pair_id_counter, valid_fg, valid_bg)
            # Store the assigned pair index back into the class attribute
            element_class.color_pair_index = pair_id_counter
            pair_id_counter += 1

        except AttributeError:
            print(f"Warning: Could not access 'color' attribute for element class '{element_class.__name__}' key '{key}'. Using default.")
            try: element_class.color_pair_index = DEFAULT_COLOR_PAIR_INDEX
            except AttributeError: pass
        except curses.error as e:
             print(f"Error initializing color pair {pair_id_counter} for element '{key}': {e}. Assigning default.")
             try: element_class.color_pair_index = DEFAULT_COLOR_PAIR_INDEX
             except AttributeError: pass
             # Don't increment pair_id_counter if init failed
        except Exception as e:
            print(f"Unexpected error setting up color for element '{key}': {e}. Using default.")
            try: element_class.color_pair_index = DEFAULT_COLOR_PAIR_INDEX
            except AttributeError: pass

    # print(f"Initialized {pair_id_counter - 1} color pairs.")
    return True

def get_command_input(stdscr, prompt="CMD> "):
    """Gets command input from the user at the bottom of the screen."""
    h, w = stdscr.getmaxyx()
    prompt_line = h - 1
    command_str = ""
    cursor_pos = len(prompt)

    curses.curs_set(1) # Show cursor for input
    stdscr.nodelay(False) # Blocking input for command entry

    while True:
        # Display prompt and current command string
        try:
            stdscr.move(prompt_line, 0)
            stdscr.clrtoeol() # Clear the line
            display_str = prompt + command_str
            stdscr.addstr(prompt_line, 0, display_str[:w-1]) # Show command, truncated
            # Move cursor to correct position within the input string
            stdscr.move(prompt_line, min(cursor_pos, w - 1))
            stdscr.refresh()
        except curses.error:
            pass # Ignore screen errors

        key = stdscr.getch() # Wait for key

        # Handle Enter
        if key == curses.KEY_ENTER or key == 10 or key == 13:
            break
        # Handle Backspace/Delete
        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            if cursor_pos > len(prompt):
                command_str = command_str[:cursor_pos - len(prompt) - 1] + command_str[cursor_pos - len(prompt):]
                cursor_pos -= 1
        # Handle regular characters
        elif 32 <= key <= 126: # Printable ASCII
             # Insert character at cursor position
             command_str = command_str[:cursor_pos - len(prompt)] + chr(key) + command_str[cursor_pos - len(prompt):]
             cursor_pos += 1
        # Handle other keys (like arrows, etc.) - currently ignored for simplicity
        elif key == curses.KEY_LEFT:
             cursor_pos = max(len(prompt), cursor_pos - 1)
        elif key == curses.KEY_RIGHT:
             cursor_pos = min(len(prompt) + len(command_str), cursor_pos + 1)
        # Add other special key handlers if needed (Home, End, Delete key, etc.)

    curses.curs_set(0) # Hide cursor again
    stdscr.nodelay(True) # Restore non-blocking input
    # Clear the prompt line after finishing
    try:
        stdscr.move(prompt_line, 0)
        stdscr.clrtoeol()
        stdscr.refresh()
    except curses.error:
        pass
    return command_str


def game_loop(stdscr):
    """The main game loop managed by curses.wrapper."""
    # --- Initial Curses Setup ---
    stdscr.nodelay(True)  # Non-blocking input
    curses.curs_set(0)    # Hide terminal cursor

    # --- Load Elements via Manager ---
    if not element_manager.is_loaded:
         element_manager.load_elements(ELEMENT_DIR)

    if not element_manager.get_registry():
        stdscr.clear()
        # Use a loop to keep message until key pressed
        while True:
            h, w = stdscr.getmaxyx()
            msg = f"Error: No elements loaded from {ELEMENT_DIR}. Press Q to exit."
            try:
                 stdscr.addstr(h // 2, max(0, (w - len(msg)) // 2), msg)
                 stdscr.refresh()
                 key = stdscr.getch()
                 if key == ord('q') or key == ord('Q'):
                     return # Exit loop function
                 time.sleep(0.1) # Prevent busy-waiting
            except curses.error: # Handle potential screen too small error
                 time.sleep(0.1)
                 key = stdscr.getch() # Still try to get input
                 if key == ord('q') or key == ord('Q'): return


    # --- Setup Colors ---
    has_colors = setup_colors()

    # --- Game Initialization ---
    height, width = stdscr.getmaxyx()
    game_instance = Game(height, width, GAME_AREA_RATIO)
    command_processor = CommandProcessor(game_instance, stdscr) # Pass game and screen

    # --- Timing ---
    last_frame_time = time.time()

    # --- Main Loop ---
    while game_instance.running:
        # Calculate dynamic frame duration based on game's target FPS
        frame_duration = 1.0 / game_instance.target_fps
        current_time = time.time()
        last_frame_time = current_time

        # --- Handle Input ---
        key = stdscr.getch() # Get input (-1 if none)

        if game_instance.command_mode:
            # Enter command input state
            command_string = get_command_input(stdscr)
            game_instance.command_mode = False # Exit command mode after input
            if command_string:
                command_processor.process_command(command_string)
            # After processing command, redraw immediately
            try:
                game_instance.draw(stdscr)
                stdscr.refresh()
            except curses.error: pass # Ignore draw errors
            continue # Skip rest of loop iteration

        # --- Handle Normal Game Input and Resize ---
        if key != -1:
            if key == curses.KEY_RESIZE:
                new_height, new_width = stdscr.getmaxyx()
                # Check if resize actually occurred and dimensions are valid
                if (new_height != game_instance.height or new_width != game_instance.width) and new_height > 0 and new_width > 0:
                     try:
                         # Important: redraw *before* resize calculations if needed
                         # stdscr.clear(); stdscr.refresh() # Maybe clear first?
                         game_instance.resize(new_height, new_width)
                         # Re-create command processor with new screen dimensions?
                         # No, it holds a reference, should be fine.
                         stdscr.clear() # Clear after resize logic completes
                         stdscr.refresh()
                     except Exception as resize_err:
                         # Log or display? Can be disruptive. Re-raise for main handler.
                         raise RuntimeError(f"Resize Error: {resize_err}") from resize_err
            else:
                # Pass other keys to game instance for handling
                game_instance.handle_input(key)


        # --- Update Simulation ---
        if game_instance.running: # Check if input caused exit
            try:
                game_instance.update()
            except Exception as sim_error:
                raise RuntimeError(f"Simulation Error: {sim_error}") from sim_error # Reraise

        # --- Draw Screen ---
        if game_instance.running:
            try:
                # Draw game state (grid, cursor, info panel)
                game_instance.draw(stdscr)
                # Refresh the physical screen AFTER drawing everything
                stdscr.refresh()
            except curses.error as draw_error:
                # Ignore common non-fatal curses errors during drawing
                # (e.g., drawing off-screen during resize transient state)
                if "addch" in str(draw_error) or "addstr" in str(draw_error):
                     pass # Often happens at edges or small terminals, try to continue
                else:
                     # Re-raise other curses errors if they seem more critical
                     raise RuntimeError(f"Drawing Error (curses): {draw_error}") from draw_error
            except Exception as draw_exception:
                 raise RuntimeError(f"Drawing Error: {draw_exception}") from draw_exception # Reraise

        # --- Frame Rate Control ---
        elapsed_time = time.time() - current_time
        sleep_time = frame_duration - elapsed_time
        if sleep_time > 0:
            time.sleep(sleep_time)

# --- Entry Point ---
def main():
    """Program entry point, sets up curses wrapper and error handling."""
    # Create elements directory early if it doesn't exist
    if not os.path.exists(ELEMENT_DIR):
        try:
            os.makedirs(ELEMENT_DIR, exist_ok=True) # exist_ok=True is safer
            print(f"Checked/Created directory: {ELEMENT_DIR}")
        except OSError as e:
            print(f"Error creating directory {ELEMENT_DIR}: {e}")
            print("Cannot proceed without element directory.")
            sys.exit(1)

    try:
        # curses.wrapper handles terminal setup and safe restoration
        curses.wrapper(game_loop)
        print("Game exited normally.")
    except RuntimeError as loop_error:
         # curses should be ended by wrapper here
         print("\n" + "="*20 + " GAME LOOP ERROR! " + "="*20)
         traceback.print_exc()
         print("="*60)
         print("Game halted due to an error during simulation, drawing, or resize.")
         sys.exit(1)
    except curses.error as ce:
        try: curses.endwin()
        except: pass
        print("\n" + "="*20 + " CURSES ERROR! " + "="*20)
        print(f"A Curses error occurred: {ce}")
        traceback.print_exc()
        print("="*60)
        print("Terminal might be in a bad state. Try running 'reset'.")
        sys.exit(1)
    except CommandError as cmd_err: # Catch command errors if they escape loop
         try: curses.endwin()
         except: pass
         print("\n" + "="*20 + " COMMAND ERROR! " + "="*20)
         print(f"Error executing command: {cmd_err}")
         traceback.print_exc()
         print("="*60)
         sys.exit(1)
    except KeyboardInterrupt:
         try: curses.endwin()
         except: pass
         print("\nGame interrupted by user (Ctrl+C).")
         sys.exit(0)
    except Exception as e:
        try: curses.endwin()
        except: pass
        print("\n" + "="*20 + " UNEXPECTED ERROR! " + "="*20)
        traceback.print_exc()
        print("="*60)
        print("An unexpected error occurred.")
        sys.exit(1)


# Run main if this script is executed directly
if __name__ == "__main__":
    main()
