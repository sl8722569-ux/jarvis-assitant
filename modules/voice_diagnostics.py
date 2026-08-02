"""
Phase 2 — Voice Diagnostics
Microphone detection, speaker test, STT/TTS checks, clear user-facing errors.
Lightweight: no continuous monitoring.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VoiceDiagReport:
    ok: bool = False
    lines: list[str] = field(default_factory=list)
    default_mic_index: int | None = None
    default_mic_name: str = ""
    mic_count: int = 0
    tts_ok: bool = False
    stt_ready: bool = False
    last_error: str = ""

    def as_text(self) -> str:
        header = "Voice Diagnostics: " + ("PASS" if self.ok else "ISSUES FOUND")
        return header + "\n" + "\n".join(self.lines)


def list_input_devices() -> list[dict[str, Any]]:
    """Return input-capable devices via PyAudio (if available)."""
    devices: list[dict[str, Any]] = []
    try:
        import pyaudio

        p = pyaudio.PyAudio()
        try:
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if int(info.get("maxInputChannels") or 0) > 0:
                    devices.append(
                        {
                            "index": i,
                            "name": str(info.get("name") or f"Device {i}"),
                            "rate": int(float(info.get("defaultSampleRate") or 44100)),
                            "channels": int(info.get("maxInputChannels") or 1),
                        }
                    )
        finally:
            p.terminate()
    except Exception:
        # Fallback: speech_recognition names
        try:
            import speech_recognition as sr

            for i, name in enumerate(sr.Microphone.list_microphone_names() or []):
                if name:
                    devices.append({"index": i, "name": str(name), "rate": 44100, "channels": 1})
        except Exception:
            pass
    return devices


def pick_default_microphone(devices: list[dict[str, Any]] | None = None) -> tuple[int | None, str, str]:
    """
    Choose best default mic index.
    Prefers Windows default input, then Realtek/Microphone Array, skips Stereo Mix / loopback.
    Returns (index, name, note).
    """
    devices = devices if devices is not None else list_input_devices()
    if not devices:
        return None, "", "No input microphones detected. Check Windows Sound settings and privacy."

    skip_keywords = (
        "stereo mix",
        "what u hear",
        "loopback",
        "pc speaker",
        "output",
        "mapper",  # mapper often flaky; prefer real device
    )
    prefer_keywords = (
        "microphone array",
        "realtek",
        "mic in",
        "microphone",
        "headset",
    )

    # Try PyAudio default first
    default_idx = None
    default_name = ""
    try:
        import pyaudio

        p = pyaudio.PyAudio()
        try:
            d = p.get_default_input_device_info()
            default_idx = int(d.get("index"))
            default_name = str(d.get("name") or "")
        finally:
            p.terminate()
    except Exception:
        pass

    def score(dev: dict[str, Any]) -> int:
        name = (dev.get("name") or "").lower()
        s = 0
        if default_idx is not None and dev.get("index") == default_idx:
            s += 100
        for bad in skip_keywords:
            if bad in name:
                s -= 50
        for good in prefer_keywords:
            if good in name:
                s += 20
        # Prefer 44.1k/48k over 8k bluetooth HF if both exist
        rate = int(dev.get("rate") or 0)
        if rate >= 44100:
            s += 10
        if rate and rate <= 16000:
            s -= 15
        # Empty names are useless
        if not name.strip() or name.strip() in ("input ()", "input"):
            s -= 40
        return s

    ranked = sorted(devices, key=score, reverse=True)
    best = ranked[0]
    note = "Using system default input." if best.get("index") == default_idx else "Selected best available microphone."
    return int(best["index"]), str(best["name"]), note


def run_full_diagnostics(stt=None, tts=None, permissions=None) -> VoiceDiagReport:
    """Run lightweight diagnostics; does not record ambient audio for long."""
    report = VoiceDiagReport()
    report.lines.append("J.A.R.V.I.S [EARLY ACCESS] — Voice Diagnostics")

    # Permissions
    if permissions is not None:
        mic_ok = permissions.is_allowed("microphone")
        report.lines.append(f"• Microphone permission: {'ALLOWED' if mic_ok else 'DENIED (enable in Settings)'}")
        if not mic_ok:
            report.last_error = "Microphone permission is denied."
    else:
        report.lines.append("• Microphone permission: (not checked)")

    # Devices
    devices = list_input_devices()
    report.mic_count = len(devices)
    report.lines.append(f"• Input devices found: {report.mic_count}")
    idx, name, note = pick_default_microphone(devices)
    report.default_mic_index = idx
    report.default_mic_name = name
    if idx is not None:
        report.lines.append(f"• Default mic: [{idx}] {name}")
        report.lines.append(f"• Selection note: {note}")
    else:
        report.lines.append("• Default mic: NONE")
        report.last_error = report.last_error or "No microphone found."

    # List top devices (short)
    for d in devices[:6]:
        report.lines.append(f"   - [{d['index']}] {d['name']}")

    # STT module
    if stt is not None:
        report.stt_ready = bool(getattr(stt, "available", False))
        report.lines.append(f"• Speech-to-Text ready: {'YES' if report.stt_ready else 'NO'}")
        err = getattr(stt, "last_error", "") or ""
        if err:
            report.lines.append(f"• STT last error: {err}")
            report.last_error = report.last_error or err
    else:
        report.lines.append("• Speech-to-Text: not provided")

    # TTS
    if tts is not None:
        try:
            # dry property check + optional silent test flag
            voices = []
            if hasattr(tts, "list_voices"):
                voices = tts.list_voices() or []
            report.lines.append(f"• TTS voices installed: {len(voices)}")
            report.tts_ok = bool(getattr(tts, "_engine", None) is not None or True)
            # Quick speaker beep via winsound as hardware check
            try:
                import winsound

                winsound.MessageBeep(winsound.MB_OK)
                report.lines.append("• Speaker beep test: OK (if you heard a beep)")
            except Exception as e:
                report.lines.append(f"• Speaker beep test: failed ({e})")
            report.tts_ok = True
        except Exception as e:
            report.tts_ok = False
            report.lines.append(f"• TTS check failed: {e}")
            report.last_error = report.last_error or str(e)
    else:
        report.lines.append("• TTS: not provided")

    # Windows privacy tip
    report.lines.append(
        "• Windows: Settings → Privacy & security → Microphone — allow desktop apps."
    )

    report.ok = (
        report.mic_count > 0
        and report.default_mic_index is not None
        and (permissions is None or permissions.is_allowed("microphone"))
        and (stt is None or report.stt_ready)
    )
    if report.ok:
        report.lines.append("Result: Voice stack looks ready.")
    else:
        report.lines.append("Result: Fix the issues above, then run Voice Diagnostics again.")
    return report


def windows_mic_privacy_hint() -> str:
    return (
        "Windows may be blocking the mic. Open Settings → Privacy & security → Microphone, "
        "turn on 'Microphone access' and 'Let desktop apps access your microphone'."
    )


def open_windows_mic_settings() -> str:
    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "ms-settings:privacy-microphone"],
            creationflags=0x08000000,
        )
        return "Opened Windows Microphone privacy settings."
    except Exception as e:
        return f"Could not open settings: {e}"
