---
description: Fill image slots and re-render a report to PDF, then self-check the pages
argument-hint: "[reports/.work/<slug>] (defaults to the most recently modified report)"
---
Re-render the magazine report at: $ARGUMENTS
(If no path was given, use the most recently modified folder in `reports/`.)

From the project root run (SKILL_DIR = the `magazine-report` skill's folder —
`skills/magazine-report` in this repo, or inside the plugin install when used as a plugin):
1. `python3 SKILL_DIR/scripts/slots.py fill <issue>`
2. `python3 SKILL_DIR/scripts/render.py <issue>`
3. Read `<issue>/previews/contact.png`, then any page that looks wrong at full size.
Fix overflow, stranded headings, half-empty pages and placeholder slots that should be
filled, and repeat until clean. End with the PDF path and the `slots.py list` table so I know
which images to drop into `<issue>/images/`.

The deliverable is only the PDF in `reports/` (render.py publishes it). Reply with the PDF link plus
at most a few short lines on what needs confirmation and which pages are pending. Do not hand over
HTML, previews, briefs or image folders.
