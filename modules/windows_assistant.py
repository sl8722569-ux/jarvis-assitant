"""Phase 2 Windows assistant extras: notes, clipboard, timers, brightness, calendar."""
from __future__ import annotations

import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


class WindowsAssistant:
    def __init__(self, root: Path, log=None):
        self.root = root
        self.log = log
        self.notes_path = root / "data" / "notes.txt"
        self.timers: dict[str, threading.Thread] = {}

    def _run(self, args: list[str] | str, shell: bool = False) -> tuple[int, str]:
        try:
            r = subprocess.run(
                args,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=0x08000000,
            )
            return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
        except Exception as e:
            return 1, str(e)

    def add_note(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return "What should I note?"
        self.notes_path.parent.mkdir(parents=True, exist_ok=True)
        line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {text}\n"
        with open(self.notes_path, "a", encoding="utf-8") as f:
            f.write(line)
        return f"Note saved. ({len(text)} chars)"

    def read_notes(self, last_n: int = 8) -> str:
        if not self.notes_path.exists():
            return "No notes yet. Say: note buy milk"
        lines = self.notes_path.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            return "Notes file is empty."
        return "Recent notes:\n" + "\n".join(lines[-last_n:])

    def clipboard_get(self) -> str:
        code, out = self._run(
            'powershell -NoProfile -Command "Get-Clipboard"',
            shell=True,
        )
        if code != 0:
            return "Could not read clipboard."
        text = (out or "").strip()
        if not text:
            return "Clipboard is empty."
        if len(text) > 400:
            return "Clipboard (preview): " + text[:400] + "…"
        return "Clipboard: " + text

    def clipboard_set(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return "Nothing to copy."
        # Use clip
        try:
            p = subprocess.run(
                ["clip"],
                input=text.encode("utf-16le"),
                capture_output=True,
                creationflags=0x08000000,
            )
            if p.returncode == 0:
                return "Copied to clipboard."
        except Exception:
            pass
        return "Could not set clipboard."

    def set_timer(self, seconds: int, label: str = "timer") -> str:
        seconds = max(1, min(int(seconds), 24 * 3600))
        label = label or "timer"

        def _fire():
            time.sleep(seconds)
            try:
                import winsound

                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:
                pass
            # also write a flag file
            flag = self.root / "data" / "timer_done.txt"
            flag.write_text(f"Timer done: {label} at {datetime.now().isoformat()}\n", encoding="utf-8")

        t = threading.Thread(target=_fire, daemon=True)
        t.start()
        self.timers[label] = t
        if seconds < 60:
            return f"Timer set for {seconds} seconds ({label})."
        return f"Timer set for {seconds // 60} min {seconds % 60}s ({label})."

    def open_calendar(self) -> str:
        # Windows Calendar app
        self._run(["cmd", "/c", "start", "outlookcal:"])
        self._run(["cmd", "/c", "start", "ms-calendar:"])
        return "Opened Calendar (if installed)."

    def brightness(self, direction: str | None = None, percent: int | None = None) -> str:
        """Best-effort brightness. May require supported hardware."""
        try:
            if percent is not None:
                p = max(0, min(100, int(percent)))
                # WMI method via powershell — may fail on some laptops
                script = (
                    f"$b=(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods);"
                    f"if($b){{$b.WmiSetBrightness(1,{p})|'Out-Null'; 'OK {p}'}} else {{'NO_WMI'}}"
                )
                code, out = self._run(["powershell", "-NoProfile", "-Command", script])
                if "OK" in out:
                    return f"Brightness set near {p}%."
                return (
                    "Could not set brightness via WMI on this device. "
                    "Use keyboard brightness keys (usually Fn + light keys)."
                )
            if direction == "up":
                return "Use Fn+brightness-up on this laptop, or say brightness 70."
            if direction == "down":
                return "Use Fn+brightness-down on this laptop, or say brightness 30."
            return "Say brightness up/down or brightness 50."
        except Exception as e:
            return f"Brightness control unavailable: {e}"

    def screenshot(self) -> str:
        code, _ = self._run(
            'powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; '
            "[System.Windows.Forms.SendKeys]::SendWait('{PrtSc}')\"",
            shell=True,
        )
        return "Screenshot sent to clipboard (Print Screen)." if code == 0 else "Screenshot failed."
