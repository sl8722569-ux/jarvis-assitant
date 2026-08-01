"""Free lightweight theme packs for JARVIS UI."""
from __future__ import annotations

from typing import Any


THEMES: dict[str, dict[str, Any]] = {
    "midnight_hud": {
        "label": "Midnight HUD",
        "bg": "#05080f",
        "panel": "#0a1220",
        "sidebar": "#071018",
        "accent": "#5ce1ff",
        "accent2": "#9ef01a",
        "text": "#d7e6f5",
        "muted": "#6a7a8a",
        "button": "#0b3d5c",
        "danger": "#3a1a1a",
        "chat_bg": "#0a1220",
        "entry_bg": "#0d1520",
        "avatar": "orb",
        "effect": "hud",
    },
    "ember_core": {
        "label": "Ember Core",
        "bg": "#120808",
        "panel": "#1a0e0e",
        "sidebar": "#140a0a",
        "accent": "#ff6b4a",
        "accent2": "#ffd166",
        "text": "#f5e6e0",
        "muted": "#8a6a6a",
        "button": "#5c1b0b",
        "danger": "#3a1010",
        "chat_bg": "#1a0e0e",
        "entry_bg": "#221212",
        "avatar": "robot",
        "effect": "heartbeat",
    },
    "forest_soft": {
        "label": "Forest Soft",
        "bg": "#07140f",
        "panel": "#0c1c16",
        "sidebar": "#091510",
        "accent": "#5ddea0",
        "accent2": "#c8facc",
        "text": "#e0f5ea",
        "muted": "#6a8a7a",
        "button": "#0b3d2c",
        "danger": "#1a2a1a",
        "chat_bg": "#0c1c16",
        "entry_bg": "#10241c",
        "avatar": "orb",
        "effect": "waveform",
    },
    "arctic_glass": {
        "label": "Arctic Glass",
        "bg": "#0a1018",
        "panel": "#121a26",
        "sidebar": "#0e1520",
        "accent": "#a8c7ff",
        "accent2": "#e8f0ff",
        "text": "#e8eef8",
        "muted": "#7a8aa0",
        "button": "#243a5c",
        "danger": "#1a2030",
        "chat_bg": "#121a26",
        "entry_bg": "#182232",
        "avatar": "orb",
        "effect": "hud",
    },
    "neon_play": {
        "label": "Neon Play",
        "bg": "#0b0614",
        "panel": "#140a22",
        "sidebar": "#10081c",
        "accent": "#d946ef",
        "accent2": "#22d3ee",
        "text": "#f5e8ff",
        "muted": "#8a7a9a",
        "button": "#4a0b5c",
        "danger": "#2a1030",
        "chat_bg": "#140a22",
        "entry_bg": "#1c1030",
        "avatar": "robot",
        "effect": "waveform",
    },
}


def get_theme(name: str) -> dict[str, Any]:
    return dict(THEMES.get(name) or THEMES["midnight_hud"])


def list_themes() -> str:
    return "Themes: " + ", ".join(f"{k} ({v['label']})" for k, v in THEMES.items())
