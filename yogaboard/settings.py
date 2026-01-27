"""Settings management for yogaboard."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Callable


@dataclass
class TouchpadSettings:
    """Touchpad-related settings."""

    pointer_sensitivity: float = 2.0
    scroll_sensitivity: float = 0.15
    tap_drag_enabled: bool = True
    tap_drag_window: float = 0.25


@dataclass
class AppearanceSettings:
    """Appearance-related settings."""

    color_scheme: str = "default"


class SettingsManager:
    """Handles loading, saving, and accessing application settings."""

    CONFIG_DIR = "yogaboard"
    CONFIG_FILE = "settings.json"

    def __init__(self):
        self.touchpad = TouchpadSettings()
        self.appearance = AppearanceSettings()
        self._config_path: str | None = None
        self._callbacks: list[Callable[[SettingsManager], None]] = []

    def get_config_path(self) -> str:
        """Get XDG-compliant config file path."""
        if self._config_path is None:
            xdg_config = os.environ.get(
                "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
            )
            config_dir = os.path.join(xdg_config, self.CONFIG_DIR)
            self._config_path = os.path.join(config_dir, self.CONFIG_FILE)
        return self._config_path

    def load(self):
        """Load settings from disk, using defaults for missing values."""
        config_path = self.get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                if "touchpad" in data:
                    # Only update fields that exist in the file
                    for key, value in data["touchpad"].items():
                        if hasattr(self.touchpad, key):
                            setattr(self.touchpad, key, value)
                if "appearance" in data:
                    for key, value in data["appearance"].items():
                        if hasattr(self.appearance, key):
                            setattr(self.appearance, key, value)
            except (json.JSONDecodeError, IOError):
                # Use defaults on error
                pass

    def save(self):
        """Save current settings to disk."""
        config_path = self.get_config_path()
        config_dir = os.path.dirname(config_path)
        os.makedirs(config_dir, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump({
                "touchpad": asdict(self.touchpad),
                "appearance": asdict(self.appearance),
            }, f, indent=2)

    def add_change_callback(self, callback: Callable[[SettingsManager], None]):
        """Register a callback for settings changes."""
        self._callbacks.append(callback)

    def notify_change(self):
        """Notify all observers that settings changed."""
        for callback in self._callbacks:
            callback(self)

    def get_available_themes(self) -> list[tuple[str, str]]:
        """Return list of (theme_id, display_name) tuples."""
        return [
            ("default", "Default"),
            ("dark", "Dark"),
        ]
