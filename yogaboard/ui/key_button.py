"""Individual key button widget."""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk


class KeyButton(Gtk.Button):
    """Button widget representing a single keyboard key."""

    def __init__(self, key):
        """
        Initialize a key button.

        Args:
            key: Key object from layout parser
        """
        super().__init__()
        self.key = key
        self.set_label(key.label)
        self.add_css_class('keyboard-key')

        if key.is_modifier:
            self.add_css_class('modifier-key')

        # Set size based on width multiplier
        # Base key width = 60px, height = 50px
        self.set_size_request(int(60 * key.width), 50)
