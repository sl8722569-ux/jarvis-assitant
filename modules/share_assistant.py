"""Sharing helpers — WhatsApp Web etc. Always confirm before send actions."""
from __future__ import annotations

import urllib.parse
import webbrowser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .permissions import PermissionManager


class ShareAssistant:
    def __init__(self, permissions: PermissionManager, log=None):
        self.permissions = permissions
        self.log = log
        self.pending: dict | None = None

    def open_whatsapp_web(self) -> str:
        ok, msg = self.permissions.require("share_apps")
        if not ok:
            ok2, msg2 = self.permissions.require("web_open")
            if not ok2:
                return msg
        webbrowser.open("https://web.whatsapp.com/", new=2)
        if self.log:
            self.log.event("share_open", {"app": "whatsapp_web"})
        return "Opened WhatsApp Web. Log in if needed. I will never send a message without your confirmation."

    def prepare_whatsapp_message(self, text: str, phone: str | None = None) -> str:
        """Stage a message — does NOT send until user confirms."""
        ok, msg = self.permissions.require("share_apps")
        if not ok:
            return msg
        text = (text or "").strip()
        if not text:
            return "What message should I prepare for WhatsApp?"
        self.pending = {"app": "whatsapp", "text": text, "phone": phone}
        preview = text if len(text) < 120 else text[:117] + "..."
        phone_bit = f" to {phone}" if phone else ""
        return (
            f"Ready to share on WhatsApp{phone_bit}:\n\"{preview}\"\n\n"
            "Say 'confirm share' or 'send it' to open WhatsApp with this message. "
            "Say 'cancel share' to abort. I will not send without confirmation."
        )

    def confirm_share(self) -> str:
        if not self.pending:
            return "Nothing pending to share."
        ok, msg = self.permissions.require("share_apps")
        if not ok:
            return msg
        item = self.pending
        self.pending = None
        if item.get("app") == "whatsapp":
            text = urllib.parse.quote(item.get("text") or "")
            phone = (item.get("phone") or "").strip()
            if phone:
                phone = "".join(ch for ch in phone if ch.isdigit() or ch == "+")
                url = f"https://wa.me/{phone.lstrip('+')}?text={text}"
            else:
                # Opens WhatsApp Web; user still chooses chat — message in URL for wa.me only
                url = f"https://web.whatsapp.com/send?text={text}"
            webbrowser.open(url, new=2)
            if self.log:
                self.log.event("share_confirm", {"app": "whatsapp"})
            return (
                "Opened WhatsApp with your message drafted. "
                "Please review and press send yourself — Jarvis does not auto-send."
            )
        return "Unknown pending share."

    def cancel_share(self) -> str:
        self.pending = None
        return "Share cancelled."
