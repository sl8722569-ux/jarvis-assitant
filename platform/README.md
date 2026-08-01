# Platform expansion (future-ready)

```
JARVIS/
  jarvis.py              # Windows desktop entry (current)
  modules/               # Shared business logic (AI, permissions, themes…)
  platform/
    windows/             # Win-specific adapters (future split)
    linux/               # future
    web/                 # future web UI
    mobile/              # future Android/iOS bridges
```

**Rule:** Keep logic in `modules/`. Platform folders only host entrypoints and OS bindings.
No heavy frameworks required for the current Windows build.
