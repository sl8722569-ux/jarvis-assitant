"""Permission manager — no mic/file/screen/app access without consent. Reversible."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULTS = {
    "microphone": False,
    "file_access": False,
    "screen": False,
    "app_control": False,
    "web_open": False,
    "share_apps": False,
    "cloud_ai": False,
}


class PermissionManager:
    """Stores grants in data/permissions.json. Revocable anytime."""

    def __init__(self, data_dir: Path, log=None):
        self.path = data_dir / "permissions.json"
        self.log = log
        self.data_dir = data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        self.grants: dict[str, Any] = dict(DEFAULTS)
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                for k in DEFAULTS:
                    if k in raw:
                        self.grants[k] = bool(raw[k])
                self.grants["_updated"] = raw.get("_updated")
            except Exception:
                pass

    def save(self) -> None:
        payload = {k: bool(self.grants.get(k, False)) for k in DEFAULTS}
        payload["_updated"] = datetime.now().isoformat(timespec="seconds")
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        if self.log:
            self.log.event("permissions_save", payload)

    def is_allowed(self, key: str) -> bool:
        return bool(self.grants.get(key, False))

    def grant(self, key: str) -> str:
        if key not in DEFAULTS:
            return f"Unknown permission: {key}"
        self.grants[key] = True
        self.save()
        return f"Permission granted: {key}. You can revoke it anytime in Settings."

    def revoke(self, key: str) -> str:
        if key not in DEFAULTS:
            return f"Unknown permission: {key}"
        self.grants[key] = False
        self.save()
        return f"Permission revoked: {key}."

    def revoke_all(self) -> str:
        for k in DEFAULTS:
            self.grants[k] = False
        self.save()
        return "All permissions revoked."

    def set_many(self, mapping: dict[str, bool]) -> None:
        for k, v in mapping.items():
            if k in DEFAULTS:
                self.grants[k] = bool(v)
        self.save()

    def status_text(self) -> str:
        lines = ["Permission status:"]
        for k in DEFAULTS:
            flag = "ALLOWED" if self.grants.get(k) else "DENIED"
            lines.append(f"  • {k}: {flag}")
        lines.append("Revoke anytime: Settings → Permissions, or say 'revoke microphone'.")
        return "\n".join(lines)

    def require(self, key: str) -> tuple[bool, str]:
        """Return (ok, message). Caller must not proceed if not ok."""
        if self.is_allowed(key):
            return True, ""
        labels = {
            "microphone": "microphone / voice input",
            "file_access": "file browsing (safe user folders only)",
            "screen": "screen-related actions",
            "app_control": "opening or closing apps",
            "web_open": "opening websites",
            "share_apps": "sharing via WhatsApp Web / similar apps",
            "cloud_ai": "optional cloud AI (ChatGPT/Gemini APIs)",
        }
        label = labels.get(key, key)
        return False, (
            f"Permission needed for {label}. "
            f"Enable it in Settings → Permissions, or say 'allow {key.replace('_', ' ')}'."
        )
