"""Virtual multi-touch touchpad device using Linux uinput subsystem."""

import time
import threading
from collections import deque
from dataclasses import dataclass
from typing import Literal
import ctypes
import os
import struct
import fcntl

# Linux input event codes
EV_SYN = 0x00
EV_KEY = 0x01
EV_ABS = 0x03

SYN_REPORT = 0x00

# Button codes
BTN_TOUCH = 0x14A
BTN_TOOL_FINGER = 0x145
BTN_TOOL_DOUBLETAP = 0x14D
BTN_TOOL_TRIPLETAP = 0x14E
BTN_TOOL_QUADTAP = 0x14F
BTN_LEFT = 0x110
BTN_RIGHT = 0x111
BTN_MIDDLE = 0x112

# Absolute axis codes
ABS_MT_SLOT = 0x2F
ABS_MT_TRACKING_ID = 0x39
ABS_MT_POSITION_X = 0x35
ABS_MT_POSITION_Y = 0x36

# Input properties
INPUT_PROP_POINTER = 0x00
INPUT_PROP_DIRECT = 0x01
INPUT_PROP_BUTTONPAD = 0x02

# uinput ioctl codes
UINPUT_IOCTL_BASE = ord("U")
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_SET_ABSBIT = 0x40045567
UI_SET_PROPBIT = 0x4004556E

# Struct formats
INPUT_EVENT_FORMAT = "llHHi"  # timeval (long, long), type, code, value
INPUT_EVENT_SIZE = struct.calcsize(INPUT_EVENT_FORMAT)

# uinput_user_dev structure for older API
UINPUT_MAX_NAME_SIZE = 80


@dataclass
class TouchEvent:
    """Represents a touch event to send."""

    event_type: Literal["down", "move", "up", "sync", "finger_count", "button"]
    slot: int = 0
    tracking_id: int = 0
    x: int = 0
    y: int = 0
    finger_count: int = 0
    button: int = 0
    pressed: bool = False


