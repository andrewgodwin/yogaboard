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

        # Split key: render as two vertically stacked labels
        if key.is_split():
            self._build_split_key(key)
        # If there's a secondary label, use an overlay layout
        elif key.secondary_label:
            self._build_secondary_label_key(key)
        else:
            # Just a single label
            self.label = Gtk.Label(label=key.label)
            self.label.set_hexpand(True)
            self.label.set_vexpand(True)
            self.append(self.label)

        self.add_css_class("keyboard-key")

        for css_class in key.classes:
            self.add_css_class(css_class)

        # Set minimum width based on key.width multiplier and allow horizontal expansion
        self.set_size_request(int(60 * key.width), -1)
        self.set_hexpand(True)

    def _build_split_key(self, key: Key):
        """Build a vertically split key with top and bottom halves."""
        self.add_css_class("split-key")

        # Top half
        self.top_label = Gtk.Label(label=key.top_key.label)
        self.top_label.set_hexpand(True)
        self.top_label.set_vexpand(True)
        self.top_label.add_css_class("split-key-top")
        self.append(self.top_label)

        # Bottom half
        self.bottom_label = Gtk.Label(label=key.bottom_key.label)
        self.bottom_label.set_hexpand(True)
        self.bottom_label.set_vexpand(True)
        self.bottom_label.add_css_class("split-key-bottom")
        self.append(self.bottom_label)

    def _build_secondary_label_key(self, key: Key):
        """Build a key with a secondary label (e.g., shift character)."""
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
