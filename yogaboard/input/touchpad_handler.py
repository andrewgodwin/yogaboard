"""Touch gesture handling for touchpad widget using raw touch events."""

from __future__ import annotations

import gi
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from yogaboard.input_device.uinput_touchpad import UInputTouchpad
from yogaboard.ui.touchpad_widget import TouchpadWidget

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk

if TYPE_CHECKING:
    from yogaboard.main import KeyboardApp


@dataclass
class TouchState:
    """State for tracking a single touch point."""

    sequence: object  # Gdk.EventSequence - opaque identifier
    start_x: float
    start_y: float
    last_x: float
    last_y: float
    start_time: float
    has_moved: bool = False  # True if movement exceeded TAP_MAX_MOVEMENT


class TouchpadHandler:
    """
    Handles raw touch events on the touchpad widget and converts them to
    pointer/scroll/click events.

    Uses EventControllerLegacy to receive raw touch events for full control
    over gesture recognition, enabling tiny movements and multi-finger taps.
    """

    # Gesture tuning parameters
    POINTER_SENSITIVITY = 2.0  # Multiplier for pointer motion
    SCROLL_SENSITIVITY = 0.15  # Multiplier for scroll events
    TAP_MAX_DURATION = 0.25  # Maximum seconds for a tap
    TAP_MAX_MOVEMENT = 15  # Maximum pixels for a tap

    def __init__(self, uinput_touchpad: UInputTouchpad, app):
        self.touchpad = uinput_touchpad
        self.app: KeyboardApp = app

        # Touch tracking state
        self.active_touches: dict[object, TouchState] = {}  # sequence -> state
        self._max_fingers_in_gesture = 0  # For tap type detection
        self._any_finger_moved = False  # For tap detection
        self.first_touch_time = 0.0

        # Pointer accumulator for sub-pixel precision
        self.pointer_accumulator_x = 0.0
        self.pointer_accumulator_y = 0.0

        # Scroll accumulator for sub-pixel precision
        self.scroll_accumulator_x = 0.0
        self.scroll_accumulator_y = 0.0

    def setup_gestures(self, widget: TouchpadWidget):
        """
        Setup raw touch event handling on the touchpad widget.

        Args:
            widget: TouchpadWidget to attach event controller to
        """
        touchpad_area = widget.touchpad_area

        # Use EventControllerLegacy for raw touch event access
        self.legacy_controller = Gtk.EventControllerLegacy.new()
        self.legacy_controller.connect("event", self._on_event)
        touchpad_area.add_controller(self.legacy_controller)

        # Connect mouse buttons with press/release for drag support
        self._setup_mouse_button(widget.left_click_button, "left")
        self._setup_mouse_button(widget.middle_click_button, "middle")
        self._setup_mouse_button(widget.right_click_button, "right")

        # Connect control buttons (if present)
        if widget.mode_button:
            widget.mode_button.connect("clicked", self._on_mode_clicked)
        if widget.close_button:
            widget.close_button.connect("clicked", self._on_close_clicked)

    def _on_event(self, controller, _event) -> bool:
        """Main event dispatcher for raw touch events."""
        # Get event from controller since callback param may be None in PyGObject
        event = controller.get_current_event()
        if event is None:
            return False
        event_type = event.get_event_type()

        if event_type == Gdk.EventType.TOUCH_BEGIN:
            self._on_touch_begin(event)
            return True
        elif event_type == Gdk.EventType.TOUCH_UPDATE:
            self._on_touch_update(event)
            return True
        elif event_type == Gdk.EventType.TOUCH_END:
            self._on_touch_end(event)
            return True
        elif event_type == Gdk.EventType.TOUCH_CANCEL:
            self._on_touch_cancel(event)
            return True

        return False  # Event not handled, let it propagate

    def _on_touch_begin(self, event):
        """Handle finger down event."""
        sequence = event.get_event_sequence()
        success, x, y = event.get_position()
        now = time.monotonic()

        # If this is the first finger, reset gesture state
        if len(self.active_touches) == 0:
            self.first_touch_time = now
            self._max_fingers_in_gesture = 0
            self._any_finger_moved = False
            self.scroll_accumulator_x = 0.0
            self.scroll_accumulator_y = 0.0
            self.pointer_accumulator_x = 0.0
            self.pointer_accumulator_y = 0.0

        # Store touch state
        self.active_touches[sequence] = TouchState(
            sequence=sequence,
            start_x=x,
            start_y=y,
            last_x=x,
            last_y=y,
            start_time=now,
            has_moved=False,
        )

        # Track maximum fingers for tap detection
        current_count = len(self.active_touches)
        self._max_fingers_in_gesture = max(
            self._max_fingers_in_gesture, current_count
        )

    def _on_touch_update(self, event):
        """Handle finger move event."""
        sequence = event.get_event_sequence()
        if sequence not in self.active_touches:
            return

        touch = self.active_touches[sequence]
        success, x, y = event.get_position()

        # Calculate delta from last position
        dx = x - touch.last_x
        dy = y - touch.last_y

        # Update last position
        touch.last_x = x
        touch.last_y = y

        # Check if this movement exceeds tap threshold
        total_movement = abs(x - touch.start_x) + abs(y - touch.start_y)
        if total_movement > self.TAP_MAX_MOVEMENT:
            touch.has_moved = True
            self._any_finger_moved = True

        # Process based on finger count
        finger_count = len(self.active_touches)

        if finger_count == 1:
            # Single finger: pointer movement
            self._process_single_finger_motion(dx, dy)
        elif finger_count >= 2:
            # Two+ fingers: scrolling
            self._process_two_finger_motion(dx, dy)

    def _on_touch_end(self, event):
        """Handle finger up event."""
        sequence = event.get_event_sequence()
        if sequence not in self.active_touches:
            return

        # Remove this touch
        del self.active_touches[sequence]

        # If all fingers are now up, check for tap gestures
        if len(self.active_touches) == 0:
            tap_result = self._detect_tap_gesture()
            if tap_result:
                self.touchpad.tap(tap_result)

    def _on_touch_cancel(self, event):
        """Handle cancelled touch - cleanup without triggering gestures."""
        sequence = event.get_event_sequence()
        if sequence in self.active_touches:
            del self.active_touches[sequence]

        # If all touches cancelled, reset state
        if len(self.active_touches) == 0:
            self._reset_gesture_state()

    def _reset_gesture_state(self):
        """Reset all gesture tracking state."""
        self.active_touches.clear()
        self.scroll_accumulator_x = 0.0
        self.scroll_accumulator_y = 0.0
        self.pointer_accumulator_x = 0.0
        self.pointer_accumulator_y = 0.0
        self._max_fingers_in_gesture = 0
        self._any_finger_moved = False

    def _process_single_finger_motion(self, dx: float, dy: float):
        """Convert finger motion to pointer movement with sub-pixel precision."""
        self.pointer_accumulator_x += dx * self.POINTER_SENSITIVITY
        self.pointer_accumulator_y += dy * self.POINTER_SENSITIVITY

        pointer_dx = int(self.pointer_accumulator_x)
        pointer_dy = int(self.pointer_accumulator_y)

        if pointer_dx != 0 or pointer_dy != 0:
            self.touchpad.move_pointer(pointer_dx, pointer_dy)
            self.pointer_accumulator_x -= pointer_dx
            self.pointer_accumulator_y -= pointer_dy

    def _process_two_finger_motion(self, dx: float, dy: float):
        """Convert two-finger motion to scroll events (natural scrolling)."""
        # Natural scrolling: finger up = content up = positive wheel
        self.scroll_accumulator_x += dx * self.SCROLL_SENSITIVITY
        self.scroll_accumulator_y -= dy * self.SCROLL_SENSITIVITY  # Inverted

        scroll_x = int(self.scroll_accumulator_x)
        scroll_y = int(self.scroll_accumulator_y)

        if scroll_x != 0 or scroll_y != 0:
            self.touchpad.scroll(scroll_x, scroll_y)
            self.scroll_accumulator_x -= scroll_x
            self.scroll_accumulator_y -= scroll_y

    def _detect_tap_gesture(self) -> str | None:
        """
        Determine if the gesture that just ended was a tap.

        Returns:
            "left" for single-finger tap
            "right" for two-finger tap
            "middle" for three-finger tap
            None if not a tap
        """
        now = time.monotonic()
        duration = now - self.first_touch_time

        # Check if duration is within tap threshold
        if duration > self.TAP_MAX_DURATION:
            return None

        # Check if any finger moved too much
        if self._any_finger_moved:
            return None

        # Determine tap type based on max finger count during gesture
        if self._max_fingers_in_gesture == 1:
            return "left"
        elif self._max_fingers_in_gesture == 2:
            return "right"
        elif self._max_fingers_in_gesture >= 3:
            return "middle"

        return None

    def _setup_mouse_button(self, button, button_name: str):
        """Setup press/release handling for a mouse button using GestureClick on Box."""
        gesture = Gtk.GestureClick.new()
        gesture.set_button(0)
        gesture.set_touch_only(True)

        def on_pressed(g, n_press, x, y):
            self.touchpad.click(button_name, pressed=True)

        def on_released(g, n_press, x, y):
            self.touchpad.click(button_name, pressed=False)

        def on_cancel(g, sequence):
            self.touchpad.click(button_name, pressed=False)

        gesture.connect("pressed", on_pressed)
        gesture.connect("released", on_released)
        gesture.connect("cancel", on_cancel)
        button.add_controller(gesture)

    def _on_mode_clicked(self, button):
        """Handle mode toggle button click."""
        self.app.toggle_mode()

    def _on_close_clicked(self, button):
        """Handle close button click."""
        self.app.quit()

    def cleanup(self):
        """Cleanup resources."""
        self._reset_gesture_state()
