"""Keyboard grid widget that renders the layout."""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .key_button import KeyButton


class KeyboardWidget(Gtk.Box):
    """Widget that renders a complete keyboard layout."""

    def __init__(self, layout):
        """
        Initialize the keyboard widget.

        Args:
            layout: Layout object from layout parser
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.layout = layout
        self.key_buttons = []

        # Add horizontal padding
        self.set_margin_start(20)
        self.set_margin_end(20)

        # Build keyboard grid row by row
        for row in layout.rows:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            row_box.set_hexpand(True)

            for key in row.keys:
                btn = KeyButton(key)
                self.key_buttons.append(btn)
                row_box.append(btn)

            self.append(row_box)

        self.add_css_class("keyboard-widget")

    def get_key_at_position(self, x, y):
        """
        Find which key is at the given coordinates.

        Args:
            x: X coordinate relative to widget
            y: Y coordinate relative to widget

        Returns:
            Key object if found, None otherwise
        """
        for btn in self.key_buttons:
            # Get button position relative to widget
            coords = btn.translate_coordinates(self, 0, 0)
            if coords is None:
                continue

            btn_x, btn_y = coords
            width = btn.get_width()
            height = btn.get_height()

            if btn_x <= x < btn_x + width and btn_y <= y < btn_y + height:
                return btn.key

        return None
