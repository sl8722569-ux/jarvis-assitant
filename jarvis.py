#!/usr/bin/env python3
"""
J.A.R.V.I.S — Early Access / Phase 1 (stable desktop foundation)

Windows entrypoint. Shared logic lives in modules/ for future
Windows packaged app, Linux, web, and mobile adapters (see platform/).

Designed for modest hardware: Intel i3, 8GB RAM, HDD.
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.ai_engine import AIEngine
from modules.ai_launcher import AILauncher
from modules.ai_providers import AIProviders
from modules.commands import CommandRouter
from modules.config_loader import Config
from modules.file_assistant import FileAssistant
from modules.language import is_exit_phrase, normalize_lang, phrase
from modules.logger import JarvisLogger
from modules.modes import ModeManager
from modules.optimizer import Optimizer
from modules.permissions import PermissionManager
from modules.share_assistant import ShareAssistant
from modules.state import JarvisState
from modules.stt_engine import STTEngine
from modules.system_ops import SystemOps
from modules.themes import get_theme
from modules.tts_engine import TTSEngine
from modules.ui import JarvisUI
from modules.web_ops import WebOps
from modules.share_project import share_jarvis


class Jarvis:
    def __init__(self):
        self.root = ROOT
        self.cfg = Config(self.root)
        self.log = JarvisLogger(self.root)
        self.log.info("JARVIS v3 starting…")

        data_dir = self.root / "data"
        data_dir.mkdir(exist_ok=True)
        self.permissions = PermissionManager(data_dir, self.log)

        vcfg = self.cfg.get("voice") or {}
        feats = self.cfg.get("features") or {}
        lang_cfg = self.cfg.get("languages") or {}
        ui_cfg = self.cfg.get("ui") or {}
        primary = normalize_lang(lang_cfg.get("primary") or "en")

        self.state = JarvisState(
            wake_word=bool(feats.get("wake_word", True)),
            hotkey=bool(feats.get("hotkey", True)),
            voice_listen=bool(feats.get("voice_listen", True)),
            voice_speak=bool(feats.get("voice_speak", True)),
            language=primary,
            personality=(self.cfg.get("personality_mode") or "friendly"),
            theme=ui_cfg.get("theme") or "midnight_hud",
            animation=ui_cfg.get("animation") or "hud",
            animations_enabled=bool(ui_cfg.get("animations_enabled", True)),
            voice_volume=float(vcfg.get("volume", 1.0)),
            voice_rate=int(vcfg.get("rate", 165)),
            room_boost=bool(vcfg.get("room_boost", True)),
            status_message="Standby — say Jarvis Activate",
            ui_state="standby",
        )

        self.providers = AIProviders(self.cfg.data, self.permissions, self.log)
        self.ops = SystemOps(self.log)
        self.ai = AIEngine(self.cfg.data, self.log, providers=self.providers)
        self.modes = ModeManager(self.ops, self.log)
        self.optimizer = Optimizer(self.root, self.log)
        self.launcher = AILauncher(self.cfg.data, self.log)
        self.files = FileAssistant(self.permissions, self.log)
        self.share = ShareAssistant(self.permissions, self.log)
        self.web = WebOps(self.permissions, self.log)

        self.tts = TTSEngine(
            rate=int(vcfg.get("rate", 165)),
            volume=float(vcfg.get("volume", 1.0)),
            style=str(vcfg.get("style", "jarvis")),
            prefer_male=bool(vcfg.get("prefer_male", True)),
            room_boost=bool(vcfg.get("room_boost", True)),
            enabled=bool(feats.get("voice_speak", True)),
            log=self.log,
        )
        self.stt = STTEngine(self.cfg.data, self.log)
        self.stt.set_language(primary)

        self.stop = False
        self.session_lock = threading.Lock()
        self._listen_thread: threading.Thread | None = None
        self.conv_cfg = self.cfg.get("conversation") or {}

        self.router = CommandRouter(
            self.ops,
            self.ai,
            self.modes,
            self.optimizer,
            self.launcher,
            self.permissions,
            self.files,
            self.share,
            self.web,
            providers=self.providers,
            tts=self.tts,
            log=self.log,
            on_exit=self.standby,
            on_pause=self.pause_features,
            on_resume=self.resume_features,
            on_conversation=self.start_conversation_mode,
            on_theme=self.set_theme,
            set_ui_state=self.set_ui_state,
        )

        self.ui = JarvisUI(
            state=self.state,
            permissions=self.permissions,
            on_activate=self.activate,
            on_text=self.handle_text_command,
            on_voice_toggle=self.toggle_speak,
            on_pause=self.pause_features,
            on_resume=self.resume_features,
            on_stop_features=self.stop_features,
            on_open_ai=self.open_named_ai,
            on_volume=self.set_voice_volume,
            on_mic_listen=self.talk_or_continue,
            on_conversation=self.start_conversation_mode,
            on_standby=self.standby,
            on_theme=self.set_theme,
            on_personality=self.set_personality,
            on_animation=self.set_animation,
            on_permission_change=self.permission_change,
            on_save_settings=self.save_settings,
            on_share_project=self.share_project,
        )

    # ----- UI helpers -----
    def set_ui_state(self, mode: str) -> None:
        self.state.set_ui_state(mode)
        self.ui.set_ui_state(mode)

    def _sync_lang(self) -> None:
        self.state.language = self.ai.language
        self.stt.set_language(self.ai.language)

    def speak(self, text: str, chat: bool = True) -> None:
        if not text:
            return
        self.state.last_reply = text
        self.state.last_event = "speak"
        self._sync_lang()
        if chat:
            self.ui.append_jarvis(text)
        self.set_ui_state("speaking")
        if self.state.voice_speak and self.tts.enabled:
            self.tts.speak(text, block=True)
        if self.state.active:
            self.set_ui_state("listening" if self.state.conversation_mode else "standby")
        else:
            self.set_ui_state("standby")

    def set_voice_volume(self, volume: float) -> None:
        self.tts.set_volume(volume)
        self.state.voice_volume = self.tts.volume
        try:
            self.cfg.data.setdefault("voice", {})["volume"] = self.tts.volume
            self.cfg.save()
        except Exception:
            pass

    def toggle_speak(self) -> None:
        self.state.voice_speak = not self.state.voice_speak
        self.tts.set_enabled(self.state.voice_speak)
        self.ui.append_system(f"Voice output {'ON' if self.state.voice_speak else 'OFF'}.")

    def open_named_ai(self, name: str) -> None:
        self.speak(self.launcher.launch(name))

    def set_theme(self, name: str) -> None:
        self.state.theme = name
        th = get_theme(name)
        self.state.animation = th.get("effect") or self.state.animation
        self.ui.apply_theme(name)
        self.cfg.data.setdefault("ui", {})["theme"] = name
        self.cfg.data["ui"]["animation"] = self.state.animation
        self.cfg.save()
        self.log.event("theme", {"name": name})

    def set_personality(self, mode: str) -> None:
        msg = self.ai.set_personality(mode)
        self.state.personality = self.ai.personality.mode
        self.cfg.data["personality_mode"] = self.state.personality
        self.cfg.save()
        self.ui.append_system(msg)
        self.speak(msg)

    def set_animation(self, name: str) -> None:
        self.state.animation = name
        self.cfg.data.setdefault("ui", {})["animation"] = name
        self.cfg.save()
        self.ui.append_system(f"Animation: {name}")

    def permission_change(self, key: str, value: bool) -> None:
        if key == "__all__":
            self.permissions.revoke_all()
            self.ui.append_system("All permissions revoked.")
            return
        if value:
            self.ui.append_system(self.permissions.grant(key))
        else:
            self.ui.append_system(self.permissions.revoke(key))

    def save_settings(self) -> None:
        self.cfg.data["personality_mode"] = self.state.personality
        ui = self.cfg.data.setdefault("ui", {})
        ui["theme"] = self.state.theme
        ui["animation"] = self.state.animation
        ui["animations_enabled"] = self.state.animations_enabled
        self.cfg.save()
        self.permissions.save()
        self.ui.append_system("Settings saved.")

    def share_project(self, method: str = "copy") -> None:
        """Settings → Share Jarvis: public project link only (no private data)."""
        msg = share_jarvis(self.cfg.data, method=method or "copy")
        self.ui.append_system(msg)
        self.log.event("share_project", {"method": method or "copy", "private_data": False})

    # ----- lifecycle -----
    def activate(self) -> None:
        if self.state.paused:
            self.resume_features()
        # Mic permission for voice after activate
        on_act = self.cfg.get("on_activate") or {}
        self.state.active = True
        self.state.conversation_mode = bool(self.conv_cfg.get("followup_after_activate", True))
        self.state.status_message = "Online"
        self.state.set_task("ai_session", True)
        self.set_ui_state("thinking")

        if on_act.get("open_app_window", True):
            self.ui.show_window(True)
            self.ui.set_active(True)

        if on_act.get("open_web_ai", False):
            threading.Thread(
                target=self.launcher.launch,
                args=(on_act.get("web_ai_provider") or "chatgpt",),
                daemon=True,
            ).start()

        greet = self.ai.personality.greeting(self.ai.language)
        if self.ai.language == "en" and self.cfg.get("greeting"):
            if self.ai.personality.mode == "friendly":
                greet = self.cfg.get("greeting") or greet

        self.log.event("activate", {})
        if on_act.get("speak_greeting", True):
            self.speak(greet)
        else:
            self.ui.append_jarvis(greet)

        # Follow-up listen without requiring wake word again
        if on_act.get("start_listening", True) and self.state.voice_listen:
            if self.permissions.is_allowed("microphone"):
                self._start_listen_loop(conversation=self.state.conversation_mode)
            else:
                self.ui.append_system(
                    "Voice follow-ups need microphone permission (Settings → Permissions)."
                )

    def start_conversation_mode(self) -> None:
        if self.state.paused:
            self.resume_features()
        if not self.permissions.is_allowed("microphone"):
            # Still allow text conversation
            self.ui.append_system(
                "Conversation (text) on. Allow microphone in Settings for voice turns."
            )
        self.state.active = True
        self.state.conversation_mode = True
        self.state.status_message = "Conversation mode"
        self.state.set_task("ai_session", True)
        self.state.set_task("conversation", True)
        self.ui.show_window(True)
        self.ui.set_active(True)
        msg = phrase("conversation_on", self.ai.language)
        self.speak(msg)
        self.log.event("conversation_on", {})
        if self.permissions.is_allowed("microphone") and self.state.voice_listen:
            self._start_listen_loop(conversation=True)

    def standby(self) -> None:
        self.state.active = False
        self.state.conversation_mode = False
        self.state.status_message = "Standby — say Jarvis Activate"
        self.state.set_task("ai_session", False)
        self.state.set_task("listening", False)
        self.state.set_task("conversation", False)
        self.set_ui_state("standby")
        msg = phrase("conversation_off", self.ai.language)
        self.ui.set_active(False, msg)
        if self.state.voice_speak:
            self.tts.speak(msg, block=False)
        self.log.event("standby", {})

    def deactivate(self) -> None:
        self.standby()

    def pause_features(self) -> None:
        self.state.paused = True
        self.state.active = False
        self.state.conversation_mode = False
        self.state.wake_word = False
        self.state.voice_listen = False
        self.state.status_message = "Paused"
        self.state.set_task("listening", False)
        self.state.set_task("wake_word", False)
        self.state.set_task("conversation", False)
        self.set_ui_state("standby")
        self.ui.append_system("Paused background listening. Text chat still works.")

    def resume_features(self) -> None:
        feats = self.cfg.get("features") or {}
        self.state.paused = False
        self.state.wake_word = bool(feats.get("wake_word", True))
        self.state.hotkey = bool(feats.get("hotkey", True))
        self.state.voice_listen = bool(feats.get("voice_listen", True))
        self.state.voice_speak = bool(feats.get("voice_speak", True))
        self.tts.set_enabled(self.state.voice_speak)
        self.state.status_message = "Resumed"
        self.state.set_task("wake_word", self.state.wake_word)
        self.ui.append_system("Features resumed.")

    def stop_features(self) -> None:
        self.state.paused = True
        self.state.active = False
        self.state.conversation_mode = False
        self.state.wake_word = False
        self.state.hotkey = False
        self.state.voice_listen = False
        for t in ("listening", "wake_word", "hotkey", "conversation"):
            self.state.set_task(t, False)
        self.state.status_message = "Features stopped"
        self.set_ui_state("standby")
        self.ui.set_active(False, "Low resource mode — listening stopped.")

    # ----- input -----
    def handle_text_command(self, text: str) -> None:
        low = (text or "").lower().strip()
        phrases = [p.lower() for p in self.cfg.get("activation_aliases", [])]
        if any(p in low for p in phrases) or low in ("activate", "jarvis"):
            self.activate()
            return
        if any(
            x in low
            for x in (
                "conversation mode",
                "start conversation",
                "talk to me",
                "let's talk",
                "lets talk",
            )
        ):
            self.start_conversation_mode()
            return
        if is_exit_phrase(text):
            self.standby()
            return

        if not self.state.active and not self.state.paused:
            self.state.active = True
            self.state.conversation_mode = True
            self.ui.show_window(True)
            self.ui.set_active(True)
            self.state.set_task("conversation", True)

        self.state.last_heard = text
        self.ai.maybe_update_language(text)
        self._sync_lang()
        self.set_ui_state("thinking")
        reply = self.router.handle(text)
        if reply:
            self.speak(reply)

    def talk_or_continue(self) -> None:
        ok, msg = self.permissions.require("microphone")
        if not ok:
            self.ui.append_system(msg)
            return
        if not self.stt.available:
            self.ui.append_system("Microphone hardware/STT not available.")
            return
        if not self.state.conversation_mode and not self.state.active:
            self.start_conversation_mode()
            return
        if self._listen_thread and self._listen_thread.is_alive():
            self.ui.append_system(phrase("listening", self.ai.language))
            return
        self._start_listen_loop(conversation=True)

    def _start_listen_loop(self, conversation: bool) -> None:
        if self._listen_thread and self._listen_thread.is_alive():
            return
        if not self.permissions.is_allowed("microphone"):
            return
        self._listen_thread = threading.Thread(
            target=self._conversation_loop if conversation else self._short_listen_loop,
            daemon=True,
        )
        self._listen_thread.start()

    def _short_listen_loop(self) -> None:
        max_idle = int(self.conv_cfg.get("activate_idle_turns", 4))
        self._run_turns(max_idle=max_idle, keep_conversation_flag=False)

    def _conversation_loop(self) -> None:
        max_idle = int(self.conv_cfg.get("conversation_idle_turns", 8))
        self._run_turns(max_idle=max_idle, keep_conversation_flag=True)

    def _run_turns(self, max_idle: int, keep_conversation_flag: bool) -> None:
        with self.session_lock:
            idle = 0
            self.state.set_task("listening", True)
            while self.state.active and not self.stop and not self.state.paused and idle < max_idle:
                if keep_conversation_flag and not self.state.conversation_mode:
                    break
                if not self.state.voice_listen or not self.stt.available:
                    break
                if not self.permissions.is_allowed("microphone"):
                    break

                self.set_ui_state("listening")
                self.ui.append_system(phrase("listening", self.ai.language))
                self.stt.set_language(self.ai.language)
                heard = self.stt.listen_once(timeout=7, language=self.ai.language)
                if not heard:
                    idle += 1
                    if idle == max(2, max_idle // 2) and keep_conversation_flag:
                        self.speak(phrase("follow_up", self.ai.language))
                    continue

                idle = 0
                self.ui.append_user(heard)
                self.state.last_heard = heard
                self.ai.maybe_update_language(heard)
                self._sync_lang()

                if is_exit_phrase(heard):
                    self.speak(phrase("conversation_off", self.ai.language))
                    self.standby()
                    break

                self.set_ui_state("thinking")
                reply = self.router.handle(heard)
                if reply:
                    self.speak(reply)

            self.state.set_task("listening", False)
            if self.state.active and idle >= max_idle:
                self.speak(phrase("conversation_off", self.ai.language))
                self.standby()

    def wake_word_loop(self) -> None:
        phrases = [p.lower() for p in self.cfg.get("activation_aliases", ["jarvis activate"])]
        self.state.set_task("wake_word", True)
        while not self.stop:
            if self.state.paused or not self.state.wake_word or self.state.active:
                time.sleep(0.6)
                continue
            if not self.permissions.is_allowed("microphone"):
                time.sleep(2.0)
                continue
            if not self.stt.available or not self.state.voice_listen:
                time.sleep(2.0)
                continue
            text = self.stt.listen_once(timeout=2.5, language="en")
            if not text:
                time.sleep(float(self.cfg.get("idle_sleep_sec", 0.5)))
                continue
            low = text.lower()
            if any(p in low for p in phrases) or (
                "jarvis" in low
                and any(w in low for w in ("activate", "online", "wake", "hey", "open", "start"))
            ):
                self.log.info(f"Wake: {text}")
                if "conversation" in low or "talk" in low:
                    self.start_conversation_mode()
                else:
                    self.activate()

    def hotkey_loop(self) -> None:
        try:
            import ctypes

            user32 = ctypes.windll.user32
            was = False
            self.state.set_task("hotkey", True)
            while not self.stop:
                if self.state.paused or not self.state.hotkey:
                    time.sleep(0.4)
                    continue
                down = bool(
                    (user32.GetAsyncKeyState(0x11) & 0x8000)
                    and (user32.GetAsyncKeyState(0x10) & 0x8000)
                    and (user32.GetAsyncKeyState(0x4A) & 0x8000)
                )
                if down and not was:
                    self.activate()
                was = down
                time.sleep(0.15)
        except Exception as e:
            self.log.warn(f"Hotkey unavailable: {e}")

    def run(self) -> None:
        self.log.info("JARVIS v3 online.")
        try:
            self.optimizer.analyze()
        except Exception:
            pass
        self.ui.start()
        time.sleep(0.8)
        self.ui.append_system(
            "Permissions default OFF — enable what you need in Settings.\n"
            "Themes · Personality · Animations · Cloud AI optional\n"
            f"Theme: {self.state.theme} · Personality: {self.state.personality}"
        )
        threading.Thread(target=self.wake_word_loop, daemon=True).start()
        threading.Thread(target=self.hotkey_loop, daemon=True).start()
        try:
            while not self.stop:
                time.sleep(1.0)
        except KeyboardInterrupt:
            self.stop = True


def main() -> None:
    Jarvis().run()


if __name__ == "__main__":
    main()