class UInputTouchpad:
    """Virtual multi-touch touchpad using Linux uinput subsystem."""

    MAX_SLOTS = 10  # Support up to 10 simultaneous touches
    DEVICE_MAX_X = 500
    DEVICE_MAX_Y = 500

    def __init__(self):
        """Initialize virtual multi-touch touchpad device."""
        self.event_queue = deque()
        self.queue_lock = threading.Lock()
        self.running = True
        self.fd = None
        self._current_slot = 0
        self._active_slots = set()

        # Start the uinput thread
        self.thread = threading.Thread(
            target=self._event_loop, daemon=True, name="uinput-touchpad-worker"
        )
        self.thread.start()

    def _event_loop(self):
        """Main event loop running in separate thread."""
        try:
            self._create_device()
            # Small delay for device registration
            time.sleep(0.1)
        except Exception as e:
            print(f"Failed to create uinput touchpad device: {e}")
            print("Make sure you have permissions to access /dev/uinput")
            self.running = False
            return

        # Process events from queue
        while self.running:
            event = None

            with self.queue_lock:
                if self.event_queue:
                    event = self.event_queue.popleft()

            if event:
                try:
                    self._send_event(event)
                except Exception as e:
                    print(f"Error sending touchpad event: {e}")
            else:
                time.sleep(0.001)

        # Cleanup device when loop exits
        self._destroy_device()

    def _create_device(self):
        """Create the uinput multi-touch device."""
        self.fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)

        # Enable event types
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_KEY)
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_ABS)
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_SYN)

        # Enable buttons
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, BTN_TOUCH)
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, BTN_TOOL_FINGER)
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, BTN_TOOL_DOUBLETAP)
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, BTN_TOOL_TRIPLETAP)
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, BTN_TOOL_QUADTAP)
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, BTN_LEFT)
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, BTN_RIGHT)
        fcntl.ioctl(self.fd, UI_SET_KEYBIT, BTN_MIDDLE)

        # Enable MT axes
        fcntl.ioctl(self.fd, UI_SET_ABSBIT, ABS_MT_SLOT)
        fcntl.ioctl(self.fd, UI_SET_ABSBIT, ABS_MT_TRACKING_ID)
        fcntl.ioctl(self.fd, UI_SET_ABSBIT, ABS_MT_POSITION_X)
        fcntl.ioctl(self.fd, UI_SET_ABSBIT, ABS_MT_POSITION_Y)

        # Set input properties to identify as touchpad
        fcntl.ioctl(self.fd, UI_SET_PROPBIT, INPUT_PROP_POINTER)
        fcntl.ioctl(self.fd, UI_SET_PROPBIT, INPUT_PROP_BUTTONPAD)

        # Create uinput_user_dev structure
        # Format: name[80], id{bustype, vendor, product, version}, ff_effects_max, absmax[64], absmin[64], absfuzz[64], absflat[64]
        name = b"Yogaboard-Virtual-Touchpad"
        name = name.ljust(UINPUT_MAX_NAME_SIZE, b"\x00")

        # Input ID: bus=0x03 (USB), vendor=0x1234, product=0x5678, version=1
        input_id = struct.pack("HHHH", 0x03, 0x1234, 0x5678, 1)

        # ff_effects_max
        ff_effects = struct.pack("I", 0)

        # ABS arrays (64 entries each for absmax, absmin, absfuzz, absflat)
        absmax = [0] * 64
        absmin = [0] * 64
        absfuzz = [0] * 64
        absflat = [0] * 64

        # Set MT axis ranges
        absmax[ABS_MT_SLOT] = self.MAX_SLOTS - 1
        absmax[ABS_MT_TRACKING_ID] = 65535
        absmax[ABS_MT_POSITION_X] = self.DEVICE_MAX_X
        absmax[ABS_MT_POSITION_Y] = self.DEVICE_MAX_Y

        absmax_data = struct.pack("64i", *absmax)
        absmin_data = struct.pack("64i", *absmin)
        absfuzz_data = struct.pack("64i", *absfuzz)
        absflat_data = struct.pack("64i", *absflat)

        uinput_user_dev = name + input_id + ff_effects + absmax_data + absmin_data + absfuzz_data + absflat_data
        os.write(self.fd, uinput_user_dev)

        # Create the device
        fcntl.ioctl(self.fd, UI_DEV_CREATE)

    def _destroy_device(self):
        """Destroy the uinput device."""
        if self.fd is not None:
            try:
                fcntl.ioctl(self.fd, UI_DEV_DESTROY)
                os.close(self.fd)
            except Exception:
                pass
            self.fd = None

    def _write_event(self, ev_type: int, code: int, value: int):
        """Write a single input event."""
        if self.fd is None:
            return
        tv_sec = int(time.time())
        tv_usec = int((time.time() % 1) * 1000000)
        event = struct.pack(INPUT_EVENT_FORMAT, tv_sec, tv_usec, ev_type, code, value)
        os.write(self.fd, event)

    def _send_event(self, event: TouchEvent):
        """Send a touch event to uinput device."""
        if self.fd is None:
            return

        if event.event_type == "down":
            # Select slot
            if self._current_slot != event.slot:
                self._write_event(EV_ABS, ABS_MT_SLOT, event.slot)
                self._current_slot = event.slot
            # Set tracking ID and position
            self._write_event(EV_ABS, ABS_MT_TRACKING_ID, event.tracking_id)
            self._write_event(EV_ABS, ABS_MT_POSITION_X, event.x)
            self._write_event(EV_ABS, ABS_MT_POSITION_Y, event.y)
            self._active_slots.add(event.slot)

        elif event.event_type == "move":
            # Select slot
            if self._current_slot != event.slot:
                self._write_event(EV_ABS, ABS_MT_SLOT, event.slot)
                self._current_slot = event.slot
            # Update position
            self._write_event(EV_ABS, ABS_MT_POSITION_X, event.x)
            self._write_event(EV_ABS, ABS_MT_POSITION_Y, event.y)

        elif event.event_type == "up":
            # Select slot
            if self._current_slot != event.slot:
                self._write_event(EV_ABS, ABS_MT_SLOT, event.slot)
                self._current_slot = event.slot
            # Release: tracking_id = -1
            self._write_event(EV_ABS, ABS_MT_TRACKING_ID, -1)
            self._active_slots.discard(event.slot)

        elif event.event_type == "finger_count":
            # Update BTN_TOUCH and BTN_TOOL_* based on finger count
            count = event.finger_count
            self._write_event(EV_KEY, BTN_TOUCH, 1 if count > 0 else 0)
            self._write_event(EV_KEY, BTN_TOOL_FINGER, 1 if count == 1 else 0)
            self._write_event(EV_KEY, BTN_TOOL_DOUBLETAP, 1 if count == 2 else 0)
            self._write_event(EV_KEY, BTN_TOOL_TRIPLETAP, 1 if count == 3 else 0)
            self._write_event(EV_KEY, BTN_TOOL_QUADTAP, 1 if count >= 4 else 0)

        elif event.event_type == "button":
            self._write_event(EV_KEY, event.button, 1 if event.pressed else 0)

        elif event.event_type == "sync":
            self._write_event(EV_SYN, SYN_REPORT, 0)

    def touch_down(self, slot: int, tracking_id: int, x: int, y: int):
        """Queue a finger touch down event."""
        event = TouchEvent(event_type="down", slot=slot, tracking_id=tracking_id, x=x, y=y)
        with self.queue_lock:
            self.event_queue.append(event)

    def touch_move(self, slot: int, x: int, y: int):
        """Queue a finger move event."""
        event = TouchEvent(event_type="move", slot=slot, x=x, y=y)
        with self.queue_lock:
            self.event_queue.append(event)

    def touch_up(self, slot: int):
        """Queue a finger lift event."""
        event = TouchEvent(event_type="up", slot=slot)
        with self.queue_lock:
            self.event_queue.append(event)

    def set_finger_count(self, count: int):
        """Queue finger count update (BTN_TOUCH, BTN_TOOL_*)."""
        event = TouchEvent(event_type="finger_count", finger_count=count)
        with self.queue_lock:
            self.event_queue.append(event)

    def sync(self):
        """Queue a sync event to commit pending events."""
        event = TouchEvent(event_type="sync")
        with self.queue_lock:
            self.event_queue.append(event)

    BUTTON_MAP = {
        "left": BTN_LEFT,
        "right": BTN_RIGHT,
        "middle": BTN_MIDDLE,
    }

    def click(self, button: str, pressed: bool):
        """Queue a button press or release event."""
        button_code = self.BUTTON_MAP.get(button)
        if button_code:
            event = TouchEvent(event_type="button", button=button_code, pressed=pressed)
            with self.queue_lock:
                self.event_queue.append(event)

    def tap(self, button: str):
        """Queue a quick tap (press + release)."""
        self.click(button, pressed=True)
        self.sync()
        self.click(button, pressed=False)
        self.sync()

    def cleanup(self):
        """Cleanup and stop the event processing thread."""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
