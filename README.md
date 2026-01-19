# Yogaboard

This is a touch keyboard that is designed for dual-screen laptops (where the bottom half of the device is also a screen, not a keyboard).

As such, it doesn't have a compact layout like a phone keyboard, but instead has all the buttons, and mode-switching so it can grow and shrink to use more or less of the screen.

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
