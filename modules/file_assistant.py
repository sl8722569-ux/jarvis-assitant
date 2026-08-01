"""Safe file assistant — user folders only, no deletes of personal files."""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .permissions import PermissionManager


SAFE_ROOTS = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Pictures",
    Path.home() / "Music",
    Path.home() / "Videos",
    Path.home() / "JARVIS",
]


class FileAssistant:
    def __init__(self, permissions: PermissionManager, log=None):
        self.permissions = permissions
        self.log = log

    def _ok(self) -> tuple[bool, str]:
        return self.permissions.require("file_access")

    def _is_safe(self, path: Path) -> bool:
        try:
            resolved = path.expanduser().resolve()
            for root in SAFE_ROOTS:
                try:
                    resolved.relative_to(root.resolve())
                    return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False

    def list_folder(self, name: str = "downloads") -> str:
        ok, msg = self._ok()
        if not ok:
            return msg
        mapping = {
            "desktop": Path.home() / "Desktop",
            "documents": Path.home() / "Documents",
            "downloads": Path.home() / "Downloads",
            "pictures": Path.home() / "Pictures",
            "music": Path.home() / "Music",
            "videos": Path.home() / "Videos",
        }
        folder = mapping.get(name.lower().strip(), Path.home() / "Downloads")
        if not folder.exists():
            return f"Folder not found: {folder}"
        items = []
        try:
            for p in sorted(folder.iterdir(), key=lambda x: x.name.lower())[:30]:
                kind = "DIR" if p.is_dir() else "FILE"
                size = ""
                if p.is_file():
                    size = f" ({p.stat().st_size // 1024} KB)"
                items.append(f"[{kind}] {p.name}{size}")
        except Exception as e:
            return f"Could not list folder: {e}"
        if not items:
            return f"{folder} is empty."
        return f"Contents of {folder} (max 30):\n" + "\n".join(items)

    def find(self, query: str, limit: int = 15) -> str:
        ok, msg = self._ok()
        if not ok:
            return msg
        q = query.lower().strip()
        hits: list[str] = []
        for root in SAFE_ROOTS:
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
            return f"No files matching '{query}' in safe user folders."
        return "Found:\n" + "\n".join(hits)

    def open_path(self, path_str: str) -> str:
        ok, msg = self._ok()
        if not ok:
            return msg
        p = Path(path_str).expanduser()
        if not p.exists():
            # try search by name
            found = self.find(path_str, limit=1)
            if found.startswith("Found:"):
                line = found.split("\n", 1)[1].split("\n")[0]
                p = Path(line)
            else:
                return f"Path not found: {path_str}"
        if not self._is_safe(p):
            return "Blocked: only Desktop, Documents, Downloads, Pictures, Music, Videos, JARVIS folders are allowed."
        try:
            os.startfile(str(p))  # type: ignore[attr-defined]
            return f"Opened {p}"
        except Exception as e:
            return f"Could not open: {e}"

    def copy_in_safe_zone(self, src: str, dest_folder: str = "desktop") -> str:
        """Copy file between safe folders only — never deletes source."""
        ok, msg = self._ok()
        if not ok:
            return msg
        src_p = Path(src).expanduser()
        if not src_p.exists() or not src_p.is_file():
            return "Source file not found."
        if not self._is_safe(src_p):
            return "Source not in safe folders."
        mapping = {
            "desktop": Path.home() / "Desktop",
            "documents": Path.home() / "Documents",
            "downloads": Path.home() / "Downloads",
        }
        dest_dir = mapping.get(dest_folder.lower(), Path.home() / "Desktop")
        dest = dest_dir / src_p.name
        if not self._is_safe(dest_dir):
            return "Destination not safe."
        try:
            shutil.copy2(src_p, dest)
            return f"Copied to {dest} (original kept)."
        except Exception as e:
            return f"Copy failed: {e}"
