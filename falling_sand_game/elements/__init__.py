# -*- coding: utf-8 -*-

# Import the singleton instance from the manager module
# from ..element_manager import element_manager

# Optionally, you could expose parts of the manager directly here if desired,
# but it's generally cleaner to import the manager instance itself.
# Example (less recommended):
# ELEMENT_REGISTRY = element_manager.get_registry()
# PLACEABLE_ELEMENTS_ORDER = element_manager.get_placeable_order()

# The primary purpose of this __init__.py now is to make 'elements' a package
# and potentially expose the manager instance. Loading happens via the manager method.
