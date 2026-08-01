"""Optional cloud AI providers (ChatGPT/OpenAI-compatible, Gemini). Permission-gated."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .permissions import PermissionManager


class AIProviders:
    def __init__(self, config: dict, permissions: PermissionManager, log=None):
        self.config = config
        self.permissions = permissions
        self.log = log

    def chat(self, messages: list[dict[str, str]], system: str) -> str | None:
        ok, _ = self.permissions.require("cloud_ai")
        if not ok:
            return None
        api = self.config.get("ai_api") or {}
        if not api.get("enabled") or not api.get("api_key"):
            # try gemini block
            gem = self.config.get("gemini_api") or {}
            if gem.get("enabled") and gem.get("api_key"):
                return self._gemini(messages, system, gem)
            return None
        provider = (api.get("provider") or "openai_compatible").lower()
        if provider in ("gemini", "google"):
            return self._gemini(messages, system, api)
        return self._openai_compatible(messages, system, api)

    def _openai_compatible(self, messages: list[dict], system: str, api: dict) -> str | None:
        try:
            import requests

            url = api.get("base_url", "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
            headers = {
                "Authorization": f"Bearer {api['api_key']}",
                "Content-Type": "application/json",
            }
            body = {
                "model": api.get("model", "gpt-4o-mini"),
                "messages": [{"role": "system", "content": system}] + messages[-10:],
                "temperature": float(api.get("temperature", 0.55)),
                "max_tokens": int(api.get("max_tokens", 400)),
            }
            r = requests.post(url, headers=headers, json=body, timeout=35)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if self.log:
                self.log.warn(f"OpenAI-compatible AI failed: {e}")
            return None

    def _gemini(self, messages: list[dict], system: str, api: dict) -> str | None:
        try:
            import requests

            key = api.get("api_key")
            model = api.get("model") or "gemini-1.5-flash"
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                f"?key={key}"
            )
            # Flatten history lightly
            parts = [{"text": system + "\n\n"}]
            for m in messages[-8:]:
                role = m.get("role", "user")
                parts.append({"text": f"{role}: {m.get('content', '')}\n"})
            body: dict[str, Any] = {
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": {"temperature": 0.55, "maxOutputTokens": 400},
            }
            r = requests.post(url, json=body, timeout=35)
            r.raise_for_status()
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            if self.log:
                self.log.warn(f"Gemini AI failed: {e}")
            return None

    def status(self) -> str:
        api = self.config.get("ai_api") or {}
        gem = self.config.get("gemini_api") or {}
        cloud_perm = self.permissions.is_allowed("cloud_ai")
        lines = [
            f"Cloud AI permission: {'ALLOWED' if cloud_perm else 'DENIED'}",
            f"OpenAI-compatible: enabled={bool(api.get('enabled'))} key={'yes' if api.get('api_key') else 'no'} model={api.get('model', '-')}",
            f"Gemini: enabled={bool(gem.get('enabled'))} key={'yes' if gem.get('api_key') else 'no'}",
            "Set keys in config.json (ai_api / gemini_api) and allow cloud_ai permission.",
        ]
        return "\n".join(lines)
