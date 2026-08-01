"""Futuristic Jarvis-style TTS — adjustable volume/rate, low overhead."""
from __future__ import annotations

import re
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .logger import JarvisLogger


class TTSEngine:
    """Clear, calm, intelligent speech. Volume 0.0–1.0; room_boost for noisy rooms."""

    def __init__(
        self,
        rate: int = 165,
        volume: float = 1.0,
        style: str = "jarvis",
        prefer_male: bool = True,
        room_boost: bool = True,
        enabled: bool = True,
        log: JarvisLogger | None = None,
    ):
        self.rate = rate
        self.volume = max(0.0, min(1.0, float(volume)))
        self.style = style
        self.prefer_male = prefer_male
        self.room_boost = room_boost
        self.enabled = enabled
        self.log = log
        self._engine = None
        self._lock = threading.Lock()
        self._voice_id = None
        self._init_engine()

    def _init_engine(self) -> None:
        try:
            import pyttsx3

            eng = pyttsx3.init()
            self._apply_props(eng)
            self._pick_voice(eng)
            self._engine = eng
            if self.log:
                self.log.info(
                    f"TTS ready style={self.style} rate={self.rate} vol={self.volume} boost={self.room_boost}"
                )
        except Exception as e:
            self._engine = None
            if self.log:
                self.log.warn(f"TTS init failed, PowerShell fallback: {e}")

    def _effective_rate(self) -> int:
        # Jarvis style: slightly measured; room_boost a bit slower for clarity over fan noise
        base = self.rate
        if self.style == "jarvis":
            base = min(base, 170)
        if self.room_boost:
            base = max(140, base - 15)
        return int(base)

    def _effective_volume(self) -> float:
        v = self.volume
        if self.room_boost:
            v = min(1.0, max(v, 0.95))
        return v

    def _apply_props(self, eng) -> None:
        eng.setProperty("rate", self._effective_rate())
        eng.setProperty("volume", self._effective_volume())
        if self._voice_id:
            try:
                eng.setProperty("voice", self._voice_id)
            except Exception:
                pass

    def _pick_voice(self, eng) -> None:
        try:
            voices = eng.getProperty("voices") or []
            scored = []
            for v in voices:
                name = (getattr(v, "name", "") or "").lower()
                vid = getattr(v, "id", "") or ""
                score = 0
                if "david" in name:
                    score += 50
                if "mark" in name or "george" in name or "james" in name:
                    score += 30
                if "zira" in name or "female" in name:
                    score += -10 if self.prefer_male else 20
                if "english" in name or "en-us" in name or "en_us" in vid.lower():
                    score += 15
                if "british" in name or "uk" in name:
                    score += 10  # slightly formal / Jarvis-adjacent
                scored.append((score, vid, name))
            scored.sort(reverse=True)
            if scored and scored[0][0] > 0:
                self._voice_id = scored[0][1]
                eng.setProperty("voice", self._voice_id)
                if self.log:
                    self.log.info(f"TTS voice: {scored[0][2]}")
        except Exception:
            pass

    def set_volume(self, volume: float) -> str:
        self.volume = max(0.0, min(1.0, float(volume)))
        if self._engine:
            try:
                self._engine.setProperty("volume", self._effective_volume())
            except Exception:
                pass
        return f"Voice volume set to {int(self.volume * 100)} percent."

    def set_rate(self, rate: int) -> str:
        self.rate = max(100, min(250, int(rate)))
        if self._engine:
            try:
                self._engine.setProperty("rate", self._effective_rate())
            except Exception:
                pass
        return f"Voice rate set to {self.rate}."

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def set_room_boost(self, on: bool) -> str:
        self.room_boost = bool(on)
        if self._engine:
            self._apply_props(self._engine)
        return f"Room boost {'on' if on else 'off'} (louder/clearer over fan noise)."

    def list_voices(self) -> list[str]:
        try:
            import pyttsx3

            eng = self._engine or pyttsx3.init()
            return [getattr(v, "name", str(v.id)) for v in (eng.getProperty("voices") or [])]
        except Exception:
            return []

    def stylize(self, text: str) -> str:
        """Light pacing for calm intelligent delivery — no heavy processing."""
        if not text:
            return text
        t = text.strip()
        # Soften abrupt walls of text for speech
        t = re.sub(r"\s+", " ", t)
        if self.style == "jarvis" and len(t) > 180:
            # Speak a concise version if very long
            t = t[:300].rsplit(" ", 1)[0] + "."
        return t

    def speak(self, text: str, block: bool = True) -> None:
        if not self.enabled or not text:
            return
        text = self.stylize(text)
        if self.log:
            self.log.info(f"SPEAK: {text[:120]}")

        def _run() -> None:
            with self._lock:
                if self._engine is not None:
                    try:
                        self._apply_props(self._engine)
                        self._engine.say(text)
                        self._engine.runAndWait()
                        return
                    except Exception:
                        pass
                self._powershell_speak(text)

        if block:
            _run()
        else:
            threading.Thread(target=_run, daemon=True).start()

    def _powershell_speak(self, text: str) -> None:
        import subprocess

        safe = text.replace("'", "''")
        rate = -1 if self.room_boost else 0  # SAPI rate -10..10
        vol = 100
        cmd = (
            "Add-Type -AssemblyName System.Speech; "
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.Rate={rate}; $s.Volume={vol}; $s.Speak('{safe}')"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            creationflags=0x08000000,
        )
