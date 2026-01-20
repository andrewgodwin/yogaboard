"""Touchpad widget with touch surface and control buttons."""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class TouchpadWidget(Gtk.Box):
    """Widget that provides a virtual touchpad surface with controls."""

    def __init__(self, show_controls=True):
        """
        Initialize the touchpad widget.

        Args:
            show_controls: Whether to show mode/close buttons (False when embedded)
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.show_controls = show_controls

        # Add padding (less when embedded)
        self.set_margin_start(10)
        self.set_margin_end(10)
        if show_controls:
            self.set_margin_top(10)
            self.set_margin_bottom(10)
        else:
            self.set_margin_top(0)
            self.set_margin_bottom(10)

        # Main touch surface
        self.touchpad_area = Gtk.DrawingArea()
        self.touchpad_area.set_hexpand(True)
        self.touchpad_area.set_vexpand(True)
        self.touchpad_area.set_can_target(True)  # Enable receiving pointer/touch events
        self.touchpad_area.add_css_class("touchpad-area")
        self.touchpad_area.set_draw_func(self._draw_touchpad)
        self.append(self.touchpad_area)

        # Mouse button row
        self.button_row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=2
        )
        self.button_row.set_margin_top(2)
        self.button_row.add_css_class("mouse-button-row")

        # Left click button
        self.left_click_button = Gtk.Button()
        self.left_click_button.set_hexpand(True)
        self.left_click_button.set_size_request(-1, 45)
        self.left_click_button.add_css_class("mouse-button")
        self.button_row.append(self.left_click_button)

        # Middle click button
        self.middle_click_button = Gtk.Button()
        self.middle_click_button.set_hexpand(True)
        self.middle_click_button.set_size_request(-1, 45)
        self.middle_click_button.add_css_class("mouse-button")
        self.button_row.append(self.middle_click_button)

        # Right click button
        self.right_click_button = Gtk.Button()
        self.right_click_button.set_hexpand(True)
        self.right_click_button.set_size_request(-1, 45)
        self.right_click_button.add_css_class("mouse-button")
        self.button_row.append(self.right_click_button)

        self.append(self.button_row)

        # Control row at bottom (only if show_controls is True)
        self.mode_button = None
        self.close_button = None

        if self.show_controls:
            self.control_row = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, spacing=8
            )
            self.control_row.set_margin_top(8)
            self.control_row.add_css_class("touchpad-controls")

            # Mode toggle button
            self.mode_button = Gtk.Button(label="⌨")
            self.mode_button.set_hexpand(True)
            self.mode_button.set_size_request(-1, 50)
            self.mode_button.add_css_class("keyboard-key")
            self.mode_button.add_css_class("mode")
            self.control_row.append(self.mode_button)

            # Close button
            self.close_button = Gtk.Button(label="✕")
            self.close_button.set_hexpand(True)
            self.close_button.set_size_request(-1, 50)
            self.close_button.add_css_class("keyboard-key")
            self.close_button.add_css_class("close")
            self.control_row.append(self.close_button)

            self.append(self.control_row)

        self.add_css_class("touchpad-widget")

    def _draw_touchpad(self, area, cr, width, height):
        """Draw the touchpad surface background."""
        # Draw a subtle border/indicator
        cr.set_source_rgba(0.3, 0.35, 0.45, 0.3)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        # Draw corner indicators
        cr.set_source_rgba(0.4, 0.45, 0.55, 0.5)
        indicator_size = 20

        # Top-left corner
        cr.move_to(0, indicator_size)
        cr.line_to(0, 0)
        cr.line_to(indicator_size, 0)
        cr.stroke()

        # Top-right corner
        cr.move_to(width - indicator_size, 0)
        cr.line_to(width, 0)
        cr.line_to(width, indicator_size)
        cr.stroke()

        # Bottom-left corner
        cr.move_to(0, height - indicator_size)
        cr.line_to(0, height)
        cr.line_to(indicator_size, height)
        cr.stroke()

        # Bottom-right corner
        cr.move_to(width - indicator_size, height)
        cr.line_to(width, height)
        cr.line_to(width, height - indicator_size)
        cr.stroke()
