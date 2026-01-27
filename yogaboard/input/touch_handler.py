"""Touch event handling with multitouch modifier support."""

from __future__ import annotations

import gi
from typing import TYPE_CHECKING

from yogaboard.input_device.uinput_keyboard import UInputKeyboard
from yogaboard.ui.key_button import KeyButton

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk

if TYPE_CHECKING:
    from yogaboard.main import KeyboardApp


class TouchHandler:
    """
    Handles touch/click events and turns them into a stream of things to send
    to our virtual keyboard.
    """

    def __init__(self, uinput_keyboard: UInputKeyboard, app):
        self.keyboard = uinput_keyboard
        self.app: KeyboardApp = app

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
        # Handle special keys that don't go to uinput
        if button.key.key.startswith("SPECIAL_"):
            self._handle_special_key(button.key.key)
            return

        # Send the key press
        key_code = button.key.get_uinput_key()
        self.keyboard.send_key(key_code, pressed=True)

    def _on_button_release(self, gesture, n_press, x, y, button: KeyButton):
        # Special keys don't need release events
        if button.key.key.startswith("SPECIAL_"):
            return

        # Send key release
        key_code = button.key.get_uinput_key()
        self.keyboard.send_key(key_code, pressed=False)

    def _on_button_cancel(self, gesture, sequence, button: KeyButton):
        # Special keys don't need release events
        if button.key.key.startswith("SPECIAL_"):
            return

        # Send key release
        key_code = button.key.get_uinput_key()
        self.keyboard.send_key(key_code, pressed=False)

    def _handle_special_key(self, key: str):
        """Handle special keys that trigger application actions instead of uinput."""
        if key == "SPECIAL_CLOSE":
            self.app.quit()
        elif key == "SPECIAL_MODE_TOGGLE":
            # Mode toggle button goes back to slim
            self.app.switch_to_layout(self.app.MODE_SLIM)
        elif key == "SPECIAL_MODE_KEYBOARD":
            self.app.switch_to_layout(self.app.MODE_KEYBOARD)
        elif key == "SPECIAL_MODE_FULL":
            self.app.switch_to_full()
        elif key == "SPECIAL_MODE_SMALL":
            self.app.switch_to_small()
        elif key == "SPECIAL_SETTINGS":
            self.app.open_settings()

    def cleanup(self):
        """Cleanup resources (no-op since uinput keyboard manages its own thread)."""
        pass
