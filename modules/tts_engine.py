"""
Phase 2 TTS — fix silent 'Speaking' state, speaker test, SAPI recovery.
"""
from __future__ import annotations

import re
import subprocess
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .logger import JarvisLogger


class TTSEngine:
    """Clear, calm speech with automatic recovery if audio fails."""

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
        self.last_error: str = ""
        self.last_method: str = ""
        self._speak_failures = 0
        self._init_engine()

    def _log(self, msg: str, level: str = "info") -> None:
        if not self.log:
            return
        if level == "warn":
            self.log.warn(msg)
        else:
            self.log.info(msg)

    def _init_engine(self) -> None:
        self._engine = None
        try:
            import pyttsx3

            # Explicit SAPI5 on Windows avoids empty drivers
            try:
                eng = pyttsx3.init(driverName="sapi5")
            except Exception:
                eng = pyttsx3.init()
            self._apply_props(eng)
            self._pick_voice(eng)
            self._engine = eng
            self.last_error = ""
            self._log(
                f"TTS ready style={self.style} rate={self.rate} vol={self.volume} boost={self.room_boost}"
            )
        except Exception as e:
            self._engine = None
            self.last_error = f"TTS init failed: {e}"
            self._log(self.last_error + " — using PowerShell SAPI fallback.", "warn")

    def recover(self) -> bool:
        """Rebuild TTS engine after silent failures."""
        self._log("TTS recovery: reinitializing engine…")
        try:
            if self._engine is not None:
                try:
                    self._engine.stop()
                except Exception:
                    pass
        except Exception:
            pass
        self._engine = None
        self._init_engine()
        self._speak_failures = 0
        return self._engine is not None

    def _effective_rate(self) -> int:
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
        return max(0.2, min(1.0, v))

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
                    score += 10
                scored.append((score, vid, name))
            scored.sort(reverse=True)
            if scored and scored[0][0] > 0:
                self._voice_id = scored[0][1]
                eng.setProperty("voice", self._voice_id)
                self._log(f"TTS voice: {scored[0][2]}")
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

            eng = self._engine or pyttsx3.init(driverName="sapi5")
            return [getattr(v, "name", str(v.id)) for v in (eng.getProperty("voices") or [])]
        except Exception:
            return []

    def stylize(self, text: str) -> str:
        if not text:
            return text
        t = text.strip()
        t = re.sub(r"\s+", " ", t)
        # Strip chars that break SAPI / PowerShell
        t = t.replace("`", "'").replace('"', "'")
        if self.style == "jarvis" and len(t) > 220:
            t = t[:300].rsplit(" ", 1)[0] + "."
        return t

    def test_speaker(self) -> str:
        """Audible speaker test with clear result."""
        phrase = "Jarvis speaker test. If you can hear this, audio output is working."
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass
        ok = self.speak(phrase, block=True)
        if ok:
            return f"Speaker test OK (method: {self.last_method or 'tts'})."
        return (
            f"Speaker test FAILED. {self.last_error or 'No audio path.'} "
            "Check Windows volume, default playback device, and that the speaker is not muted."
        )

    def stop(self) -> None:
        try:
            if self._engine is not None:
                self._engine.stop()
        except Exception:
            pass

    def speak(self, text: str, block: bool = True) -> bool:
        """
        Speak text. Returns True if a backend accepted the speech.
        Fixes silent 'Speaking' by falling back to PowerShell SAPI and recovering engine.
        """
        if not self.enabled:
            self.last_error = "TTS is disabled in settings."
            return False
        if not text or not str(text).strip():
            self.last_error = "Nothing to speak."
            return False

        text = self.stylize(str(text))
        self._log(f"SPEAK: {text[:120]}")

        result = {"ok": False}

        def _run() -> None:
            with self._lock:
                # Attempt 1: pyttsx3 SAPI
                if self._engine is not None:
                    try:
                        self._apply_props(self._engine)
                        try:
                            self._engine.stop()
                        except Exception:
                            pass
                        self._engine.say(text)
                        self._engine.runAndWait()
                        self.last_method = "pyttsx3-sapi5"
                        self.last_error = ""
                        self._speak_failures = 0
                        result["ok"] = True
                        return
                    except Exception as e:
                        self.last_error = f"pyttsx3 speak failed: {e}"
                        self._speak_failures += 1
                        self._log(self.last_error, "warn")
                        if self._speak_failures >= 1:
                            self.recover()

                # Attempt 2: re-init once more
                if self._engine is None:
                    self._init_engine()
                if self._engine is not None:
                    try:
                        self._apply_props(self._engine)
                        self._engine.say(text)
                        self._engine.runAndWait()
                        self.last_method = "pyttsx3-recovered"
                        self.last_error = ""
                        result["ok"] = True
                        return
                    except Exception as e:
                        self.last_error = f"TTS retry failed: {e}"
                        self._log(self.last_error, "warn")

                # Attempt 3: PowerShell System.Speech (most reliable on Windows)
                if self._powershell_speak(text):
                    self.last_method = "powershell-sapi"
                    self.last_error = ""
                    result["ok"] = True
                    return

                self.last_error = self.last_error or "All TTS backends failed."
                result["ok"] = False

        if block:
            _run()
        else:
            threading.Thread(target=_run, daemon=True).start()
            # non-blocking: assume scheduled OK
            return True
        return bool(result["ok"])

    def _powershell_speak(self, text: str) -> bool:
        try:
            safe = text.replace("'", "''")
            # Clamp length for command line
            if len(safe) > 800:
                safe = safe[:800] + "..."
            rate = -1 if self.room_boost else 0
            vol = int(self._effective_volume() * 100)
            cmd = (
                "Add-Type -AssemblyName System.Speech; "
                "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$s.Rate={rate}; $s.Volume={vol}; "
                f"$s.Speak('{safe}')"
            )
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                timeout=60,
                creationflags=0x08000000,
            )
            if r.returncode != 0:
                err = (r.stderr or b"").decode("utf-8", errors="ignore")
                self.last_error = f"PowerShell TTS failed: {err or r.returncode}"
                return False
            return True
        except Exception as e:
            self.last_error = f"PowerShell TTS error: {e}"
            return False
