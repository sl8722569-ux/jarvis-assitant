#!/usr/bin/env bash
# J.A.R.V.I.S [EARLY ACCESS] — macOS installer (user-local)
set -euo pipefail
SRC="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="${HOME}/Applications/JARVIS"
echo "=== J.A.R.V.I.S macOS installer ==="
if ! command -v python3 >/dev/null 2>&1; then
  echo "Install Python 3 from python.org or Homebrew (brew install python), then re-run."
  exit 1
fi
mkdir -p "$DEST/data" "$DEST/logs"
cp -a "$SRC/jarvis.py" "$SRC/requirements.txt" "$SRC/config.example.json" "$SRC/README.md" "$SRC/LICENSE" "$DEST/" 2>/dev/null || true
cp -a "$SRC/modules" "$SRC/platform" "$SRC/docs" "$DEST/" 2>/dev/null || true
[ -f "$DEST/config.json" ] || cp "$DEST/config.example.json" "$DEST/config.json"
python3 -m venv "$DEST/.venv"
"$DEST/.venv/bin/pip" install --upgrade pip
"$DEST/.venv/bin/pip" install -r "$DEST/requirements.txt" || true
cat > "$DEST/Start JARVIS.command" <<EOF
#!/bin/bash
cd "$DEST"
exec "$DEST/.venv/bin/python" jarvis.py
EOF
chmod +x "$DEST/Start JARVIS.command"
echo "Installed to $DEST"
echo "Double-click Start JARVIS.command or run it from Terminal."
