# Monthly issue playbook

A monthly issue reports **one calendar month** (default: the previous month) from four
source families, in this priority order for both facts and photos:

| Priority | Source | How | Feeds |
|---|---|---|---|
| 1 | **Google Drive** (photos, data sheets, monthly reports) | Drive connector → `drive_save.py` / `sheet_extract.py` | cover collage, events, impact story, grants, lifetime, initiative |
| 2 | **Website** (posts, events, projects, grantees, resources) | `fetch_web.py` (WordPress REST → sitemap → RSS) | events, campaign, impact story, timeline |
| 3 | **X / Twitter** (the org's own posts) | `fetch_x.py` (twitter-cli via Agent Reach) | digital-footprint page, highlights, post images |
| 4 | **Stock** (only to fill photo gaps) | `stock.py` (Pexels / Unsplash keys, else Openverse CC) | atmosphere images only, never "event" photos |

`report.config.json` (project root) holds handles, site, Drive folders/sheets, theme and
stock keywords. Read it first.

## Run order

```bash
S=SKILL_DIR/scripts
python3 $S/new_issue.py --monthly --month YYYY-MM        # → reports/<org>-YYYY-MM/ (theme from config)
python3 $S/fetch_web.py reports/<issue> --month YYYY-MM
python3 $S/fetch_x.py   reports/<issue> --month YYYY-MM  # exit 2 = no cookies → page pending
# Drive (connector tools, see below) → drive_save.py / sheet_extract.py
python3 $S/digest.py     reports/<issue>
python3 $S/candidates.py reports/<issue>                 # Read previews/candidates-*.png
python3 $S/stock.py      reports/<issue> --query "<config keyword>" --n 3   # only if gaps remain
# write content into report.html, then:
python3 $S/slots.py fill reports/<issue> --assign SLOT=images/candidates/<file> ...
python3 $S/render.py     reports/<issue>                 # Read previews/contact.png + any bad page
```

## Google Drive steps (connector tools)

1. **Photos of the month**: `search_files` with
   `mimeType contains 'image/' and createdTime >= '<start>T00:00:00Z' and createdTime < '<end+7d>T00:00:00Z'`
   (a week of slack: photos are often uploaded after the event). Also search the folders in
   `drive.photo_folders`. Skip titles matching `drive.skip_title_patterns` (logos, AI images, screenshots).
2. Download 6–12 promising ones with `download_file_content` (no exportMimeType). Each result is
   saved to a `tool-results/*.txt` file; pass all paths to `drive_save.py <issue> <paths...>`.
   Never paste base64 into the conversation.
3. **Data sheets** (`drive.data_sheets`): `read_file_content` only shows one sample row per tab.
   For real numbers export the whole workbook: `download_file_content` with
   `exportMimeType = application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, then
   `sheet_extract.py <saved.txt> reports/<issue>/sources/raw/<sheet-slug>` → one CSV per tab.
   Compute with Python from the CSVs; watch for **"Grand Total" rows** (exclude before summing,
   use them as a cross-check).
4. **Monthly documents** in `drive.monthly_reports_folder` (e.g. Legal Activity Reports, consolidated
   records): `read_file_content`. Use the one dated in or just after the month.
5. Record every file used (title, id, modified date) in `brief.md → Drive inventory`.

## Hindu Fund page ↔ source map (theme `hindu-fund`)

| Page | Source | Notes |
|---|---|---|
| 01 Cover collage | 5 best Drive photos of the month | people and places, not posters |
| 02 Founder's note | written from the month's facts | **DRAFT** — founder approves before release |
| 03 Shubhchintak | manual input: new members + one community post | pending if missing |
| 04 Digital footprint | `x.json` (top 3 posts verbatim, real metrics) + follower counts | follower counts for non-X platforms are manual inputs |
| 05 Webinar / Campaign | website `events` + poster from Drive/website | if no webinar happened, feature the month's main campaign |
| 06 Donor contributions | donor counts/amounts by type for the month | MIS Sheet; pending if the month's columns don't exist yet |
| 07 Grants disbursed | `Hindu Fund \| Lifetime Grants` → tab `2026-27` → month column | orgs = distinct grantees with amount > 0; areas from "Area of Work" |
| 08 Major events | website items of the month + X posts + Drive photos | 4 items; posters use `data-fit="contain"` |
| 09 Major initiative | Legal Activity Report / consolidated record | avoid naming private individuals; public figures only if the org already named them publicly |
| 10 Impact story | a grantee funded this month that has Drive photos + website profile | |
| 11 Lifetime impact | Lifetime Grants "Grand Total" + website grantee count | |
| 12–13 | static (process flow, priority projects, appeal) | review once a quarter |

## Rules

- **No invented numbers.** If a figure has no source, hide the page with
  `hidden data-pending="<what is missing>"` on its `<section>`; `render.py` lists pending pages.
- **Cross-check** a computed figure against any previously published value (e.g. last month's PDF in
  `design-references/`) and flag mismatches in `brief.md → Needs confirmation` — never silently
  "fix" them.
- **X**: only the org's own posts, quoted verbatim. If `fetch_x.py` exits 2, the page is pending;
  tell the user to set `TWITTER_AUTH_TOKEN` / `TWITTER_CT0` (README).
- **Photos**: Drive first, then the org's own X/website images, then stock. Stock is only for
  atmosphere (temples, lamps, manuscripts), never to illustrate a specific event or person, and its
  credit line is mandatory (`slots.py fill` inserts it automatically).
- Look at `previews/candidates-*.png` before assigning; reject logos, AI images, off-topic stock.
- Posters and text-heavy graphics: add `data-fit="contain"` to the slot.
- End with `brief.md` sections: Sources used · Drive inventory · Needs confirmation · Pending pages
  (with exactly what input is needed) · Image credits.
