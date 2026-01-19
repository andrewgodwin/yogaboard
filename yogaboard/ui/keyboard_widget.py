"""Keyboard grid widget that renders the layout."""

import gi

from yogaboard.layout.parser import Layout

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .key_button import KeyButton


class KeyboardWidget(Gtk.Box):
    """Widget that renders a complete keyboard layout."""

    horizontal_spacing: int = 8
    vertical_spacing: int = 8

    def __init__(self, layout: Layout):
        """
        Initialize the keyboard widget.

        Args:
            layout: Layout object from layout parser
        """
        super().__init__(
            orientation=Gtk.Orientation.VERTICAL, spacing=self.vertical_spacing
        )
        self.layout = layout
        self.key_buttons = []

        # Add horizontal padding
        self.set_margin_start(10)
        self.set_margin_end(10)

        # Build keyboard grid row by row
        for row in layout.rows:
            row_box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, spacing=self.horizontal_spacing
            )
            row_box.set_hexpand(True)
            row_box.set_vexpand(True)
            row_box.set_size_request(-1, row.height)

            for key in row.keys:
                btn = KeyButton(key)
                self.key_buttons.append(btn)
                row_box.append(btn)

            self.append(row_box)

        self.add_css_class("keyboard-widget")
