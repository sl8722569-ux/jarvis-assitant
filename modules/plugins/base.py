"""Plugin base + manager (lightweight, no auto-load heavy deps)."""
from __future__ import annotations

from typing import Callable


class Plugin:
    id: str = "base"
    name: str = "Base"
    description: str = ""

    def handle(self, text: str) -> str | None:
        """Return reply if this plugin handles the text, else None."""
        return None


class PluginManager:
    def __init__(self):
        self.plugins: list[Plugin] = []

    def register(self, plugin: Plugin) -> None:
        self.plugins.append(plugin)

    def list_plugins(self) -> str:
        if not self.plugins:
            return "No plugins loaded."
        lines = ["Installed plugins:"]
        for p in self.plugins:
            lines.append(f"  • {p.name} ({p.id}) — {p.description}")
        return "\n".join(lines)

    def try_handle(self, text: str) -> str | None:
        for p in self.plugins:
            try:
                out = p.handle(text)
                if out:
                    return out
            except Exception as e:
                return f"Plugin {p.id} error: {e}"
        return None
