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
        # Map modifier names to their uinput key codes
        self._modifier_keys = {
            "shift": "KEY_LEFTSHIFT",
            "ctrl": "KEY_LEFTCTRL",
            "alt": "KEY_LEFTALT",
        }

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
        """
        Handle button press event.

        Args:
            gesture: GestureClick that triggered the event
            n_press: Number of consecutive presses
            x: X coordinate of press (relative to button)
            y: Y coordinate of press (relative to button)
            button: KeyButton that was pressed
        """
        try:
            # Send the key press
            key_code = button.key.get_uinput_key()
            self.keyboard.send_key(key_code, pressed=True)

        except Exception as e:
            print(f"Error in _on_button_press: {e}")
            traceback.print_exc()

    def _on_button_release(self, gesture, n_press, x, y, button: KeyButton):
        """
        Handle button release event.

        Args:
            gesture: GestureClick that triggered the event
            n_press: Number of consecutive presses
            x: X coordinate of release (relative to button)
            y: Y coordinate of release (relative to button)
            button: KeyButton that was released
        """
        try:
            # Send key release
            key_code = button.key.get_uinput_key()
            print(f"[touch] sending key release for '{button.key.label}'")
            self.keyboard.send_key(key_code, pressed=False)

        except Exception as e:
            print(f"Error in _on_button_release: {e}")
            traceback.print_exc()

    def _on_button_cancel(self, gesture, sequence, button: KeyButton):
        """
        Handle gesture cancellation.

        Args:
            gesture: GestureClick that was cancelled
            sequence: Event sequence that was cancelled
            button: KeyButton associated with the gesture
        """

        # Send key release
        key_code = button.key.get_uinput_key()
        print(f"[touch] sending key release for '{button.key.label}'")
        self.keyboard.send_key(key_code, pressed=False)

    def cleanup(self):
        """Cleanup resources (no-op since uinput keyboard manages its own thread)."""
        pass
