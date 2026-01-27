"""Touch event forwarding for virtual multi-touch touchpad."""

from __future__ import annotations

import gi
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from yogaboard.input_device.uinput_touchpad import UInputTouchpad
from yogaboard.ui.touchpad_widget import TouchpadWidget

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, Graphene

if TYPE_CHECKING:
    from yogaboard.main import KeyboardApp


@dataclass
class SlotInfo:
    """Tracking info for a touch slot."""

    slot: int
    tracking_id: int


class TouchpadHandler:
    """
    Forwards raw touch events to the virtual multi-touch touchpad device.

    The actual gesture interpretation (scrolling, taps, swipes) is handled
    by libinput and the desktop environment.
    """

    def __init__(self, uinput_touchpad: UInputTouchpad, app):
        self.touchpad = uinput_touchpad
        self.app: KeyboardApp = app

        # Slot management: map EventSequence -> SlotInfo
        self.sequence_to_slot: dict[object, SlotInfo] = {}
        self.available_slots: list[int] = list(range(UInputTouchpad.MAX_SLOTS))
        self._next_tracking_id = 1

        # Widget dimensions for coordinate mapping
        self.widget_width = 1
        self.widget_height = 1

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

        # Track widget size for coordinate mapping
        touchpad_area.connect("notify::width-request", self._on_size_changed)
        touchpad_area.connect("notify::height-request", self._on_size_changed)

        # Connect mouse buttons with press/release
        self._setup_mouse_button(widget.left_click_button, "left")
        self._setup_mouse_button(widget.middle_click_button, "middle")
        self._setup_mouse_button(widget.right_click_button, "right")

        # Connect control buttons (if present)
        if widget.mode_button:
            widget.mode_button.connect("clicked", self._on_mode_clicked)
        if widget.close_button:
            widget.close_button.connect("clicked", self._on_close_clicked)

        # Store reference to widget for size queries
        self._widget = widget

    def _on_size_changed(self, widget, pspec):
        """Handle widget size changes."""
        self._update_widget_size()

    def _update_widget_size(self):
        """Update cached widget dimensions."""
        if hasattr(self, "_widget"):
            alloc = self._widget.touchpad_area.get_allocation()
            if alloc.width > 0 and alloc.height > 0:
                self.widget_width = alloc.width
                self.widget_height = alloc.height

    def _get_widget_local_coords(self, event) -> tuple[float, float]:
        """Get event coordinates relative to the touchpad widget."""
        # get_position returns coordinates relative to the event's surface (root window)
        success, surface_x, surface_y = event.get_position()

        # Transform from root/surface coords to widget-local coords
        widget = self._widget.touchpad_area
        root = widget.get_root()

        # Use graphene point transformation: from root coords to widget coords
        point = Graphene.Point()
        point.x = surface_x
        point.y = surface_y

        # compute_point transforms FROM source TO dest
        # We want: root coords -> widget coords
        success, local_point = root.compute_point(widget, point)
        if success:
            return local_point.x, local_point.y

        # Fallback: return surface coords (will be wrong but won't crash)
        return surface_x, surface_y

    def _map_coordinates(self, x: float, y: float) -> tuple[int, int]:
        """Map widget coordinates to device coordinates."""
        self._update_widget_size()
        device_x = int((x / self.widget_width) * UInputTouchpad.DEVICE_MAX_X)
        device_y = int((y / self.widget_height) * UInputTouchpad.DEVICE_MAX_Y)
        # Clamp to valid range
        device_x = max(0, min(UInputTouchpad.DEVICE_MAX_X, device_x))
        device_y = max(0, min(UInputTouchpad.DEVICE_MAX_Y, device_y))
        return device_x, device_y

    def _allocate_slot(self, sequence: object) -> SlotInfo:
        """Allocate a slot for a new touch."""
        if not self.available_slots:
            # All slots in use, reuse slot 0
            slot = 0
        else:
            slot = self.available_slots.pop(0)

        tracking_id = self._next_tracking_id
        self._next_tracking_id += 1
        if self._next_tracking_id > 65535:
            self._next_tracking_id = 1

        info = SlotInfo(slot=slot, tracking_id=tracking_id)
        self.sequence_to_slot[sequence] = info
        return info

    def _release_slot(self, sequence: object):
        """Release a slot when touch ends."""
        if sequence in self.sequence_to_slot:
            info = self.sequence_to_slot.pop(sequence)
            if info.slot not in self.available_slots:
                self.available_slots.append(info.slot)
                self.available_slots.sort()

    def _on_event(self, controller, _event) -> bool:
        """Main event dispatcher for raw touch events."""
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

        return False

    def _on_touch_begin(self, event):
        """Handle finger down event - forward to uinput."""
        sequence = event.get_event_sequence()
        x, y = self._get_widget_local_coords(event)

        # Allocate slot and get device coordinates
        info = self._allocate_slot(sequence)
        device_x, device_y = self._map_coordinates(x, y)

        # Send touch down
        self.touchpad.touch_down(info.slot, info.tracking_id, device_x, device_y)

        # Update finger count
        finger_count = len(self.sequence_to_slot)
        self.touchpad.set_finger_count(finger_count)

        self.touchpad.sync()

    def _on_touch_update(self, event):
        """Handle finger move event - forward to uinput."""
        sequence = event.get_event_sequence()
        if sequence not in self.sequence_to_slot:
            return

        x, y = self._get_widget_local_coords(event)
        info = self.sequence_to_slot[sequence]
        device_x, device_y = self._map_coordinates(x, y)

        # Send touch move
        self.touchpad.touch_move(info.slot, device_x, device_y)
        self.touchpad.sync()

    def _on_touch_end(self, event):
        """Handle finger up event - forward to uinput."""
        sequence = event.get_event_sequence()
        if sequence not in self.sequence_to_slot:
            return

        info = self.sequence_to_slot[sequence]

        # Send touch up
        self.touchpad.touch_up(info.slot)

        # Release slot
        self._release_slot(sequence)

        # Update finger count
        finger_count = len(self.sequence_to_slot)
        self.touchpad.set_finger_count(finger_count)

        self.touchpad.sync()

    def _on_touch_cancel(self, event):
        """Handle cancelled touch - forward to uinput."""
        sequence = event.get_event_sequence()
        if sequence not in self.sequence_to_slot:
            return

        info = self.sequence_to_slot[sequence]

        # Send touch up
        self.touchpad.touch_up(info.slot)

        # Release slot
        self._release_slot(sequence)

        # Update finger count
        finger_count = len(self.sequence_to_slot)
        self.touchpad.set_finger_count(finger_count)

        self.touchpad.sync()

    def _setup_mouse_button(self, button, button_name: str):
        """Setup press/release handling for a mouse button."""
        gesture = Gtk.GestureClick.new()
        gesture.set_button(0)
        gesture.set_touch_only(True)

        def on_pressed(g, n_press, x, y):
            self.touchpad.click(button_name, pressed=True)
            self.touchpad.sync()

        def on_released(g, n_press, x, y):
            self.touchpad.click(button_name, pressed=False)
            self.touchpad.sync()

        def on_cancel(g, sequence):
            self.touchpad.click(button_name, pressed=False)
            self.touchpad.sync()

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
        # Release all active slots
        for sequence in list(self.sequence_to_slot.keys()):
            info = self.sequence_to_slot[sequence]
            self.touchpad.touch_up(info.slot)
        self.sequence_to_slot.clear()
        self.available_slots = list(range(UInputTouchpad.MAX_SLOTS))
        self.touchpad.set_finger_count(0)
        self.touchpad.sync()
