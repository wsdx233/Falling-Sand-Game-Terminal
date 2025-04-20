# -*- coding: utf-8 -*-
import os
import importlib
import inspect
import threading

# Import Base Element for type checking during loading
# Avoid importing specific elements here
from .elements.base import Element
from .config import ELEMENT_DIR # Get element directory from config

class ElementManager:
    """
    Singleton class to manage the element registry and loading process.
    """
    _instance = None
    _lock = threading.Lock() # For thread safety during first instantiation

    # Original order reference moved here
    _ORIGINAL_ORDER = [
        'S', '#', 'W', 'L', 'I', 'A', 'J', 'Z', 'O', 'D', 'C', 'P', 'E', 'M',
        'X', 'U', 'T', 'N', 'Y', 'H', 'B', 'R', 'G', 'K', 'F', 'V', '?',
    ]

    def __new__(cls, *args, **kwargs):
        # Double-checked locking for thread-safe singleton initialization
        if cls._instance is None:
            with cls._lock:
                # Check again inside the lock
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    # Initialize attributes only once
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Prevent re-initialization
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            self.registry = {}
            self.placeable_order = []
            self._loaded = False
            self._initialized = True
            print("ElementManager initialized.") # Debug print

    @property
    def is_loaded(self):
        return self._loaded

    def load_elements(self, element_dir=ELEMENT_DIR):
        """
        Dynamically loads element classes from .py files in the specified directory
        and its subdirectories. Populates the manager's registry and placeable_order.
        """
        # Prevent reloading if already loaded, unless forced? For now, load once.
        if self._loaded:
            print("Elements already loaded.")
            return

        print(f"Loading elements from: {element_dir} and its subdirectories.")
        self.registry = {} # Reset registry before loading
        loaded_keys = set()

        # Ensure the base directory exists
        if not os.path.isdir(element_dir):
            print(f"Warning: Element directory '{element_dir}' not found.")
            self._loaded = True # Mark as loaded (even if empty) to prevent retries
            return

        # Use os.walk to traverse directories
        for root, _, files in os.walk(element_dir):
            # Calculate the package path relative to the base element_dir
            # Replace os.sep with '.' for module path
            relative_path = os.path.relpath(root, element_dir).replace(os.sep, '.')
            # Handle the case where root is element_dir itself
            package_prefix = f"falling_sand_game.elements.{relative_path}" if relative_path != '.' else "falling_sand_game.elements"

            for filename in files:
                if filename.endswith(".py") and filename != "__init__.py" and filename != "base.py":
                    module_name = filename[:-3]  # Remove '.py'
                    # Construct the full module path
                    module_path = f"{package_prefix}.{module_name}"

                    try:
                        module = importlib.import_module(module_path)
                        for name, obj in inspect.getmembers(module):
                            # Check if it's a class, is a subclass of Element, is not Element itself,
                            # and is defined in the loaded module (not imported)
                            if inspect.isclass(obj) and \
                               issubclass(obj, Element) and \
                               obj is not Element and \
                               obj.__module__ == module_path: # Ensure it's defined in this specific module
                                # Instantiate once to get class properties like 'key'
                                try:
                                    # Need a way to get key without full init if possible,
                                    # but fallback to temp instance. Use getattr on class.
                                    key = getattr(obj, 'key', None)
                                    if key is None:
                                        # Fallback: create temp instance (requires elements not needing args)
                                        # Be cautious here if element constructors require specific args
                                        # A more robust way is to enforce 'key' as a class attribute.
                                        try:
                                            temp_instance = obj(0, 0) # Assuming base init needs y,x
                                            key = temp_instance.key
                                        except TypeError:
                                            print(f"Warning: Could not instantiate element {name} from {module_path} to get key. Ensure 'key' is a class attribute or constructor takes y,x.")
                                            continue # Skip this element if key cannot be determined


                                    if key in self.registry:
                                         print(f"Warning: Duplicate element key '{key}' found in {module_path}. Overwriting.")
                                    if key and key != ' ': # Don't register the empty space element if defined
                                        self.registry[key] = obj # Store the class itself
                                        loaded_keys.add(key)
                                except Exception as e:
                                    print(f"Error processing element class {name} from {module_path}: {e}")

                    except ImportError as e:
                        print(f"Error importing element module {module_path}: {e}")
                        # Potentially log traceback here for more detail
                        # import traceback; traceback.print_exc()
                    except Exception as e:
                        print(f"An unexpected error occurred loading {module_path}: {e}")
                        # import traceback; traceback.print_exc()


        # Build the placeable elements list based on the original order
        self.placeable_order = [key for key in self._ORIGINAL_ORDER if key in loaded_keys]
        # self.placeable_order = [key for key in selfin loaded_keys]
        # Add any newly found elements that weren't in the original order (optional)
        # This adds them at the end of the placeable list
        for key in loaded_keys:
            if key not in self.placeable_order:
                print("NEW KEY",key)
                self.placeable_order.append(key)

        self._loaded = True
        print(f"Loaded {len(self.registry)} elements: {list(self.registry.keys())}")
        print(f"Placeable elements order: {self.placeable_order}")


    def get_element_class(self, key):
        """Gets the element class from the registry."""
        return self.registry.get(key)

    def get_registry(self):
        """Returns the element registry dictionary."""
        return self.registry

    def get_placeable_order(self):
        """Returns the list of placeable element keys in order."""
        return self.placeable_order


# Instantiate the singleton when the module is imported
element_manager = ElementManager()
