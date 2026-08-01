"""Launch web AIs or installed AI apps — lightweight, reversible, no file deletes."""
from __future__ import annotations

import os
import subprocess
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .logger import JarvisLogger


def _expand(p: str) -> str:
    return os.path.expandvars(os.path.expanduser(p))


class AILauncher:
    """Open ChatGPT, Gemini, Copilot, etc. as app if installed, else browser."""

    ALIASES = {
        "chatgpt": "chatgpt",
        "chat gpt": "chatgpt",
        "gpt": "chatgpt",
        "openai": "chatgpt",
        "gemini": "gemini",
        "google gemini": "gemini",
        "bard": "gemini",
        "copilot": "copilot",
        "microsoft copilot": "copilot",
        "bing ai": "copilot",
        "claude": "claude",
        "anthropic": "claude",
        "perplexity": "perplexity",
        "grok": "grok",
        "x ai": "grok",
    }

    def __init__(self, config: dict[str, Any], log: JarvisLogger | None = None):
        self.config = config
        self.log = log
        self.targets: dict = config.get("ai_targets") or {}

    def resolve_name(self, spoken: str) -> str | None:
        t = spoken.lower().strip()
        t = t.replace("jarvis", "").replace(",", " ").strip()
        for phrase, key in sorted(self.ALIASES.items(), key=lambda x: -len(x[0])):
            if phrase in t:
                return key
        # direct key
        if t in self.targets:
            return t
        return None

    def launch(self, name: str) -> str:
        key = self.resolve_name(name) or name.lower().strip()
        target = self.targets.get(key)
        if not target:
            # generic web search fallback for unknown AI names
            q = name.strip()
            url = f"https://www.google.com/search?q={q.replace(' ', '+')}+ai"
            webbrowser.open(url, new=2)
            return f"I don't have a saved shortcut for {name}. Opened a web search instead."

        # 1) Prefer installed app
        for raw in target.get("app_paths") or []:
            path = Path(_expand(raw))
            if path.exists():
                try:
                    os.startfile(str(path))  # type: ignore[attr-defined]
                    if self.log:
                        self.log.event("launch_ai_app", {"name": key, "path": str(path)})
                    return f"Opening {key} app."
                except Exception as e:
                    if self.log:
                        self.log.warn(f"App launch failed {path}: {e}")

        # 2) Browser URL(s)
        for url in target.get("urls") or []:
            try:
                webbrowser.open(url, new=2)
                if self.log:
                    self.log.event("launch_ai_web", {"name": key, "url": url})
                return f"Opening {key} in your browser."
            except Exception:
                try:
                    subprocess.Popen(["cmd", "/c", "start", "", url], creationflags=0x08000000)
                    return f"Opening {key} in your browser."
                except Exception as e:
                    if self.log:
                        self.log.warn(f"URL launch failed: {e}")

        return f"Could not open {key}."

    def list_available(self) -> str:
        names = ", ".join(sorted(self.targets.keys()))
        return f"Available AI assistants: {names}."
