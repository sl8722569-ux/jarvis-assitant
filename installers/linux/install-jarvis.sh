#!/usr/bin/env bash
# J.A.R.V.I.S [EARLY ACCESS] — Linux installer (user-local, no root required)
set -euo pipefail
PRODUCT="J.A.R.V.I.S [EARLY ACCESS]"
SRC="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="${HOME}/.local/share/jarvis"
BIN="${HOME}/.local/bin"
APP="${HOME}/.local/share/applications"

echo "=== ${PRODUCT} Linux installer ==="
echo "From: $SRC"
echo "To:   $DEST"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required. Install Python 3.11+ with your package manager, then re-run."
  exit 1
fi

mkdir -p "$DEST" "$BIN" "$APP" "$DEST/data" "$DEST/logs"
cp -a "$SRC/jarvis.py" "$SRC/requirements.txt" "$SRC/README.md" "$SRC/LICENSE" \
  "$SRC/config.example.json" "$SRC/VERSION" "$DEST/" 2>/dev/null || true
cp -a "$SRC/modules" "$SRC/platform" "$SRC/scripts" "$SRC/docs" "$DEST/" 2>/dev/null || true
if [ ! -f "$DEST/config.json" ]; then
  cp "$DEST/config.example.json" "$DEST/config.json"
fi

python3 -m venv "$DEST/.venv"
"$DEST/.venv/bin/pip" install --upgrade pip
"$DEST/.venv/bin/pip" install -r "$DEST/requirements.txt" || true

cat > "$DEST/jarvis.sh" <<EOF
#!/usr/bin/env bash
cd "$DEST"
exec "$DEST/.venv/bin/python" jarvis.py "\$@"
EOF
chmod +x "$DEST/jarvis.sh"
ln -sf "$DEST/jarvis.sh" "$BIN/jarvis"

cat > "$APP/jarvis.desktop" <<EOF
[Desktop Entry]
Name=J.A.R.V.I.S
Comment=J.A.R.V.I.S [EARLY ACCESS] personal assistant
Exec=$DEST/jarvis.sh
Terminal=false
Type=Application
Categories=Utility;
EOF
chmod +x "$APP/jarvis.desktop"

echo "Install complete. Run: jarvis"
echo "Or: $DEST/jarvis.sh"
echo "Uninstall: rm -rf $DEST $BIN/jarvis $APP/jarvis.desktop"
