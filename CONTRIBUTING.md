# Contributing to JARVIS (Early Access)

Thanks for helping improve Phase 1+.

## Rules
1. **Never commit secrets** — API keys, `.env`, real `config.json` with keys, personal logs.
2. Use `config.example.json` for docs; keep local overrides in `config.local.json` (gitignored pattern via local edits).
3. Prefer small PRs and keep the app **lightweight** (i3 / 8GB / HDD friendly).
4. Put shared logic in `modules/`; OS-specific entrypoints under `platform/`.
5. Do not add features that delete user personal files.

## Dev setup
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
python jarvis.py
```

## Code style
- Clear module docstrings and comments on non-obvious logic
- Avoid heavy dependencies
- Test permission-gated features with permissions both on and off
