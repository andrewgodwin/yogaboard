"""Individual key button widget."""

import gi

from yogaboard.layout.parser import Key

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class KeyButton(Gtk.Box):
    """Box widget representing a single keyboard key."""

    def __init__(self, key: Key):
        """
        Initialize a key button.

        Args:
            key: Key object from layout parser
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.key = key

        # Create a label to display the key text
        self.label = Gtk.Label(label=key.label)
        self.label.set_hexpand(True)
        self.label.set_vexpand(True)
        self.append(self.label)

        self.add_css_class("keyboard-key")

        if key.is_modifier:
            self.add_css_class("modifier-key")

        # Set size based on width multiplier
        # Base key width = 60px, height = 50px
        self.set_size_request(int(60 * key.width), 50)
