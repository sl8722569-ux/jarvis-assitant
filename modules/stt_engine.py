"""
Phase 2 STT — default mic detection, recovery, clear errors, wake reliability.
"""
from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, Callable

from .language import STT_CODES, normalize_lang
from .voice_diagnostics import list_input_devices, pick_default_microphone, windows_mic_privacy_hint

if TYPE_CHECKING:
    from .logger import JarvisLogger


class STTEngine:
    def __init__(self, config: dict, log: JarvisLogger | None = None, device_index: int | None = None):
        self.config = config
        self.log = log
        self.recognizer = None
        self.mic = None
        self.available = False
        self.device_index: int | None = device_index
        self.device_name: str = ""
        self.last_error: str = ""
        self.last_heard: str = ""
        self.language = normalize_lang(
            (config.get("languages") or {}).get("primary") or config.get("language") or "en"
        )
        self._fail_streak = 0
        self._init()

    def set_language(self, lang: str) -> None:
        self.language = normalize_lang(lang)

    def _log(self, msg: str, level: str = "info") -> None:
        if not self.log:
            return
        if level == "warn":
            self.log.warn(msg)
        else:
            self.log.info(msg)

    def _init(self) -> None:
        try:
            import speech_recognition as sr

            self.sr = sr
            self.recognizer = sr.Recognizer()
            # Slightly more sensitive for laptop arrays in noisy rooms
            self.recognizer.energy_threshold = int(self.config.get("energy_threshold", 300))
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = float(self.config.get("pause_threshold", 0.75))
            self.recognizer.non_speaking_duration = 0.4
            self.recognizer.operation_timeout = None

            if self.device_index is None:
                idx, name, note = pick_default_microphone()
                self.device_index = idx
                self.device_name = name
                self._log(f"Mic select: [{idx}] {name} ({note})")
            else:
                # resolve name
                for d in list_input_devices():
                    if d["index"] == self.device_index:
                        self.device_name = d["name"]
                        break

            if self.device_index is None:
                self.available = False
                self.last_error = "No microphone detected. " + windows_mic_privacy_hint()
                self._log(self.last_error, "warn")
                return

            self.mic = sr.Microphone(device_index=self.device_index)
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
            self.available = True
            self.last_error = ""
            self._log(f"STT ready on mic [{self.device_index}] {self.device_name}")
        except OSError as e:
            self.available = False
            self.last_error = (
                f"Microphone open failed: {e}. Another app may be using it, or Windows privacy is blocking access. "
                + windows_mic_privacy_hint()
            )
            self._log(self.last_error, "warn")
        except Exception as e:
            self.available = False
            self.last_error = f"STT init failed: {e}"
            self._log(self.last_error, "warn")

    def recover(self) -> bool:
        """Re-detect mic and re-init after failures."""
        self._log("STT recovery: re-detecting microphone…")
        self.device_index = None
        self.mic = None
        self.available = False
        try:
            if self.recognizer:
                self.recognizer.energy_threshold = int(self.config.get("energy_threshold", 300))
        except Exception:
            pass
        self._init()
        return self.available

    def test_microphone(self, seconds: float = 2.0) -> str:
        """Capture ambient RMS-ish level to verify mic works (no cloud)."""
        if not self.available or not self.mic:
            if self.recover():
                pass
            else:
                return f"Microphone test FAILED. {self.last_error or 'Mic unavailable.'}"
        try:
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.record(source, duration=max(0.5, min(seconds, 3.0)))
            raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
            # crude energy
            import array

            samples = array.array("h")
            samples.frombytes(raw)
            if not samples:
                return "Microphone test: captured silence. Check mic mute / Windows levels."
            avg = sum(abs(s) for s in samples) / len(samples)
            peak = max(abs(s) for s in samples)
            self._fail_streak = 0
            if peak < 80:
                return (
                    f"Microphone test: very quiet (avg={avg:.0f}, peak={peak}). "
                    "Speak louder, unmute mic, or pick another device in diagnostics."
                )
            return (
                f"Microphone test OK — [{self.device_index}] {self.device_name} "
                f"(avg={avg:.0f}, peak={peak})."
            )
        except Exception as e:
            self.last_error = str(e)
            self._fail_streak += 1
            if self._fail_streak >= 2:
                self.recover()
            return f"Microphone test FAILED: {e}"

    def listen_once(
        self,
        prompt: str | None = None,
        timeout: float | None = None,
        language: str | None = None,
    ) -> str | None:
        if not self.available:
            if not self.recover():
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

            codes = [stt_code]
            if stt_code != "en-IN":
                codes.append("en-IN")
            elif (self.config.get("languages") or {}).get("auto_detect", True):
                codes.append("hi-IN")

            last_err = None
            for code in codes:
                try:
                    text = self.recognizer.recognize_google(audio, language=code)
                    if text and text.strip():
                        self.last_heard = text.strip()
                        self.last_error = ""
                        self._fail_streak = 0
                        self._log(f"HEARD ({code}): {text}")
                        return text.strip()
                except self.sr.UnknownValueError:
                    continue
                except self.sr.RequestError as e:
                    last_err = e
                    self.last_error = (
                        f"Speech recognition network error: {e}. "
                        "Check internet connection (Google STT needs network)."
                    )
                    break
            if last_err:
                self._log(self.last_error, "warn")
            return None
        except Exception as e:
            msg = str(e).lower()
            if "timed out" in msg or "timeout" in msg:
                return None
            self.last_error = f"Listen error: {e}"
            self._fail_streak += 1
            self._log(self.last_error, "warn")
            if self._fail_streak >= 3:
                self.recover()
                self._fail_streak = 0
            return None

    @staticmethod
    def matches_wake_phrase(text: str, phrases: list[str] | None = None) -> bool:
        """More reliable wake matching (handles jarvis/jar vis, activate/activation)."""
        if not text:
            return False
        low = text.lower().strip()
        # normalize punctuation
        low = re.sub(r"[^\w\s]", " ", low)
        low = re.sub(r"\s+", " ", low).strip()
        # common mis-hears
        low = low.replace("jar vis", "jarvis").replace("jarvice", "jarvis")
        low = low.replace("jarves", "jarvis").replace("gervais", "jarvis")
        low = low.replace("activation", "activate").replace("activated", "activate")

        phrases = phrases or ["jarvis activate"]
        for p in phrases:
            p2 = re.sub(r"[^\w\s]", " ", p.lower())
            p2 = re.sub(r"\s+", " ", p2).strip()
            if p2 in low:
                return True
        if "jarvis" in low and any(
            w in low for w in ("activate", "online", "wake", "hey", "hello", "start", "open")
        ):
            return True
        # partial: only "activate jarvis"
        if "activate" in low and "jarvis" in low:
            return True
        return False

    def wait_for_activation(
        self,
        phrases: list[str],
        stop_flag: Callable[[], bool],
        on_tick: Callable[[], None] | None = None,
    ) -> bool:
        idle = float(self.config.get("idle_sleep_sec", 0.5))
        while not stop_flag():
            if on_tick:
                on_tick()
            if not self.available:
                self.recover()
                time.sleep(1.0)
                continue
            text = self.listen_once(timeout=3, language="en")
            if text and self.matches_wake_phrase(text, phrases):
                return True
            time.sleep(idle)
        return False
