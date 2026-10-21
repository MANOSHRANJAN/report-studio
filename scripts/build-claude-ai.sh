#!/usr/bin/env bash
# Package each skill as a zip for claude.ai → Settings → Capabilities → Skills → Upload skill.
# Output: dist/<skill>.zip (one folder per zip, SKILL.md inside it).
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf dist && mkdir -p dist
for dir in skills/*/; do
  name=$(basename "$dir")
  [[ -f "$dir/SKILL.md" ]] || continue
  (cd skills && zip -qr "../dist/$name.zip" "$name" -x '*/__pycache__/*' '*.DS_Store' '*/evals/*')
  printf '%-24s %s\n' "$name" "$(du -h "dist/$name.zip" | cut -f1)"
done
echo "Upload the zips in dist/ at claude.ai → Settings → Capabilities → Skills."
