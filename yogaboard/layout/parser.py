"""Layout parser for JSON keyboard layout files."""

import json
import uinput
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Key:
    """Represents a single key on the keyboard."""

    label: str
    key: str  # uinput key name (e.g., "KEY_A")
    width: float = 1.0
    is_modifier: bool = False
    modifier: Optional[str] = None

    def get_uinput_key(self):
        """Convert key name string to uinput constant (key code only)."""
        key_tuple = getattr(uinput, self.key)
        # uinput keys are tuples like (EV_KEY, KEY_CODE)
        # We only need the key code (second element)
        if isinstance(key_tuple, tuple):
            return key_tuple[1]
        return key_tuple


@dataclass
class Row:
    """Represents a row of keys."""

    keys: List[Key]


@dataclass
class Layout:
    """Represents a complete keyboard layout."""

    name: str
    rows: List[Row]


class LayoutParser:
    """Parser for JSON keyboard layout files."""

    @staticmethod
    def load(filepath: str) -> Layout:
        """
        Load a keyboard layout from a JSON file.

        Args:
            filepath: Path to the JSON layout file

        Returns:
            Layout object containing all keyboard configuration
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        rows = []
        for row_data in data["rows"]:
            keys = [Key(**key_data) for key_data in row_data["keys"]]
            rows.append(Row(keys=keys))

        return Layout(name=data["name"], rows=rows)
