"""Virtual touchpad device using Linux uinput subsystem."""

import uinput
import time
import threading
from collections import deque
from dataclasses import dataclass
from typing import Literal


@dataclass
class TouchpadEvent:
    """Represents a touchpad event."""

    event_type: Literal["move", "scroll", "click"]
    # For move/scroll: dx, dy values
    # For click: button name and pressed state
    dx: int = 0
    dy: int = 0
    button: str = ""
    pressed: bool = False


class UInputTouchpad:
    """Virtual touchpad using Linux uinput subsystem with threaded event processing."""

    SUPPORTED_EVENTS = [
        uinput.REL_X,  # Pointer X motion
        uinput.REL_Y,  # Pointer Y motion
        uinput.REL_WHEEL,  # Vertical scroll
        uinput.REL_HWHEEL,  # Horizontal scroll
        uinput.BTN_LEFT,  # Left click
        uinput.BTN_RIGHT,  # Right click
        uinput.BTN_MIDDLE,  # Middle click
    ]

    BUTTON_MAP = {
        "left": uinput.BTN_LEFT,
        "right": uinput.BTN_RIGHT,
        "middle": uinput.BTN_MIDDLE,
    }

    def __init__(self):
        """Initialize virtual touchpad device with threaded event processing."""
        self.event_queue = deque()
        self.queue_lock = threading.Lock()
        self.running = True
        self.device = None

        # Start the uinput thread
        self.thread = threading.Thread(
            target=self._event_loop, daemon=True, name="uinput-touchpad-worker"
        )
        self.thread.start()

    def _event_loop(self):
        """Main event loop running in separate thread."""
        try:
            # Create uinput device with touchpad capabilities
            self.device = uinput.Device(
                self.SUPPORTED_EVENTS,
                name="Yogaboard-Virtual-Touchpad",
            )

            # Small delay for device registration
            time.sleep(0.1)

        except Exception as e:
            print(f"Failed to create uinput touchpad device: {e}")
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
                    self._send_event(event)
                except Exception as e:
                    print(f"Error sending touchpad event: {e}")
            else:
                # Sleep briefly if queue is empty to avoid busy-waiting
                time.sleep(0.001)

        # Cleanup device when loop exits
        if self.device:
            self.device.destroy()

    def _send_event(self, event: TouchpadEvent):
        """Send a touchpad event to uinput device."""
        if not self.device:
            return

        if event.event_type == "move":
            if event.dx != 0:
                self.device.emit(uinput.REL_X, event.dx)
            if event.dy != 0:
                self.device.emit(uinput.REL_Y, event.dy)
        elif event.event_type == "scroll":
            # Natural scrolling: finger up = content up (positive wheel value)
            if event.dy != 0:
                self.device.emit(uinput.REL_WHEEL, event.dy)
            if event.dx != 0:
                self.device.emit(uinput.REL_HWHEEL, event.dx)
        elif event.event_type == "click":
            button_code = self.BUTTON_MAP.get(event.button)
            if button_code:
                self.device.emit(button_code, 1 if event.pressed else 0)

        self.device.syn()

    def move_pointer(self, dx: int, dy: int):
        """
        Queue pointer motion event.

        Args:
            dx: Horizontal movement (positive = right)
            dy: Vertical movement (positive = down)
        """
        if dx == 0 and dy == 0:
            return
        event = TouchpadEvent(event_type="move", dx=dx, dy=dy)
        with self.queue_lock:
            self.event_queue.append(event)

    def scroll(self, dx: int, dy: int):
        """
        Queue scroll event with natural scrolling.

        Args:
            dx: Horizontal scroll (positive = right)
            dy: Vertical scroll (positive = up, natural scrolling)
        """
        if dx == 0 and dy == 0:
            return
        event = TouchpadEvent(event_type="scroll", dx=dx, dy=dy)
        with self.queue_lock:
            self.event_queue.append(event)

    def click(self, button: str, pressed: bool):
        """
        Queue a button press or release event.

        Args:
            button: "left", "right", or "middle"
            pressed: True for press, False for release
        """
        event = TouchpadEvent(event_type="click", button=button, pressed=pressed)
        with self.queue_lock:
            self.event_queue.append(event)

    def tap(self, button: str):
        """
        Queue a quick tap (press + release).

        Args:
            button: "left", "right", or "middle"
        """
        self.click(button, pressed=True)
        self.click(button, pressed=False)

    def cleanup(self):
        """Cleanup and stop the event processing thread."""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
