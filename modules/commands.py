"""Command router — apps, web, files, share, personality, permissions, system."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .ai_engine import AIEngine
    from .ai_launcher import AILauncher
    from .ai_providers import AIProviders
    from .file_assistant import FileAssistant
    from .logger import JarvisLogger
    from .modes import ModeManager
    from .optimizer import Optimizer
    from .permissions import PermissionManager
    from .share_assistant import ShareAssistant
    from .system_ops import SystemOps
    from .tts_engine import TTSEngine
    from .web_ops import WebOps


class CommandRouter:
    def __init__(
        self,
        ops: SystemOps,
        ai: AIEngine,
        modes: ModeManager,
        optimizer: Optimizer,
        launcher: AILauncher,
        permissions: PermissionManager,
        files: FileAssistant,
        share: ShareAssistant,
        web: WebOps,
        providers: AIProviders | None = None,
        tts: TTSEngine | None = None,
        log: JarvisLogger | None = None,
        on_exit: Callable[[], None] | None = None,
        on_pause: Callable[[], None] | None = None,
        on_resume: Callable[[], None] | None = None,
        on_conversation: Callable[[], None] | None = None,
        on_theme: Callable[[str], None] | None = None,
        set_ui_state: Callable[[str], None] | None = None,
        win=None,
        smart=None,
        plugins=None,
        on_usage_mode: Callable[[str], None] | None = None,
        on_layout: Callable[[str], None] | None = None,
    ):
        self.ops = ops
        self.ai = ai
        self.modes = modes
        self.optimizer = optimizer
        self.launcher = launcher
        self.permissions = permissions
        self.files = files
        self.share = share
        self.web = web
        self.providers = providers
        self.tts = tts
        self.log = log
        self.on_exit = on_exit
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_conversation = on_conversation
        self.on_theme = on_theme
        self.set_ui_state = set_ui_state
        self.win = win
        self.smart = smart
        self.plugins = plugins
        self.on_usage_mode = on_usage_mode
        self.on_layout = on_layout

    def handle(self, text: str) -> str:
        raw = (text or "").strip()
        if not raw:
            return "I did not catch that."
        t = raw.lower().strip()
        t = re.sub(r"^jarvis[,\s]+", "", t).strip()
        if self.log:
            self.log.event("command", {"text": raw})
        self.ai.maybe_update_language(raw)
        if self.set_ui_state:
            self.set_ui_state("thinking")

        # Conversation
        if re.search(
            r"\b(conversation mode|start conversation|let'?s talk|talk to me|baat karo|gal karo)\b",
            t,
        ):
            if self.on_conversation:
                self.on_conversation()
            return ""

        # Phase 2: Jarvis Standby + exit
        if re.search(
            r"\b(jarvis standby|jarvis stand by|goodbye|go to sleep|deactivate|exit jarvis|standby|"
            r"stop conversation|end conversation|bas karo|band karo|alvida)\b",
            t,
        ):
            if self.on_exit:
                self.on_exit()
            return ""

        # Usage modes
        if re.search(r"\b(full jarvis mode|full mode)\b", t):
            if self.on_usage_mode:
                return self.on_usage_mode("full") or "Full Jarvis Mode on."
            return "Full Jarvis Mode."
        if re.search(r"\b(sidebar companion|sidebar mode)\b", t):
            if self.on_usage_mode:
                return self.on_usage_mode("sidebar") or "Sidebar Companion Mode on."
            return "Sidebar Companion Mode."
        if re.search(r"\b(voice only mode|voice mode)\b", t):
            if self.on_usage_mode:
                return self.on_usage_mode("voice_only") or "Voice Only Mode on."
            return "Voice Only Mode."

        # Layout
        if re.search(r"\b(floating assistant|float mode)\b", t):
            if self.on_layout:
                return self.on_layout("floating") or "Floating assistant."
        if re.search(r"\b(compact mode)\b", t):
            if self.on_layout:
                return self.on_layout("compact") or "Compact mode."
        if re.search(r"\b(performance mode ui|light mode|dark mode)\b", t) or t in (
            "performance ui",
            "enable light mode",
            "enable dark mode",
        ):
            if "light" in t and self.on_theme:
                self.on_theme("light_mode")
                return "Light mode theme applied."
            if "dark" in t and self.on_theme:
                self.on_theme("midnight_hud")
                return "Dark mode theme applied."
            if "performance" in t:
                return "Performance mode: animations can be disabled in Settings. Prefer compact layout."

        # Plugins first (fast route)
        if self.plugins:
            plug = self.plugins.try_handle(raw)
            if plug:
                return plug
            if re.search(r"\b(list plugins|plugins|skills)\b", t):
                return self.plugins.list_plugins()

        # Smart tips (only when asked)
        if self.smart:
            tip = self.smart.handle(raw)
            if tip:
                return tip

        # Windows assistant extras
        if self.win:
            if t.startswith("note ") or t.startswith("remember "):
                body = raw.split(" ", 1)[1] if " " in raw else ""
                return self.win.add_note(body)
            if re.search(r"\b(show notes|read notes|my notes)\b", t):
                return self.win.read_notes()
            if re.search(r"\b(clipboard|what.?s on clipboard|show clipboard)\b", t):
                return self.win.clipboard_get()
            m = re.search(r"\b(?:copy|clipboard set)\s+(.+)$", t)
            if m:
                return self.win.clipboard_set(m.group(1))
            m = re.search(r"\b(?:set )?timer\s+(\d+)\s*(seconds|second|sec|s|minutes|minute|min|m)?\b", t)
            if m:
                n = int(m.group(1))
                unit = (m.group(2) or "sec").lower()
                secs = n * 60 if unit.startswith("m") else n
                return self.win.set_timer(secs, "jarvis")
            if "calendar" in t and any(w in t for w in ("open", "show", "launch")):
                return self.win.open_calendar()
            if re.search(r"\bbrightness\s+(\d{1,3})\b", t):
                return self.win.brightness(percent=int(re.search(r"(\d{1,3})", t).group(1)))
            if "brightness up" in t:
                return self.win.brightness(direction="up")
            if "brightness down" in t:
                return self.win.brightness(direction="down")
            if "screenshot" in t:
                ok, msg = self.permissions.require("screen")
                if not ok:
                    return msg
                return self.win.screenshot()

        # File share via WhatsApp
        m = re.search(r"\b(?:send|share)\s+(?:this\s+)?file\s+(?:through|via|on)\s+whatsapp(?:\s+web)?\s*(.*)$", t)
        if m:
            path = m.group(1).strip() or "the selected file"
            prep = self.share.prepare_whatsapp_message(
                f"Sharing file: {path} (open WhatsApp Web and attach manually after confirm)."
            )
            return prep + "\nAfter confirm, attach the file yourself in WhatsApp — Jarvis never auto-sends files."
        if re.search(r"\b(pause jarvis|pause features)\b", t) or re.fullmatch(r"pause", t):
            if self.on_pause:
                self.on_pause()
            return "Features paused. Text chat still works."
        if re.search(r"\b(resume jarvis|resume features|unpause)\b", t) or re.fullmatch(r"resume", t):
            if self.on_resume:
                self.on_resume()
            return "Features resumed."

        # Phase 2 voice diagnostics / tests
        if re.search(r"\b(voice diagnostics|run diagnostics|diagnose voice|audio diagnostics)\b", t):
            from .voice_diagnostics import run_full_diagnostics

            rep = run_full_diagnostics(self._stt_ref() if hasattr(self, "_stt_ref") else None, self.tts, self.permissions)
            # Prefer engine refs injected later — see jarvis wiring via setattr
            stt = getattr(self, "stt", None)
            rep = run_full_diagnostics(stt, self.tts, self.permissions)
            return rep.as_text()
        if re.search(r"\b(test microphone|microphone test|mic test)\b", t):
            stt = getattr(self, "stt", None)
            if not self.permissions.is_allowed("microphone"):
                return "Microphone permission denied. Enable it in Settings first."
            if stt is None:
                return "STT engine not available."
            return stt.test_microphone(2.0)
        if re.search(r"\b(test speaker|speaker test|test speakers|audio test)\b", t):
            if self.tts is None:
                return "TTS engine not available."
            return self.tts.test_speaker()
        if re.search(r"\b(open mic settings|microphone settings|windows mic)\b", t):
            from .voice_diagnostics import open_windows_mic_settings

            return open_windows_mic_settings()
        if re.search(r"\b(recover voice|fix voice|reset microphone)\b", t):
            stt = getattr(self, "stt", None)
            parts = []
            if stt is not None:
                parts.append("STT recovered." if stt.recover() else f"STT still down: {stt.last_error}")
            if self.tts is not None:
                parts.append("TTS recovered." if self.tts.recover() else f"TTS still down: {self.tts.last_error}")
            return " ".join(parts) or "No voice engines to recover."

        # Permissions
        m = re.search(r"\b(?:allow|grant|enable)\s+([\w\s]+)$", t)
        if m and any(x in t for x in ("allow", "grant", "enable")):
            key = self._perm_key(m.group(1))
            if key:
                return self.permissions.grant(key)
        m = re.search(r"\b(?:revoke|disable|deny)\s+([\w\s]+)$", t)
        if m and any(x in t for x in ("revoke", "disable", "deny")):
            if "all" in m.group(1):
                return self.permissions.revoke_all()
            key = self._perm_key(m.group(1))
            if key:
                return self.permissions.revoke(key)
        if "permission status" in t or "permissions" == t.strip():
            return self.permissions.status_text()

        # Personality
        m = re.search(r"\bpersonality\s+(professional|friendly|playful|pro|fun|formal)\b", t)
        if m:
            return self.ai.set_personality(m.group(1))
        if "set personality" in t or t.startswith("be more "):
            for mode in ("professional", "friendly", "playful"):
                if mode in t or (mode == "playful" and "fun" in t):
                    return self.ai.set_personality(mode)

        # Theme
        m = re.search(
            r"\btheme\s+(midnight_hud|ember_core|forest_soft|arctic_glass|neon_play|"
            r"armor_ai|green_power|shield_hero|cosmic_energy|speed_tech|light_mode)\b",
            t,
        )
        if m:
            if self.on_theme:
                self.on_theme(m.group(1))
            return f"Theme set to {m.group(1)}."
        if "list themes" in t or t == "themes":
            from .themes import list_themes

            return list_themes()

        # Cloud AI status
        if "cloud ai status" in t or "ai provider status" in t:
            return self.providers.status() if self.providers else "No providers."

        # Share project (public link only)
        if re.search(r"\b(share jarvis|share project|share the project)\b", t):
            from .share_project import share_jarvis

            return share_jarvis(self.ai.config if hasattr(self.ai, "config") else None, method="copy")

        # Share / WhatsApp
        if re.search(r"\b(open whatsapp|whatsapp web|open whatsapp web)\b", t):
            return self.share.open_whatsapp_web()
        m = re.search(r"\b(?:share on whatsapp|whatsapp message|send whatsapp|prepare whatsapp)\s+(.+)$", t)
        if m:
            return self.share.prepare_whatsapp_message(m.group(1))
        if re.search(r"\b(confirm share|send it|confirm send|yes send)\b", t):
            return self.share.confirm_share()
        if re.search(r"\b(cancel share|abort share|don't send|do not send)\b", t):
            return self.share.cancel_share()

        # Open AI assistants
        m = re.search(
            r"\b(?:open|launch|start)\s+"
            r"(chatgpt|chat gpt|gpt|gemini|copilot|claude|perplexity|grok)\b",
            t,
        )
        if m:
            return self.launcher.launch(m.group(1))
        if "list ai" in t:
            return self.launcher.list_available()

        # Websites
        m = re.search(r"\b(?:open website|open site|open web|browse)\s+(.+)$", t)
        if m:
            return self.web.open_site(m.group(1).strip())
        m = re.search(r"\b(?:search web for|google|search online)\s+(.+)$", t)
        if m:
            return self.web.search(m.group(1).strip())
        m = re.search(
            r"\bopen\s+(youtube|google|gmail|github|whatsapp|facebook|instagram|twitter|reddit|netflix|amazon|wikipedia|maps)\b",
            t,
        )
        if m:
            return self.web.open_site(m.group(1))
        # open example.com
        m = re.search(r"\bopen\s+((?:https?://)?[\w.-]+\.[\w.-]+(?:/[\w./?=%&-]*)?)\b", t)
        if m:
            return self.web.open_site(m.group(1))

        # Files
        m = re.search(r"\blist\s+(desktop|documents|downloads|pictures|music|videos)\b", t)
        if m:
            return self.files.list_folder(m.group(1))
        m = re.search(r"\b(?:find files?|search files? for)\s+(.+)$", t)
        if m:
            return self.files.find(m.group(1).strip())
        m = re.search(r"\bopen file\s+(.+)$", t)
        if m:
            return self.files.open_path(m.group(1).strip())

        # Voice controls
        if self.tts:
            m = re.search(r"\b(?:voice\s+)?volume\s+(\d{1,3})\b", t)
            if m:
                return self.tts.set_volume(int(m.group(1)) / 100.0)
            if "speak louder" in t or "voice louder" in t:
                return self.tts.set_volume(min(1.0, self.tts.volume + 0.15))
            if "speak quieter" in t or "voice quieter" in t:
                return self.tts.set_volume(max(0.2, self.tts.volume - 0.15))
            if "room boost on" in t:
                return self.tts.set_room_boost(True)
            if "room boost off" in t:
                return self.tts.set_room_boost(False)

        # Modes / optimize
        if "gaming mode" in t or t in ("game mode", "gaming"):
            ok, msg = self.permissions.require("app_control")
            if not ok:
                # gaming mode kills apps — require permission
                return msg
            return self.modes.gaming_mode()
        if "study mode" in t:
            return self.modes.study_mode()
        if "performance mode" in t or t in ("performance", "boost"):
            return self.modes.performance_mode()
        if t in ("optimize", "optimise") or "run optimization" in t:
            return self.optimizer.full_safe_optimize()
        if "restore startup" in t:
            return self.optimizer.restore_startup()
        if "analyze" in t and ("system" in t or "performance" in t or t == "analyze"):
            info = self.optimizer.analyze()
            return (
                f"Analysis saved. CPU {info.get('cpu_percent', '?')}%, "
                f"RAM {info.get('ram_percent', '?')}%, free disk {info.get('disk_c_free_gb', '?')} GB."
            )

        # Language
        m = re.search(
            r"(?:switch\s+)?(?:to\s+)?language(?:\s+to)?\s+(\w+)|"
            r"(?:speak|switch to|use)\s+(english|hindi|punjabi|panjabi|en|hi|pa)\b",
            t,
        )
        if m:
            return self.ai.set_language(m.group(1) or m.group(2))
        if "हिंदी" in raw:
            return self.ai.set_language("hi")
        if "ਪੰਜਾਬੀ" in raw:
            return self.ai.set_language("pa")

        # System volume
        if re.search(r"\b(mute|unmute)\b", t) and "voice" not in t:
            return self.ops.set_volume(mute=True)
        if "volume up" in t or ("louder" in t and "speak" not in t):
            return self.ops.set_volume(direction="up")
        if "volume down" in t or ("quieter" in t and "speak" not in t):
            return self.ops.set_volume(direction="down")

        if "battery" in t:
            return self.ops.battery_info()
        if re.search(r"\b(system info|system status|pc status|resources)\b", t):
            return self.ops.system_info()

        # Open / close apps (permission)
        m = re.search(r"\b(?:open|launch|start|run)\s+(.+)$", t)
        if m:
            target = m.group(1).strip()
            if self.launcher.resolve_name(target):
                return self.launcher.launch(target)
            if target in self.ops.FOLDER_MAP or target.startswith("folder "):
                return self.ops.open_folder(target.replace("folder ", "").strip())
            # website-ish
            if "." in target and " " not in target:
                return self.web.open_site(target)
            ok, msg = self.permissions.require("app_control")
            if not ok:
                return msg
            return self.ops.open_app(target)

        m = re.search(r"\b(?:close|kill|quit)\s+(.+)$", t)
        if m and "jarvis" not in m.group(1):
            ok, msg = self.permissions.require("app_control")
            if not ok:
                return msg
            return self.ops.close_app(m.group(1).strip())

        m = re.search(r"\b(?:open\s+folder|show\s+folder|go\s+to)\s+(.+)$", t)
        if m:
            return self.ops.open_folder(m.group(1).strip())

        if "lock" in t and any(x in t for x in ("screen", "pc", "computer")):
            return self.ops.run_command_safe("lock")
        if "recycle" in t:
            return self.ops.run_command_safe("empty recycle")
        if "screenshot" in t:
            ok, msg = self.permissions.require("screen")
            if not ok:
                return msg
            return self.ops.run_command_safe("screenshot")

        if t in ("help", "what can you do", "commands"):
            return self.ai.reply("what can you do")

        # Default: natural AI conversation (follow-ups supported via history)
        return self.ai.reply(raw, ui_state_cb=self.set_ui_state)

    @staticmethod
    def _perm_key(phrase: str) -> str | None:
        p = phrase.lower().strip().replace(" ", "_")
        aliases = {
            "microphone": "microphone",
            "mic": "microphone",
            "voice": "microphone",
            "camera": "camera",
            "file_access": "file_access",
            "files": "file_access",
            "file": "file_access",
            "screen": "screen",
            "app_control": "app_control",
            "apps": "app_control",
            "app": "app_control",
            "web_open": "web_open",
            "web": "web_open",
            "website": "web_open",
            "websites": "web_open",
            "share_apps": "share_apps",
            "share": "share_apps",
            "whatsapp": "share_apps",
            "cloud_ai": "cloud_ai",
            "cloud": "cloud_ai",
            "ai": "cloud_ai",
            "notifications": "notifications",
            "notification": "notifications",
        }
        if p in aliases:
            return aliases[p]
        for k, v in aliases.items():
            if k in phrase.lower():
                return v
        return None
