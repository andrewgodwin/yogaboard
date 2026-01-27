# Yogaboard

This is a touch keyboard that is designed for dual-screen laptops (where the bottom half of the device is also a screen, not a keyboard).

As such, it doesn't have a compact layout like a phone keyboard, but instead has all the buttons, and mode-switching so it can grow and shrink to use more or less of the screen, as well as a virtual touchpad in some of the modes.

It **requires a Wayland compositor that supports `layer-shell`**, which basically means "it'll work on almost anything except GNOME".

## Installation

I find it easiest to do it via Flatpak's build system:
```bash
make build && make install
```

## Permissions

The keyboard requires access to `/dev/uinput` to send key events. You should already have access if you're in the `input` group or if `/dev/uinput` has appropriate permissions.

If you don't have access, add yourself to the input group:
```bash
sudo usermod -a -G input $USER
```
Then log out and back in.

## Dev Notes

The keyboard emulates a normal keyboard using uinput, including the held state of all keys, so you can hold down Ctrl and left-click with a mouse to open a new tab, for example.

The touchpad actually emulates a relative mouse (trackball), as emulating a proper multitouch touchpad will confuse the compositor (as we can't cancel the first set of touch events). This means that gestures like two-finger scrolling and double-tap-drag are implemented in yogaboard and sent over as mouse button events.

There is a potential workaround to this by disabling the bottom screen from being listened to by the compositor entirely while the keyboard is up, but that results in far more complex code, and what is there now works well enough.
