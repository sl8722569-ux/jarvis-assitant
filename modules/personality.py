"""Jarvis personality profiles — professional / friendly / playful."""
from __future__ import annotations

from typing import Any


PROFILES = {
    "professional": {
        "label": "Professional",
        "system": (
            "You are JARVIS in Professional mode: precise, calm, respectful, concise. "
            "No jokes unless asked. Prefer clear structured answers."
        ),
        "greet": {
            "en": "Systems online. How may I assist you?",
            "hi": "सिस्टम ऑनलाइन हैं। मैं आपकी कैसे सहायता करूँ?",
            "pa": "ਸਿਸਟਮ ਆਨਲਾਈਨ ਹਨ। ਮੈਂ ਕਿਵੇਂ ਮਦਦ ਕਰਾਂ?",
        },
        "prefix": "",
        "humor": 0.0,
    },
    "friendly": {
        "label": "Friendly",
        "system": (
            "You are JARVIS in Friendly mode: warm, calm, helpful, intelligent. "
            "Natural conversation partner. Light warmth, no sarcasm."
        ),
        "greet": {
            "en": "Yes sir, I am online. How may I assist you?",
            "hi": "जी हाँ, मैं ऑनलाइन हूँ। बताइए, कैसे मदद करूँ?",
            "pa": "ਜੀ ਹਾਂ, ਮੈਂ ਆਨਲਾਈਨ ਹਾਂ। ਦੱਸੋ, ਕਿਵੇਂ ਮਦਦ ਕਰਾਂ?",
        },
        "prefix": "",
        "humor": 0.15,
    },
    "playful": {
        "label": "Playful",
        "system": (
            "You are JARVIS in Playful mode: still helpful and smart, with optional light humor. "
            "Stay respectful. One short witty line is ok, never mean."
        ),
        "greet": {
            "en": "Online and caffeinated — well, digitally. What are we fixing or exploring today?",
            "hi": "ऑनलाइन और तैयार! आज क्या तय करेंगे — काम, गेम, या कुछ मज़ेदार?",
            "pa": "ਆਨਲਾਈਨ ਅਤੇ ਤਿਆਰ! ਅੱਜ ਕੀ ਕਰੀਏ — ਕੰਮ, ਖੇਡ, ਜਾਂ ਕੁਝ ਮਜ਼ੇਦਾਰ?",
        },
        "prefix": "",
        "humor": 0.55,
    },
}


class PersonalityEngine:
    def __init__(self, mode: str = "friendly"):
        self.mode = mode if mode in PROFILES else "friendly"

    def set_mode(self, mode: str) -> str:
        mode = (mode or "").lower().strip()
        aliases = {
            "pro": "professional",
            "formal": "professional",
            "fun": "playful",
            "funny": "playful",
            "casual": "friendly",
            "default": "friendly",
        }
        mode = aliases.get(mode, mode)
        if mode not in PROFILES:
            return f"Unknown personality. Choose: professional, friendly, playful."
        self.mode = mode
        return f"Personality set to {PROFILES[mode]['label']}."

    def profile(self) -> dict[str, Any]:
        return PROFILES[self.mode]

    def system_prompt(self, lang_name: str = "English") -> str:
        p = self.profile()
        return (
            f"{p['system']} Always reply in {lang_name}. "
            "Hardware: low-end Windows laptop (i3, 8GB, HDD) — keep advice practical and light."
        )

    def greeting(self, lang: str = "en") -> str:
        g = self.profile()["greet"]
        return g.get(lang) or g["en"]

    def flavor(self, text: str) -> str:
        """Optional light touch for local replies (no heavy processing)."""
        if self.mode != "playful" or not text:
            return text
        # Only append tiny flourish sometimes for short replies
        if len(text) < 160 and not text.endswith("?"):
            extras = [
                " Easy does it.",
                " You've got this.",
                " Smooth and steady.",
            ]
            # deterministic tiny spice from length
            extra = extras[len(text) % len(extras)]
            if extra.strip() not in text:
                return text.rstrip(".") + "." + extra
        return text
