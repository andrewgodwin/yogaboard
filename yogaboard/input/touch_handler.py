"""Touch event handling with multitouch modifier support."""

import gi

from yogaboard.input_device.uinput_keyboard import UInputKeyboard
from yogaboard.ui.key_button import KeyButton

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk
from .modifier_state import ModifierState
import traceback


class TouchHandler:
    """
    Handles touch/click events and turns them into a stream of things to send
    to our virtual keyboard.
    """

    def __init__(self, uinput_keyboard: UInputKeyboard):
        self.keyboard = uinput_keyboard

    def setup_gestures(self, keyboard_widget):
        """
        Setup touch gesture recognition on each button.

        Args:
            keyboard_widget: KeyboardWidget containing buttons
        """
        for btn in keyboard_widget.key_buttons:
            gesture = Gtk.GestureClick.new()
            gesture.set_button(0)  # All buttons/touches
            gesture.set_exclusive(False)  # Allow multiple simultaneous gestures
            gesture.connect("pressed", self._on_button_press, btn)
            gesture.connect("released", self._on_button_release, btn)
            gesture.connect("cancel", self._on_button_cancel, btn)
            btn.add_controller(gesture)

    def _on_button_press(self, gesture, n_press, x, y, button: KeyButton):
        # Send the key press
        key_code = button.key.get_uinput_key()
        self.keyboard.send_key(key_code, pressed=True)

    def _on_button_release(self, gesture, n_press, x, y, button: KeyButton):
        # Send key release
        key_code = button.key.get_uinput_key()
        self.keyboard.send_key(key_code, pressed=False)

    def _on_button_cancel(self, gesture, sequence, button: KeyButton):
        # Send key release
        key_code = button.key.get_uinput_key()
        self.keyboard.send_key(key_code, pressed=False)

    def cleanup(self):
        """Cleanup resources (no-op since uinput keyboard manages its own thread)."""
        pass
