"""Touch gesture handling for touchpad widget."""

from __future__ import annotations

import gi
import time
from typing import TYPE_CHECKING

from yogaboard.input_device.uinput_touchpad import UInputTouchpad
from yogaboard.ui.touchpad_widget import TouchpadWidget

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk

if TYPE_CHECKING:
    from yogaboard.main import KeyboardApp


class TouchpadHandler:
    """
    Handles touch gestures on the touchpad widget and converts them to
    pointer/scroll/click events.

    Uses GestureDrag for single-finger motion and GestureZoom for two-finger scroll.
    Mouse buttons are provided via dedicated UI buttons.
    """

    # Gesture tuning parameters
    POINTER_SENSITIVITY = 2.0  # Multiplier for pointer motion
    SCROLL_SENSITIVITY = 0.15  # Multiplier for scroll events
    TAP_MAX_DURATION = 0.25  # Maximum seconds for a tap
    TAP_MAX_MOVEMENT = 15  # Maximum pixels for a tap

    def __init__(self, uinput_touchpad: UInputTouchpad, app):
        self.touchpad = uinput_touchpad
        self.app: KeyboardApp = app

        # Track gesture states
        self.two_finger_active = False
        self.drag_start_x = 0.0
        self.drag_start_y = 0.0
        self.drag_last_x = 0.0
        self.drag_last_y = 0.0

        # For two-finger scroll tracking
        self.scroll_last_x = 0.0
        self.scroll_last_y = 0.0
        self.scroll_accumulator_x = 0.0
        self.scroll_accumulator_y = 0.0

        # Tap tracking
        self.drag_start_time = 0.0

    def setup_gestures(self, widget: TouchpadWidget):
        """
        Setup touch gesture recognition on the touchpad widget.

        Args:
            widget: TouchpadWidget to attach gestures to
        """
        touchpad_area = widget.touchpad_area

        # Drag gesture for single-finger motion tracking
        self.drag_gesture = Gtk.GestureDrag.new()
        self.drag_gesture.set_touch_only(True)
        self.drag_gesture.connect("drag-begin", self._on_drag_begin)
        self.drag_gesture.connect("drag-update", self._on_drag_update)
        self.drag_gesture.connect("drag-end", self._on_drag_end)
        touchpad_area.add_controller(self.drag_gesture)

        # Zoom gesture to detect two-finger gestures for scrolling
        self.zoom_gesture = Gtk.GestureZoom.new()
        self.zoom_gesture.connect("begin", self._on_zoom_begin)
        self.zoom_gesture.connect("scale-changed", self._on_zoom_update)
        self.zoom_gesture.connect("end", self._on_zoom_end)
        touchpad_area.add_controller(self.zoom_gesture)

        # Connect mouse buttons
        widget.left_click_button.connect("clicked", self._on_left_click)
        widget.middle_click_button.connect("clicked", self._on_middle_click)
        widget.right_click_button.connect("clicked", self._on_right_click)

        # Connect control buttons (if present)
        if widget.mode_button:
            widget.mode_button.connect("clicked", self._on_mode_clicked)
        if widget.close_button:
            widget.close_button.connect("clicked", self._on_close_clicked)

    def _on_drag_begin(self, gesture, start_x, start_y):
        """Handle start of drag gesture."""
        self.drag_start_x = start_x
        self.drag_start_y = start_y
        self.drag_last_x = start_x
        self.drag_last_y = start_y
        self.drag_start_time = time.monotonic()

    def _on_drag_update(self, gesture, offset_x, offset_y):
        """Handle drag motion - pointer movement when single finger."""
        if self.two_finger_active:
            return

        current_x = self.drag_start_x + offset_x
        current_y = self.drag_start_y + offset_y

        dx = current_x - self.drag_last_x
        dy = current_y - self.drag_last_y

        self.drag_last_x = current_x
        self.drag_last_y = current_y

        pointer_dx = int(dx * self.POINTER_SENSITIVITY)
        pointer_dy = int(dy * self.POINTER_SENSITIVITY)
        self.touchpad.move_pointer(pointer_dx, pointer_dy)

    def _on_drag_end(self, gesture, offset_x, offset_y):
        """Handle end of drag gesture - detect single-finger taps."""
        if self.two_finger_active:
            return

        duration = time.monotonic() - self.drag_start_time
        movement = abs(offset_x) + abs(offset_y)

        if duration < self.TAP_MAX_DURATION and movement < self.TAP_MAX_MOVEMENT:
            self.touchpad.tap("left")

    def _on_zoom_begin(self, gesture, sequence):
        """Handle start of two-finger gesture."""
        self.two_finger_active = True

        success, rect = gesture.get_bounding_box()
        if success:
            self.scroll_last_x = rect.x + rect.width / 2
            self.scroll_last_y = rect.y + rect.height / 2

        self.scroll_accumulator_x = 0.0
        self.scroll_accumulator_y = 0.0

    def _on_zoom_update(self, gesture, scale):
        """Handle two-finger gesture update - scrolling."""
        success, rect = gesture.get_bounding_box()
        if not success:
            return

        current_x = rect.x + rect.width / 2
        current_y = rect.y + rect.height / 2

        dx = current_x - self.scroll_last_x
        dy = current_y - self.scroll_last_y

        self.scroll_last_x = current_x
        self.scroll_last_y = current_y

        # Natural scrolling
        self.scroll_accumulator_x += dx * self.SCROLL_SENSITIVITY
        self.scroll_accumulator_y -= dy * self.SCROLL_SENSITIVITY

        scroll_x = int(self.scroll_accumulator_x)
        scroll_y = int(self.scroll_accumulator_y)

        if scroll_x != 0 or scroll_y != 0:
            self.touchpad.scroll(scroll_x, scroll_y)
            self.scroll_accumulator_x -= scroll_x
            self.scroll_accumulator_y -= scroll_y

    def _on_zoom_end(self, gesture, sequence):
        """Handle end of two-finger gesture."""
        self.two_finger_active = False
        self.scroll_accumulator_x = 0.0
        self.scroll_accumulator_y = 0.0

    def _on_left_click(self, button):
        """Handle left click button."""
        self.touchpad.tap("left")

    def _on_middle_click(self, button):
        """Handle middle click button."""
        self.touchpad.tap("middle")

    def _on_right_click(self, button):
        """Handle right click button."""
        self.touchpad.tap("right")

    def _on_mode_clicked(self, button):
        """Handle mode toggle button click."""
        self.app.toggle_mode()

    def _on_close_clicked(self, button):
        """Handle close button click."""
        self.app.quit()

    def cleanup(self):
        """Cleanup resources."""
        self.two_finger_active = False
