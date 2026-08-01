"""JARVIS UI v3 — themes, animations, states, settings, permissions. Lightweight tkinter."""
from __future__ import annotations

import math
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import TYPE_CHECKING, Callable

from .themes import THEMES, get_theme

if TYPE_CHECKING:
    from .permissions import PermissionManager
    from .state import JarvisState


class JarvisUI:
    def __init__(
        self,
        state: JarvisState,
        permissions: PermissionManager,
        on_activate: Callable | None = None,
        on_text: Callable | None = None,
        on_voice_toggle: Callable | None = None,
        on_pause: Callable | None = None,
        on_resume: Callable | None = None,
        on_stop_features: Callable | None = None,
        on_open_ai: Callable | None = None,
        on_volume: Callable | None = None,
        on_mic_listen: Callable | None = None,
        on_conversation: Callable | None = None,
        on_standby: Callable | None = None,
        on_theme: Callable | None = None,
        on_personality: Callable | None = None,
        on_animation: Callable | None = None,
        on_permission_change: Callable | None = None,
        on_save_settings: Callable | None = None,
        on_share_project: Callable | None = None,
    ):
        self.state = state
        self.permissions = permissions
        self.on_activate = on_activate
        self.on_text = on_text
        self.on_voice_toggle = on_voice_toggle
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_stop_features = on_stop_features
        self.on_open_ai = on_open_ai
        self.on_volume = on_volume
        self.on_mic_listen = on_mic_listen
        self.on_conversation = on_conversation
        self.on_standby = on_standby
        self.on_theme = on_theme
        self.on_personality = on_personality
        self.on_animation = on_animation
        self.on_permission_change = on_permission_change
        self.on_save_settings = on_save_settings
        self.on_share_project = on_share_project  # public project link only

        self.theme = get_theme(state.theme)
        self.root: tk.Tk | None = None
        self.notebook: ttk.Notebook | None = None
        self.chat: scrolledtext.ScrolledText | None = None
        self.entry: tk.Entry | None = None
        self.status_var: tk.StringVar | None = None
        self.state_var: tk.StringVar | None = None
        self.panel_vars: dict[str, tk.StringVar] = {}
        self.canvas: tk.Canvas | None = None
        self.vol_var: tk.DoubleVar | None = None
        self.perm_vars: dict[str, tk.BooleanVar] = {}
        self._widgets_bg: list[tk.Widget] = []
        self._pulse = 0
        self._thread: threading.Thread | None = None
        self._theme_name_var: tk.StringVar | None = None
        self._pers_var: tk.StringVar | None = None
        self._anim_var: tk.StringVar | None = None
        self._anim_enabled_var: tk.BooleanVar | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        self.theme = get_theme(self.state.theme)
        self.root = tk.Tk()
        self.root.title("JARVIS AI Assistant")
        self.root.geometry("600x740+50+20")
        self.root.minsize(460, 560)
        self.root.configure(bg=self.theme["bg"])
        try:
            self.root.attributes("-topmost", True)
            self.root.after(500, lambda: self.root.attributes("-topmost", False))
        except Exception:
            pass

        self._setup_style()
        self.status_var = tk.StringVar(value="STANDBY")
        self.state_var = tk.StringVar(value="standby")

        # Header
        header = tk.Frame(self.root, bg=self.theme["bg"])
        header.pack(fill="x", padx=12, pady=(10, 2))
        self._widgets_bg.append(header)
        tk.Label(
            header, text="J.A.R.V.I.S", fg=self.theme["accent"], bg=self.theme["bg"],
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left")
        right = tk.Frame(header, bg=self.theme["bg"])
        right.pack(side="right")
        tk.Label(right, textvariable=self.state_var, fg=self.theme["muted"], bg=self.theme["bg"], font=("Consolas", 9)).pack(side="right", padx=8)
        tk.Label(right, textvariable=self.status_var, fg=self.theme["accent2"], bg=self.theme["bg"], font=("Consolas", 10, "bold")).pack(side="right")

        self.canvas = tk.Canvas(
            self.root, width=200, height=90, bg=self.theme["bg"], highlightthickness=0
        )
        self.canvas.pack()
        self._draw_visual(0.3)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=6)

        self._build_assistant_tab()
        self._build_control_tab()
        self._build_settings_tab()
        self._build_help_tab()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._animate()
        self._refresh_panel()
        self.root.mainloop()

    def _setup_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TNotebook", background=self.theme["bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=self.theme["panel"],
            foreground=self.theme["muted"],
            padding=[10, 5],
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.theme["button"])],
            foreground=[("selected", self.theme["text"])],
        )

    # ----- tabs -----
    def _build_assistant_tab(self) -> None:
        tab = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(tab, text="  AI Chat  ")
        self.chat = scrolledtext.ScrolledText(
            tab, wrap=tk.WORD, bg=self.theme["chat_bg"], fg=self.theme["text"],
            font=("Segoe UI", 10), relief="flat", state="disabled", padx=8, pady=8,
        )
        self.chat.pack(fill="both", expand=True, padx=4, pady=4)
        self.chat.tag_config("jarvis", foreground=self.theme["accent"], font=("Segoe UI", 10, "bold"))
        self.chat.tag_config("user", foreground=self.theme["accent2"], font=("Segoe UI", 10, "bold"))
        self.chat.tag_config("sys", foreground=self.theme["muted"], font=("Segoe UI", 9, "italic"))
        self.chat.tag_config("body", foreground=self.theme["text"])

        ai_row = tk.Frame(tab, bg=self.theme["bg"])
        ai_row.pack(fill="x", padx=4, pady=2)
        tk.Label(ai_row, text="Open AI:", fg=self.theme["muted"], bg=self.theme["bg"], font=("Segoe UI", 9)).pack(side="left")
        for name in ("ChatGPT", "Gemini", "Copilot", "Claude", "Grok"):
            tk.Button(
                ai_row, text=name, command=lambda n=name: self._open_ai(n),
                bg=self.theme["panel"], fg=self.theme["text"], relief="flat", padx=6, pady=2, font=("Segoe UI", 8),
            ).pack(side="left", padx=2)

        act = tk.Frame(tab, bg=self.theme["bg"])
        act.pack(fill="x", padx=4, pady=4)
        for text, cmd, key in (
            ("Activate", self._click_activate, "button"),
            ("Conversation", self._click_conversation, "button"),
            ("Talk / Enter", self._click_mic, "panel"),
            ("Standby", self._click_standby, "danger"),
        ):
            tk.Button(
                act, text=text, command=cmd, bg=self.theme[key], fg=self.theme["text"],
                relief="flat", padx=8, pady=5,
            ).pack(side="left", padx=2)

        entry_row = tk.Frame(tab, bg=self.theme["bg"])
        entry_row.pack(fill="x", padx=4, pady=(2, 8))
        self.entry = tk.Entry(
            entry_row, bg=self.theme["entry_bg"], fg=self.theme["text"],
            insertbackground=self.theme["accent"], relief="flat", font=("Segoe UI", 11),
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 6))
        self.entry.bind("<Return>", self._submit_or_talk)
        tk.Button(
            entry_row, text="Send", command=self._submit, bg=self.theme["button"],
            fg=self.theme["text"], relief="flat", padx=12, pady=6,
        ).pack(side="right")

        self.append_system(
            "v3 ready · themes · permissions · natural chat\n"
            "Activate · Conversation · Talk/Enter · Standby\n"
            "Settings tab: personality, theme, animation, permissions"
        )

    def _build_control_tab(self) -> None:
        tab = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(tab, text="  Control  ")
        tk.Label(
            tab, text="Management", fg=self.theme["accent"], bg=self.theme["bg"], font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 6))
        grid = tk.Frame(tab, bg=self.theme["bg"])
        grid.pack(fill="x", padx=10)
        for key, title in (
            ("status", "Status"),
            ("mode", "Mode"),
            ("ui_state", "UI state"),
            ("language", "Language"),
            ("personality", "Personality"),
            ("theme", "Theme"),
            ("voice_mode", "Voice"),
            ("tasks", "Tasks"),
            ("last_heard", "Last heard"),
            ("last_reply", "Last reply"),
            ("features", "Features"),
        ):
            row = tk.Frame(grid, bg=self.theme["panel"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=title, fg=self.theme["muted"], bg=self.theme["panel"], width=12, anchor="w").pack(
                side="left", padx=6, pady=3
            )
            var = tk.StringVar(value="—")
            self.panel_vars[key] = var
            tk.Label(row, textvariable=var, fg=self.theme["text"], bg=self.theme["panel"], anchor="w", wraplength=400).pack(
                side="left", fill="x", expand=True
            )

        vol_frame = tk.Frame(tab, bg=self.theme["bg"])
        vol_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(vol_frame, text="Voice volume", fg=self.theme["muted"], bg=self.theme["bg"]).pack(anchor="w")
        self.vol_var = tk.DoubleVar(value=self.state.voice_volume * 100)
        tk.Scale(
            vol_frame, from_=20, to=100, orient="horizontal", variable=self.vol_var,
            bg=self.theme["bg"], fg=self.theme["accent"], highlightthickness=0,
            troughcolor=self.theme["panel"], command=self._vol_changed,
        ).pack(fill="x")

        row = tk.Frame(tab, bg=self.theme["bg"])
        row.pack(fill="x", padx=10, pady=6)
        for text, cmd, key in (
            ("Activate", self._click_activate, "button"),
            ("Pause", lambda: self._cb(self.on_pause), "panel"),
            ("Resume", lambda: self._cb(self.on_resume), "button"),
            ("Stop features", lambda: self._cb(self.on_stop_features), "danger"),
            ("Toggle speak", lambda: self._cb(self.on_voice_toggle), "panel"),
        ):
            tk.Button(row, text=text, command=cmd, bg=self.theme[key], fg=self.theme["text"], relief="flat", padx=8, pady=5).pack(
                side="left", padx=3, pady=2
            )

    def _build_settings_tab(self) -> None:
        tab = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(tab, text="  Settings  ")

        tk.Label(tab, text="Customization", fg=self.theme["accent"], bg=self.theme["bg"], font=("Segoe UI", 12, "bold")).pack(
            anchor="w", padx=12, pady=(10, 4)
        )

        # Theme
        f1 = tk.Frame(tab, bg=self.theme["bg"])
        f1.pack(fill="x", padx=12, pady=4)
        tk.Label(f1, text="Theme", fg=self.theme["muted"], bg=self.theme["bg"], width=14, anchor="w").pack(side="left")
        self._theme_name_var = tk.StringVar(value=self.state.theme)
        om = tk.OptionMenu(f1, self._theme_name_var, *THEMES.keys(), command=self._theme_picked)
        om.config(bg=self.theme["panel"], fg=self.theme["text"], highlightthickness=0)
        om.pack(side="left")

        # Personality
        f2 = tk.Frame(tab, bg=self.theme["bg"])
        f2.pack(fill="x", padx=12, pady=4)
        tk.Label(f2, text="Personality", fg=self.theme["muted"], bg=self.theme["bg"], width=14, anchor="w").pack(side="left")
        self._pers_var = tk.StringVar(value=self.state.personality)
        om2 = tk.OptionMenu(
            f2, self._pers_var, "professional", "friendly", "playful", command=self._pers_picked
        )
        om2.config(bg=self.theme["panel"], fg=self.theme["text"], highlightthickness=0)
        om2.pack(side="left")

        # Animation
        f3 = tk.Frame(tab, bg=self.theme["bg"])
        f3.pack(fill="x", padx=12, pady=4)
        tk.Label(f3, text="Animation", fg=self.theme["muted"], bg=self.theme["bg"], width=14, anchor="w").pack(side="left")
        self._anim_var = tk.StringVar(value=self.state.animation)
        om3 = tk.OptionMenu(
            f3, self._anim_var, "hud", "heartbeat", "waveform", "robot", "none", command=self._anim_picked
        )
        om3.config(bg=self.theme["panel"], fg=self.theme["text"], highlightthickness=0)
        om3.pack(side="left")
        self._anim_enabled_var = tk.BooleanVar(value=self.state.animations_enabled)
        tk.Checkbutton(
            f3, text="Enable animations", variable=self._anim_enabled_var,
            bg=self.theme["bg"], fg=self.theme["text"], selectcolor=self.theme["panel"],
            activebackground=self.theme["bg"], command=self._anim_enabled_toggled,
        ).pack(side="left", padx=12)

        # Permissions
        tk.Label(
            tab, text="Privacy & Permissions (off by default — grant only what you need)",
            fg=self.theme["accent"], bg=self.theme["bg"], font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=12, pady=(14, 4))

        perm_box = tk.Frame(tab, bg=self.theme["panel"])
        perm_box.pack(fill="x", padx=12, pady=4)
        for key, label in (
            ("microphone", "Microphone / voice"),
            ("file_access", "Safe file access"),
            ("screen", "Screen actions"),
            ("app_control", "Open/close apps"),
            ("web_open", "Open websites"),
            ("share_apps", "Share apps (WhatsApp Web)"),
            ("cloud_ai", "Cloud AI APIs (ChatGPT/Gemini)"),
        ):
            var = tk.BooleanVar(value=self.permissions.is_allowed(key))
            self.perm_vars[key] = var
            tk.Checkbutton(
                perm_box, text=label, variable=var, bg=self.theme["panel"], fg=self.theme["text"],
                selectcolor=self.theme["bg"], activebackground=self.theme["panel"],
                anchor="w", command=lambda k=key: self._perm_toggled(k),
            ).pack(fill="x", padx=8, pady=2)

        btn_row = tk.Frame(tab, bg=self.theme["bg"])
        btn_row.pack(fill="x", padx=12, pady=10)
        tk.Button(
            btn_row, text="Revoke all permissions", command=self._revoke_all,
            bg=self.theme["danger"], fg=self.theme["text"], relief="flat", padx=10, pady=6,
        ).pack(side="left")
        tk.Button(
            btn_row, text="Save settings", command=lambda: self._cb(self.on_save_settings),
            bg=self.theme["button"], fg=self.theme["text"], relief="flat", padx=10, pady=6,
        ).pack(side="left", padx=8)

        # Share Jarvis — public project link only (no personal data)
        tk.Label(
            tab,
            text="Share Jarvis (optional — public project link only)",
            fg=self.theme["accent"],
            bg=self.theme["bg"],
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=12, pady=(14, 4))
        share_row = tk.Frame(tab, bg=self.theme["bg"])
        share_row.pack(fill="x", padx=12, pady=4)
        tk.Button(
            share_row,
            text="Share Jarvis (copy link)",
            command=lambda: self._cb(self.on_share_project, "copy"),
            bg=self.theme["button"],
            fg=self.theme["text"],
            relief="flat",
            padx=10,
            pady=6,
        ).pack(side="left")
        tk.Button(
            share_row,
            text="Share draft in browser",
            command=lambda: self._cb(self.on_share_project, "browser"),
            bg=self.theme["panel"],
            fg=self.theme["text"],
            relief="flat",
            padx=10,
            pady=6,
        ).pack(side="left", padx=8)
        tk.Label(
            tab,
            text="Shares only the official GitHub/app link + short public blurb.\n"
            "Never shares your settings, logs, API keys, chats, or personal files.",
            fg=self.theme["muted"],
            bg=self.theme["bg"],
            justify="left",
            font=("Segoe UI", 8),
        ).pack(anchor="w", padx=12, pady=4)

        tk.Label(
            tab,
            text="No mic/files/web/apps/cloud without permission.\n"
            "Revoke anytime. File access is limited to your user folders.\n"
            "J.A.R.V.I.S Early Access · Phase 1",
            fg=self.theme["muted"], bg=self.theme["bg"], justify="left", font=("Segoe UI", 8),
        ).pack(anchor="w", padx=12, pady=6)

    def _build_help_tab(self) -> None:
        tab = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(tab, text="  Commands  ")
        help_text = (
            "ACTIVATE / CONVERSATION\n"
            "  Jarvis Activate · Conversation · Talk/Enter · standby/goodbye\n\n"
            "APPS & WEB (need permissions)\n"
            "  open notepad · open youtube · open github.com\n"
            "  search web for weather · close edge\n\n"
            "SYSTEM\n"
            "  system info · battery status · gaming mode · performance mode\n\n"
            "FILES (safe folders, need file_access)\n"
            "  list downloads · find files report · open file notes.txt\n\n"
            "SHARE (need share_apps, always confirms)\n"
            "  open whatsapp web · share on whatsapp hello\n"
            "  confirm share · cancel share\n\n"
            "PERSONALITY / THEME\n"
            "  personality professional|friendly|playful\n"
            "  theme midnight_hud|ember_core|forest_soft|arctic_glass|neon_play\n\n"
            "PERMISSIONS\n"
            "  allow microphone · revoke web open · permission status\n\n"
            "CLOUD AI (optional keys in config.json)\n"
            "  allow cloud ai · then chat uses ChatGPT/Gemini if configured\n"
        )
        st = scrolledtext.ScrolledText(
            tab, wrap=tk.WORD, bg=self.theme["chat_bg"], fg=self.theme["text"],
            font=("Consolas", 9), relief="flat",
        )
        st.pack(fill="both", expand=True, padx=8, pady=8)
        st.insert("1.0", help_text)
        st.configure(state="disabled")

    # ----- callbacks -----
    def _cb(self, fn: Callable | None, *a) -> None:
        if fn:
            threading.Thread(target=fn, args=a, daemon=True).start()

    def _click_activate(self) -> None:
        self._cb(self.on_activate)

    def _click_conversation(self) -> None:
        self._cb(self.on_conversation)

    def _click_mic(self) -> None:
        self.append_system("Listening…")
        self._cb(self.on_mic_listen)

    def _click_standby(self) -> None:
        self._cb(self.on_standby)

    def _open_ai(self, name: str) -> None:
        self._cb(self.on_open_ai, name)

    def _submit_or_talk(self, event=None) -> None:
        if not self.entry:
            return
        if not self.entry.get().strip():
            self._click_mic()
            return
        self._submit()

    def _submit(self, event=None) -> None:
        if not self.entry:
            return
        text = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if not text:
            return
        self.append_user(text)
        self._cb(self.on_text, text)

    def _vol_changed(self, _=None) -> None:
        if self.vol_var is not None and self.on_volume:
            self.on_volume(float(self.vol_var.get()) / 100.0)

    def _theme_picked(self, name: str) -> None:
        self._cb(self.on_theme, name)

    def _pers_picked(self, name: str) -> None:
        self._cb(self.on_personality, name)

    def _anim_picked(self, name: str) -> None:
        self._cb(self.on_animation, name)

    def _anim_enabled_toggled(self) -> None:
        self.state.animations_enabled = bool(self._anim_enabled_var.get()) if self._anim_enabled_var else True

    def _perm_toggled(self, key: str) -> None:
        val = bool(self.perm_vars[key].get())
        if self.on_permission_change:
            self.on_permission_change(key, val)

    def _revoke_all(self) -> None:
        for k, v in self.perm_vars.items():
            v.set(False)
        if self.on_permission_change:
            self.on_permission_change("__all__", False)

    def _on_close(self) -> None:
        if self.root:
            self.root.withdraw()

    # ----- public -----
    def apply_theme(self, name: str) -> None:
        self.theme = get_theme(name)
        self.state.theme = name

        def _ui() -> None:
            if not self.root:
                return
            self.root.configure(bg=self.theme["bg"])
            if self.canvas:
                self.canvas.configure(bg=self.theme["bg"])
            self.append_system(f"Theme applied: {self.theme.get('label', name)}. Restart JARVIS for full chrome refresh if needed.")

        self._safe(_ui)

    def show_window(self, expand: bool = True) -> None:
        def _ui() -> None:
            if not self.root:
                return
            self.root.deiconify()
            self.root.lift()
            try:
                self.root.focus_force()
            except Exception:
                pass
            if expand:
                self.root.geometry("600x740+50+20")

        self._safe(_ui)

    def set_active(self, active: bool, message: str | None = None) -> None:
        def _ui() -> None:
            if self.status_var:
                if self.state.paused:
                    self.status_var.set("PAUSED")
                else:
                    self.status_var.set("ONLINE" if active else "STANDBY")
            if active:
                self.show_window(True)
            if message:
                self.append_system(message)

        self._safe(_ui)

    def set_ui_state(self, mode: str) -> None:
        self.state.set_ui_state(mode)

        def _ui() -> None:
            if self.state_var:
                self.state_var.set(mode)

        self._safe(_ui)

    def set_status(self, message: str) -> None:
        self.append_system(message)

    def append_user(self, text: str) -> None:
        self._append("You", text, "user")

    def append_jarvis(self, text: str) -> None:
        self._append("JARVIS", text, "jarvis")

    def append_system(self, text: str) -> None:
        self._append("System", text, "sys")

    def _append(self, who: str, text: str, tag: str) -> None:
        def _ui() -> None:
            if not self.chat:
                return
            self.chat.configure(state="normal")
            self.chat.insert(tk.END, f"{who}\n", tag)
            self.chat.insert(tk.END, f"{text}\n\n", "body")
            self.chat.see(tk.END)
            self.chat.configure(state="disabled")

        self._safe(_ui)

    def _refresh_panel(self) -> None:
        if not self.root:
            return
        snap = self.state.snapshot()
        if self.panel_vars:
            self.panel_vars.get("status", tk.StringVar()).set(snap["status_message"])
            if snap.get("conversation_mode"):
                mode = "CONVERSATION"
            elif snap["active"]:
                mode = "ACTIVE"
            elif snap["paused"]:
                mode = "PAUSED"
            else:
                mode = "STANDBY"
            if "mode" in self.panel_vars:
                self.panel_vars["mode"].set(mode)
            if "ui_state" in self.panel_vars:
                self.panel_vars["ui_state"].set(snap.get("ui_state", "standby"))
            if "language" in self.panel_vars:
                names = {"en": "English", "hi": "Hindi", "pa": "Punjabi"}
                self.panel_vars["language"].set(names.get(snap.get("language", "en"), snap.get("language", "en")))
            if "personality" in self.panel_vars:
                self.panel_vars["personality"].set(snap.get("personality", "friendly"))
            if "theme" in self.panel_vars:
                self.panel_vars["theme"].set(snap.get("theme", "midnight_hud"))
            if "voice_mode" in self.panel_vars:
                self.panel_vars["voice_mode"].set(
                    f"Speak {'ON' if snap['voice_speak'] else 'OFF'} · "
                    f"Listen {'ON' if snap['voice_listen'] else 'OFF'} · "
                    f"Vol {int(snap['voice_volume']*100)}%"
                )
            if "tasks" in self.panel_vars:
                self.panel_vars["tasks"].set(", ".join(snap["tasks"]) or "none")
            if "last_heard" in self.panel_vars:
                self.panel_vars["last_heard"].set(snap["last_heard"] or "—")
            if "last_reply" in self.panel_vars:
                self.panel_vars["last_reply"].set(snap["last_reply"] or "—")
            if "features" in self.panel_vars:
                feats = []
                if snap["wake_word"]:
                    feats.append("wake")
                if snap["hotkey"]:
                    feats.append("hotkey")
                if snap["voice_listen"]:
                    feats.append("mic")
                if snap["voice_speak"]:
                    feats.append("tts")
                self.panel_vars["features"].set(", ".join(feats) or "stopped")
        if self.status_var:
            if snap["paused"]:
                self.status_var.set("PAUSED")
            elif snap["active"]:
                self.status_var.set("ONLINE")
            else:
                self.status_var.set("STANDBY")
        if self.state_var:
            self.state_var.set(snap.get("ui_state", "standby"))
        self.root.after(1000, self._refresh_panel)

    def _safe(self, fn: Callable) -> None:
        if self.root is None:
            return
        try:
            self.root.after(0, fn)
        except Exception:
            pass

    # ----- lightweight visuals -----
    def _draw_visual(self, intensity: float) -> None:
        if not self.canvas:
            return
        self.canvas.delete("all")
        anim = self.state.animation if self.state.animations_enabled else "none"
        ui = self.state.ui_state
        accent = self.theme["accent"]
        w, h = 200, 90
        cx, cy = w // 2, h // 2

        if anim == "none":
            self.canvas.create_oval(cx - 10, cy - 10, cx + 10, cy + 10, fill=accent, outline="")
            self.canvas.create_text(cx, h - 10, text=ui, fill=self.theme["muted"], font=("Consolas", 8))
            return

        if anim == "heartbeat" or (anim == "hud" and ui == "speaking"):
            # ECG-like line
            pts = []
            beat = 1.0 + (0.5 if ui in ("speaking", "listening") else 0.15) * math.sin(self._pulse / 3)
            for x in range(0, w, 4):
                y = cy
                phase = (x + self._pulse * 6) % 80
                if 30 < phase < 40:
                    y = cy - 22 * beat
                elif 40 <= phase < 48:
                    y = cy + 14 * beat
                elif 48 <= phase < 56:
                    y = cy - 8 * beat
                pts.extend([x, y])
            if len(pts) >= 4:
                self.canvas.create_line(*pts, fill=accent, width=2, smooth=True)
            self.canvas.create_text(cx, h - 8, text=f"♥ {ui}", fill=self.theme["muted"], font=("Consolas", 8))
            return

        if anim == "waveform" or ui == "listening":
            for i in range(16):
                x = 20 + i * 11
                amp = 8 + 20 * intensity * abs(math.sin(self._pulse / 4 + i * 0.5))
                if ui == "thinking":
                    amp *= 0.5
                self.canvas.create_rectangle(
                    x, cy - amp, x + 6, cy + amp, fill=accent, outline=""
                )
            self.canvas.create_text(cx, h - 8, text=ui, fill=self.theme["muted"], font=("Consolas", 8))
            return

        if anim == "robot" or self.theme.get("avatar") == "robot":
            # Simple cartoon robot face
            self.canvas.create_rectangle(cx - 40, cy - 28, cx + 40, cy + 28, outline=accent, width=2)
            eye_y = cy - 8
            blink = 2 if (self._pulse // 20) % 7 == 0 else 8
            self.canvas.create_oval(cx - 22, eye_y - blink, cx - 10, eye_y + blink, fill=accent, outline="")
            self.canvas.create_oval(cx + 10, eye_y - blink, cx + 22, eye_y + blink, fill=accent, outline="")
            mouth_w = 18 if ui == "speaking" else 10
            mouth_h = 6 + (4 if ui == "speaking" else 0) * abs(math.sin(self._pulse / 3))
            self.canvas.create_oval(cx - mouth_w, cy + 8, cx + mouth_w, cy + 8 + mouth_h, outline=accent, width=2)
            self.canvas.create_text(cx, h - 8, text=f"robot · {ui}", fill=self.theme["muted"], font=("Consolas", 8))
            return

        # Default HUD rings
        for i, r in enumerate((36, 26, 16, 8)):
            a = max(0.2, intensity - i * 0.1)
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=accent, width=2)
        self.canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=accent, outline="")
        # corner brackets
        self.canvas.create_line(8, 8, 28, 8, fill=accent)
        self.canvas.create_line(8, 8, 8, 28, fill=accent)
        self.canvas.create_line(w - 8, 8, w - 28, 8, fill=accent)
        self.canvas.create_line(w - 8, 8, w - 8, 28, fill=accent)
        self.canvas.create_text(cx, h - 8, text=f"HUD · {ui}", fill=self.theme["muted"], font=("Consolas", 8))

    def _animate(self) -> None:
        if not self.root:
            return
        self._pulse += 1
        ui = self.state.ui_state
        if ui == "listening":
            base = 0.85
        elif ui == "speaking":
            base = 0.75
        elif ui == "thinking":
            base = 0.45
        elif self.state.active:
            base = 0.55
        else:
            base = 0.25
        wave = (math.sin(self._pulse / 7) + 1) / 2
        self._draw_visual(base + wave * 0.2)
        # slower when standby — save CPU
        delay = 50 if ui in ("listening", "speaking") else (90 if self.state.active else 160)
        if not self.state.animations_enabled:
            delay = 400
        self.root.after(delay, self._animate)
