"""
Share JARVIS project link only — never personal settings, logs, or files.

Used by Settings → "Share Jarvis". User-controlled and optional.
"""
from __future__ import annotations

import subprocess
import urllib.parse
import webbrowser
from typing import Any


# Safe default until the user sets their real GitHub URL in config.json → project.official_url
DEFAULT_OFFICIAL_URL = "https://github.com/YOUR_USERNAME/jarvis-assistant"
DEFAULT_SHARE_TEXT = (
    "Try JARVIS — a lightweight personal Windows AI assistant "
    "(Early Access / Phase 1). Free, privacy-first, open source."
)


def get_share_payload(config: dict[str, Any] | None = None) -> dict[str, str]:
    """Build public share text + URL from config (no secrets, no local paths)."""
    cfg = config or {}
    project = cfg.get("project") or {}
    url = (project.get("official_url") or DEFAULT_OFFICIAL_URL).strip()
    text = (project.get("share_text") or DEFAULT_SHARE_TEXT).strip()
    # Never append API keys or local identity
    message = f"{text}\n\n{url}"
    return {"url": url, "text": text, "message": message}


def copy_to_clipboard(text: str) -> bool:
    """Copy text to Windows clipboard (lightweight)."""
    try:
        # clip.exe is available on modern Windows
        p = subprocess.run(
            ["clip"],
            input=text.encode("utf-16le"),
            check=False,
            capture_output=True,
            creationflags=0x08000000,
        )
        return p.returncode == 0
    except Exception:
        try:
            import tkinter as tk

            r = tk.Tk()
            r.withdraw()
            r.clipboard_clear()
            r.clipboard_append(text)
            r.update()
            r.destroy()
            return True
        except Exception:
            return False


def share_jarvis(config: dict[str, Any] | None = None, method: str = "copy") -> str:
    """
    Share the official project link.

    methods:
      - copy: clipboard only (safest default)
      - system: Windows share sheet if available
      - browser: open a prefilled share page (X/Twitter intent) with public text only
    """
    payload = get_share_payload(config)
    url = payload["url"]
    message = payload["message"]

    if "YOUR_USERNAME" in url:
        note = (
            " Official GitHub URL is still a placeholder. "
            "Set project.official_url in config.json before publishing."
        )
    else:
        note = ""

    method = (method or "copy").lower().strip()

    if method == "browser":
        # Public text only — no local settings
        intent = "https://twitter.com/intent/tweet?text=" + urllib.parse.quote(message)
        webbrowser.open(intent, new=2)
        return f"Opened a share draft in your browser with the public project link only.{note}"

    if method == "system":
        # PowerShell share helper — shares the message string, not files
        try:
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                f"[System.Windows.Forms.Clipboard]::SetText(@'\n{message}\n'@); "
                "Start-Process 'ms-windows-store://home'"
            )
            # Prefer clipboard + open default mail/share is unreliable; copy + instruct
            copy_to_clipboard(message)
            return (
                f"Project link copied for sharing (public URL only). "
                f"Paste it into WhatsApp, Discord, email, etc.{note}"
            )
        except Exception:
            copy_to_clipboard(message)
            return f"Link copied to clipboard.{note}"

    # default: copy
    ok = copy_to_clipboard(message)
    if ok:
        return (
            f"JARVIS project link copied to clipboard (public info only — "
            f"no settings, logs, or personal files).\n{url}{note}"
        )
    return f"Could not access clipboard. Share this link manually:\n{url}{note}"
