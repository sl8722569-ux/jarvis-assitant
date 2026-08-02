# Future packaging (Phase 2 prep — do not auto-publish)

## Windows / Microsoft Store (future)
- Entry: `jarvis.py` / packaged EXE via PyInstaller or MSIX
- Identity, store listing, privacy policy required before submit
- Do **not** auto-publish from CI without human approval

## Android / Google Play (future)
- Bridge via `platform/mobile/` — WebView or native shell calling shared API
- Permissions map: mic, files, notifications

## iOS (future)
- Similar bridge; App Store review for mic/files

## Linux (future)
- Same Python stack; SAPI TTS replaced with espeak/festival adapters

## Web
- Use `platform/web/responsive.css` + future API server wrapping `modules/`

## Rule
Logic stays in `modules/`. Platform folders only host shells and packaging configs.
