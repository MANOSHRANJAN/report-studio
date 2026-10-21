# Report Studio

This repo is a Claude Code plugin + project for making magazine-style reports.

- Any request to make/compile/design a report, briefing, digest or "magazine" → use the
  `magazine-report` skill (phases: GATHER → BRIEF → DESIGN → RENDER, never skip BRIEF).
- Twitter/X, Reddit, YouTube, LinkedIn, RSS → `agent-reach` skill. Run `agent-reach doctor` first.
- Design critique/polish → `impeccable`; anti-slop checks → `design-taste-frontend`;
  `frontend-design` for general visual direction. In reports, magazine-design.md wins over
  their web-page patterns.
- Before designing, read everything in `design-references/`.
- Generated issues go in `reports/<slug>/` (git-ignored). Do not commit images you did not create.
- Credentials: Twitter cookies live only in env vars `TWITTER_AUTH_TOKEN` / `TWITTER_CT0`.
  Never write them to files in this repo, never ask the user to paste them in chat.
- Google Drive: read-only use of the Drive connector tools unless the user asks to upload.
- `.claude/skills` and `.claude/commands` are symlinks to `skills/` and `commands/`. Edit the
  real folders.
