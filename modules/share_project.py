"""
Share J.A.R.V.I.S [EARLY ACCESS] public project link only.

Never shares personal settings, logs, API keys, chats, or files.
Used by Settings → "Share Jarvis". Optional and user-controlled.
"""
from __future__ import annotations

import subprocess
import urllib.parse
import webbrowser
from typing import Any


# Product branding (Phase 1)
PRODUCT_NAME = "J.A.R.V.I.S [EARLY ACCESS]"

# Placeholder until a real public URL is set in config → project.official_url
DEFAULT_OFFICIAL_URL = "https://github.com/YOUR_USERNAME/jarvis-early-access"
DEFAULT_SHARE_TEXT = (
    f"Try {PRODUCT_NAME} — a lightweight personal Windows AI assistant. "
    "Phase 1 · privacy-first · free & open source."
)


def get_share_payload(config: dict[str, Any] | None = None) -> dict[str, str]:
    """Build public share text + URL (no secrets, no local paths)."""
    cfg = config or {}
    project = cfg.get("project") or {}
    url = (project.get("official_url") or DEFAULT_OFFICIAL_URL).strip()
    text = (project.get("share_text") or DEFAULT_SHARE_TEXT).strip()
    # Always lead with product name if missing
    if "J.A.R.V.I.S" not in text.upper().replace(" ", ""):
        text = f"{PRODUCT_NAME}\n{text}"
    message = f"{text}\n\n{url}"
    return {
        "url": url,
        "text": text,
        "message": message,
        "product": PRODUCT_NAME,
    }


def copy_to_clipboard(text: str) -> bool:
    """Copy text to Windows clipboard."""
    try:
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
    Share the official J.A.R.V.I.S [EARLY ACCESS] project link.

    methods: copy | system | browser
    """
    payload = get_share_payload(config)
    url = payload["url"]
    message = payload["message"]
    product = payload["product"]

    if "YOUR_USERNAME" in url:
        note = (
            f"\n\nNote: set project.official_url in config to your real public page for {product}."
        )
    else:
        note = ""

    method = (method or "copy").lower().strip()

    if method == "browser":
        intent = "https://twitter.com/intent/tweet?text=" + urllib.parse.quote(message)
        webbrowser.open(intent, new=2)
        return (
            f"Opened a public share draft for {product} (project link only — no private data).{note}"
        )

    if method == "system":
        copy_to_clipboard(message)
        return (
            f"{product} public link copied. Paste into WhatsApp, Discord, email, etc. "
            f"(No settings, logs, or personal files included.){note}"
        )

    ok = copy_to_clipboard(message)
    if ok:
        return (
            f"{product} link copied to clipboard (public info only).\n{url}{note}"
        )
    return f"Could not use clipboard. Share this link manually:\n{url}{note}"
