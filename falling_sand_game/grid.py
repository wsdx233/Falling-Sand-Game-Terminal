# -*- coding: utf-8 -*-

class Grid:
    """Encapsulates the simulation grid and provides safe access methods."""

    def __init__(self, height, width, element_manager_instance):
        if height <= 0 or width <= 0:
            raise ValueError("Grid dimensions must be positive")
        self._height = height
        self._width = width
        # Initialize grid with None (representing empty cells)
        self._grid = [[None for _ in range(width)] for _ in range(height)]
        self._element_manager = element_manager_instance # Store the manager instance

    # Remove set_registry, pass manager in constructor

    def create_element(self, key, y, x, tags=None):
        """
        Creates a new element instance using the element manager.
        Optionally applies tags during creation.
        """
        if self._element_manager is None:
            print("Error: Element manager not set in Grid.")
            return None

        element_class = self._element_manager.get_element_class(key)
        if element_class:
            try:
                # Create the new element instance, passing coordinates
                new_element = element_class(y, x)
                # Apply tags if provided
                if tags is not None:
                    # Ensure tags is a list copy, not a reference
                    new_element.tags = list(tags)
                return new_element
            except Exception as e:
                print(f"Error instantiating element '{key}' at ({y},{x}): {e}")
                return None
        else:
            # Warning already printed by manager usually, but can add one here too
            # print(f"Warning: Element key '{key}' not found during creation.")
            return None

    @property
    def height(self):
        return self._height

    @property
    def width(self):
        return self._width

    def is_valid(self, y, x):
        """Checks if the coordinates (y, x) are within the grid boundaries."""
        return 0 <= y < self._height and 0 <= x < self._width

    def get_element(self, y, x):
        """Gets the element object at (y, x). Returns None if empty or out of bounds."""
        if self.is_valid(y, x):
            return self._grid[y][x]
        return None

    def set_element(self, y, x, element):
        """
        Sets the element object at (y, x).
        If element is None, clears the cell.
        Handles boundary checks.
        Updates the element's internal coordinates if it's not None.
        Returns True if successful, False otherwise (e.g., out of bounds).
        """
        if self.is_valid(y, x):
            # Get current element before overwriting
            # old_element = self._grid[y][x]
            # Optional: Cleanup logic if needed when an element is overwritten
            # if old_element and old_element != element:
            #     pass # e.g., old_element.cleanup()

            # If placing an element (not None), update its coordinates
            if element:
                element.y = y
                element.x = x
            self._grid[y][x] = element
            return True
        return False

    def clear(self):
        """Clears the entire grid, setting all cells to None."""
        # Optional: Add cleanup logic for removed elements if necessary
        # for element in self.get_all_elements():
        #     element.cleanup() # If elements need explicit cleanup
        self._grid = [[None for _ in range(self.width)] for _ in range(self.height)]

    def reset_processed_flags(self):
        """Resets the 'processed' flag for all elements on the grid."""
        for r in range(self._height):
            for c in range(self._width):
                element = self._grid[r][c]
                if element:
                    element.processed = False

    def get_all_elements(self):
        """Generator yielding all non-None elements in the grid."""
        for r in range(self._height):
            for c in range(self._width):
                element = self._grid[r][c]
                if element:
                    yield element

    def __iter__(self):
        """Allows iterating through rows of the grid."""
        return iter(self._grid)

    def __len__(self):
        """Returns the height of the grid."""
        return self._height

