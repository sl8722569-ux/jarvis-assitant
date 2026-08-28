"""Installed-app launch with install ask + official website fallback. No silent installs."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _user() -> str:
    return os.environ.get("USERNAME", "")


def _expand(p: str) -> str:
    return os.path.expandvars(p.replace("{user}", _user()))


# Official apps only. website = legitimate service. winget_id = Microsoft/winget package if any.
CATALOG: list[dict[str, Any]] = [
    {
        "id": "chrome",
        "names": ["chrome", "google chrome", "googlechrome"],
        "paths": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{user}\AppData\Local\Google\Chrome\Application\chrome.exe",
        ],
        "which": ["chrome", "chrome.exe"],
        "winget_id": "Google.Chrome",
        "store": None,
        "website": "https://www.google.com/chrome/",
        "web_app": "https://www.google.com",
    },
    {
        "id": "edge",
        "names": ["edge", "microsoft edge", "msedge"],
        "paths": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ],
        "which": ["msedge"],
        "winget_id": "Microsoft.Edge",
        "website": "https://www.microsoft.com/edge",
        "web_app": None,
    },
    {
        "id": "firefox",
        "names": ["firefox", "mozilla", "mozilla firefox"],
        "paths": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ],
        "which": ["firefox"],
        "winget_id": "Mozilla.Firefox",
        "website": "https://www.mozilla.org/firefox/",
        "web_app": None,
    },
    {
        "id": "vscode",
        "names": ["vscode", "vs code", "visual studio code", "code"],
        "paths": [
            r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            r"C:\Program Files\Microsoft VS Code\Code.exe",
        ],
        "which": ["code", "code.cmd"],
        "winget_id": "Microsoft.VisualStudioCode",
        "website": "https://code.visualstudio.com/",
        "web_app": None,
    },
    {
        "id": "notepad",
        "names": ["notepad"],
        "paths": [r"C:\Windows\System32\notepad.exe"],
        "which": ["notepad"],
        "winget_id": None,
        "website": None,
        "web_app": None,
    },
    {
        "id": "calculator",
        "names": ["calculator", "calc"],
        "paths": [r"C:\Windows\System32\calc.exe"],
        "which": ["calc"],
        "winget_id": None,
        "website": None,
        "web_app": None,
    },
    {
        "id": "paint",
        "names": ["paint", "mspaint"],
        "paths": [r"C:\Windows\System32\mspaint.exe"],
        "which": ["mspaint"],
        "winget_id": None,
        "website": None,
        "web_app": None,
    },
    {
        "id": "explorer",
        "names": ["explorer", "file explorer", "files"],
        "paths": [r"C:\Windows\explorer.exe"],
        "which": ["explorer"],
        "winget_id": None,
        "website": None,
        "web_app": None,
    },
    {
        "id": "settings",
        "names": ["settings", "windows settings"],
        "paths": [],
        "uri": "ms-settings:",
        "which": [],
        "winget_id": None,
        "website": None,
        "web_app": None,
    },
    {
        "id": "steam",
        "names": ["steam"],
        "paths": [
            r"C:\Program Files (x86)\Steam\steam.exe",
            r"C:\Program Files\Steam\steam.exe",
        ],
        "which": ["steam"],
        "winget_id": "Valve.Steam",
        "website": "https://store.steampowered.com/",
        "web_app": "https://store.steampowered.com/",
    },
    {
        "id": "spotify",
        "names": ["spotify"],
        "paths": [r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe"],
        "which": ["spotify"],
        "winget_id": "Spotify.Spotify",
        "website": "https://open.spotify.com/",
        "web_app": "https://open.spotify.com/",
    },
    {
        "id": "discord",
        "names": ["discord"],
        "paths": [r"C:\Users\{user}\AppData\Local\Discord\Update.exe"],
        "which": ["discord"],
        "winget_id": "Discord.Discord",
        "website": "https://discord.com/app",
        "web_app": "https://discord.com/app",
    },
    {
        "id": "teams",
        "names": ["teams", "microsoft teams", "ms teams"],
        "paths": [
            r"C:\Users\{user}\AppData\Local\Microsoft\Teams\current\Teams.exe",
            r"C:\Users\{user}\AppData\Local\Microsoft\WindowsApps\ms-teams.exe",
        ],
        "which": ["ms-teams", "Teams"],
        "winget_id": "Microsoft.Teams",
        "website": "https://teams.microsoft.com/",
        "web_app": "https://teams.microsoft.com/",
    },
    {
        "id": "whatsapp",
        "names": ["whatsapp"],
        "paths": [
            r"C:\Users\{user}\AppData\Local\WhatsApp\WhatsApp.exe",
        ],
        "which": ["whatsapp"],
        "winget_id": "9NKSQGP7F2NH",
        "store": "ms-windows-store://pdp/?productid=9NKSQGP7F2NH",
        "website": "https://web.whatsapp.com/",
        "web_app": "https://web.whatsapp.com/",
    },
    {
        "id": "gmail",
        "names": ["gmail", "google mail", "googlemail"],
        "paths": [],
        "which": [],
        "winget_id": None,
        "store": None,
        "website": "https://mail.google.com/",
        "web_app": "https://mail.google.com/",
    },
    {
        "id": "youtube",
        "names": ["youtube"],
        "paths": [],
        "which": [],
        "winget_id": None,
        "website": "https://www.youtube.com/",
        "web_app": "https://www.youtube.com/",
    },
    {
        "id": "github",
        "names": ["github"],
        "paths": [r"C:\Users\{user}\AppData\Local\GitHubDesktop\GitHubDesktop.exe"],
        "which": ["github"],
        "winget_id": "GitHub.GitHubDesktop",
        "website": "https://github.com/",
        "web_app": "https://github.com/",
    },
    {
        "id": "outlook",
        "names": ["outlook", "mail"],
        "paths": [
            r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
            r"C:\Users\{user}\AppData\Local\Microsoft\WindowsApps\olk.exe",
        ],
        "which": ["outlook", "olk"],
        "winget_id": None,
        "website": "https://outlook.live.com/",
        "web_app": "https://outlook.live.com/",
    },
]


def resolve(name: str) -> dict[str, Any] | None:
    t = (name or "").lower().strip()
    t = t.replace("the ", "").replace("app", "").strip()
    best = None
    best_len = 0
    for item in CATALOG:
        for n in item["names"]:
            if t == n or t.startswith(n + " ") or n == t:
                if len(n) >= best_len:
                    best, best_len = item, len(n)
    return best


def installed_path(item: dict[str, Any]) -> str | None:
    if item.get("uri"):
        return item["uri"]
    for raw in item.get("paths") or []:
        p = Path(_expand(raw))
        if p.is_file():
            return str(p)
        # skip directory-only placeholders (WhatsApp WindowsApps)
        if p.suffix.lower() == ".exe" and p.exists():
            return str(p)
    for cmd in item.get("which") or []:
        found = shutil.which(cmd)
        if found:
            return found
    return None


def launch_installed(item: dict[str, Any]) -> tuple[bool, str]:
    uri = item.get("uri")
    if uri:
        subprocess.run(["cmd", "/c", "start", "", uri], creationflags=0x08000000, timeout=20)
        return True, f"Opened {item['id']}."
    path = installed_path(item)
    if not path:
        return False, f"{item['id']} is not installed."
    try:
        os.startfile(path)  # type: ignore[attr-defined]
        return True, f"Opening {item['id']}."
    except OSError as e:
        return False, f"Could not start {item['id']}: {e}"


def try_install(item: dict[str, Any]) -> str:
    """Visible, official installer only. Never silent. May still show UAC."""
    store = item.get("store")
    winget = item.get("winget_id")
    if store:
        subprocess.Popen(["cmd", "/c", "start", "", store], creationflags=0x08000000)
        return (
            f"Opened the Microsoft Store page for {item['id']}. "
            "I will not install it for you — you confirm in the Store."
        )
    if winget and shutil.which("winget"):
        subprocess.Popen(
            ["winget", "install", "--id", winget, "-e"],
            creationflags=0x08000000,
        )
        return (
            f"Started the official winget installer for {item['id']}. "
            "Windows may ask you to approve. I will not bypass UAC, PIN, or passwords."
        )
    site = item.get("website")
    if site:
        return (
            f"I cannot install {item['id']} from here (no Store/winget package on this PC). "
            f"Official download page: {site}. Say yes if I should open that page."
        )
    return f"No legitimate installer is configured for {item['id']}."
