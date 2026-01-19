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

    key_code: tuple[int, int]
    action: Literal["press", "release"]


class UInputKeyboard:
    """Virtual keyboard using Linux uinput subsystem with threaded event processing."""

    # Map of all keyboard keys we want to support (standard 105-key keyboard)
    # Using uinput key codes (KEY_*)
    SUPPORTED_KEYS = [
        # Letters (A-Z)
        uinput.KEY_A,
        uinput.KEY_B,
        uinput.KEY_C,
        uinput.KEY_D,
        uinput.KEY_E,
        uinput.KEY_F,
        uinput.KEY_G,
        uinput.KEY_H,
        uinput.KEY_I,
        uinput.KEY_J,
        uinput.KEY_K,
        uinput.KEY_L,
        uinput.KEY_M,
        uinput.KEY_N,
        uinput.KEY_O,
        uinput.KEY_P,
        uinput.KEY_Q,
        uinput.KEY_R,
        uinput.KEY_S,
        uinput.KEY_T,
        uinput.KEY_U,
        uinput.KEY_V,
        uinput.KEY_W,
        uinput.KEY_X,
        uinput.KEY_Y,
        uinput.KEY_Z,
        # Numbers (0-9)
        uinput.KEY_0,
        uinput.KEY_1,
        uinput.KEY_2,
        uinput.KEY_3,
        uinput.KEY_4,
        uinput.KEY_5,
        uinput.KEY_6,
        uinput.KEY_7,
        uinput.KEY_8,
        uinput.KEY_9,
        # Function keys (F1-F12)
        uinput.KEY_F1,
        uinput.KEY_F2,
        uinput.KEY_F3,
        uinput.KEY_F4,
        uinput.KEY_F5,
        uinput.KEY_F6,
        uinput.KEY_F7,
        uinput.KEY_F8,
        uinput.KEY_F9,
        uinput.KEY_F10,
        uinput.KEY_F11,
        uinput.KEY_F12,
        # Modifiers
        uinput.KEY_LEFTSHIFT,
        uinput.KEY_RIGHTSHIFT,
        uinput.KEY_LEFTCTRL,
        uinput.KEY_RIGHTCTRL,
        uinput.KEY_LEFTALT,
        uinput.KEY_RIGHTALT,
        uinput.KEY_LEFTMETA,
        uinput.KEY_RIGHTMETA,  # Super/Windows key
        # Special keys
        uinput.KEY_SPACE,
        uinput.KEY_ENTER,
        uinput.KEY_BACKSPACE,
        uinput.KEY_TAB,
        uinput.KEY_ESC,
        uinput.KEY_CAPSLOCK,
        # Punctuation and symbols
        uinput.KEY_MINUS,
        uinput.KEY_EQUAL,
        uinput.KEY_LEFTBRACE,
        uinput.KEY_RIGHTBRACE,
        uinput.KEY_SEMICOLON,
        uinput.KEY_APOSTROPHE,
        uinput.KEY_GRAVE,
        uinput.KEY_BACKSLASH,
        uinput.KEY_COMMA,
        uinput.KEY_DOT,
        uinput.KEY_SLASH,
        # Navigation keys
        uinput.KEY_UP,
        uinput.KEY_DOWN,
        uinput.KEY_LEFT,
        uinput.KEY_RIGHT,
        uinput.KEY_HOME,
        uinput.KEY_END,
        uinput.KEY_PAGEUP,
        uinput.KEY_PAGEDOWN,
        uinput.KEY_INSERT,
        uinput.KEY_DELETE,
        # System keys
        uinput.KEY_SYSRQ,
        uinput.KEY_SCROLLLOCK,
        uinput.KEY_PAUSE,
        uinput.KEY_PRINT,
        # Numpad keys
        uinput.KEY_NUMLOCK,
        uinput.KEY_KP0,
        uinput.KEY_KP1,
        uinput.KEY_KP2,
        uinput.KEY_KP3,
        uinput.KEY_KP4,
        uinput.KEY_KP5,
        uinput.KEY_KP6,
        uinput.KEY_KP7,
        uinput.KEY_KP8,
        uinput.KEY_KP9,
        uinput.KEY_KPSLASH,
        uinput.KEY_KPASTERISK,
        uinput.KEY_KPMINUS,
        uinput.KEY_KPPLUS,
        uinput.KEY_KPENTER,
        uinput.KEY_KPDOT,
        # Additional European 105-key specific
        uinput.KEY_102ND,  # The extra key on European keyboards (between left shift and Z)
        # Context menu key (between right Windows and right Ctrl)
        uinput.KEY_COMPOSE,
        # Media control keys
        uinput.KEY_MUTE,
        uinput.KEY_VOLUMEDOWN,
        uinput.KEY_VOLUMEUP,
        uinput.KEY_PLAYPAUSE,
        uinput.KEY_STOPCD,
        uinput.KEY_PREVIOUSSONG,
        uinput.KEY_NEXTSONG,
        uinput.KEY_MEDIA,  # Media player key
        # Display/brightness controls
        uinput.KEY_BRIGHTNESSDOWN,
        uinput.KEY_BRIGHTNESSUP,
        uinput.KEY_DISPLAY_OFF,
        uinput.KEY_SWITCHVIDEOMODE,  # Display toggle (external monitor)
        # Power management
        uinput.KEY_SLEEP,
        uinput.KEY_WAKEUP,
        uinput.KEY_POWER,
        uinput.KEY_SUSPEND,
        # Laptop function keys
        uinput.KEY_BATTERY,
        uinput.KEY_WLAN,  # WiFi toggle
        uinput.KEY_BLUETOOTH,
        uinput.KEY_TOUCHPAD_TOGGLE,
        uinput.KEY_TOUCHPAD_ON,
        uinput.KEY_TOUCHPAD_OFF,
        uinput.KEY_CAMERA,  # Camera toggle
        uinput.KEY_MICMUTE,  # Microphone mute
        # Application shortcuts
        uinput.KEY_MAIL,
        uinput.KEY_HOMEPAGE,
        uinput.KEY_SEARCH,
        uinput.KEY_BOOKMARKS,
        uinput.KEY_BACK,  # Browser back
        uinput.KEY_FORWARD,  # Browser forward
        uinput.KEY_STOP,  # Browser stop
        uinput.KEY_REFRESH,  # Browser refresh
        uinput.KEY_CALC,  # Calculator
        uinput.KEY_FILE,  # File manager
        uinput.KEY_COMPUTER,
        # Screen capture
        uinput.KEY_PRINT,  # Print screen / screenshot
        # Additional F-keys (F13-F24 for extended keyboards)
        uinput.KEY_F13,
        uinput.KEY_F14,
        uinput.KEY_F15,
        uinput.KEY_F16,
        uinput.KEY_F17,
        uinput.KEY_F18,
        uinput.KEY_F19,
        uinput.KEY_F20,
        uinput.KEY_F21,
        uinput.KEY_F22,
        uinput.KEY_F23,
        uinput.KEY_F24,
        # Zoom controls (useful for presentations)
        uinput.KEY_ZOOM,
        uinput.KEY_ZOOMIN,
        uinput.KEY_ZOOMOUT,
        uinput.KEY_ZOOMRESET,
        # Additional useful keys
        uinput.KEY_SCREENSAVER,
        uinput.KEY_COFFEE,  # Screen lock
        uinput.KEY_PROG1,  # Programmable key 1
        uinput.KEY_PROG2,  # Programmable key 2
        uinput.KEY_PROG3,  # Programmable key 3
        uinput.KEY_PROG4,  # Programmable key 4
    ]

    def __init__(self):
        """Initialize virtual keyboard device with threaded event processing."""
        self.event_queue = deque()
        self.queue_lock = threading.Lock()
        self.running = True
        self.device = None

        # Start the uinput thread
        self.thread = threading.Thread(
            target=self._event_loop, daemon=True, name="uinput-worker"
        )
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

        if event.action == "press":
            self.device.emit(event.key_code, 1)
        else:  # release
            self.device.emit(event.key_code, 0)

        # Sync event to ensure proper event ordering
        self.device.syn()

    def send_key(self, key_code: tuple[int, int], pressed=True):
        """
        Queue a key press or release event.

        Args:
            key_code: uinput key code (e.g., uinput.KEY_A)
            pressed: True for press, False for release
        """
        action = "press" if pressed else "release"
        event = KeyEvent(key_code=key_code, action=action)

        with self.queue_lock:
            self.event_queue.append(event)

    def cleanup(self):
        """Cleanup and stop the event processing thread."""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
