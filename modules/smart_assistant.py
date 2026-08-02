"""
Phase 2 Smart Assistant — tips for apps/games only after user asks / activation.
Never background-monitors other apps.
"""
from __future__ import annotations


class SmartAssistant:
    TIPS = {
        "steam": "Close heavy browsers first. Use High Performance power while gaming. Exit Steam when done to free RAM.",
        "chrome": "Too many tabs fill 8GB RAM fast. Keep under ~8 tabs on this laptop.",
        "edge": "Edge + many tabs competes with games. Close unused windows before DBC14.",
        "code": "VS Code uses a lot of RAM. Close it before gaming for smoother play.",
        "dbc": "Use gaming mode, then DBC14 Optimized launcher. Keep only Steam + game open.",
        "cricket": "Don Bradman Cricket 14 runs better with browsers closed and disk idle.",
        "word": "Save often to HDD. Large docs open slower — give it a few seconds.",
        "excel": "Big sheets are CPU-heavy on dual-core i3 — avoid other heavy apps.",
        "general": "I only help when you ask. I do not monitor your screen or apps in the background.",
    }

    def tip_for(self, topic: str) -> str:
        t = (topic or "general").lower().strip()
        for key, tip in self.TIPS.items():
            if key in t:
                return f"Tip ({key}): {tip}"
        return self.TIPS["general"]

    def handle(self, text: str) -> str | None:
        low = (text or "").lower()
        if not any(k in low for k in ("tip", "help with", "how do i", "how to", "assist with", "inside")):
            # game/app help phrases
            if not any(k in low for k in ("steam tip", "game help", "browser tip", "coding tip")):
                return None
        # extract topic
        for key in self.TIPS:
            if key in low:
                return self.tip_for(key)
        if "game" in low:
            return self.tip_for("steam")
        if "browser" in low:
            return self.tip_for("chrome")
        return self.tip_for("general")
