"""Tracks where the physical keyboard is, using the yoga-keyboard daemon."""

import fcntl
import glob
import os
from typing import Callable

from gi.repository import GLib


def _ior(nr: int, size: int) -> int:
    """Build the number of a read ioctl on an evdev device."""
    return (2 << 30) | (size << 16) | (ord("E") << 8) | nr


NAME_SIZE = 256
EVIOCGNAME = _ior(0x06, NAME_SIZE)
ABS_MISC = 0x28
ABS_INFO_SIZE = 24
EVIOCGABS_MISC = _ior(0x40 + ABS_MISC, ABS_INFO_SIZE)
INPUT_EVENT_SIZE = 24


class KeyboardPositionMonitor:
    """Calls back on the GTK main loop when the physical keyboard moves.

    The daemon may start after us or restart, so if the device is missing we
    keep looking for it. The current value is always read from the kernel
    rather than from the events, which means dropped events can't confuse us.
    """

    DEVICE_NAME = "Yoga Keyboard Position"
    RETRY_SECONDS = 5

    POSITION_OFF = 0
    POSITION_HINGE = 1
    POSITION_FAR = 2

    def __init__(self, callback: Callable[[int], None]):
        self.callback = callback
        self.position = None
        self.fd = None
        self.watch_id = None
        self.retry_id = None

    def start(self):
        """Report the current position, and then watch for changes."""
        if not self._connect():
            self.retry_id = GLib.timeout_add_seconds(self.RETRY_SECONDS, self._retry)

    def cleanup(self):
        """Stop watching for changes."""
        if self.retry_id is not None:
            GLib.source_remove(self.retry_id)
            self.retry_id = None
        self._disconnect()

    def _find_device(self) -> int | None:
        """Return an open fd for the position device, if it's there."""
        for path in glob.glob("/dev/input/event*"):
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            except OSError:
                # We only have access to some of the input devices
                continue
            try:
                name = bytearray(NAME_SIZE)
                fcntl.ioctl(fd, EVIOCGNAME, name)
                if name.split(b"\0")[0].decode(errors="replace") == self.DEVICE_NAME:
                    return fd
            except OSError:
                pass
            os.close(fd)
        return None

    def _connect(self) -> bool:
        self.fd = self._find_device()
        if self.fd is None:
            return False
        self.watch_id = GLib.io_add_watch(
            self.fd,
            GLib.PRIORITY_DEFAULT,
            GLib.IO_IN | GLib.IO_HUP | GLib.IO_ERR,
            self._on_event,
        )
        self._update_position()
        return True

    def _disconnect(self):
        if self.watch_id is not None:
            GLib.source_remove(self.watch_id)
            self.watch_id = None
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def _retry(self) -> bool:
        if self._connect():
            self.retry_id = None
            return GLib.SOURCE_REMOVE
        return GLib.SOURCE_CONTINUE

    def _on_event(self, _fd, _condition) -> bool:
        try:
            # The events only tell us to look, so discard them
            os.read(self.fd, INPUT_EVENT_SIZE * 64)
            self._update_position()
        except BlockingIOError:
            pass
        except OSError:
            # The device is gone, so the daemon has stopped
            self.watch_id = None
            self._disconnect()
            self.retry_id = GLib.timeout_add_seconds(self.RETRY_SECONDS, self._retry)
            return GLib.SOURCE_REMOVE
        return GLib.SOURCE_CONTINUE

    def _update_position(self):
        info = bytearray(ABS_INFO_SIZE)
        fcntl.ioctl(self.fd, EVIOCGABS_MISC, info)
        # The first field of input_absinfo is the current value
        position = int.from_bytes(info[:4], "little", signed=True)
        if position != self.position:
            self.position = position
            self.callback(position)
