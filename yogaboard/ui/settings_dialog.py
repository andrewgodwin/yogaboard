"""Settings dialog for yogaboard configuration."""

from __future__ import annotations

import gi
from typing import TYPE_CHECKING

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

if TYPE_CHECKING:
    from yogaboard.main import KeyboardApp
    from yogaboard.settings import SettingsManager


class SettingsDialog(Gtk.Window):
    """Modal settings dialog for configuring yogaboard."""

    def __init__(self, app: KeyboardApp, settings_manager: SettingsManager):
        super().__init__(title="Yogaboard Settings")
        self.app = app
        self.settings_manager = settings_manager

        # Regular window (not layer-shell) for keyboard focus
        self.set_default_size(400, 300)
        self.set_resizable(False)

        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)

        # Section header
        header = Gtk.Label(label="Touchpad Settings")
        header.add_css_class("title-2")
        header.set_halign(Gtk.Align.START)
        main_box.append(header)

        # Pointer sensitivity
        pointer_row = self._create_scale_row(
            "Pointer Sensitivity",
            min_val=0.5,
            max_val=5.0,
            step=0.1,
            current=settings_manager.touchpad.pointer_sensitivity,
        )
        self.pointer_scale = pointer_row.get_last_child()
        main_box.append(pointer_row)

        # Scroll sensitivity
        scroll_row = self._create_scale_row(
            "Scroll Sensitivity",
            min_val=0.05,
            max_val=0.5,
            step=0.01,
            current=settings_manager.touchpad.scroll_sensitivity,
        )
        self.scroll_scale = scroll_row.get_last_child()
        main_box.append(scroll_row)

        # Tap-and-drag checkbox
        self.tap_drag_check = Gtk.CheckButton(label="Enable tap-and-drag gesture")
        self.tap_drag_check.set_active(settings_manager.touchpad.tap_drag_enabled)
        main_box.append(self.tap_drag_check)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        main_box.append(spacer)

        # Button row
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)

        apply_btn = Gtk.Button(label="Apply")
        apply_btn.connect("clicked", self._on_apply)
        button_box.append(apply_btn)

        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", self._on_close)
        button_box.append(close_btn)

        main_box.append(button_box)
        self.set_child(main_box)

    def _create_scale_row(
        self, label: str, min_val: float, max_val: float, step: float, current: float
    ) -> Gtk.Box:
        """Create a labeled slider row."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        lbl = Gtk.Label(label=label)
        lbl.set_halign(Gtk.Align.START)
        box.append(lbl)

        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, min_val, max_val, step)
        scale.set_value(current)
        scale.set_draw_value(True)
        scale.set_hexpand(True)
        box.append(scale)

        return box

    def _on_apply(self, button):
        """Save settings and notify handlers."""
        settings = self.settings_manager.touchpad

        # Get values from UI
        settings.pointer_sensitivity = self.pointer_scale.get_value()
        settings.scroll_sensitivity = self.scroll_scale.get_value()
        settings.tap_drag_enabled = self.tap_drag_check.get_active()

        # Save to disk
        self.settings_manager.save()

        # Notify handlers of changes
        self.settings_manager.notify_change()

    def _on_close(self, button):
        """Close the dialog."""
        self.close()
