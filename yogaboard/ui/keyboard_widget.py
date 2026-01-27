"""Keyboard grid widget that renders the layout."""

import gi

from yogaboard.layout.parser import Layout, Key

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
                if key.is_split():
                    # Create a vertical container for two stacked buttons
                    split_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                    split_box.set_hexpand(True)
                    split_box.set_size_request(int(60 * key.width), -1)

                    # Create Key objects from split keys
                    top_key_obj = Key(
                        label=key.top_key.label,
                        key=key.top_key.key,
                        width=key.width,
                        classes=key.classes,
                    )
                    bottom_key_obj = Key(
                        label=key.bottom_key.label,
                        key=key.bottom_key.key,
                        width=key.width,
                        classes=key.classes,
                    )

                    top_btn = KeyButton(top_key_obj)
                    bottom_btn = KeyButton(bottom_key_obj)

                    self.key_buttons.append(top_btn)
                    self.key_buttons.append(bottom_btn)

                    split_box.append(top_btn)
                    split_box.append(bottom_btn)
                    row_box.append(split_box)
                else:
                    btn = KeyButton(key)
                    self.key_buttons.append(btn)
                    row_box.append(btn)

            self.append(row_box)

        self.add_css_class("keyboard-widget")
