"""Touch event handling with multitouch modifier support."""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk
from .modifier_state import ModifierState
import traceback


class TouchHandler:
    """Handle touch/click events and coordinate with virtual keyboard."""

    def __init__(self, uinput_keyboard, modifier_state):
        """
        Initialize touch handler.

        Args:
            uinput_keyboard: UInputKeyboard instance for sending key events
            modifier_state: ModifierState instance for tracking modifiers
        """
        self.keyboard = uinput_keyboard
        self.modifier_state = modifier_state
        self.active_touches = {}  # {sequence_id: (Key, touch_id)}
        self._next_touch_id = 0
        # Track which modifiers have been physically sent to uinput
        self._pressed_modifiers = (
            set()
        )  # Set of modifier names currently pressed in uinput
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

        print(
            f"[touch] Gesture controllers setup for {len(keyboard_widget.key_buttons)} buttons"
        )

    def _on_button_press(self, gesture, n_press, x, y, button):
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
            sequence = gesture.get_current_sequence()
            # Use string representation for sequence as key (handles None for mouse)
            sequence_key = str(id(sequence)) if sequence else "mouse"

            touch_id = self._next_touch_id
            self._next_touch_id += 1

            print(
                f"[touch] press: key={button.key.label} seq={sequence_key} touch_id={touch_id}"
            )

            # Store the touch with its button and touch_id
            self.active_touches[sequence_key] = (button.key, touch_id)

            if button.key.is_modifier:
                # Track modifier state but don't send to uinput yet
                print(f"[touch] modifier '{button.key.modifier}' pressed")
                self.modifier_state.press(button.key.modifier, touch_id)
            else:
                # For non-modifier keys, first press any active modifiers
                self._press_active_modifiers()

                # Then send the key press
                key_code = button.key.get_uinput_key()
                print(f"[touch] sending key press for '{button.key.label}'")
                self.keyboard.send_key(key_code, pressed=True)

        except Exception as e:
            print(f"Error in _on_button_press: {e}")
            traceback.print_exc()

    def _on_button_release(self, gesture, n_press, x, y, button):
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
            sequence = gesture.get_current_sequence()
            # Use string representation for sequence as key (handles None for mouse)
            sequence_key = str(id(sequence)) if sequence else "mouse"

            print(
                f"[touch] release: seq={sequence_key} active_touches={list(self.active_touches.keys())}"
            )

            if sequence_key not in self.active_touches:
                print(f"[touch] release: sequence {sequence_key} not in active touches")
                return

            key, touch_id = self.active_touches[sequence_key]
            print(
                f"[touch] release: key={key.label} seq={sequence_key} touch_id={touch_id}"
            )

            if key.is_modifier:
                # Release modifier state tracking
                print(f"[touch] modifier '{key.modifier}' released")
                self.modifier_state.release(key.modifier, touch_id)
                # Release any modifier keys that were pressed to uinput
                self._release_active_modifiers()
            else:
                # Send key release
                key_code = key.get_uinput_key()
                print(f"[touch] sending key release for '{key.label}'")
                self.keyboard.send_key(key_code, pressed=False)

                # Release any modifier keys that were pressed with this key
                self._release_active_modifiers()

            del self.active_touches[sequence_key]

        except Exception as e:
            print(f"Error in _on_button_release: {e}")
            traceback.print_exc()

    def _press_active_modifiers(self):
        """Press any active modifiers that aren't already pressed in uinput."""
        import uinput

        active = self.modifier_state.get_all_active()
        for modifier in active:
            if modifier not in self._pressed_modifiers:
                # Press this modifier key in uinput
                key_name = self._modifier_keys.get(modifier)
                if key_name:
                    key_tuple = getattr(uinput, key_name)
                    # Extract key code from tuple (event_type, key_code)
                    key_code = (
                        key_tuple[1] if isinstance(key_tuple, tuple) else key_tuple
                    )
                    self.keyboard.send_key(key_code, pressed=True)
                    self._pressed_modifiers.add(modifier)

    def _release_active_modifiers(self):
        """Release any modifiers that were pressed in uinput but are no longer held."""
        import uinput

        active = self.modifier_state.get_all_active()
        # Release modifiers that are pressed in uinput but no longer active
        to_release = self._pressed_modifiers - active
        for modifier in to_release:
            key_name = self._modifier_keys.get(modifier)
            if key_name:
                key_tuple = getattr(uinput, key_name)
                # Extract key code from tuple (event_type, key_code)
                key_code = key_tuple[1] if isinstance(key_tuple, tuple) else key_tuple
                self.keyboard.send_key(key_code, pressed=False)
        # Update the set of pressed modifiers
        self._pressed_modifiers = self._pressed_modifiers & active

    def _on_button_cancel(self, gesture, sequence, button):
        """
        Handle gesture cancellation.

        Args:
            gesture: GestureClick that was cancelled
            sequence: Event sequence that was cancelled
            button: KeyButton associated with the gesture
        """
        sequence_key = str(id(sequence)) if sequence else "mouse"
        print(f"[touch] gesture cancelled: seq={sequence_key}")

        # Treat cancel as release for any active touches
        if sequence_key in self.active_touches:
            key, touch_id = self.active_touches[sequence_key]
            print(f"[touch] cancelling active touch for key={key.label}")

            if key.is_modifier:
                self.modifier_state.release(key.modifier, touch_id)
                self._release_active_modifiers()
            else:
                key_code = key.get_uinput_key()
                self.keyboard.send_key(key_code, pressed=False)
                self._release_active_modifiers()

            del self.active_touches[sequence_key]

    def cleanup(self):
        """Cleanup resources (no-op since uinput keyboard manages its own thread)."""
        pass
