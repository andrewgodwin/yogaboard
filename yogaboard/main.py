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

    def __init__(self):
        super().__init__(application_id="org.aeracode.yogaboard")

    def do_activate(self):
        """Initialize and show the virtual keyboard."""
        try:
            # Initialize uinput virtual keyboard
            self.uinput_keyboard = UInputKeyboard()

            # Load layout
            layout_path = os.path.join(
                os.path.dirname(__file__), "../layouts/qwerty.json"
            )
            layout = LayoutParser.load(layout_path)

            # Create main window
            window = KeyboardWindow(self)

            # Create keyboard widget
            keyboard = KeyboardWidget(layout)
            window.set_child(keyboard)

            # Setup touch handling
            self.touch_handler = TouchHandler(self.uinput_keyboard)
            self.touch_handler.setup_gestures(keyboard)

            # Load CSS styling
            css_provider = Gtk.CssProvider()
            css_path = os.path.join(os.path.dirname(__file__), "../resources/style.css")
            css_provider.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_display(
                window.get_display(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

            window.present()

        except Exception as e:
            print(f"Error starting yogaboard: {e}")
            import traceback

            traceback.print_exc()
            self.quit()

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
