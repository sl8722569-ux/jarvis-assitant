"""Open websites safely with permission check."""
from __future__ import annotations

import re
import webbrowser
from typing import TYPE_CHECKING
from urllib.parse import quote_plus

if TYPE_CHECKING:
    from .permissions import PermissionManager


SITE_MAP = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com",
    "whatsapp web": "https://web.whatsapp.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "reddit": "https://www.reddit.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "wikipedia": "https://www.wikipedia.org",
    "maps": "https://maps.google.com",
    "news": "https://news.google.com",
}


class WebOps:
    def __init__(self, permissions: PermissionManager, log=None):
        self.permissions = permissions
        self.log = log

    def open_site(self, name_or_url: str) -> str:
        ok, msg = self.permissions.require("web_open")
        if not ok:
            return msg
        raw = (name_or_url or "").strip()
        if not raw:
            return "Which website should I open?"
        low = raw.lower()
        if low in SITE_MAP:
            url = SITE_MAP[low]
        elif re.match(r"^https?://", raw, re.I):
            url = raw
        elif "." in raw and " " not in raw:
            url = "https://" + raw.lstrip("/")
        else:
            url = SITE_MAP.get(low)
            if not url:
                url = f"https://www.google.com/search?q={quote_plus(raw)}"
                webbrowser.open(url, new=2)
                return f"Searching the web for: {raw}"
        webbrowser.open(url, new=2)
        if self.log:
            self.log.event("web_open", {"url": url})
        return f"Opening {url}"

    def search(self, query: str) -> str:
        ok, msg = self.permissions.require("web_open")
        if not ok:
            return msg
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        webbrowser.open(url, new=2)
        return f"Searching for: {query}"
