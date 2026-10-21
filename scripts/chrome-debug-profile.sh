#!/usr/bin/env bash
# Start a COPY of one of your Chrome profiles with remote debugging on port 9222, so the
# Playwright MCP (--cdp-endpoint http://127.0.0.1:9222) can browse as that profile — e.g. read
# X/Twitter while logged in, without exporting any cookies.
#
#   bash scripts/chrome-debug-profile.sh "Sarayu Trust"
#
# Run it in macOS Terminal.app (the Claude app is not allowed to read Chrome's folder).
# Chrome ≥136 ignores --remote-debugging-port on the default profile folder, hence the copy.
# The copy lives in ~/.chrome-debug-profiles/<name>/ and is refreshed (logins only, no caches)
# each time you run this. Your normal Chrome keeps running untouched.
set -euo pipefail
NAME="${1:-Sarayu Trust}"
PORT="${PORT:-9222}"
SRC="$HOME/Library/Application Support/Google/Chrome"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

DEST="$HOME/.chrome-debug-profiles/$(echo "$NAME" | tr ' /' '__')"
mkdir -p "$DEST/Default"
START_URL="https://x.com/home"

if [[ -r "$SRC/Local State" ]] && DIR=$(python3 - "$SRC/Local State" "$NAME" <<'EOF'
import json, sys
cache = json.load(open(sys.argv[1]))["profile"]["info_cache"]
want = sys.argv[2].strip().lower().replace(" ", "")
names = {k: v.get("name", "").strip().lower().replace(" ", "") for k, v in cache.items()}
hits = [k for k, n in names.items() if n == want] or [k for k, n in names.items() if want in n or n in want]
print(hits[0] if hits else "")
if not hits:
    print("profiles: " + ", ".join(v.get("name", "") for v in cache.values()), file=sys.stderr)
EOF
) && [[ -n "$DIR" ]]; then
  cp "$SRC/Local State" "$DEST/Local State"
  rsync -a --delete \
    --exclude 'Cache' --exclude 'Code Cache' --exclude 'GPUCache' --exclude 'Service Worker/CacheStorage' \
    --exclude 'Service Worker/ScriptCache' --exclude 'DawnCache' --exclude 'GrShaderCache' \
    --exclude 'File System' --exclude 'IndexedDB' --exclude 'blob_storage' --exclude 'Extensions' \
    "$SRC/$DIR/" "$DEST/Default/"
  echo "Profile \"$NAME\" ($DIR) copied to $DEST"
else
  # Chrome's folder is not readable from here (macOS app-data protection, e.g. inside the
  # Claude app). Use the dedicated profile in $DEST instead: log in to X there once — it stays
  # logged in for future runs.
  echo "Can't read Chrome's profile folder from this app — using the dedicated profile $DEST."
  echo "If X asks you to log in, do it once in the window that opens (it is remembered)."
fi

if curl -s -m 2 "http://127.0.0.1:$PORT/json/version" >/dev/null; then
  echo "Something is already listening on port $PORT — close that Chrome window first."; exit 1
fi
"$CHROME" --user-data-dir="$DEST" --profile-directory=Default --remote-debugging-port="$PORT" \
  --no-first-run --no-default-browser-check "https://x.com/home" >/dev/null 2>&1 &
sleep 3
curl -s -m 5 "http://127.0.0.1:$PORT/json/version" | grep -q Browser \
  && echo "Ready: Chrome (\"$NAME\") is listening on 127.0.0.1:$PORT. Tell Claude to continue." \
  || echo "Chrome started but port $PORT is not answering yet — wait a few seconds."
