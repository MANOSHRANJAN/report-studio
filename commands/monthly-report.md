---
description: Build the monthly impact report for a month (X posts + website + Drive photos/data, stock only for gaps)
argument-hint: "[YYYY-MM] (default: last month) [extra notes, e.g. new member count, follower counts]"
---
Make the monthly report for: $ARGUMENTS
(If no month is given, use the previous calendar month.)

Use the `magazine-report` skill and follow `references/monthly.md` exactly:
1. `new_issue.py --monthly --month <YYYY-MM>` (theme + brand from report.config.json).
2. Gather: `fetch_web.py`, `fetch_x.py`, Drive photos of the month (`drive_save.py`), Drive data
   sheets (`sheet_extract.py`) and the month's documents in the monthly reports folder.
3. `digest.py`, `candidates.py` (look at the sheet), stock only for remaining gaps.
4. Write every page from the data; hide pages whose data is missing (`hidden data-pending`).
   Treat any numbers I gave in the arguments as manual inputs and cite them as "provided by team".
5. `slots.py fill`, `render.py`, look at the previews, fix, re-render.
6. Keep notes in the hidden working folder's `brief.md` (for the next run), not in the reply.

The deliverable is only the PDF in `reports/` (render.py publishes it). Reply with the PDF link plus
at most a few short lines on what needs confirmation and which pages are pending. Do not hand over
HTML, previews, briefs or image folders.
