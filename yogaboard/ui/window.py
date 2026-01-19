"""GTK4 window with layer-shell integration for Wayland overlay."""

from ctypes import CDLL

# Must load layer-shell before importing GTK
CDLL("libgtk4-layer-shell.so.0")

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gtk4LayerShell as LayerShell


class KeyboardWindow(Gtk.ApplicationWindow):
    """Main window for the virtual keyboard using layer-shell."""

    def __init__(self, app):
        super().__init__(application=app)
        self.app = app

        # Initialize layer-shell for Wayland overlay
        LayerShell.init_for_window(self)
        LayerShell.set_layer(self, LayerShell.Layer.OVERLAY)

        # Position at bottom of screen
        LayerShell.set_anchor(self, LayerShell.Edge.BOTTOM, True)
        LayerShell.set_anchor(self, LayerShell.Edge.LEFT, True)
        LayerShell.set_anchor(self, LayerShell.Edge.RIGHT, True)

        # Reserve space (exclusive zone) so windows don't overlap keyboard
        LayerShell.auto_exclusive_zone_enable(self)

        # Don't accept keyboard focus - this is critical for virtual keyboards
        # so that touching keys doesn't steal focus from the target application
        LayerShell.set_keyboard_mode(self, LayerShell.KeyboardMode.NONE)

        # Set window size
        self.set_default_size(-1, 400)

        # Create overlay container for close button
        self.overlay = Gtk.Overlay()
        super().set_child(self.overlay)

        # Create close button with diagonal X symbol
        self.close_button = Gtk.Button(label="✕")
        self.close_button.set_halign(Gtk.Align.END)
        self.close_button.set_valign(Gtk.Align.START)
        self.close_button.set_margin_top(10)
        self.close_button.set_margin_end(10)
        self.close_button.add_css_class("close-button")
        self.close_button.connect("clicked", self._on_close_clicked)
        self.overlay.add_overlay(self.close_button)

    def _on_close_clicked(self, button):
        """Handle close button click."""
        self.app.quit()

    def set_child(self, child):
        """Override set_child to place content in overlay."""
        self.overlay.set_child(child)
