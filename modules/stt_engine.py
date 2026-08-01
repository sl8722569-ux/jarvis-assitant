"""Speech-to-text with language-aware recognition (en / hi / pa)."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Callable

from .language import STT_CODES, normalize_lang

if TYPE_CHECKING:
    from .logger import JarvisLogger


class STTEngine:
    def __init__(self, config: dict, log: JarvisLogger | None = None):
        self.config = config
        self.log = log
        self.recognizer = None
        self.mic = None
        self.available = False
        self.language = normalize_lang(
            (config.get("languages") or {}).get("primary") or config.get("language") or "en"
        )
        self._init()

    def set_language(self, lang: str) -> None:
        self.language = normalize_lang(lang)

    def _init(self) -> None:
        try:
            import speech_recognition as sr

            self.sr = sr
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = int(self.config.get("energy_threshold", 350))
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.mic = sr.Microphone()
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self.available = True
            if self.log:
                self.log.info("STT engine ready (microphone available)")
        except Exception as e:
            self.available = False
            if self.log:
                self.log.warn(
                    f"Microphone/STT unavailable ({e}). Text mode + hotkey still work."
                )

    def listen_once(
        self,
        prompt: str | None = None,
        timeout: float | None = None,
        language: str | None = None,
    ) -> str | None:
        if not self.available:
            return None
        timeout = timeout if timeout is not None else float(self.config.get("listen_timeout_sec", 6))
        limit = float(self.config.get("phrase_time_limit_sec", 10))
        lang = normalize_lang(language or self.language)
        stt_code = STT_CODES.get(lang, "en-IN")

        try:
            with self.mic as source:
                if prompt and self.log:
                    self.log.info(prompt)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=limit)

            # Prefer active language; one light fallback only (keeps i3/HDD snappy)
            codes = [stt_code]
            if stt_code != "en-IN":
                codes.append("en-IN")
            # If English primary, single extra try of Hindi (covers many bilingual users)
            elif (self.config.get("languages") or {}).get("auto_detect", True):
                codes.append("hi-IN")

            last_err = None
            for code in codes:
                try:
                    text = self.recognizer.recognize_google(audio, language=code)
                    if text and text.strip():
                        if self.log:
                            self.log.info(f"HEARD ({code}): {text}")
                        return text.strip()
                except self.sr.UnknownValueError:
                    continue
                except self.sr.RequestError as e:
                    last_err = e
                    break
            if last_err and self.log:
                self.log.warn(f"STT network error: {last_err}")
            return None
        except Exception as e:
            msg = str(e).lower()
            if "timed out" in msg or "timeout" in msg:
                return None
            if self.log:
                self.log.warn(f"Listen error: {e}")
            return None

    def wait_for_activation(
        self,
        phrases: list[str],
        stop_flag: Callable[[], bool],
        on_tick: Callable[[], None] | None = None,
    ) -> bool:
        phrases = [p.lower().strip() for p in phrases]
        idle = float(self.config.get("idle_sleep_sec", 0.5))
        while not stop_flag():
            if on_tick:
                on_tick()
            if not self.available:
                time.sleep(1.0)
                continue
            text = self.listen_once(timeout=3, language="en")
            if text:
                low = text.lower().strip()
                for p in phrases:
                    if p in low:
                        return True
                if "jarvis" in low and any(
                    w in low for w in ("activate", "online", "wake", "hello", "hey")
                ):
                    return True
            time.sleep(idle)
        return False
