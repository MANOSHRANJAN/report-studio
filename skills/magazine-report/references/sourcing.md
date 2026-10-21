# Sourcing recipes

Save every source to `reports/.work/<slug>/sources/NN-<name>.md` with this header:

```
source: <URL | drive:<fileId> "<path>" | https://x.com/<user>/status/<id>>
fetched: <YYYY-MM-DD>
channel: <webfetch | jina | pdftotext | drive | twitter-cli | syndication>
---
<content>
```

## Websites

1. `WebFetch` the URL with a prompt asking for the full text, tables and figure captions,
   not a summary.
2. If it is blocked, JS-rendered or truncated: `curl -sL "https://r.jina.ai/<URL>"`
   (returns clean markdown). Add `-H "X-Return-Format: text"` for plain text.
3. Listing pages ("Reports", "Publications", "Insights"): fetch the listing, collect
   the report links + dates, pick the ones matching the brief, then fetch each one.
   Respect robots and paywalls — if a report is gated behind a form, tell the user
   and ask them to download it into `sources/` themselves (do not fill lead forms).

## PDF reports

```bash
mkdir -p reports/.work/<slug>/sources/raw
curl -sL -o reports/.work/<slug>/sources/raw/<name>.pdf "<pdf-url>"
pdftotext -layout reports/.work/<slug>/sources/raw/<name>.pdf - | head -400   # poppler
```

- No `pdftotext`? Use the `anthropic-skills:pdf` skill or `python3 -m pip install pypdf`
  and extract per page. Scanned PDFs: Read the PDF directly with the `pages` parameter.
- Keep page numbers: cite as "(Source, p. 14)".
- Tables: re-type the numbers you use into a small CSV in `sources/` so charts can be
  rebuilt from them.

## Google Drive

Use the Google Drive connector tools (names end in `search_files`, `read_file_content`,
`download_file_content`, `get_file_metadata`, `list_recent_files`). If they are listed
as deferred, load them with ToolSearch (`"google drive search_files read_file_content"`).

- **Find**: `search_files` with the topic keywords, and again with likely file names
  ("Q3 report", "impact", "deck"). For a folder the user names, search for the folder
  first, then for files whose parent is that folder.
- **Inventory for the brief**: name, type, owner, modified date, link — for every match,
  even the ones you do not read.
- **Read**: Docs/Sheets/Slides → `read_file_content`. PDFs/images →
  `download_file_content` into `sources/raw/`, then process as above. Images the user
  keeps in Drive for the report → download into `images/` named after the slot they fill.
- Never change sharing, move, or trash Drive files. Writing back to Drive (uploading the
  finished PDF) only when the user asks.
- If no Drive tools are available in this session (e.g. connector not enabled in the
  cloud environment), say so in the brief and ask the user to connect Google Drive in
  their claude.ai connector settings.

## Twitter / X (agent-reach + twitter-cli)

Check status first: `agent-reach doctor`. Twitter needs two cookies exported as env vars
in the shell that runs `twitter`:

```
TWITTER_AUTH_TOKEN   TWITTER_CT0
```

In the cloud these come from the environment's secret variables; locally from the user's
shell profile. If they are missing, do not ask for them in chat — tell the user how to set
them (see project README) and continue with the no-login fallback.

Commands (add `--json` for structured output):

```bash
twitter tweet <url-or-id> --json          # tweet + replies (threads)
twitter article <url-or-id>               # long-form X Articles
twitter user-posts @handle -n 30 --json   # someone's recent posts
twitter user @handle --json               # profile, follower counts
twitter search "query" -n 20 --json       # can 404 when X changes endpoints
```

`search` retry chain: retry once → `uv tool upgrade twitter-cli` (or `pipx upgrade`) and
retry → Exa via agent-reach (`mcporter call 'exa.web_search_exa(query: "site:x.com <q>")'`)
→ fall back to `user-posts` of known accounts.

### No-login fallback for single tweet URLs (always works, read-only)

```bash
ID=1234567890123456789
curl -s -A "Mozilla/5.0" "https://cdn.syndication.twimg.com/tweet-result?id=$ID&token=a" \
  | python3 -c 'import sys,json;t=json.load(sys.stdin);print(t["user"]["name"],"@"+t["user"]["screen_name"],t["created_at"]);print(t["text"]);print("likes",t.get("favorite_count"));[print("media",m.get("media_url_https")) for m in t.get("mediaDetails",[])]'
```

Gives text, author, date, like count and media URLs. No search, no timelines, no replies.

### Using tweets in the report

- Quote verbatim, with name, @handle, date and link. Do not paraphrase inside quote marks.
- Render as a designed pull-quote or "social wall" module (see magazine-design.md),
  not as a screenshot of the X UI.
- Cloud machines use datacenter IPs: keep Twitter calls few and slow (no follower
  scraping, no loops of hundreds of requests) to avoid the account being flagged.

## Other channels

Reddit, YouTube transcripts, LinkedIn, GitHub, RSS, podcasts → use the `agent-reach`
skill's routing table. Exa semantic search (`mcporter call 'exa.web_search_exa(...)'`)
is the best way to discover new report URLs on a topic.
