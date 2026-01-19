"""Main application entry point for yogaboard virtual keyboard."""

from ctypes import CDLL

# Must load layer-shell before importing GTK
CDLL("libgtk4-layer-shell.so.0")

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gio

from yogaboard.ui.window import KeyboardWindow
from yogaboard.ui.keyboard_widget import KeyboardWidget
from yogaboard.layout.parser import LayoutParser
from yogaboard.input_device.uinput_keyboard import UInputKeyboard
from yogaboard.input.touch_handler import TouchHandler
from yogaboard.input.modifier_state import ModifierState
import os


class KeyboardApp(Gtk.Application):
    """Main GTK application for yogaboard virtual keyboard."""

    MODE_KEYBOARD = "keyboard"
    MODE_SLIM = "slim"

    def __init__(self):
        super().__init__(application_id="org.aeracode.yogaboard")
        self.current_mode = self.MODE_KEYBOARD
        self.keyboard_widget = None

    def do_activate(self):
        """Initialize and show the virtual keyboard."""
        try:
            # Initialize uinput virtual keyboard
            self.uinput_keyboard = UInputKeyboard()

            # Load both layouts
            qwerty_layout_path = os.path.join(
                os.path.dirname(__file__), "../layouts/qwerty.json"
            )
            slim_layout_path = os.path.join(
                os.path.dirname(__file__), "../layouts/slim.json"
            )
            qwerty_layout = LayoutParser.load(qwerty_layout_path)
            slim_layout = LayoutParser.load(slim_layout_path)

            self.layouts = {
                self.MODE_KEYBOARD: qwerty_layout,
                self.MODE_SLIM: slim_layout
            }

            # Create main window
            self.window = KeyboardWindow(self)

            # Setup touch handling with app reference
            self.touch_handler = TouchHandler(self.uinput_keyboard, app=self)

            # Load CSS styling
            css_provider = Gtk.CssProvider()
            css_path = os.path.join(os.path.dirname(__file__), "../resources/style.css")
            css_provider.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_display(
                self.window.get_display(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

            # Start in keyboard mode
            self.switch_to_layout(self.MODE_KEYBOARD)

            self.window.present()

        except Exception as e:
            print(f"Error starting yogaboard: {e}")
            import traceback

            traceback.print_exc()
            self.quit()

    def toggle_mode(self):
        """Switch between keyboard and slim modes."""
        if self.current_mode == self.MODE_KEYBOARD:
            self.switch_to_layout(self.MODE_SLIM)
        else:
            self.switch_to_layout(self.MODE_KEYBOARD)

    def switch_to_layout(self, mode):
        """Switch to a specific layout mode."""
        self.current_mode = mode
        layout = self.layouts[mode]

        # Use window height from layout, or fallback to 400px
        height = layout.window_height if layout.window_height else 400

        # Update window height
        self.window.set_default_size(-1, height)

        # Swap keyboard widget
        if self.keyboard_widget:
            self.window.set_child(None)

        self.keyboard_widget = KeyboardWidget(layout)
        self.window.set_child(self.keyboard_widget)

        # Re-setup touch handlers
        self.touch_handler.setup_gestures(self.keyboard_widget)

    def do_shutdown(self):
        """Cleanup when application is closing."""
        if hasattr(self, "touch_handler"):
            self.touch_handler.cleanup()
        if hasattr(self, "uinput_keyboard"):
            self.uinput_keyboard.cleanup()
        Gtk.Application.do_shutdown(self)


def main():
    """Main entry point for the application."""
    app = KeyboardApp()
    return app.run(None)


if __name__ == "__main__":
    main()
