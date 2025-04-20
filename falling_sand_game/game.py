# -*- coding: utf-8 -*-
import curses
import math
import random
import time # For potential timing/debug

from .grid import Grid
# Import the manager instance directly
from .element_manager import element_manager
from .config import EMPTY_CHAR, DEFAULT_CURSOR_SIZE, MAX_CURSOR_SIZE, DEFAULT_COLOR_PAIR_INDEX, DEFAULT_TARGET_FPS

class Game:
    """Manages the overall game state, grid, drawing, and update loop."""

    def __init__(self, height, width, game_area_ratio):
        self.height = max(1, height) # Ensure height is at least 1
        self.width = max(1, width) # Ensure width is at least 1
        self.game_area_ratio = game_area_ratio
        # Get registry and order from the manager instance
        self.element_types = element_manager.get_registry()
        self.placeable_elements_keys = element_manager.get_placeable_order()

        self._recalculate_layout() # Calculate game_width, info_width, etc.

        # Pass the manager instance to the Grid constructor
        self.grid = Grid(self.game_height, self.game_width, element_manager)

        # Game State
        self.cursor_x = self.game_width // 2
        self.cursor_y = self.game_height // 2
        self.cursor_size = DEFAULT_CURSOR_SIZE
        self.selected_index = 0 # Index into placeable_elements_keys
        self.element_scroll_offset = 0 # For scrolling the element list UI
        self.current_tags = [] # Tags to apply when placing elements
        self.target_fps = DEFAULT_TARGET_FPS # Current target FPS, can be changed by commands

        self.running = True
        self.command_mode = False # Flag for command input mode

    def _recalculate_layout(self):
        """Calculates game area and info panel dimensions."""
        self.game_width = max(1, math.floor(self.width * self.game_area_ratio))
        self.info_width = max(0, self.width - self.game_width - 1) # -1 for potential separator
        # Game height should not exceed screen height - 1 (to leave space for command line)
        self.game_height = max(1, self.height -1) # Game area uses almost full screen height

    def resize(self, new_height, new_width):
        """Handles terminal resize events."""
        old_height = self.height
        old_width = self.width
        # Ensure new dimensions are positive
        self.height = max(1, new_height)
        self.width = max(1, new_width)

        # Recalculate layout with new dimensions
        old_game_width = self.game_width
        old_game_height = self.game_height
        self._recalculate_layout() # This now recalculates game_height based on new self.height

        # Create a new grid, passing the manager instance
        new_grid = Grid(self.game_height, self.game_width, element_manager)
        # Copy old elements, considering the potentially changed game_height
        for r in range(min(old_game_height, self.game_height)):
            for c in range(min(old_game_width, self.game_width)):
                element = self.grid.get_element(r, c)
                if element:
                    # Use the factory method on the NEW grid to create elements
                    # Preserve tags when resizing
                    new_element = new_grid.create_element(element.key, r, c)
                    if new_element:
                        new_element.tags = list(element.tags) # Copy tags
                        new_grid.set_element(r, c, new_element)

        self.grid = new_grid

        # Adjust cursor position to be within new bounds
        self.cursor_x = min(max(0, self.cursor_x), self.game_width - 1)
        self.cursor_y = min(max(0, self.cursor_y), self.game_height - 1)

        # Reset scroll might be best after resize
        self.element_scroll_offset = 0


    def update(self):
        """Runs one simulation step."""
        # 1. Reset processed flags for all elements
        self.grid.reset_processed_flags()

        # 2. Iterate and update elements
        update_order = list(range(self.grid.height - 1, -1, -1)) # Default: bottom-up

        # Simple check: if 'a' (AntiGravityPowder) is loaded, alternate directions
        if 'a' in element_manager.get_registry():
             if int(time.time()) % 2 == 0:
                  update_order = list(range(self.grid.height)) # Top-down

        for y in update_order:
            x_indices = list(range(self.grid.width))
            random.shuffle(x_indices)
            for x in x_indices:
                element = self.grid.get_element(y, x)
                if element and not element.processed and element.y == y and element.x == x:
                    try:
                        element.update(self.grid)
                    except Exception as e:
                        raise RuntimeError(f"Error updating element {element.key} at ({x},{y}): {e}") from e

    def _get_selected_element_class(self):
        """Gets the class of the currently selected element."""
        if not self.placeable_elements_keys:
            return None
        if 0 <= self.selected_index < len(self.placeable_elements_keys):
            key = self.placeable_elements_keys[self.selected_index]
            return element_manager.get_element_class(key)
        # Handle potential index out of bounds if list shrinks? Reset index?
        elif self.placeable_elements_keys: # If list not empty but index invalid
            self.selected_index = 0
            return element_manager.get_element_class(self.placeable_elements_keys[0])
        return None

    def _get_list_max_height(self):
        """Calculates the maximum height available for the element list display."""
        # Needs to account for controls height, title, status lines, and the reserved bottom line
        # Estimate controls height (can be dynamic later if needed)
        controls_height = 10 # Approximate number of lines for controls section
        title_height = 1
        status_height = 4 # Approximate lines for status + tags + border
        reserved_bottom_line = 1
        # Ensure height is positive
        available_height = self.height - controls_height - title_height - status_height - reserved_bottom_line
        return max(1, available_height)

    def _adjust_scroll_for_selection(self):
        """Adjusts scroll offset to make the current selection visible."""
        if not self.placeable_elements_keys: return # No elements to scroll/select

        list_max_height_recalc = self._get_list_max_height()
        total_elements = len(self.placeable_elements_keys)
        max_offset = max(0, total_elements - list_max_height_recalc)

        if self.selected_index < self.element_scroll_offset:
            self.element_scroll_offset = self.selected_index
        elif self.selected_index >= self.element_scroll_offset + list_max_height_recalc:
            self.element_scroll_offset = self.selected_index - list_max_height_recalc + 1
        self.element_scroll_offset = max(0, min(self.element_scroll_offset, max_offset))


    def handle_input(self, key):
        """Processes user input. Returns True if input was handled, False otherwise."""
        if self.command_mode:
            return False # Let main loop handle command input

        list_max_height_recalc = self._get_list_max_height()
        total_elements = len(self.placeable_elements_keys) if self.placeable_elements_keys else 0
        max_offset = max(0, total_elements - list_max_height_recalc) if total_elements > 0 else 0

        if key == ord('q') or key == ord('Q'):
            self.running = False; return True
        elif key == curses.KEY_UP or key == ord('k'):
            self.cursor_y = max(0, self.cursor_y - 1); return True
        elif key == curses.KEY_DOWN or key == ord('j'):
            # Ensure cursor stays within the valid game area grid
            self.cursor_y = min(self.grid.height - 1, self.cursor_y + 1); return True
        elif key == curses.KEY_LEFT or key == ord('h'):
            self.cursor_x = max(0, self.cursor_x - 1); return True
        elif key == curses.KEY_RIGHT or key == ord('l'):
            # Ensure cursor stays within the valid game area grid
            self.cursor_x = min(self.grid.width - 1, self.cursor_x + 1); return True
        elif key == ord('['):
            self.cursor_size = max(1, self.cursor_size - 1); return True
        elif key == ord(']'):
            self.cursor_size = min(MAX_CURSOR_SIZE, self.cursor_size + 1); return True
        elif key == ord(' '): # Place element
            element_class = self._get_selected_element_class()
            if element_class:
                 try:
                    element_key = getattr(element_class, 'key', None)
                    if element_key is None: element_key = element_class(0,0).key
                    if element_key:
                        self._apply_cursor_action(lambda y, x: self.grid.create_element(element_key, y, x, tags=self.current_tags))
                 except Exception: pass
                 return True
            return False # No element selected
        elif key == curses.KEY_DC or key == ord('x'): # Delete element
             self._apply_cursor_action(lambda y, x: None)
             return True
        elif ord('1') <= key <= ord('9'):
            if total_elements > 0:
                num = key - ord('1')
                if num < total_elements:
                    self.selected_index = num
                    self._adjust_scroll_for_selection()
                return True
        elif key == ord('+') or key == ord('='):
            if total_elements > 0:
                self.selected_index = (self.selected_index + 1) % total_elements
                self._adjust_scroll_for_selection()
            return True
        elif key == ord('-') or key == ord('_'):
             if total_elements > 0:
                self.selected_index = (self.selected_index - 1 + total_elements) % total_elements
                self._adjust_scroll_for_selection()
             return True
        elif key == curses.KEY_NPAGE: # PageDown scroll
            self.element_scroll_offset += list_max_height_recalc // 2
            self.element_scroll_offset = min(max_offset, self.element_scroll_offset)
            return True
        elif key == curses.KEY_PPAGE: # PageUp scroll
            self.element_scroll_offset -= list_max_height_recalc // 2
            self.element_scroll_offset = max(0, self.element_scroll_offset)
            return True
        elif key == ord('c') or key == ord('C'):
            self.grid.clear()
            return True
        elif key == ord('/'):
            self.command_mode = True
            return True

        return False


    def _apply_cursor_action(self, action_func):
        """Helper to apply an action within the cursor area."""
        half_size = (self.cursor_size - 1) // 2
        start_cx = self.cursor_x - half_size
        start_cy = self.cursor_y - half_size
        end_cx = start_cx + self.cursor_size
        end_cy = start_cy + self.cursor_size

        for cy in range(start_cy, end_cy):
            for cx in range(start_cx, end_cx):
                # Check against grid boundaries, not screen boundaries
                if self.grid.is_valid(cy, cx):
                    element_to_set = action_func(cy, cx)
                    self.grid.set_element(cy, cx, element_to_set)

    def set_target_fps(self, new_fps):
        """Sets the target FPS for the simulation."""
        self.target_fps = max(1.0, new_fps)


    def draw(self, stdscr):
        """Draws the entire game screen (grid, cursor, info panel)."""
        # Check if screen dimensions are valid before drawing anything
        if self.height <= 0 or self.width <= 0:
            return
        screen_h = self.height
        screen_w = self.width
        # Reserve the last line for commands/messages
        drawable_screen_h = screen_h - 1

        try:
            stdscr.erase()
        except curses.error:
             return # Ignore error if terminal too small

        curses.curs_set(0) # Hide physical cursor

        # --- Draw Game Grid ---
        # Draw only within the game grid area, up to drawable_screen_h
        for r in range(min(self.game_height, drawable_screen_h)):
            for c in range(self.game_width):
                # Additional check against overall screen width just in case
                if c >= screen_w: continue
                element = self.grid.get_element(r, c)
                try:
                    if element:
                        char, color_pair_idx = element.get_drawing_info()
                        attr = curses.A_NORMAL
                        if "bold" in element.tags: attr |= curses.A_BOLD
                        if "flash" in element.tags and int(time.time() * 2) % 2 == 0: attr |= curses.A_BLINK
                        color_attr = curses.color_pair(color_pair_idx) | attr
                    else:
                        char = EMPTY_CHAR
                        color_attr = curses.color_pair(DEFAULT_COLOR_PAIR_INDEX)
                    stdscr.addch(r, c, char, color_attr)
                except curses.error:
                    pass # Ignore errors at screen edges

        # --- Draw Game Cursor ---
        if not self.command_mode:
            half_size = (self.cursor_size - 1) // 2
            start_cy = self.cursor_y - half_size
            start_cx = self.cursor_x - half_size
            end_cy = start_cy + self.cursor_size
            end_cx = start_cx + self.cursor_size

            for cy in range(start_cy, end_cy):
                for cx in range(start_cx, end_cx):
                    # Ensure cursor is within grid bounds AND drawable screen height
                    if self.grid.is_valid(cy, cx) and cy < drawable_screen_h and cx < screen_w:
                        try:
                            element = self.grid.get_element(cy, cx)
                            if element:
                                char, color_pair_idx = element.get_drawing_info()
                                color_attr = curses.color_pair(color_pair_idx)
                                # Apply tag attributes if any for cursor preview
                                if "bold" in element.tags: color_attr |= curses.A_BOLD
                                if "flash" in element.tags and int(time.time() * 2) % 2 == 0: color_attr |= curses.A_BLINK
                            else:
                                char = EMPTY_CHAR
                                color_attr = curses.color_pair(DEFAULT_COLOR_PAIR_INDEX)
                            # Apply reverse attribute for cursor highlight
                            stdscr.addch(cy, cx, char, color_attr | curses.A_REVERSE)
                        except curses.error:
                            pass # Ignore edge errors

        # --- Draw Info Panel ---
        if self.info_width <= 0:
             return # No space for info panel

        info_col_start = self.game_width + 1

        # Helper to print lines in the info panel, respecting drawable height
        def print_info(r, text, attr=curses.A_NORMAL):
            if 0 <= r < drawable_screen_h and info_col_start < screen_w:
                max_len = screen_w - info_col_start
                if max_len > 0:
                    padded_text = text[:max_len].ljust(max_len)
                    try:
                        stdscr.addstr(r, info_col_start, padded_text, attr)
                    except curses.error:
                        pass

        # --- Panel Content ---
        row = 0
        # Draw controls, check row against drawable_screen_h
        controls_lines = [
            ("--- 控制 ---", curses.A_BOLD),
            ("方向键: 移动", curses.A_NORMAL),
            ("空格键: 放置", curses.A_NORMAL),
            ("Del/X: 删除", curses.A_NORMAL),
            ("[ / ]: 光标大小", curses.A_NORMAL),
            ("1-9:   快速选择", curses.A_NORMAL),
            ("+ / -: 循环选择", curses.A_NORMAL),
            ("PgUp/Dn: 列表滚动", curses.A_NORMAL),
            ("C:     清空", curses.A_NORMAL),
            ("/:     命令模式", curses.A_NORMAL),
            ("Q:     退出", curses.A_NORMAL),
        ]
        for text, attr in controls_lines:
             if row < drawable_screen_h: print_info(row, text, attr); row += 1
             else: break
        if row >= drawable_screen_h: return # Stop if no more space

        # --- Element List ---
        list_title_row = row
        print_info(list_title_row, "--- 元素列表 ---", curses.A_BOLD); row += 1
        if row >= drawable_screen_h: return # Stop if no more space

        list_start_row = row
        list_max_height = self._get_list_max_height() # Use helper to get calculated height
        total_elements = len(self.placeable_elements_keys) if self.placeable_elements_keys else 0

        # Ensure scroll offset is valid
        max_offset = max(0, total_elements - list_max_height) if total_elements > 0 else 0
        self.element_scroll_offset = max(0, min(self.element_scroll_offset, max_offset))

        visible_start_index = self.element_scroll_offset
        visible_end_index = min(total_elements, self.element_scroll_offset + list_max_height) if total_elements > 0 else 0

        # Up scroll indicator (check bounds)
        if self.element_scroll_offset > 0:
             indicator_row = list_start_row - 1
             if indicator_row >= list_title_row and indicator_row < drawable_screen_h:
                 print_info(indicator_row , "^^^ 更多 ^^^".center(self.info_width))

        # List items (check bounds for each item)
        list_draw_row = list_start_row
        for i in range(visible_start_index, visible_end_index):
            if list_draw_row >= drawable_screen_h: break # Stop drawing if exceeds drawable height

            key = self.placeable_elements_keys[i]
            element_class = element_manager.get_element_class(key)
            if not element_class: continue

            try:
                name = getattr(element_class, 'name', 'N/A')
                char_repr = getattr(element_class, 'char', '?')
                color_idx = getattr(element_class, 'color_pair_index', DEFAULT_COLOR_PAIR_INDEX)
                color_attr = curses.color_pair(color_idx)
            except Exception:
                name = "Error"; char_repr = "?"; color_attr = curses.color_pair(DEFAULT_COLOR_PAIR_INDEX) | curses.A_BOLD

            prefix = ">" if i == self.selected_index else " "
            num_hint = f"({i + 1})" if i < 9 else ""
            line = f"{prefix}{num_hint} {name} ({char_repr})"

            attr_list = color_attr
            if i == self.selected_index:
                attr_list |= curses.A_REVERSE

            print_info(list_draw_row, line, attr_list)
            list_draw_row += 1

        # Down scroll indicator (check bounds)
        list_end_row = list_draw_row
        if visible_end_index < total_elements:
             # Place below list content, but before the very bottom
             scroll_indicator_row = list_end_row
             if scroll_indicator_row < drawable_screen_h:
                 print_info(scroll_indicator_row, "vvv 更多 vvv".center(self.info_width))
                 list_end_row += 1 # Account for indicator height

        # --- Status Info ---
        # Start status below the list section, check against drawable height
        status_start_row = list_end_row + 1 # Add gap
        row = status_start_row
        if row >= drawable_screen_h: return # No space left for status

        print_info(row, "--- 状态 ---", curses.A_BOLD); row += 1
        if row >= drawable_screen_h : return

        # Selected element display
        selected_class = self._get_selected_element_class()
        if selected_class:
             try:
                 selected_name = getattr(selected_class, 'name', 'N/A')
                 selected_char = getattr(selected_class, 'char', '?')
                 selected_color_idx = getattr(selected_class, 'color_pair_index', DEFAULT_COLOR_PAIR_INDEX)
                 selected_color_attr = curses.color_pair(selected_color_idx)
                 print_info(row, f"当前: {selected_name} ({selected_char})", selected_color_attr | curses.A_BOLD)
             except Exception:
                 print_info(row, "当前: Error", curses.color_pair(DEFAULT_COLOR_PAIR_INDEX) | curses.A_BOLD)
        else:
             print_info(row, "当前: 无", curses.color_pair(DEFAULT_COLOR_PAIR_INDEX))
        row += 1
        if row >= drawable_screen_h : return

        # Cursor info
        print_info(row, f"光标:({self.cursor_x},{self.cursor_y}) 大小:{self.cursor_size} FPS:{self.target_fps:.1f}")
        row += 1
        if row >= drawable_screen_h : return

        # Current Tags info
        tags_str = ', '.join(self.current_tags) if self.current_tags else "无"
        # Truncate tags string if too long for panel width
        max_tag_len = self.info_width - len("标签: []") - 1 # Estimate max length
        if len(tags_str) > max_tag_len:
             tags_str = tags_str[:max_tag_len] + "..."
        print_info(row, f"标签: [{tags_str}]")
        # row += 1 # Last line of status

        # --- Refresh Screen --- handled by main loop ---
