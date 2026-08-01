"""Lightweight English / Hindi / Punjabi detection and phrases for JARVIS."""
from __future__ import annotations

import re
from typing import Any


# STT language codes (Google free recognizer)
STT_CODES = {
    "en": "en-IN",
    "hi": "hi-IN",
    "pa": "pa-IN",
}

LANG_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "pa": "Punjabi",
}


def normalize_lang(code: str) -> str:
    c = (code or "en").lower().strip()
    aliases = {
        "english": "en",
        "eng": "en",
        "en-in": "en",
        "en-us": "en",
        "hindi": "hi",
        "hin": "hi",
        "हिंदी": "hi",
        "हिन्दी": "hi",
        "punjabi": "pa",
        "panjabi": "pa",
        "pa-in": "pa",
        "ਪੰਜਾਬੀ": "pa",
    }
    if c in aliases:
        return aliases[c]
    return c[:2] if c[:2] in STT_CODES else "en"


def detect_language(text: str, default: str = "en") -> str:
    """Heuristic language detect — no heavy ML."""
    if not text or not text.strip():
        return default
    t = text.strip()
    low = t.lower()

    # Scripts first (most reliable)
    if re.search(r"[\u0A00-\u0A7F]", t):  # Gurmukhi
        return "pa"
    if re.search(r"[\u0900-\u097F]", t):  # Devanagari (Hindi)
        return "hi"

    # Romanized Punjabi cues
    pa_words = (
        r"\b(sat sri akal|ss akal|ki haal|ki haal ae|ki haal a|theek haan|theek haan ji|"
        r"kithe|kiddan|kidaan|twinu|tusi|tuhada|mera naa|shukriya ji|bahut vadiya|"
        r"punjabi|panjabi|bhangra|pind|yaar ki haal)\b"
    )
    if re.search(pa_words, low):
        return "pa"

    # Romanized Hindi / Hinglish cues
    hi_words = (
        r"\b(namaste|namaskar|kaise ho|kaisi ho|kya haal|kya kar rahe|shukriya|dhanyavad|"
        r"dhanyavaad|kripya|please karo|mujhe|tumhara|aapka|haan|nahi|theek hai|"
        r"accha|achha|bhai|yaar|kya|kaise|kahan|kyun|mat lab|samajh|madad|"
        r"hindi mein|hinglish)\b"
    )
    if re.search(hi_words, low):
        return "hi"

    # Explicit language switch phrases
    if re.search(r"\b(in hindi|speak hindi|switch to hindi|हिंदी में)\b", low):
        return "hi"
    if re.search(r"\b(in punjabi|speak punjabi|switch to punjabi|ਪੰਜਾਬੀ)\b", low):
        return "pa"
    if re.search(r"\b(in english|speak english|switch to english)\b", low):
        return "en"

    return default


def is_exit_phrase(text: str) -> bool:
    t = (text or "").lower().strip()
    patterns = (
        r"\b(goodbye|good bye|bye bye|standby|stand by|go to sleep|deactivate|"
        r"stop conversation|end conversation|exit conversation|stop talking|"
        r"that's all|that is all|cancel conversation)\b",
        r"\b(bas karo|band karo|band kar do|chup ho jao|ab bas|alvida|सो जाओ|बंद करो|बात खत्म)\b",
        r"\b(bas kar|band kar|gal baat khatam|ruko|stop kar|ਬੰਦ ਕਰੋ|ਬਸ ਕਰੋ)\b",
    )
    return any(re.search(p, t) for p in patterns)


def phrase(key: str, lang: str, **kwargs: Any) -> str:
    """Natural short system phrases in en / hi / pa."""
    lang = normalize_lang(lang)
    table = {
        "listening": {
            "en": "I'm listening…",
            "hi": "मैं सुन रहा हूँ…",
            "pa": "ਮੈਂ ਸੁਣ ਰਿਹਾ ਹਾਂ…",
        },
        "conversation_on": {
            "en": "Conversation mode on. Talk naturally — no need to say Jarvis each time. Say 'standby' or 'goodbye' to exit.",
            "hi": "बातचीत मोड चालू है। आराम से बात करें — हर बार Jarvis कहने की ज़रूरत नहीं। बंद करने के लिए 'standby' या 'goodbye' कहें।",
            "pa": "ਗੱਲਬਾਤ ਮੋਡ ਚਾਲੂ ਹੈ। ਆਰਾਮ ਨਾਲ ਗੱਲ ਕਰੋ — ਹਰ ਵਾਰੀ Jarvis ਕਹਿਣ ਦੀ ਲੋੜ ਨਹੀਂ। ਬੰਦ ਕਰਨ ਲਈ 'standby' ਜਾਂ 'goodbye' ਕਹੋ।",
        },
        "conversation_off": {
            "en": "Back to standby. Say Jarvis Activate when you need me.",
            "hi": "स्टैंडबाय पर वापस। ज़रूरत हो तो Jarvis Activate कहें।",
            "pa": "ਸਟੈਂਡਬਾਈ 'ਤੇ ਵਾਪਸ। ਲੋੜ ਹੋਵੇ ਤਾਂ Jarvis Activate ਕਹੋ।",
        },
        "activated": {
            "en": "Yes sir, I am online. How may I assist you?",
            "hi": "जी हाँ, मैं ऑनलाइन हूँ। मैं आपकी कैसे मदद कर सकता हूँ?",
            "pa": "ਜੀ ਹਾਂ, ਮੈਂ ਆਨਲਾਈਨ ਹਾਂ। ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
        },
        "didnt_catch": {
            "en": "I didn't catch that. Please try again.",
            "hi": "समझ नहीं पाया। फिर से कहें।",
            "pa": "ਸਮਝ ਨਹੀਂ ਆਇਆ। ਫਿਰ ਕਹੋ ਜੀ।",
        },
        "still_here": {
            "en": "I'm still here. What would you like next?",
            "hi": "मैं यहीं हूँ। आगे क्या करें?",
            "pa": "ਮੈਂ ਇੱਥੇ ਹੀ ਹਾਂ। ਅੱਗੇ ਕੀ ਕਰੀਏ?",
        },
        "no_speech": {
            "en": "No speech detected. Press Enter or click Talk to try again.",
            "hi": "आवाज़ नहीं मिली। Enter दबाएँ या Talk पर क्लिक करें।",
            "pa": "ਅਵਾਜ਼ ਨਹੀਂ ਮਿਲੀ। Enter ਦਬਾਓ ਜਾਂ Talk 'ਤੇ ਕਲਿੱਕ ਕਰੋ।",
        },
        "lang_set": {
            "en": "Language set to {name}.",
            "hi": "भाषा {name} पर सेट की गई।",
            "pa": "ਭਾਸ਼ਾ {name} 'ਤੇ ਸੈੱਟ ਕੀਤੀ ਗਈ।",
        },
        "follow_up": {
            "en": "Go on, I'm listening.",
            "hi": "बोलिए, मैं सुन रहा हूँ।",
            "pa": "ਬੋਲੋ ਜੀ, ਮੈਂ ਸੁਣ ਰਿਹਾ ਹਾਂ।",
        },
    }
    block = table.get(key, {})
    text = block.get(lang) or block.get("en") or key
    try:
        return text.format(**kwargs)
    except Exception:
        return text
