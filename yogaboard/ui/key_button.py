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

        # If there's a secondary label, use an overlay layout
        if key.secondary_label:
            # Create an overlay to position labels
            overlay = Gtk.Overlay()

            # Primary label (centered)
            self.label = Gtk.Label(label=key.label)
            self.label.set_hexpand(True)
            self.label.set_vexpand(True)
            self.label.set_halign(Gtk.Align.CENTER)
            self.label.set_valign(Gtk.Align.CENTER)
            overlay.set_child(self.label)

            # Secondary label (top-right, smaller)
            self.secondary_label = Gtk.Label(label=key.secondary_label)
            self.secondary_label.set_halign(Gtk.Align.END)
            self.secondary_label.set_valign(Gtk.Align.START)
            self.secondary_label.add_css_class("secondary-label")
            self.secondary_label.set_margin_top(4)
            self.secondary_label.set_margin_end(6)
            overlay.add_overlay(self.secondary_label)

            self.append(overlay)
        else:
            # Just a single label
            self.label = Gtk.Label(label=key.label)
            self.label.set_hexpand(True)
            self.label.set_vexpand(True)
            self.append(self.label)

        self.add_css_class("keyboard-key")

        if key.is_modifier:
            self.add_css_class("modifier-key")

        # Set minimum height and allow horizontal expansion
        # Height = 50px, width expands based on key.width multiplier
        self.set_size_request(-1, 50)
        self.set_hexpand(True)

        # Use natural width as a weight for expansion
        if key.width != 1.0:
            self.set_size_request(int(60 * key.width), 50)
