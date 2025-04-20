# -*- coding: utf-8 -*-

# --- 可配置项 (Configuration Options) ---
# TARGET_FPS is now the DEFAULT, actual FPS is managed in Game/Main
DEFAULT_TARGET_FPS = 25   # 默认目标游戏帧率
TARGET_FPS = 25
GAME_AREA_RATIO = 0.7   # 游戏区域占屏幕宽度的比例
EMPTY_CHAR = ' '          # 代表空格子的字符 (Now less critical, use grid.get_element is None)
MAX_CURSOR_SIZE = 10      # 光标的最大尺寸 (Increased limit)
DEFAULT_CURSOR_SIZE = 1   # 默认光标尺寸
ELEMENT_DIR = "falling_sand_game/elements" # Path to elements directory

# --- Colors ---
# Define a default color pair ID, maybe for errors or unloaded elements
DEFAULT_COLOR_PAIR_INDEX = 0

# It's generally better to let curses assign pairs dynamically,
# but we might define a fallback pair if needed.
# For now, rely on dynamic assignment in main.py

# You could add more configuration here, e.g., default background color if needed
# DEFAULT_BACKGROUND = curses.COLOR_BLACK or -1 for terminal default
