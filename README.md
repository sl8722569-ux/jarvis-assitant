# J.A.R.V.I.S — Early Access

**Just A Rather Very Intelligent System** — a **lightweight personal AI assistant for Windows**, built to stay usable on modest hardware (Intel i3, 8 GB RAM, HDD).

> **Phase status:** Early Access **v3.2.0** (Windows).  
> Native Android APK/XAPK is **not** published. Phones use the **web companion** (Add to Home Screen).

---

## What is JARVIS?

JARVIS is a local-first assistant that can:

- Talk and listen (optional microphone permission)
- Chat in text with natural follow-ups
- Open apps, websites, and optional web AIs (ChatGPT, Gemini, …)
- Help with simple Windows tasks and safe folder helpers
- Stay private by default (permissions start **off**)

It is designed to be **fast enough on low-end PCs**, not a heavy Electron or local-LLM stack.

---

## Features (Phase 1)

| Area | Highlights |
|------|------------|
| **Voice & chat** | Wake phrase *“Jarvis Activate”*, conversation mode, text chat |
| **Languages** | English (primary), Hindi, Punjabi + light auto-detect |
| **Personality** | Professional / Friendly / Playful |
| **UI** | Themes, optional HUD / heartbeat / waveform / robot animations |
| **Permissions** | Mic, files, apps, web, share, cloud AI — grant & revoke anytime |
| **Smart tools** | System info, gaming/performance modes, safe file list/find |
| **Sharing apps** | WhatsApp Web message **prepare + confirm** (never auto-send) |
| **Cloud AI** | Optional OpenAI-compatible or Gemini API keys |
| **Share Jarvis** | Share only the **public project link** (no private data) |

---

## Project structure

```
JARVIS/
├── jarvis.py              # Windows entrypoint
├── Start_JARVIS.bat       # Double-click launcher
├── config.example.json    # Safe template for GitHub
├── config.json            # Your local config (do not commit secrets)
├── requirements.txt
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── modules/               # Core logic (maintain here)
├── platform/              # Future Windows/Linux/Web/Mobile adapters
├── scripts/               # Install / shortcut helpers
├── data/                  # Runtime user data (gitignored contents)
├── logs/                  # Local logs (gitignored)
└── assets/                # Optional media
```

---

## Requirements

- **Windows 10/11**
- **Python 3.11+** (3.12 recommended)
- Microphone optional (for voice)
- Internet optional (for speech recognition + cloud AI)

---

## Installation

```bash
# 1) Clone (after you publish)
git clone https://github.com/sl8722569-ux/jarvis-assitant.git
cd jarvis-assitant

# 2) Virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate

# 3) Dependencies
pip install -r requirements.txt

# Optional: microphone support
pip install pyaudio

# 4) Config
copy config.example.json config.json
# Edit config.json — set project.official_url to your real GitHub URL
# Add API keys only on your machine (never commit them)
```

### Quick start (already installed locally)

```text
Double-click Start_JARVIS.bat
```

or:

```bash
python jarvis.py
```

---

## How to use

1. Launch JARVIS  
2. Open **Settings** → enable only the permissions you need (e.g. microphone)  
3. Say **“Jarvis Activate”**, press **Ctrl+Shift+J**, or click **Activate**  
4. Use **Conversation** for multi-turn talk without the wake phrase every time  
5. Exit with **Standby**, or say *goodbye* / *standby*

### Share Jarvis (public link only)

**Settings → Share Jarvis**

- Copies the **official project URL + short public blurb**
- Does **not** share settings, logs, API keys, files, or chat history

Set your real repo URL in `config.json`:

```json
"project": {
  "official_url": "https://github.com/YOUR_USERNAME/jarvis-assistant",
  "share_text": "Try JARVIS — lightweight Windows AI assistant (Early Access)."
}
```

---

## Configuration & secrets

| File | Purpose |
|------|---------|
| `config.example.json` | Safe template for the repo |
| `config.json` | Local runtime config |
| `data/permissions.json` | Local permission grants (gitignored) |
| `logs/` | Local logs (gitignored) |

**Never commit:**

- API keys (`ai_api.api_key`, `gemini_api.api_key`)
- `.env`
- Personal logs or permission dumps with private paths

---

## Privacy (Phase 1)

- Permissions default to **denied**
- File helpers only touch normal user folders (Desktop, Documents, Downloads, …)
- WhatsApp: draft + user confirmation; no silent sends
- Share Jarvis: **project link only**

---

## Roadmap (after Phase 1)

- Packaged Windows installer / app identity  
- Deeper web UI  
- Linux desktop adapter  
- Mobile bridges  
- Optional stronger AI backends  

See `platform/README.md` and `CHANGELOG.md`.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Phase 1 complete

This repository marks the end of **J.A.R.V.I.S [EARLY ACCESS] / Phase 1**: a clean, maintainable, shareable foundation for later app and website releases.
