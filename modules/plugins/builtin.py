"""Built-in Phase 2 plugins: calculator, translator stub, weather stub, steam/music helpers."""
from __future__ import annotations

import re
import webbrowser
from urllib.parse import quote_plus

from .base import Plugin


class CalculatorPlugin(Plugin):
    id = "calculator"
    name = "Calculator"
    description = "Evaluate simple math (e.g. calculate 12*8+3)"

    def handle(self, text: str) -> str | None:
        t = text.lower().strip()
        m = re.search(r"(?:calculate|calc|what is|math)\s+([0-9\.\+\-\*\/\%\(\)\s]+)$", t)
        if not m and re.fullmatch(r"[\d\.\+\-\*\/\%\(\)\s]+", t) and any(c in t for c in "+-*/"):
            expr = t
        elif m:
            expr = m.group(1)
        else:
            return None
        expr = expr.strip()
        if not re.fullmatch(r"[0-9\.\+\-\*\/\%\(\)\s]+", expr):
            return "I can only calculate basic numbers and + - * / % ()."
        try:
            # Safe eval: no names
            val = eval(expr, {"__builtins__": {}}, {})
            return f"{expr} = {val}"
        except Exception:
            return "Could not calculate that expression."


class TranslatorPlugin(Plugin):
    id = "translator"
    name = "Translator"
    description = "Open web translate for a phrase"

    def handle(self, text: str) -> str | None:
        t = text.strip()
        m = re.search(r"(?:translate|translate to (english|hindi|punjabi))\s+(.+)$", t, re.I)
        if not m:
            return None
        phrase = m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)
        if not phrase:
            return None
        url = "https://translate.google.com/?sl=auto&tl=en&text=" + quote_plus(phrase)
        webbrowser.open(url, new=2)
        return f"Opened translator for: {phrase}"


class WeatherPlugin(Plugin):
    id = "weather"
    name = "Weather"
    description = "Open weather search (no always-on tracking)"

    def handle(self, text: str) -> str | None:
        t = text.lower()
        if "weather" not in t:
            return None
        m = re.search(r"weather(?:\s+in|\s+for)?\s+(.+)$", t)
        place = m.group(1).strip() if m else "near me"
        webbrowser.open("https://www.google.com/search?q=" + quote_plus(f"weather {place}"), new=2)
        return f"Opened weather for: {place}"


class SteamHelperPlugin(Plugin):
    id = "steam_helper"
    name = "Steam Helper"
    description = "Tips and launch help for Steam / DBC14"

    def handle(self, text: str) -> str | None:
        t = text.lower()
        if not any(k in t for k in ("steam", "dbc", "cricket", "bradman", "game tip")):
            return None
        if "tip" in t or "help" in t or "how" in t:
            return (
                "Steam tip: close browser/VS Code first (8GB RAM). Use gaming mode, then open Steam. "
                "For DBC14 use Desktop DBC14 Optimized if present. I only assist after you ask."
            )
        if "open steam" in t or "launch steam" in t:
            return None  # let main router open app
        return (
            "Steam Helper ready. Say 'gaming mode' then 'open steam' or ask for a game tip."
        )


class MusicHelperPlugin(Plugin):
    id = "music_helper"
    name = "Music Helper"
    description = "Open YouTube Music / search a song"

    def handle(self, text: str) -> str | None:
        t = text.lower()
        m = re.search(r"(?:play|music|song)\s+(.+)$", t)
        if "youtube music" in t:
            webbrowser.open("https://music.youtube.com", new=2)
            return "Opened YouTube Music."
        if m and any(k in t for k in ("play", "music", "song")):
            q = m.group(1).strip()
            webbrowser.open("https://www.youtube.com/results?search_query=" + quote_plus(q), new=2)
            return f"Searching music for: {q}"
        return None


class ProductivityPlugin(Plugin):
    id = "productivity"
    name = "Productivity Tools"
    description = "Quick note, timer reminders (local)"

    def handle(self, text: str) -> str | None:
        t = text.lower().strip()
        if t.startswith("note ") or t.startswith("remember "):
            return None  # handled by windows assistant notes
        return None


def load_builtin_plugins(manager) -> None:
    for cls in (
        CalculatorPlugin,
        TranslatorPlugin,
        WeatherPlugin,
        SteamHelperPlugin,
        MusicHelperPlugin,
        ProductivityPlugin,
    ):
        manager.register(cls())
