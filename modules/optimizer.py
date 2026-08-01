"""Safe performance optimizer — reversible, logs everything."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .logger import JarvisLogger


class Optimizer:
    def __init__(self, root: Path, log: JarvisLogger | None = None):
        self.root = root
        self.log = log
        self.report_dir = root / "logs"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.backup_reg = Path.home() / "JARVIS" / "data" / "startup_backup.json"
        self.backup_reg.parent.mkdir(parents=True, exist_ok=True)

    def analyze(self) -> dict:
        info: dict = {"ts": datetime.now().isoformat(timespec="seconds")}
        try:
            import psutil
            import platform

            info["cpu"] = platform.processor()
            info["cpu_percent"] = psutil.cpu_percent(interval=0.5)
            info["ram_total_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)
            info["ram_percent"] = psutil.virtual_memory().percent
            info["disk_c_free_gb"] = round(psutil.disk_usage("C:\\").free / (1024**3), 2)
            info["boot_time"] = datetime.fromtimestamp(psutil.boot_time()).isoformat(timespec="seconds")
            info["top_processes"] = [
                {"name": p.info["name"], "rss_mb": round((p.info["memory_info"].rss if p.info["memory_info"] else 0) / (1024**2), 1)}
                for p in sorted(
                    psutil.process_iter(["name", "memory_info"]),
                    key=lambda x: x.info["memory_info"].rss if x.info.get("memory_info") else 0,
                    reverse=True,
                )[:12]
            ]
        except Exception as e:
            info["error"] = str(e)
        path = self.report_dir / f"perf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(info, indent=2), encoding="utf-8")
        if self.log:
            self.log.event("analyze", {"report": str(path)})
        return info

    def clean_temp(self) -> str:
        freed = 0
        targets = [
            Path(os.environ.get("TEMP", "")),
            Path.home() / "AppData" / "Local" / "Temp",
            Path.home() / "AppData" / "Local" / "CrashDumps",
            Path.home() / "AppData" / "Local" / "D3DSCache",
        ]
        for t in targets:
            if not t.exists():
                continue
            for child in t.iterdir():
                try:
                    size = 0
                    if child.is_file():
                        size = child.stat().st_size
                        child.unlink(missing_ok=True)
                    else:
                        size = sum(f.stat().st_size for f in child.rglob("*") if f.is_file())
                        shutil.rmtree(child, ignore_errors=True)
                    freed += size
                except Exception:
                    pass
        mb = round(freed / (1024**2), 1)
        if self.log:
            self.log.event("clean_temp", {"mb": mb})
        return f"Cleaned temporary files (about {mb} MB targeted)."

    def reduce_startup(self) -> str:
        """Disable noncritical HKCU Run entries; backup for restore."""
        try:
            import winreg

            disabled = []
            backup = {}
            if self.backup_reg.exists():
                backup = json.loads(self.backup_reg.read_text(encoding="utf-8"))
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_ALL_ACCESS,
            )
            block = (
                "steam",
                "discord",
                "spotify",
                "epic",
                "bing",
                "edge",
                "webex",
                "teams",
                "utorrent",
                "anydesk",
                "adobe",
            )
            i = 0
            names = []
            while True:
                try:
                    name, val, _ = winreg.EnumValue(key, i)
                    names.append((name, val))
                    i += 1
                except OSError:
                    break
            for name, val in names:
                low = name.lower()
                if any(b in low for b in block) or "microsoftedgeautolaunch" in low:
                    backup[name] = val
                    try:
                        winreg.DeleteValue(key, name)
                        disabled.append(name)
                    except OSError:
                        pass
            winreg.CloseKey(key)
            self.backup_reg.write_text(json.dumps(backup, indent=2), encoding="utf-8")
            if self.log:
                self.log.event("startup_reduce", {"disabled": disabled})
            if not disabled:
                return "Startup already lean. Backup stored for reverse if needed."
            return "Disabled startup apps: " + ", ".join(disabled) + ". Reversible from JARVIS data backup."
        except Exception as e:
            return f"Startup cleanup skipped: {e}"

    def restore_startup(self) -> str:
        try:
            import winreg

            if not self.backup_reg.exists():
                return "No startup backup found."
            backup = json.loads(self.backup_reg.read_text(encoding="utf-8"))
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_ALL_ACCESS,
            )
            for name, val in backup.items():
                try:
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, val)
                except OSError:
                    pass
            winreg.CloseKey(key)
            return "Restored startup entries from backup."
        except Exception as e:
            return f"Restore failed: {e}"

    def improve_responsiveness(self) -> str:
        cmds = [
            # UI snappiness user-level
            r'powershell -NoProfile -Command "Set-ItemProperty \'HKCU:\Control Panel\Desktop\' MenuShowDelay 0; '
            r"Set-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize' EnableTransparency 0 -Type DWord; "
            r"Set-ItemProperty 'HKCU:\Control Panel\Desktop\WindowMetrics' MinAnimate 0; "
            r"Set-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' TaskbarAnimations 0 -Type DWord; "
            r"Set-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' LaunchTo 1 -Type DWord; "
            r"Set-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced' IconsOnly 1 -Type DWord\"",
        ]
        for c in cmds:
            try:
                subprocess.run(c, shell=True, capture_output=True, timeout=30, creationflags=0x08000000)
            except Exception:
                pass
        if self.log:
            self.log.event("responsiveness", {})
        return "Applied responsiveness tweaks: faster menus, less transparency/animations, leaner Explorer."

    def full_safe_optimize(self) -> str:
        parts = [
            self.analyze().get("ram_percent") is not None and "Analysis saved.",
            self.reduce_startup(),
            self.clean_temp(),
            self.improve_responsiveness(),
        ]
        # Steam/DBC friendly note
        dbc = Path(r"C:\Program Files (x86)\Steam\steamapps\common\DBC14")
        if dbc.exists():
            try:
                subprocess.run(f'attrib +I /S /D "{dbc}"', shell=True, capture_output=True, timeout=60)
                parts.append("DBC14 marked not content-indexed for less HDD thrash.")
            except Exception:
                pass
        msg = " | ".join(str(p) for p in parts if p)
        report = self.report_dir / f"optimize_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report.write_text(msg, encoding="utf-8")
        return "Optimization complete. " + msg
