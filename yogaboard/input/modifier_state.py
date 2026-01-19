"""Modifier key state tracking for multitouch support."""

from typing import Dict


class ModifierState:
    """Track which modifiers are currently pressed and by which touch."""

    def __init__(self):
        """Initialize modifier state tracker."""
        self._active_modifiers: Dict[str, int] = {}  # {modifier_name: touch_id}

    def press(self, modifier: str, touch_id: int):
        """
        Mark a modifier as pressed by a specific touch.

        Args:
            modifier: Name of modifier (e.g., 'shift', 'ctrl', 'alt')
            touch_id: ID of the touch that pressed this modifier
        """
        self._active_modifiers[modifier] = touch_id

    def release(self, modifier: str, touch_id: int):
        """
        Release a modifier only if it's owned by this touch.

        This ensures that if you press Shift with finger 1,
        releasing finger 2 won't release Shift.

        Args:
            modifier: Name of modifier to release
            touch_id: ID of the touch attempting to release
        """
        if self._active_modifiers.get(modifier) == touch_id:
            del self._active_modifiers[modifier]

    def is_active(self, modifier: str) -> bool:
        """
        Check if a modifier is currently pressed.

        Args:
            modifier: Name of modifier to check

        Returns:
            True if modifier is currently pressed
        """
        return modifier in self._active_modifiers

    def get_all_active(self) -> set:
        """
        Get set of all currently active modifiers.

        Returns:
            Set of modifier names currently pressed
        """
        return set(self._active_modifiers.keys())
