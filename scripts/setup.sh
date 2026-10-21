#!/usr/bin/env bash
# Report Studio environment setup. Idempotent; safe to run every session.
#
#   Cloud (CLAUDE_CODE_REMOTE=true) or --install : installs anything missing
#   Local, no flag                               : only checks, prints what is missing
#
# Installs: uv, Agent Reach (+ Twitter channel via twitter-cli), poppler (if apt),
#           Chromium for PDF rendering (via Playwright) when no Chrome is present.
# Never reads browser cookies. Twitter needs TWITTER_AUTH_TOKEN + TWITTER_CT0 set as
# environment variables / secrets by the user.

set -uo pipefail
INSTALL=0; QUIET=0
[[ "${CLAUDE_CODE_REMOTE:-}" == "true" ]] && INSTALL=1
for arg in "$@"; do
  case "$arg" in
    --install) INSTALL=1 ;;
    --hook)    QUIET=1 ;;   # SessionStart hook: only speak when something is missing
  esac
done

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
missing=()
log() { [[ $QUIET == 1 ]] || echo "$@"; }
have() { command -v "$1" >/dev/null 2>&1; }

# ---------- uv ----------
if ! have uv; then
  if [[ $INSTALL == 1 ]]; then
    log "installing uv"; curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1
    export PATH="$HOME/.local/bin:$PATH"
  else missing+=("uv"); fi
fi

# ---------- Agent Reach ----------
if ! have agent-reach; then
  if [[ $INSTALL == 1 ]] && have uv; then
    log "installing agent-reach"
    uv tool install --quiet "git+https://github.com/Panniantong/Agent-Reach.git" >/dev/null 2>&1 \
      || log "agent-reach install failed"
  else missing+=("agent-reach"); fi
fi

# ---------- twitter-cli (Agent Reach Twitter backend) ----------
if ! have twitter; then
  if [[ $INSTALL == 1 ]] && have uv; then
    log "installing twitter-cli"; uv tool install --quiet twitter-cli >/dev/null 2>&1 || log "twitter-cli install failed"
  else missing+=("twitter-cli"); fi
fi

# ---------- poppler (pdftotext / pdftoppm) ----------
if ! have pdftotext && [[ $INSTALL == 1 ]]; then
  if have apt-get; then (sudo -n apt-get install -y -qq poppler-utils || apt-get install -y -qq poppler-utils) >/dev/null 2>&1
  elif have brew; then brew install -q poppler >/dev/null 2>&1; fi
fi
have pdftotext || missing+=("poppler (optional: pdftotext/pdftoppm)")

# ---------- Chrome / Chromium for rendering ----------
chrome_found() {
  [[ -n "${CHROME_PATH:-}" && -x "${CHROME_PATH:-}" ]] && return 0
  [[ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]] && return 0
  for b in google-chrome google-chrome-stable chromium chromium-browser; do have "$b" && return 0; done
  ls "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux*/chrome >/dev/null 2>&1 && return 0
  return 1
}
if ! chrome_found; then
  if [[ $INSTALL == 1 ]] && have npx; then
    log "installing chromium (playwright)"
    npx -y playwright@latest install --with-deps chromium >/dev/null 2>&1 \
      || npx -y playwright@latest install chromium >/dev/null 2>&1 || log "chromium install failed"
  fi
  chrome_found || missing+=("chrome/chromium (PDF rendering)")
fi
# expose the Playwright chromium to later shell commands in this session
PW=$(ls -d "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux*/chrome 2>/dev/null | sort | tail -1)
if [[ -n "$PW" && -n "${CLAUDE_ENV_FILE:-}" ]]; then echo "export CHROME_PATH=\"$PW\"" >> "$CLAUDE_ENV_FILE"; fi
if [[ -n "${CLAUDE_ENV_FILE:-}" ]]; then echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"; fi

# ---------- Twitter credentials ----------
tw="not configured (set TWITTER_AUTH_TOKEN + TWITTER_CT0; single-tweet fallback still works)"
[[ -n "${TWITTER_AUTH_TOKEN:-}" && -n "${TWITTER_CT0:-}" ]] && tw="cookies present"

# ---------- report ----------
if [[ ${#missing[@]} -gt 0 ]]; then
  echo "[report-studio] missing: ${missing[*]} — run: bash scripts/setup.sh --install"
fi
if [[ $QUIET == 0 || ${#missing[@]} -gt 0 ]]; then
  echo "[report-studio] twitter: $tw"
fi
exit 0
