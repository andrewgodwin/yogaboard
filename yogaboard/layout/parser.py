"""Layout parser for JSON keyboard layout files."""

import json
import uinput
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SplitKey:
    """Represents one half of a split key."""

    label: str
    key: str  # uinput key name (e.g., "KEY_UP")

    def get_uinput_key(self) -> tuple[int, int]:
        return getattr(uinput, self.key)


@dataclass
class Key:
    """Represents a single key on the keyboard."""

    label: str
    key: str  # uinput key name (e.g., "KEY_A")
    width: float = 1.0
    classes: list[str] = field(default_factory=list)
    modifier: Optional[str] = None
    secondary_label: Optional[str] = None
    # Split key support: if both are set, key is rendered as top/bottom split
    top_key: Optional[SplitKey] = None
    bottom_key: Optional[SplitKey] = None

    def is_split(self) -> bool:
        """Return True if this is a vertically split key."""
        return self.top_key is not None and self.bottom_key is not None

    def get_uinput_key(self) -> tuple[int, int]:
        return getattr(uinput, self.key)


@dataclass
class Row:
    """Represents a row of keys."""

    keys: List[Key]
    height: int = 100


@dataclass
class Layout:
    """Represents a complete keyboard layout."""

    name: str
    rows: List[Row]
    window_height: Optional[int] = None


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
            keys = []
            for key_data in row_data["keys"]:
                # Parse nested SplitKey objects if present
                if "top_key" in key_data and key_data["top_key"] is not None:
                    key_data["top_key"] = SplitKey(**key_data["top_key"])
                if "bottom_key" in key_data and key_data["bottom_key"] is not None:
                    key_data["bottom_key"] = SplitKey(**key_data["bottom_key"])
                keys.append(Key(**key_data))
            del row_data["keys"]
            rows.append(Row(keys=keys, **row_data))

        return Layout(
            name=data["name"], rows=rows, window_height=data.get("window_height")
        )
