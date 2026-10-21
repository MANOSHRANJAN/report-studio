---
description: Check and install Report Studio dependencies (Agent Reach, twitter-cli, Chrome)
---
Run `bash scripts/setup.sh --install` from the project root (or
`bash "${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh" --install` when installed as a plugin), then
`agent-reach doctor`. Report which channels work. If Twitter cookies are missing, explain how
to set TWITTER_AUTH_TOKEN and TWITTER_CT0 (README → Twitter access) — never ask me to paste
them into chat. Check whether Google Drive connector tools are available in this session.
