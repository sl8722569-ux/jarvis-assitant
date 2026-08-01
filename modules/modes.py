"""Smart automation modes: gaming, study, performance, startup."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .logger import JarvisLogger
    from .system_ops import SystemOps


def _silent(cmd: list[str] | str, shell: bool = False) -> None:
    try:
        flags = 0x08000000 if os.name == "nt" else 0
        subprocess.run(cmd, shell=shell, capture_output=True, timeout=45, creationflags=flags)
    except Exception:
        pass


class ModeManager:
    HEAVY_PROCS = [
        "msedge.exe",
        "chrome.exe",
        "M365Copilot.exe",
        "OneDrive.exe",
        "SearchHost.exe",
        "Widgets.exe",
        "YourPhone.exe",
        "Skype.exe",
        "Discord.exe",
        "Spotify.exe",
        "Teams.exe",
        "ms-teams.exe",
    ]

    def __init__(self, ops: SystemOps, log: JarvisLogger | None = None):
        self.ops = ops
        self.log = log
        self.active_mode = "normal"

    def gaming_mode(self) -> str:
        self.active_mode = "gaming"
        for p in self.HEAVY_PROCS:
            _silent(["taskkill", "/F", "/IM", p, "/T"])
        # High performance scheme if present
        _silent(["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"])
        # Game mode registry
        _silent(
            'powershell -NoProfile -Command "'
            "New-Item 'HKCU:\\Software\\Microsoft\\GameBar' -Force | Out-Null; "
            "Set-ItemProperty 'HKCU:\\Software\\Microsoft\\GameBar' AutoGameModeEnabled 1 -Type DWord; "
            "Set-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR' AppCaptureEnabled 0 -Type DWord -ErrorAction SilentlyContinue"
            '"',
            shell=True,
        )
        if self.log:
            self.log.event("mode", {"name": "gaming"})
        return (
            "Gaming mode on. Closed heavy background apps, set high performance power, "
            "and enabled Game Mode. Ready for Steam or Don Bradman Cricket 14."
        )

    def study_mode(self) -> str:
        self.active_mode = "study"
        for p in ["Discord.exe", "Steam.exe", "Spotify.exe", "msedge.exe", "chrome.exe"]:
            # do not kill edge if user needs web research — kill only social/noise
            if p in ("Discord.exe", "Steam.exe", "Spotify.exe"):
                _silent(["taskkill", "/F", "/IM", p, "/T"])
        # Open study tools
        self.ops.open_app("notepad")
        docs = Path.home() / "Documents"
        if docs.exists():
            os.startfile(str(docs))  # type: ignore[attr-defined]
        if self.log:
            self.log.event("mode", {"name": "study"})
        return "Study mode on. Distractions reduced. Documents and Notepad are ready."

    def performance_mode(self) -> str:
        self.active_mode = "performance"
        for p in self.HEAVY_PROCS:
            _silent(["taskkill", "/F", "/IM", p, "/T"])
        _silent(["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"])
        # Clear user temp safely
        temp = Path(os.environ.get("TEMP", ""))
        if temp.exists():
            for child in temp.iterdir():
                try:
                    if child.is_file():
                        child.unlink(missing_ok=True)
                    elif child.is_dir():
                        import shutil

                        shutil.rmtree(child, ignore_errors=True)
                except Exception:
                    pass
        if self.log:
            self.log.event("mode", {"name": "performance"})
        return "Performance mode on. Freed background apps and temp files. System prioritized for speed."

    def startup_assistant(self, apps: list[str] | None = None) -> str:
        apps = apps or []
        opened = []
        for a in apps:
            self.ops.open_app(a)
            opened.append(a)
        if self.log:
            self.log.event("mode", {"name": "startup", "apps": opened})
        if not opened:
            return "Startup assistant ready. Enable apps in config.json under startup_assistant."
        return "Startup assistant opened: " + ", ".join(opened)
