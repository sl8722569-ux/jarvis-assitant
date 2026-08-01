"""Load and save JARVIS configuration (local config.json; example as fallback)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


class Config:
    """Runtime config. Prefer config.json; bootstrap from config.example.json if missing."""

    def __init__(self, root: Path):
        self.root = root
        self.path = root / "config.json"
        self.example = root / "config.example.json"
        self.data: dict[str, Any] = {}
        self._ensure_config()
        self.reload()

    def _ensure_config(self) -> None:
        if not self.path.exists() and self.example.exists():
            shutil.copy2(self.example, self.path)

    def reload(self) -> None:
        path = self.path if self.path.exists() else self.example
        with open(path, encoding="utf-8") as f:
            self.data = json.load(f)

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()
