---
name: magazine-report
description: Build a magazine-style, print-ready report (HTML + PDF) from real sources — reports and PDFs fetched from websites, files in Google Drive, and Twitter/X posts. Use when the user asks to make, compile, design or update a report, briefing, deep-dive, industry/market report, research digest, newsletter issue, annual/impact report, or "magazine"; when they share report URLs, Drive files/folders, or tweets to turn into a publication; or when they ask what is in their Drive / what a set of reports says. Also use to restyle an existing report into an editorial magazine layout with image slots.
---

# Magazine Report

Turn scattered sources into an editorial publication that looks designed, not generated.
Four phases, always in this order. Do not skip the brief.

```
1. GATHER   websites · PDFs · Google Drive · Twitter/X   → reports/<slug>/sources/
2. BRIEF    tell the user what was found, before designing → reports/<slug>/brief.md
3. DESIGN   magazine layout with named image slots       → reports/<slug>/report.html
4. RENDER   PDF + page previews, self-check, report slots → reports/<slug>/report.pdf
```

`SKILL_DIR` = the folder this SKILL.md is in (`skills/magazine-report` in the Report Studio
repo, or the plugin's install path). Issues are created in `reports/` under the current
working directory.

## 0. Set up the issue folder

```bash
python3 SKILL_DIR/scripts/new_issue.py "<Report title>"   # prints reports/<slug>/
```

Creates `sources/`, `images/`, `brief.md`, and copies `assets/magazine-template.html` →
`report.html`. Every later step writes inside that folder.

## 1. GATHER — read `references/sourcing.md` for the exact recipes

Pick the channel per source. Save every raw source as a file in `sources/`
(`NN-<short-name>.md`) with its URL / Drive ID / tweet URL and fetch date at the top,
so every number in the final report is traceable.

| Source | First choice | Fallback |
|---|---|---|
| Web page / article | `WebFetch` | `curl -sL https://r.jina.ai/<URL>` |
| PDF report on a site | download → `pdftotext -layout` / `pdf` skill | Jina Reader on the PDF URL |
| Google Drive | Drive connector tools (`search_files`, `read_file_content`, `download_file_content`, `get_file_metadata`) | ask the user to share the file / export to PDF |
| Single tweet URL | `twitter tweet <url>` (agent-reach) | syndication endpoint (no login) — see sourcing.md |
| Search / timelines / threads | `twitter search`, `twitter user-posts`, `twitter tweet` | `agent-reach` skill routing; Exa search |
| Anything else social (Reddit, YouTube, LinkedIn…) | `agent-reach` skill | — |

Rules:
- Run `agent-reach doctor` once at the start to know which channels are live. If
  Twitter shows `[!]`, the cookies are not set — say so in the brief and use the
  no-login fallback for individual tweet URLs. Never ask the user to paste cookies into chat.
- Prefer primary sources (the actual PDF, the actual post) over write-ups about them.
- Pull the source's own charts/figures only if the user owns them or they are clearly
  licensed for reuse; otherwise re-draw the data as your own chart and cite the source.
- Download candidate photos into `images/` only when the user provided them or asked
  for stock; otherwise leave the slot empty (see §3) — the user pastes their own.

## 2. BRIEF — inform the user before designing

Write `brief.md` and post a short version in chat:

- **What I found** — one line per source: title, origin (site / Drive path / @handle),
  date, length, and the 1–2 facts worth using from it.
- **Drive inventory** (when Drive was searched) — the files that matched, with
  modified date and owner, and which ones were read.
- **Channels that failed** — e.g. "Twitter search blocked (no cookies); used 4 tweet URLs
  via the no-login fallback."
- **Proposed storyline** — 5–9 sections with a working headline each, and the hero stat.
- **Image plan** — the slot list (id, page, size, what should go there).

If the user is present, wait for a quick "go" or edits. In an unattended/cloud run,
proceed and keep the brief in the folder.

## 3. DESIGN — read `references/magazine-design.md` first

- If `design-references/` (project root) holds images or PDFs, **open every one with Read
  before designing** and write down in `brief.md`: grid/columns, type pairing (serif/sans,
  weights, sizes), colour palette, how images are cropped and placed, page furniture
  (folios, running heads, kickers, rules). Match that system; do not average it with defaults.
- Start from `report.html` (the template). Keep its print engine (A4 `.page` sheets, CSS
  variables, slot system); replace content, palette and fonts.
- Use the installed design skills as critics, not as layout sources:
  `impeccable` (critique / typeset / polish passes) and `design-taste-frontend`
  (anti-slop tells, type and colour references). Their web-page patterns
  (hero sections, nav bars, cards, CTAs) do **not** belong in a magazine.
- Every picture is a **named slot** — never a hard-coded random image:

```html
<figure class="slot" data-slot="cover-hero" data-ratio="3/4"
        data-hint="Portrait of founder, outdoors, warm light">
  <img src="images/cover-hero.jpg" alt="">
  <figcaption>Caption text. <span class="credit">Photo: …</span></figcaption>
</figure>
```

  If `images/cover-hero.jpg` is missing the page shows a labelled placeholder with the slot
  id, ratio and hint, so the user sees exactly where to paste which image. Any of
  `.jpg .jpeg .png .webp .avif` works — `slots.py fill` rewrites the extension.

## 4. RENDER + self-check

```bash
python3 SKILL_DIR/scripts/slots.py list reports/<slug>      # which slots are filled/empty
python3 SKILL_DIR/scripts/slots.py fill reports/<slug>      # match images/* to slots by name
python3 SKILL_DIR/scripts/render.py reports/<slug>          # → report.pdf + preview.png
```

Then **Read `preview.png`** and check: text overflowing a page, orphaned headings at the
bottom of a page, empty half-pages, clashing colours, slot placeholders that should have been
filled. Fix and re-render until clean. Ship nothing you have not looked at.

Final message to the user:
1. Paths to `report.pdf` and `report.html`.
2. The slot table from `slots.py list` — "drop a file named `<slot-id>.jpg` into
   `reports/<slug>/images/` and re-run render" — so they know where each image goes.
3. Sources that could not be read and why.

## Running in claude.ai (uploaded skill)

The scripts need Python 3 and a Chrome/Chromium. In the claude.ai sandbox, try
`pip install playwright && playwright install chromium` and set `CHROME_PATH` to the
binary it prints. If that is blocked, deliver `report.html` (the user prints it to PDF
from their browser — the CSS is print-ready) and list the slots from `slots.py list`.
Google Drive works through the claude.ai Google Drive connector. Twitter with cookies
needs the Report Studio Claude Code setup; in claude.ai use the no-login single-tweet
fallback when its domain is reachable, otherwise web search.

## Updating an existing issue

Re-run GATHER only for new/changed sources (compare fetch dates in `sources/`), update
`brief.md` with a "What changed" section, edit `report.html` in place, re-render.
