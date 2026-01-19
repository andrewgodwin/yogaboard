# Yogaboard - Virtual Keyboard for Wayland

A GTK4-based virtual keyboard for Wayland that uses uinput for universal compatibility across all compositors.

## Features

- **Universal Compatibility**: Works on KDE, GNOME, Sway, and any Wayland compositor
- **Multitouch Support**: Hold Shift/Ctrl/Alt with one finger while pressing other keys
- **Layer-Shell Integration**: Appears as a persistent overlay at the bottom of the screen
- **Configurable Layouts**: JSON-based keyboard layouts (currently QWERTY)
- **Clean Design**: Minimal, distraction-free interface

## Requirements

### System Packages (Fedora)
```bash
sudo dnf install gtk4 gtk4-devel gtk4-layer-shell \
    gobject-introspection-devel python3-gobject python3-devel \
    cairo-devel cairo-gobject-devel pkg-config
```

### Python Dependencies
Automatically installed via pip:
- PyGObject >= 3.42
- python-uinput >= 0.11.2

## Installation

### Option 1: Flatpak (Recommended for Fedora Atomic/Immutable Systems)

Build and install as a Flatpak:
```bash
flatpak-builder --user --install --force-clean build-dir org.aeracode.yogaboard.json
```

Then run:
```bash
flatpak run org.aeracode.yogaboard
```

See [FLATPAK.md](FLATPAK.md) for detailed Flatpak build instructions.

### Option 2: Direct Installation (Traditional Systems)

1. Clone or download this repository
2. Install in editable mode:
   ```bash
   pip install -e .
   ```

## Permissions

The keyboard requires access to `/dev/uinput` to send key events. You should already have access if you're in the `input` group or if `/dev/uinput` has appropriate permissions.

To check your access:
```bash
ls -la /dev/uinput
groups
```

If you don't have access, add yourself to the input group:
```bash
sudo usermod -a -G input $USER
```
Then log out and back in.

## Usage

Run the keyboard:
```bash
yogaboard
```

Or run directly from the source:
```bash
python -m yogaboard.main
```

The keyboard will appear at the bottom of your screen as a persistent overlay.

### Multitouch Usage

1. **Normal typing**: Click or tap keys
2. **Shift + letter**: Hold Shift with one finger, tap letter with another
3. **Ctrl + C**: Hold Ctrl with one finger, tap C with another
4. **Multiple modifiers**: Hold Ctrl and Shift together, then press a key

## Customization

### Layouts

Keyboard layouts are defined in `layouts/` as JSON files. The default is `qwerty.json`.

To create a custom layout, copy `qwerty.json` and modify the keys. Each key has:
- `label`: Text displayed on the key
- `key`: uinput key code (e.g., "KEY_A", "KEY_SPACE")
- `width`: Width multiplier (1.0 = standard width)
- `is_modifier`: (optional) true for Shift/Ctrl/Alt keys
- `modifier`: (optional) modifier type ("shift", "ctrl", "alt")

### Styling

Modify `resources/style.css` to change colors, sizes, and appearance.

## Troubleshooting

### "Failed to create uinput device"
- Check permissions: `ls -la /dev/uinput`
- Add yourself to input group: `sudo usermod -a -G input $USER`
- Log out and back in after group changes

### Window not appearing
- Make sure gtk4-layer-shell is installed
- Check: `ldconfig -p | grep layer-shell`
- Install: `sudo dnf install gtk4-layer-shell`

### Keys not working
- Verify the virtual device was created: `cat /proc/bus/input/devices | grep Yogaboard`
- You should see "Yogaboard-Virtual-Keyboard" listed

### Import errors
- Make sure PyGObject is installed: `pip list | grep PyGObject`
- Make sure python-uinput is installed: `pip list | grep uinput`

## Architecture

- **uinput**: Creates a virtual keyboard device at the kernel level
- **GTK4**: Modern toolkit for the user interface
- **gtk4-layer-shell**: Wayland layer-shell protocol for overlay windows
- **Multitouch**: GTK gesture controllers with per-touch state tracking

## License

MIT License - See LICENSE file for details

## Future Enhancements

- Additional layouts (numbers, symbols, emoji)
- Layout switcher button
- Configurable position and size
- Key repeat on long-press
- Visual feedback for key presses
- Auto-hide functionality
- Configuration file for preferences
