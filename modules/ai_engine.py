"""Conversation-aware local AI + optional cloud providers. Personality-aware."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .language import LANG_NAMES, detect_language, normalize_lang, phrase
from .personality import PersonalityEngine

if TYPE_CHECKING:
    from .ai_providers import AIProviders
    from .logger import JarvisLogger


class AIEngine:
    def __init__(self, config: dict, log: JarvisLogger | None = None, providers: AIProviders | None = None):
        self.config = config
        self.log = log
        self.providers = providers
        self.history: list[dict[str, str]] = []
        self.topics: list[str] = []
        lang_cfg = config.get("languages") or {}
        self.language = normalize_lang(lang_cfg.get("primary") or config.get("language") or "en")
        self.auto_detect = bool(lang_cfg.get("auto_detect", True))
        self.supported = [normalize_lang(x) for x in (lang_cfg.get("supported") or ["en", "hi", "pa"])]
        pers = (config.get("personality_mode") or "friendly").lower()
        self.personality = PersonalityEngine(pers)

    def set_language(self, lang: str) -> str:
        self.language = normalize_lang(lang)
        name = LANG_NAMES.get(self.language, self.language)
        return phrase("lang_set", self.language, name=name)

    def set_personality(self, mode: str) -> str:
        msg = self.personality.set_mode(mode)
        try:
            self.config["personality_mode"] = self.personality.mode
        except Exception:
            pass
        return msg

    def maybe_update_language(self, text: str) -> str:
        if not self.auto_detect:
            return self.language
        low = text.lower()
        if re.search(r"\b(switch to |speak |language )?(english|en)\b", low) and (
            "language" in low or "speak" in low or "switch" in low
        ):
            self.language = "en"
            return self.language
        if re.search(r"\b(switch to |speak |language )?(hindi|hi)\b", low) or "हिंदी" in text:
            if "language" in low or "speak" in low or "switch" in low or "हिंदी" in text:
                self.language = "hi"
                return self.language
        if re.search(r"\b(switch to |speak |language )?(punjabi|panjabi|pa)\b", low) or "ਪੰਜਾਬੀ" in text:
            if "language" in low or "speak" in low or "switch" in low or "ਪੰਜਾਬੀ" in text:
                self.language = "pa"
                return self.language
        detected = detect_language(text, default=self.language)
        if detected in self.supported:
            self.language = detected
        return self.language

    def reply(self, user_text: str, ui_state_cb=None) -> str:
        text = (user_text or "").strip()
        if not text:
            return phrase("didnt_catch", self.language)

        self.maybe_update_language(text)
        self.history.append({"role": "user", "content": text})
        # Phase 2: longer session memory (still light)
        self.history = self.history[-28:]
        self._note_topic(text)
        # Fast route: short intents skip deep local reasoning later via commands

        # Natural short acknowledgements
        if re.fullmatch(
            r"(ok|okay|hmm|han|haan|ji|yes|yeah|theek|theek hai|acha|accha|oh|right|sure|got it)",
            text.lower().strip(),
        ):
            ans = phrase("still_here", self.language)
            self.history.append({"role": "assistant", "content": ans})
            return ans

        # Follow-up references: "what about...", "and also...", "explain more"
        if ui_state_cb:
            ui_state_cb("thinking")

        lang_name = LANG_NAMES.get(self.language, "English")
        system = self.personality.system_prompt(lang_name)

        # Cloud first if available
        if self.providers:
            cloud = self.providers.chat(self.history, system)
            if cloud:
                cloud = self.personality.flavor(cloud) if self.personality.mode == "playful" else cloud
                self.history.append({"role": "assistant", "content": cloud})
                return cloud

        answer = self._local_reply(text)
        answer = self.personality.flavor(answer)
        self.history.append({"role": "assistant", "content": answer})
        return answer

    def _note_topic(self, text: str) -> None:
        t = text.lower()
        for key in ("python", "game", "battery", "steam", "cricket", "windows", "file", "whatsapp"):
            if key in t and key not in self.topics:
                self.topics.append(key)
        self.topics = self.topics[-6:]

    def _local_reply(self, text: str) -> str:
        t = text.lower().strip()
        follow = self._is_followup(t)

        if re.search(
            r"\b(hi|hello|hey|good morning|good evening|namaste|namaskar|sat sri akal)\b", t
        ) or "नमस्ते" in text:
            return self.personality.greeting(self.language)

        if re.search(r"\b(who are you|what are you|your name)\b", t):
            return self._pick(
                en="I'm JARVIS — your friendly Windows assistant. Chat, open apps and sites, check your PC, and help with everyday tasks.",
                hi="मैं JARVIS हूँ — आपका Windows सहायक। बातचीत, ऐप्स, वेबसाइट और PC मदद।",
                pa="ਮੈਂ JARVIS ਹਾਂ — ਤੁਹਾਡਾ Windows ਸਹਾਇਕ। ਗੱਲਬਾਤ, ਐਪਸ, ਵੈੱਬਸਾਈਟ ਅਤੇ PC ਮਦਦ।",
            )

        if re.search(r"\b(thank|thanks|shukriya|dhanyavad)\b", t):
            return self._pick(en="You're welcome.", hi="आपका स्वागत है।", pa="ਜੀ ਬਿਲਕੁਲ।")

        if re.search(r"\b(how are you|kaise ho|ki haal)\b", t):
            return self._pick(
                en="All systems steady. What would you like to do?",
                hi="सब ठीक है। आप क्या करना चाहेंगे?",
                pa="ਸਭ ਠੀਕ ਹੈ। ਤੁਸੀਂ ਕੀ ਕਰਨਾ ਚਾਹੋਗੇ?",
            )

        if re.search(r"\b(what can you do|help|commands)\b", t):
            return self._pick(
                en=(
                    "I can chat naturally, open apps and websites, show system info, "
                    "help with safe files, prepare WhatsApp shares (with your confirmation), "
                    "and connect optional ChatGPT/Gemini APIs. Say conversation mode for longer talks."
                ),
                hi="मैं बातचीत, ऐप्स/वेबसाइट खोलना, सिस्टम जानकारी, सुरक्षित फ़ाइल मदद, और WhatsApp शेयर (पुष्टि के साथ) कर सकता हूँ।",
                pa="ਮੈਂ ਗੱਲਬਾਤ, ਐਪਸ/ਵੈੱਬਸਾਈਟ, ਸਿਸਟਮ ਜਾਣਕਾਰੀ, ਸੁਰੱਖਿਅਤ ਫਾਈਲ ਮਦਦ, ਅਤੇ WhatsApp ਸ਼ੇਅਰ (ਪੁਸ਼ਟੀ ਨਾਲ) ਕਰ ਸਕਦਾ ਹਾਂ।",
            )

        if any(w in t for w in ("slow", "lag", "hang", "freeze")):
            return self._pick(
                en="On i3 + 8GB + HDD, close heavy apps, try performance mode, and keep chats light. An SSD helps most long-term.",
                hi="i3 + 8GB + HDD पर भारी ऐप्स बंद करें, performance mode आज़माएँ। SSD सबसे बड़ा सुधार है।",
                pa="i3 + 8GB + HDD 'ਤੇ ਭਾਰੀ ਐਪਸ ਬੰਦ ਕਰੋ, performance mode ਅਜ਼ਮਾਓ। SSD ਸਭ ਤੋਂ ਵੱਡਾ ਸੁਧਾਰ ਹੈ।",
            )

        if "python" in t and any(w in t for w in ("code", "script", "example", "function", "how")):
            tip = "def greet(name):\n    return f'Hello, {name}!'\nprint(greet('friend'))"
            more = " Want a file-save example next?" if follow or "more" in t else " What should we build?"
            return self._pick(
                en=f"Here's a small Python example:\n{tip}\n{more}",
                hi=f"छोटा Python उदाहरण:\n{tip}\nआगे क्या चाहिए?",
                pa=f"ਛੋਟਾ Python ਉਦਾਹਰਣ:\n{tip}\nਅੱਗੇ ਕੀ ਚਾਹੀਦਾ ਹੈ?",
            )

        # Follow-up: "tell me more", "why", "and then"
        if follow and self.topics:
            topic = self.topics[-1]
            return self._pick(
                en=f"Continuing on {topic}: I can go deeper, open a related app, or search the web if you allow web permission. What angle do you want?",
                hi=f"{topic} पर आगे: और गहराई, ऐप खोलना, या वेब खोज (अनुमति के साथ)। क्या चाहिए?",
                pa=f"{topic} 'ਤੇ ਅੱਗੇ: ਹੋਰ ਡੂੰਘਾਈ, ਐਪ, ਜਾਂ ਵੈੱਬ ਖੋਜ (ਇਜਾਜ਼ਤ ਨਾਲ)। ਕੀ ਚਾਹੀਦਾ ਹੈ?",
            )

        if re.search(r"\b(explain more|tell me more|go on|continue|and then|what about|why)\b", t):
            last_q = ""
            for h in reversed(self.history[:-1]):
                if h.get("role") == "user":
                    last_q = h.get("content", "")
                    break
            if last_q:
                return self._pick(
                    en=f"Building on \"{last_q[:80]}\": the practical next step on this PC is keep one heavy app closed while you work, and ask me for a specific action (open, check battery, optimize). Want me to do one of those?",
                    hi="पिछली बात को आगे बढ़ाते हुए: बताएँ कि ऐप खोलना है, बैटरी जाँचनी है, या optimize करना है?",
                    pa="ਪਿਛਲੀ ਗੱਲ ਤੋਂ ਅੱਗੇ: ਦੱਸੋ ਐਪ ਖੋਲ੍ਹਣੀ ਹੈ, ਬੈਟਰੀ ਚੈੱਕ, ਜਾਂ optimize?",
                )

        if "language" in t or "bhasha" in t:
            return self._pick(
                en="English (primary), Hindi, and Punjabi — auto-detect is on. Or say switch language to Hindi.",
                hi="अंग्रेज़ी, हिंदी, पंजाबी — ऑटो डिटेक्ट चालू है।",
                pa="ਅੰਗਰੇਜ਼ੀ, ਹਿੰਦੀ, ਪੰਜਾਬੀ — ਆਟੋ ਡਿਟੈਕਟ ਚਾਲੂ ਹੈ।",
            )

        if "personality" in t or "humor" in t or "playful" in t:
            return self._pick(
                en="Personality modes: professional, friendly, playful. Say 'personality playful' to switch.",
                hi="व्यक्तित्व: professional, friendly, playful. 'personality playful' कहें।",
                pa="ਸ਼ਖਸੀਅਤ: professional, friendly, playful.",
            )

        # Natural fallback with memory
        prev = ""
        for h in reversed(self.history[:-1]):
            if h.get("role") == "user":
                prev = h.get("content", "")
                break
        if prev:
            return self._pick(
                en=f"On \"{text}\" — related to your earlier note about \"{prev[:60]}\". I can open an app, a site, check the system, or explain more. What next?",
                hi=f"\"{text}\" के बारे में — पहले आपने \"{prev[:40]}\" कहा था। आगे ऐप, वेब, या समझाइश?",
                pa=f"\"{text}\" ਬਾਰੇ — ਪਹਿਲਾਂ \"{prev[:40]}\"। ਅੱਗੇ ਐਪ, ਵੈੱਬ, ਜਾਂ ਹੋਰ ਵਿਆਖਿਆ?",
            )

        return self._pick(
            en=f"I heard: \"{text}\". Ask me anything, or try: open youtube, system info, list downloads, conversation mode.",
            hi=f"सुना: \"{text}\". कुछ भी पूछें, या कहें: open youtube, system info, conversation mode.",
            pa=f"ਸੁਣਿਆ: \"{text}\". ਕੁਝ ਵੀ ਪੁੱਛੋ, ਜਾਂ: open youtube, system info, conversation mode.",
        )

    def _is_followup(self, t: str) -> bool:
        return bool(
            re.search(
                r"\b(what about|and also|also|then|more|again|that|it|why|how so|continue|explain)\b",
                t,
            )
            or t.startswith(("and ", "also ", "but ", "so "))
        )

    def _pick(self, en: str, hi: str | None = None, pa: str | None = None) -> str:
        if self.language == "hi" and hi:
            return hi
        if self.language == "pa" and pa:
            return pa
        return en
