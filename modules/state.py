"""Shared runtime state — UI states, theme, personality, permissions snapshot."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class JarvisState:
    running: bool = True
    active: bool = False
    conversation_mode: bool = False
    paused: bool = False
    wake_word: bool = True
    hotkey: bool = True
    voice_listen: bool = True
    voice_speak: bool = True
    language: str = "en"
    personality: str = "friendly"
    theme: str = "midnight_hud"
    animation: str = "hud"  # heartbeat | waveform | robot | hud | none
    ui_state: str = "standby"  # listening | thinking | speaking | standby
    last_heard: str = ""
    last_reply: str = ""
    last_event: str = "boot"
    tasks: list[str] = field(default_factory=list)
    status_message: str = "Standby"
    voice_volume: float = 1.0
    voice_rate: int = 165
    room_boost: bool = True
    animations_enabled: bool = True
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def set_task(self, name: str, on: bool = True) -> None:
        with self._lock:
            if on and name not in self.tasks:
                self.tasks.append(name)
            if not on and name in self.tasks:
                self.tasks.remove(name)

    def set_ui_state(self, mode: str) -> None:
        if mode in ("listening", "thinking", "speaking", "standby"):
            self.ui_state = mode

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "time": datetime.now().strftime("%H:%M:%S"),
                "running": self.running,
                "active": self.active,
                "conversation_mode": self.conversation_mode,
                "paused": self.paused,
                "wake_word": self.wake_word,
                "hotkey": self.hotkey,
                "voice_listen": self.voice_listen,
                "voice_speak": self.voice_speak,
                "language": self.language,
                "personality": self.personality,
                "theme": self.theme,
                "animation": self.animation,
                "ui_state": self.ui_state,
                "last_heard": self.last_heard,
                "last_reply": self.last_reply[:120],
                "last_event": self.last_event,
                "tasks": list(self.tasks),
                "status_message": self.status_message,
                "voice_volume": self.voice_volume,
                "voice_rate": self.voice_rate,
                "room_boost": self.room_boost,
                "animations_enabled": self.animations_enabled,
            }
