"""Safe system operations — reversible, no personal file deletion."""
from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .logger import JarvisLogger


def _run(cmd: list[str] | str, shell: bool = False) -> tuple[int, str]:
    try:
        flags = 0x08000000 if os.name == "nt" else 0
        r = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=flags,
        )
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode, out.strip()
    except Exception as e:
        return 1, str(e)


class SystemOps:
    APP_MAP = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "paint": "mspaint.exe",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "steam": r"C:\Program Files (x86)\Steam\steam.exe",
        "settings": "ms-settings:",
        "task manager": "taskmgr.exe",
        "vscode": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "code": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "dbc14": r"C:\Program Files (x86)\Steam\steamapps\common\DBC14\cricket14.exe",
        "don bradman": r"C:\Program Files (x86)\Steam\steamapps\common\DBC14\cricket14.exe",
        "cricket": r"C:\Program Files (x86)\Steam\steamapps\common\DBC14\cricket14.exe",
    }

    FOLDER_MAP = {
        "downloads": str(Path.home() / "Downloads"),
        "documents": str(Path.home() / "Documents"),
        "desktop": str(Path.home() / "Desktop"),
        "pictures": str(Path.home() / "Pictures"),
        "music": str(Path.home() / "Music"),
        "videos": str(Path.home() / "Videos"),
        "home": str(Path.home()),
        "steam": r"C:\Program Files (x86)\Steam",
        "jarvis": str(Path.home() / "JARVIS"),
    }

    def __init__(self, log: JarvisLogger | None = None):
        self.log = log
        self.user = os.environ.get("USERNAME", "")
        self._muted = False

    def open_app(self, name: str) -> str:
        key = name.lower().strip()
        target = self.APP_MAP.get(key)
        if not target:
            known = ", ".join(sorted(self.APP_MAP.keys()))
            return f"I only open known apps ({known}). I will not run arbitrary names."
        target = target.replace("{user}", self.user)
        if target.startswith("ms-settings"):
            _run(["cmd", "/c", "start", target])
            return "Opened Settings."
        path = Path(target)
        if path.exists():
            os.startfile(str(path))  # type: ignore[attr-defined]
            return f"Opening {name}."
        code, _ = _run(["cmd", "/c", "start", "", target])
        return f"Opening {name}." if code == 0 else f"Could not find {name}."

    def close_app(self, name: str) -> str:
        mapping = {
            "edge": "msedge.exe",
            "chrome": "chrome.exe",
            "notepad": "notepad.exe",
            "steam": "steam.exe",
            "code": "Code.exe",
            "vscode": "Code.exe",
            "copilot": "M365Copilot.exe",
            "dbc14": "cricket14.exe",
            "cricket": "cricket14.exe",
        }
        key = name.lower().strip()
        proc = mapping.get(key, name if key.endswith(".exe") else f"{name}.exe")
        code, _ = _run(["taskkill", "/F", "/IM", proc, "/T"])
        return f"Closed {name}." if code == 0 else f"Could not close {name} (maybe not running)."

    def open_folder(self, name: str) -> str:
        key = name.lower().strip()
        if key not in self.FOLDER_MAP:
            return "Unknown folder. Try downloads, documents, desktop, or home."
        path = self.FOLDER_MAP[key]
        p = Path(path)
        if p.exists():
            os.startfile(str(p))  # type: ignore[attr-defined]
            return f"Opened {path}."
        return f"Folder not found: {path}"

    def set_volume(self, level: int | None = None, mute: bool | None = None, direction: str | None = None) -> str:
        def _key(code: int, times: int = 1) -> None:
            for _ in range(times):
                _run(
                    f'powershell -NoProfile -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]{code})"',
                    shell=True,
                )

        if mute is True:
            if not self._muted:
                _key(173)
                self._muted = True
            return "Muted."
        if mute is False:
            if self._muted:
                _key(173)
                self._muted = False
            return "Unmuted."
        if direction == "up":
            for _ in range(4):
                _run(
                    'powershell -NoProfile -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"',
                    shell=True,
                )
            return "Volume up."
        if direction == "down":
            for _ in range(4):
                _run(
                    'powershell -NoProfile -Command "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"',
                    shell=True,
                )
            return "Volume down."
        if level is not None:
            level = max(0, min(100, int(level)))
            _key(174, 50)
            steps = max(0, level // 2)
            if steps:
                _key(175, steps)
            if self._muted:
                _key(173)
                self._muted = False
            return f"Volume set near {level}%."
        return "Specify volume up, down, mute, or unmute."

    def battery_info(self) -> str:
        try:
            import psutil

            b = psutil.sensors_battery()
            if not b:
                return "No battery information available."
            plug = "plugged in" if b.power_plugged else "on battery"
            return f"Battery at {int(b.percent)} percent, {plug}."
        except Exception:
            code, out = _run(
                'powershell -NoProfile -Command "(Get-CimInstance Win32_Battery).EstimatedChargeRemaining"',
                shell=True,
            )
            if out.strip().isdigit():
                return f"Battery at approximately {out.strip()} percent."
            return "Could not read battery status."

    def system_info(self) -> str:
        try:
            import psutil

            cpu = psutil.cpu_percent(interval=0.4)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")
            return (
                f"CPU usage {cpu:.0f} percent. "
                f"RAM {mem.percent:.0f} percent used "
                f"({mem.available // (1024**2)} MB free). "
                f"Disk C {disk.percent:.0f} percent used "
                f"({disk.free // (1024**3)} GB free). "
                f"System {platform.system()} {platform.release()}."
            )
        except Exception:
            return f"System {platform.platform()}."

    def search_files(self, query: str, limit: int = 12) -> str:
        roots = [Path.home() / "Desktop", Path.home() / "Documents", Path.home() / "Downloads"]
        hits: list[str] = []
        q = query.lower()
        for root in roots:
            if not root.exists():
                continue
            try:
                for p in root.rglob("*"):
                    if p.is_file() and q in p.name.lower():
                        hits.append(str(p))
                        if len(hits) >= limit:
                            break
            except Exception:
                continue
            if len(hits) >= limit:
                break
        if not hits:
            return f"No files matching '{query}' in Desktop, Documents, or Downloads."
        return "Found: " + "; ".join(hits[:limit])

    def run_command_safe(self, action: str) -> str:
        action = action.lower().strip()
        if action in ("lock", "lock screen"):
            _run(["rundll32.exe", "user32.dll,LockWorkStation"])
            return "Locking the screen."
        if action in ("empty recycle", "clear recycle bin"):
            _run(
                'powershell -NoProfile -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"',
                shell=True,
            )
            return "Recycle Bin cleared."
        if action in ("screenshot", "take screenshot"):
            _run(
                'powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; '
                "[System.Windows.Forms.SendKeys]::SendWait('{PrtSc}')\"",
                shell=True,
            )
            return "Screenshot captured to clipboard."
        return "Unknown system action."
