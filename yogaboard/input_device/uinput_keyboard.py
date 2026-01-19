"""Virtual keyboard device using Linux uinput subsystem."""

import uinput
import time
import threading
from collections import deque
from dataclasses import dataclass
from typing import Literal


@dataclass
class KeyEvent:
    """Represents a key press or release event."""
    key_code: int
    action: Literal['press', 'release']


class UInputKeyboard:
    """Virtual keyboard using Linux uinput subsystem with threaded event processing."""

    # Map of all keyboard keys we want to support (standard 105-key keyboard)
    # Using uinput key codes (KEY_*)
    SUPPORTED_KEYS = [
        # Letters (A-Z)
        uinput.KEY_A, uinput.KEY_B, uinput.KEY_C, uinput.KEY_D,
        uinput.KEY_E, uinput.KEY_F, uinput.KEY_G, uinput.KEY_H,
        uinput.KEY_I, uinput.KEY_J, uinput.KEY_K, uinput.KEY_L,
        uinput.KEY_M, uinput.KEY_N, uinput.KEY_O, uinput.KEY_P,
        uinput.KEY_Q, uinput.KEY_R, uinput.KEY_S, uinput.KEY_T,
        uinput.KEY_U, uinput.KEY_V, uinput.KEY_W, uinput.KEY_X,
        uinput.KEY_Y, uinput.KEY_Z,

        # Numbers (0-9)
        uinput.KEY_0, uinput.KEY_1, uinput.KEY_2, uinput.KEY_3,
        uinput.KEY_4, uinput.KEY_5, uinput.KEY_6, uinput.KEY_7,
        uinput.KEY_8, uinput.KEY_9,

        # Function keys (F1-F12)
        uinput.KEY_F1, uinput.KEY_F2, uinput.KEY_F3, uinput.KEY_F4,
        uinput.KEY_F5, uinput.KEY_F6, uinput.KEY_F7, uinput.KEY_F8,
        uinput.KEY_F9, uinput.KEY_F10, uinput.KEY_F11, uinput.KEY_F12,

        # Modifiers
        uinput.KEY_LEFTSHIFT, uinput.KEY_RIGHTSHIFT,
        uinput.KEY_LEFTCTRL, uinput.KEY_RIGHTCTRL,
        uinput.KEY_LEFTALT, uinput.KEY_RIGHTALT,
        uinput.KEY_LEFTMETA, uinput.KEY_RIGHTMETA,  # Super/Windows key

        # Special keys
        uinput.KEY_SPACE, uinput.KEY_ENTER, uinput.KEY_BACKSPACE,
        uinput.KEY_TAB, uinput.KEY_ESC, uinput.KEY_CAPSLOCK,

        # Punctuation and symbols
        uinput.KEY_MINUS, uinput.KEY_EQUAL,
        uinput.KEY_LEFTBRACE, uinput.KEY_RIGHTBRACE,
        uinput.KEY_SEMICOLON, uinput.KEY_APOSTROPHE,
        uinput.KEY_GRAVE, uinput.KEY_BACKSLASH,
        uinput.KEY_COMMA, uinput.KEY_DOT, uinput.KEY_SLASH,

        # Navigation keys
        uinput.KEY_UP, uinput.KEY_DOWN, uinput.KEY_LEFT, uinput.KEY_RIGHT,
        uinput.KEY_HOME, uinput.KEY_END,
        uinput.KEY_PAGEUP, uinput.KEY_PAGEDOWN,
        uinput.KEY_INSERT, uinput.KEY_DELETE,

        # System keys
        uinput.KEY_SYSRQ, uinput.KEY_SCROLLLOCK, uinput.KEY_PAUSE,
        uinput.KEY_PRINT,

        # Numpad keys
        uinput.KEY_NUMLOCK,
        uinput.KEY_KP0, uinput.KEY_KP1, uinput.KEY_KP2, uinput.KEY_KP3,
        uinput.KEY_KP4, uinput.KEY_KP5, uinput.KEY_KP6, uinput.KEY_KP7,
        uinput.KEY_KP8, uinput.KEY_KP9,
        uinput.KEY_KPSLASH, uinput.KEY_KPASTERISK,
        uinput.KEY_KPMINUS, uinput.KEY_KPPLUS,
        uinput.KEY_KPENTER, uinput.KEY_KPDOT,

        # Additional European 105-key specific
        uinput.KEY_102ND,  # The extra key on European keyboards (between left shift and Z)

        # Context menu key (between right Windows and right Ctrl)
        uinput.KEY_COMPOSE,
    ]

    def __init__(self):
        """Initialize virtual keyboard device with threaded event processing."""
        self.event_queue = deque()
        self.queue_lock = threading.Lock()
        self.running = True
        self.device = None

        # Start the uinput thread
        self.thread = threading.Thread(target=self._event_loop, daemon=True, name="uinput-worker")
        self.thread.start()

    def _event_loop(self):
        """Main event loop running in separate thread."""
        try:
            # Create uinput device with keyboard capabilities
            self.device = uinput.Device(
                self.SUPPORTED_KEYS,
                name="Yogaboard-Virtual-Keyboard",
            )

            # Small delay for device registration
            time.sleep(0.1)

        except Exception as e:
            print(f"Failed to create uinput device: {e}")
            print("Make sure you have permissions to access /dev/uinput")
            print("Run: sudo usermod -a -G input $USER")
            self.running = False
            return

        # Process events from queue
        while self.running:
            event = None

            # Get next event from queue
            with self.queue_lock:
                if self.event_queue:
                    event = self.event_queue.popleft()

            if event:
                try:
                    self._send_key_event(event)
                except Exception as e:
                    print(f"Error sending key event: {e}")
            else:
                # Sleep briefly if queue is empty to avoid busy-waiting
                time.sleep(0.001)

        # Cleanup device when loop exits
        if self.device:
            self.device.destroy()

    def _send_key_event(self, event: KeyEvent):
        """
        Send a key event to uinput device.

        Args:
            event: KeyEvent containing key_code and action
        """
        if not self.device:
            return

        # Log the event for debugging
        print(f"[uinput] {event.action}: key_code={event.key_code}")

        if event.action == 'press':
            self.device.emit(event.key_code, 1)
        else:  # release
            self.device.emit(event.key_code, 0)

        # Sync event to ensure proper event ordering
        self.device.syn()

    def send_key(self, key_code, pressed=True):
        """
        Queue a key press or release event.

        Args:
            key_code: uinput key code (e.g., uinput.KEY_A)
            pressed: True for press, False for release
        """
        action = 'press' if pressed else 'release'
        event = KeyEvent(key_code=key_code, action=action)

        with self.queue_lock:
            self.event_queue.append(event)

    def cleanup(self):
        """Cleanup and stop the event processing thread."""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
