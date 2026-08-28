# Changelog

## 3.2.1-phase1

- Typing is first-class: Enter sends, Shift+Enter newline, Stop / Copy / Clear / Regenerate
- Open installed apps first; if missing, ask to install (Store/winget) then official website
- Multitask foundation: open A, B and C; task board; cancel / pause / continue
- Hindi/Punjabi open phrases (kholo / खोलो / ਖੋਲ੍ਹੋ)
- Web companion: same typing UX; browser speech optional; no fake Windows launches

## 3.2.0-early-access

- Download truth: no fake APK/XAPK on latest Releases
- Mute and unmute are separate; volume percent uses system volume keys
- Open AI sites requires `web_open` permission
- Unknown app names are refused (no arbitrary `start`)
- Gaming mode no longer force-kills browsers or Teams
- Version aligned with GitHub tag `v3.2.0-installers`

## 3.0.0-early-access — Phase 1 complete (Early Access)

End of **J.A.R.V.I.S [EARLY ACCESS] / Phase 1**.

### Included
- Voice + text assistant with wake phrase and conversation mode
- English / Hindi / Punjabi language support
- Themes, personality modes, lightweight animations
- Permission manager (mic, files, apps, web, share, cloud AI)
- Optional ChatGPT / Gemini API hooks
- Safe file helper, WhatsApp Web prepare-with-confirm
- System optimize helpers (safe, reversible)
- Share Jarvis (public project link only)
- GitHub-ready layout, `.gitignore`, example config

### Not included yet (future phases)
- Packaged Windows Store / installer app
- Mobile (Android/iOS) clients
- Full web app
- Heavy local LLMs

### Privacy
- Permissions default **off**
- Logs and `data/permissions.json` are gitignored
- API keys must never be committed
