# -*- coding: utf-8 -*-
import curses
import shlex # For parsing command arguments safely
import json # For saving/loading game state
import os # For path manipulation
from collections import deque # For fill command BFS
from .element_manager import element_manager
from .config import TARGET_FPS as DEFAULT_TARGET_FPS, MAX_CURSOR_SIZE

class CommandError(Exception):
    """Custom exception for command processing errors."""
    pass

class CommandProcessor:
    """Handles parsing and execution of user commands."""

    # In-memory quick save slots
    quick_saves = {} # {number: grid_state_dict}

    def __init__(self, game_instance, screen_interface):
        self.game = game_instance
        self.screen = screen_interface # To interact with curses (e.g., show messages)
        self.commands = {
            "fill": self._cmd_fill,
            "clear": self._cmd_clear,
            "select": self._cmd_select,
            "size": self._cmd_size,
            "fps": self._cmd_fps,
            "speed": self._cmd_speed,
            "tag": self._cmd_tag,
            "help": self._cmd_help,
            "save": self._cmd_save,       # Added save command
            "load": self._cmd_load,       # Added load command
            "quick_save": self._cmd_quick_save, # Added quick_save command
            "quick_load": self._cmd_quick_load, # Added quick_load command
            "info": self._cmd_info,       # Added info command
        }

    def show_message(self, message, duration=1.5):
        """Displays a message at the bottom of the screen."""
        if not self.screen: return
        h, w = self.screen.getmaxyx()
        prompt_line = h - 1
        try:
            # Clear the line first
            self.screen.move(prompt_line, 0)
            self.screen.clrtoeol()
            # Add the message
            # Ensure message doesn't exceed screen width
            message_to_display = message[:w-1]
            self.screen.addstr(prompt_line, 0, message_to_display)
            self.screen.refresh()
            curses.napms(int(duration * 1000)) # Wait
            # Clear the message line again
            self.screen.move(prompt_line, 0)
            self.screen.addstr(prompt_line, 0, " " * w)
            self.screen.clrtoeol()
            self.screen.refresh()
        except curses.error:
            pass # Ignore errors if screen size is weird

    def process_command(self, command_string):
        """Parses and executes a command string."""
        if not command_string.strip():
            return # Ignore empty commands

        try:
            # Safely split the command string into parts
            parts = shlex.split(command_string)
            if not parts: return # Should not happen with strip(), but safety first

            command_name = parts[0].lower()
            args = parts[1:]

            if command_name in self.commands:
                # Call the corresponding command handler
                result = self.commands[command_name](args)
                if result is not None: # Show success message if command returns one
                    self.show_message(f"OK: {result}")
            else:
                # If command name is not found, check if it's an element key for 'select'
                element_key = command_name # Treat command name as a potential element key
                element_class = element_manager.get_element_class(element_key)
                if element_class:
                    # If it's a valid element key, treat it as a 'select' command
                    result = self._cmd_select([element_key])
                    if result is not None:
                         self.show_message(f"OK: {result}")
                else:
                    # Check if it's an element name for 'select' (requires iterating)
                    found_key_by_name = None
                    for key, element_cls in element_manager.get_registry().items():
                        if getattr(element_cls, 'name', '').lower() == command_name:
                            found_key_by_name = key
                            break

                    if found_key_by_name:
                         result = self._cmd_select([found_key_by_name])
                         if result is not None:
                              self.show_message(f"OK: {result}")
                    else:
                         # Still not found, it's an unknown command
                         raise CommandError(f"Unknown command or element: '{command_name}'. Type 'help' for list.")

        except CommandError as e:
            self.show_message(f"错误: {e}")
        except ValueError as e:
            self.show_message(f"无效参数: {e}")
        except Exception as e:
            # Catch unexpected errors during command execution
            self.show_message(f"意外错误: {e}")
            # Optionally log traceback here
            # import traceback
            # traceback.print_exc() # To console

    def _cmd_help(self, args):
        """Lists available commands."""
        # Also mention that element keys/names can be used directly to select
        available_cmds = ", ".join(sorted(self.commands.keys()))
        self.show_message(f"命令: {available_cmds}. 可直接输入元素Key/名称选择.", duration=3)
        return None # No specific success message needed

    def _cmd_fill(self, args):
        """
        Fills the grid with a specified element using a 'paint bucket' method
        from the current cursor position.
        """
        if len(args) != 1:
            raise CommandError("用法: fill <element_key_or_name>")

        element_identifier = args[0]
        element_key = element_identifier # Assume key first
        element_class = element_manager.get_element_class(element_key)

        if not element_class:
            # Try searching by name if key not found
            for key, element_cls in element_manager.get_registry().items():
                if getattr(element_cls, 'name', '').lower() == element_identifier.lower():
                    element_key = key
                    element_class = element_cls
                    break

        if not element_class:
            raise CommandError(f"未找到元素: '{element_identifier}'.")

        start_y, start_x = self.game.cursor_y, self.game.cursor_x

        # Check if the starting point is within bounds
        if not self.game.grid.is_valid(start_y, start_x):
             raise CommandError(f"光标位置 ({start_x},{start_y}) 超出网格范围.")

        target_element = self.game.grid.get_element(start_y, start_x)
        target_key = target_element.key if target_element else None # Key of the element to replace

        # If the target element is the same as the fill element, do nothing
        if target_key == element_key:
             return f"目标元素已经是 '{element_class.name}' ({element_key}), 无需填充."

        # Use BFS/DFS to find connected components
        queue = deque([(start_y, start_x)])
        visited = set([(start_y, start_x)])
        filled_count = 0

        # Use grid factory method, passing current tags
        def create_fill_element(y, x):
            # Important: Create *new* element instance for each cell
            element = self.game.grid.create_element(element_key, y, x)
            if element:
                element.tags = list(self.game.current_tags) # Apply current tags
            return element

        # Directions for adjacent check (orthogonal)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        while queue:
            cy, cx = queue.popleft()

            # Place the new element at the current cell
            element_to_set = create_fill_element(cy, cx)
            self.game.grid.set_element(cy, cx, element_to_set)
            filled_count += 1

            # Check neighbors
            for dy, dx in directions:
                ny, nx = cy + dy, cx + dx

                # Check bounds and if not visited
                if self.game.grid.is_valid(ny, nx) and (ny, nx) not in visited:
                    neighbor_element = self.game.grid.get_element(ny, nx)
                    neighbor_key = neighbor_element.key if neighbor_element else None

                    # If the neighbor is the same type as the *original* target element, add to queue
                    if neighbor_key == target_key:
                        visited.add((ny, nx))
                        queue.append((ny, nx))

        return f"从 ({start_x},{start_y}) 填充 {filled_count} 个单元格为 '{element_class.name}' ({element_key})."


    def _cmd_clear(self, args):
        """Clears the grid."""
        if args:
            raise CommandError("用法: clear (无参数)")
        self.game.grid.clear()
        return "网格已清空."

    def _cmd_select(self, args):
        """Selects an element by its key or Chinese name."""
        if len(args) != 1:
            # Show list of available elements if no argument provided
            element_list = [f"'{k}' ({getattr(v, 'name', 'N/A')})" for k, v in element_manager.get_registry().items()]
            self.show_message(f"可用元素: {', '.join(element_list)}", duration=5)
            raise CommandError("用法: select <element_key_or_name>")

        element_identifier = args[0] # Can be key or name

        # 1. Try searching by key first (case-sensitive keys)
        element_class = element_manager.get_element_class(element_identifier)
        selected_key = element_identifier

        if not element_class:
            # 2. Try searching by Chinese name (case-insensitive name match)
            found_key = None
            for key, element_cls in element_manager.get_registry().items():
                # Check if the element name matches the identifier (case-insensitive)
                element_name = getattr(element_cls, 'name', '')
                if element_name and element_name.lower() == element_identifier.lower():
                    found_key = key
                    element_class = element_cls
                    selected_key = key # Store the actual key
                    break

        if not element_class:
            raise CommandError(f"未找到元素Key或名称: '{element_identifier}'.")

        # Ensure the found element is actually placeable
        if selected_key not in self.game.placeable_elements_keys:
             # Add it to placeable_elements_keys if not already there?
             # Or only allow selecting from the existing placeable list?
             # Let's stick to the placeable list for consistency with UI.
             raise CommandError(f"元素 '{getattr(element_class, 'name', selected_key)}' ({selected_key}) 不在可放置列表中.")

        try:
            index = self.game.placeable_elements_keys.index(selected_key)
            self.game.selected_index = index
            # Adjust scroll automatically
            self.game._adjust_scroll_for_selection()
            return f"已选择 '{getattr(element_class, 'name', selected_key)}' ({selected_key})."
        except ValueError:
             # This case should ideally not be reached if selected_key is checked against placeable_elements_keys
             # But keep it as a fallback error message.
             raise CommandError(f"元素 '{getattr(element_class, 'name', selected_key)}' ({selected_key}) 不在可放置列表中.")


    def _cmd_size(self, args):
        """Sets the cursor size."""
        if len(args) != 1:
            raise CommandError("用法: size <number>")
        try:
            new_size = int(args[0])
            if 1 <= new_size <= MAX_CURSOR_SIZE:
                self.game.cursor_size = new_size
                return f"光标大小设置为 {new_size}."
            else:
                raise CommandError(f"大小必须在 1 到 {MAX_CURSOR_SIZE} 之间.")
        except ValueError:
            raise CommandError("大小必须是数字.")

    def _cmd_fps(self, args):
        """Sets the target frames per second."""
        if len(args) != 1:
            raise CommandError("用法: fps <number>")
        try:
            new_fps = float(args[0])
            if new_fps > 0:
                self.game.set_target_fps(new_fps)
                return f"目标帧率设置为 {new_fps:.1f}."
            else:
                raise CommandError("帧率必须为正数.")
        except ValueError:
            raise CommandError("帧率必须是数字.")

    def _cmd_speed(self, args):
        """Sets the target FPS based on a multiplier of the default."""
        if len(args) != 1:
            raise CommandError("用法: speed <multiplier>")
        try:
            multiplier = float(args[0])
            if multiplier > 0:
                new_fps = DEFAULT_TARGET_FPS * multiplier
                self.game.set_target_fps(new_fps)
                return f"速度倍率设置为 {multiplier}x (目标帧率: {new_fps:.1f})."
            else:
                raise CommandError("倍率必须为正数.")
        except ValueError:
            raise CommandError("倍率必须是数字.")

    def _cmd_tag(self, args):
        """Manages the tags applied by the cursor."""
        if not args:
            current_tags_str = ', '.join(self.game.current_tags) if self.game.current_tags else "无"
            self.show_message(f"当前标签: [{current_tags_str}]. 用法: 'tag add|remove|set|clear <tag_name>'", duration=3)
            return None

        sub_command = args[0].lower()
        tag_args = args[1:]

        if sub_command == "add":
            if not tag_args: raise CommandError("用法: tag add <tag_name>")
            tag_to_add = tag_args[0]
            if tag_to_add not in self.game.current_tags:
                self.game.current_tags.append(tag_to_add)
                return f"添加标签: '{tag_to_add}'"
            else:
                return f"标签 '{tag_to_add}' 已存在."
        elif sub_command == "remove":
            if not tag_args: raise CommandError("用法: tag remove <tag_name>")
            tag_to_remove = tag_args[0]
            if tag_to_remove in self.game.current_tags:
                self.game.current_tags.remove(tag_to_remove)
                return f"移除标签: '{tag_to_remove}'"
            else:
                raise CommandError(f"标签 '{tag_to_remove}' 未找到.")
        elif sub_command == "set":
            # 'set' replaces all current tags
            self.game.current_tags = list(tag_args) # Use all remaining arguments as tags
            tags_str = ', '.join(self.game.current_tags) if self.game.current_tags else "无"
            return f"当前标签设置为: [{tags_str}]"
        elif sub_command == "clear":
             if tag_args: raise CommandError("用法: tag clear (无参数)")
             self.game.current_tags = []
             return "已清空所有当前标签."
        else:
            raise CommandError("无效的 tag 命令. 用法: add, remove, set, 或 clear.")

    # --- New Commands ---

    def _grid_to_dict(self, grid):
        """Serializes the grid state to a dictionary."""
        # This is a basic implementation. More complex elements might need custom serialization.
        grid_data = {
            "height": grid.height,
            "width": grid.width,
            "elements": [] # List of element dictionaries
        }
        for r in range(grid.height):
            for c in range(grid.width):
                element = grid.get_element(r, c)
                if element:
                    element_data = {
                        "key": element.key,
                        "y": element.y,
                        "x": element.x,
                        "tags": list(element.tags) # Save tags
                        # Add any other essential element state here if needed
                        # For example, Thermite's burn_timer, Photosensitive's is_solidified etc.
                        # This requires adding serialization logic to Element base or subclasses.
                        # Simple approach: check for known state attributes
                    }
                    # Add specific state for elements that need it
                    if hasattr(element, 'is_burning'): # Thermite
                        element_data['is_burning'] = element.is_burning
                        element_data['burn_timer'] = getattr(element, 'burn_timer', 0)
                    if hasattr(element, 'is_solidified'): # PhotosensitivePowder
                         element_data['is_solidified'] = element.is_solidified
                    # Add more element-specific states as needed
                    grid_data["elements"].append(element_data)
        return grid_data

    def _dict_to_grid(self, grid_data):
        """Deserializes grid state from a dictionary."""
        if not grid_data or "height" not in grid_data or "width" not in grid_data or "elements" not in grid_data:
            raise ValueError("Invalid grid data format.")

        height = grid_data["height"]
        width = grid_data["width"]
        elements_data = grid_data["elements"]

        # Create a new grid with specified dimensions
        new_grid = self.game.grid.__class__(height, width, element_manager) # Use same Grid class

        # Place elements from data
        for element_data in elements_data:
            key = element_data.get("key")
            y = element_data.get("y")
            x = element_data.get("x")
            tags = element_data.get("tags", []) # Load tags

            if key is None or y is None or x is None:
                print(f"Warning: Skipping malformed element data: {element_data}")
                continue

            # Create element instance using the new grid's factory method
            element = new_grid.create_element(key, y, x)

            if element:
                # Apply tags
                if tags:
                    element.tags = list(tags)

                # Load specific state for elements
                if 'is_burning' in element_data and hasattr(element, 'is_burning'):
                    element.is_burning = element_data['is_burning']
                    element.burn_timer = element_data.get('burn_timer', 0)
                    element.is_heat_source = element.is_burning # Ensure heat source state is correct
                if 'is_solidified' in element_data and hasattr(element, 'is_solidified'):
                    element.is_solidified = element_data['is_solidified']
                    # Update characteristics based on solidification state
                    if element.is_solidified:
                         element.is_powder = False
                         element.is_static = True
                         element.char = getattr(element, 'solidified_char', element.char)
                         element.density = getattr(element, 'solidified_density', element.density)
                    else:
                         element.is_powder = True
                         element.is_static = False
                         element.char = getattr(element, 'char', element.char) # Revert to powder char
                         element.density = 4.5 # Revert to powder density (hardcoded or use class attr?)
                         # Assuming powder density is 4.5 based on PhotosensitivePowder definition

                # Add more element-specific state loading as needed

                # Place the element on the new grid
                new_grid.set_element(y, x, element)
            else:
                 print(f"Warning: Element class for key '{key}' not found during loading.")

        return new_grid


    def _cmd_save(self, args):
        """Saves the current game state to a file."""
        if len(args) != 1:
            raise CommandError("用法: save <file_name>")
        file_name = args[0]
        # Add .json extension if not present
        if not file_name.lower().endswith(".json"):
             file_name += ".json"

        save_path = os.path.join(".", file_name) # Save in current directory

        try:
            grid_data = self._grid_to_dict(self.game.grid)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(grid_data, f, ensure_ascii=False, indent=4)
            return f"游戏状态已保存到 '{save_path}'."
        except Exception as e:
            raise CommandError(f"保存游戏状态失败: {e}")

    def _cmd_load(self, args):
        """Loads game state from a file."""
        if len(args) != 1:
            raise CommandError("用法: load <file_name>")
        file_name = args[0]
        if not file_name.lower().endswith(".json"):
             file_name += ".json"

        load_path = os.path.join(".", file_name)

        if not os.path.exists(load_path):
            raise CommandError(f"文件 '{load_path}' 未找到.")

        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                grid_data = json.load(f)

            # Create and set the new grid
            new_grid = self._dict_to_grid(grid_data)
            self.game.grid = new_grid
            # Adjust game dimensions if necessary based on loaded grid size
            # This might be tricky with fixed curses window.
            # For simplicity, let's assume loaded grid fits current window or handle resize later.
            # If loaded grid is smaller, fine. If larger, drawing might be clipped.
            # A more robust solution would involve resizing the curses window or game area.
            # For now, just update the game instance's grid reference.
            self.game.game_height = new_grid.height # Update game dimensions based on loaded grid
            self.game.game_width = new_grid.width
            # Recalculate info panel position might be needed if game area size changed significantly
            self.game._recalculate_layout() # This recalculates info_width etc.

            # Adjust cursor position to be within new bounds
            self.game.cursor_x = min(max(0, self.game.cursor_x), self.game.game_width - 1)
            self.game.cursor_y = min(max(0, self.game.cursor_y), self.game.game_height - 1)

            return f"游戏状态已从 '{load_path}' 加载."
        except FileNotFoundError:
            raise CommandError(f"文件 '{load_path}' 未找到.")
        except json.JSONDecodeError:
            raise CommandError(f"无法解析文件 '{load_path}' 为有效的JSON.")
        except ValueError as ve:
             raise CommandError(f"加载数据格式错误: {ve}")
        except Exception as e:
            raise CommandError(f"加载游戏状态失败: {e}")


    def _cmd_quick_save(self, args):
        """Saves the current game state to an in-memory slot."""
        if len(args) != 1:
            raise CommandError("用法: quick_save <number>")
        try:
            slot_number = int(args[0])
            if slot_number < 0 or slot_number > 9: # Example limit for quick save slots
                 raise CommandError("快速保存槽位数字必须在 0 到 9 之间.")

            # Serialize the current grid state to a dictionary
            grid_data = self._grid_to_dict(self.game.grid)
            # Store the dictionary in the quick_saves dictionary
            CommandProcessor.quick_saves[slot_number] = grid_data

            return f"快速保存状态到槽位 {slot_number}."
        except ValueError:
            raise CommandError("槽位号必须是数字.")
        except Exception as e:
            raise CommandError(f"快速保存失败: {e}")


    def _cmd_quick_load(self, args):
        """Loads game state from an in-memory slot."""
        if len(args) != 1:
            raise CommandError("用法: quick_load <number>")
        try:
            slot_number = int(args[0])
            if slot_number < 0 or slot_number > 9:
                 raise CommandError("快速加载槽位数字必须在 0 到 9 之间.")

            if slot_number not in CommandProcessor.quick_saves:
                 raise CommandError(f"快速保存槽位 {slot_number} 为空.")

            # Retrieve the grid state dictionary from the quick save slot
            grid_data = CommandProcessor.quick_saves[slot_number]

            # Create and set the new grid from the dictionary
            new_grid = self._dict_to_grid(grid_data)
            self.game.grid = new_grid
            # Adjust game dimensions if necessary
            self.game.game_height = new_grid.height
            self.game.game_width = new_grid.width
            self.game._recalculate_layout()

            # Adjust cursor position
            self.game.cursor_x = min(max(0, self.game.cursor_x), self.game.game_width - 1)
            self.game.cursor_y = min(max(0, self.game.cursor_y), self.game.game_height - 1)


            return f"从快速保存槽位 {slot_number} 加载状态."
        except ValueError:
            raise CommandError("槽位号必须是数字.")
        except ValueError as ve:
             raise CommandError(f"快速加载数据格式错误: {ve}")
        except Exception as e:
            raise CommandError(f"快速加载失败: {e}")

    def _cmd_info(self, args):
         """Displays information about the element under the cursor."""
         if args:
              raise CommandError("用法: info (无参数)")

         cursor_y, cursor_x = self.game.cursor_y, self.game.cursor_x

         if not self.game.grid.is_valid(cursor_y, cursor_x):
              self.show_message(f"光标位置 ({cursor_x},{cursor_y}) 超出网格范围.", duration=2)
              return None

         element = self.game.grid.get_element(cursor_y, cursor_x)

         if element:
              info_msg = f"元素: '{getattr(element, 'name', '未知')}' ({element.key}). 位置: ({element.x},{element.y}). 密度: {getattr(element, 'density', 'N/A'):.1f}. 标签: [{', '.join(element.tags) if element.tags else '无'}]."
              # Add element-specific state info if available
              if hasattr(element, 'is_burning'):
                  info_msg += f" 燃烧: {element.is_burning} (剩余: {getattr(element, 'burn_timer', 0)})."
              if hasattr(element, 'is_solidified'):
                  info_msg += f" 固化: {element.is_solidified}."
              # Add more checks for other complex states

         else:
              info_msg = f"位置 ({cursor_x},{cursor_y}) 为空."

         self.show_message(info_msg, duration=4) # Show message for a bit longer
         return None # No success message returned


