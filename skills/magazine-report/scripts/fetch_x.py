#!/usr/bin/env python3
"""Collect everything an X/Twitter account posted in one month (via twitter-cli / Agent Reach).

usage: fetch_x.py <issue-dir> [--month YYYY-MM] [--handle NAME ...] [--max 300]
                  [--include-replies] [--include-retweets] [--from-json FILE] [--config ...]

Needs TWITTER_AUTH_TOKEN + TWITTER_CT0 in the environment (see README → Twitter access).
--from-json parses a file saved earlier with `twitter ... --json -o FILE` instead of calling X.
Writes sources/x.json, sources/x.md and images/candidates/x-*.jpg (photos attached to posts).
Exit code 2 = no credentials (nothing fetched).
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys

from _common import add_credit, in_window, load_config, month_window, save_image, write_json


def run_twitter(args):
    exe = shutil.which("twitter") or os.path.expanduser("~/.local/bin/twitter")
    if not os.path.exists(exe):
        return None, "twitter-cli not installed (bash scripts/setup.sh --install)"
    try:
        r = subprocess.run([exe, *args, "--json"], capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired:
        return None, "twitter-cli timed out"
    try:
        payload = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None, (r.stderr or r.stdout)[-400:]
    if isinstance(payload, dict) and payload.get("ok") is False:
        return None, json.dumps(payload.get("error"))[:400]
    data = payload.get("data") if isinstance(payload, dict) else payload
    return (data if isinstance(data, list) else []), None


def from_opencli(row):
    """Normalise an `opencli twitter search/tweets -f json` row (Agent Reach's browser-session
    backend) to twitter-cli's schema."""
    media = []
    for u in row.get("media_urls") or []:
        if "pbs.twimg.com/media" in u:
            media.append({"type": "photo", "url": u.split("?")[0]})
    for u in row.get("media_posters") or []:  # video poster frames work as photos
        if u:
            media.append({"type": "photo", "url": u.split("?")[0], "poster": True})
    handle = row.get("author") or ""
    return {"id": str(row.get("id")), "text": row.get("text", ""),
            "author": {"screenName": handle, "name": handle},
            "metrics": {"likes": int(row.get("likes") or 0), "views": int(row.get("views") or 0)},
            "createdAt": row.get("created_at", ""), "media": media, "urls": [],
            "isRetweet": (row.get("text") or "").startswith("RT @")}


def created_iso(t):
    iso = t.get("createdAtISO") or ""
    if iso[:4].isdigit():
        return iso
    try:  # raw Twitter format: "Wed Oct 10 20:19:24 +0000 2018"
        return dt.datetime.strptime(t.get("createdAt", ""), "%a %b %d %H:%M:%S %z %Y").isoformat()
    except ValueError:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("issue")
    ap.add_argument("--month")
    ap.add_argument("--handle", action="append")
    ap.add_argument("--max", type=int)
    ap.add_argument("--include-replies", action="store_true")
    ap.add_argument("--include-retweets", action="store_true")
    ap.add_argument("--from-json", action="append",
                    help="parse saved JSON instead of fetching: twitter-cli output, x_from_browser.mjs "
                         "output, or `opencli twitter search ... -f json` (repeatable)")
    ap.add_argument("--config")
    a = ap.parse_args()

    cfg = load_config(a.config).get("twitter", {})
    handles = [h.lstrip("@") for h in (a.handle or cfg.get("handles") or [])]
    if not handles and not a.from_json:
        sys.exit("no handle: pass --handle or set twitter.handles in report.config.json")
    max_n = a.max or cfg.get("max_posts", 300)
    replies = a.include_replies or cfg.get("include_replies", False)
    retweets = a.include_retweets or cfg.get("include_retweets", False)
    win = month_window(a.month)
    issue = pathlib.Path(a.issue).resolve()
    since, until = win["start"].isoformat(), win["end"].isoformat()

    raw, methods, errors = [], [], []
    if a.from_json:
        for f in a.from_json:
            payload = json.loads(pathlib.Path(f).read_text())
            rows = payload.get("data", payload) if isinstance(payload, dict) else payload
            if rows and isinstance(rows[0].get("author"), str):  # opencli rows
                rows = [from_opencli(r) for r in rows]
                methods.append(f"opencli:{pathlib.Path(f).name}")
            else:
                methods.append(f"file:{pathlib.Path(f).name}")
            raw += rows
        handles = handles or sorted({(r.get("author") or {}).get("screenName", "") for r in raw} - {""})
    else:
        if not (os.environ.get("TWITTER_AUTH_TOKEN") and os.environ.get("TWITTER_CT0")):
            write_json(issue / "sources" / "x.json", {"status": "no-auth", "handles": handles, "month": win["key"]})
            print("X: TWITTER_AUTH_TOKEN / TWITTER_CT0 not set — nothing fetched.\n"
                  "   Set them (README → Twitter access), or save posts manually and use --from-json.\n"
                  "   Single tweet URLs still work via the no-login syndication endpoint (sourcing.md).")
            sys.exit(2)
        for h in handles:
            args = ["search", "--from", h, "--since", since, "--until", until, "-t", "latest", "-n", str(max_n)]
            if not replies:
                args += ["--exclude", "replies"]
            if not retweets:
                args += ["--exclude", "retweets"]
            data, err = run_twitter(args)
            if data:
                raw += data
                methods.append(f"search:{h}")
                continue
            errors.append(f"search {h}: {err or 'no results'}")
            # fallback: recent timeline, filtered to the month (works only for recent months)
            data, err = run_twitter(["user-posts", h, "-n", str(max_n)])
            if data:
                raw += data
                methods.append(f"user-posts:{h}")
            else:
                errors.append(f"user-posts {h}: {err or 'no results'}")

    tweets, seen = [], set()
    for t in raw:
        iso = created_iso(t)
        if not iso or not in_window(iso, win) or t.get("id") in seen:
            continue
        if t.get("isRetweet") and not retweets:
            continue
        if not replies and (t.get("text") or "").startswith("@"):
            continue
        seen.add(t.get("id"))
        author = t.get("author") or {}
        handle = author.get("screenName") or (handles[0] if handles else "")
        m = t.get("metrics") or {}
        tweets.append({
            "id": t.get("id"), "date": iso[:10], "created": iso, "handle": handle,
            "url": f"https://x.com/{handle}/status/{t.get('id')}",
            "text": t.get("text", ""), "metrics": {k: int(m.get(k) or 0) for k in
                                                   ("views", "likes", "retweets", "replies", "quotes", "bookmarks")},
            "media": [x for x in t.get("media") or [] if x.get("type") == "photo"],
            "urls": t.get("urls") or [], "article_title": t.get("articleTitle"),
        })
    tweets.sort(key=lambda x: x["created"])

    cand = issue / "images" / "candidates"
    for tw in tweets:
        tw["local_images"] = []
        for i, med in enumerate(tw["media"], 1):
            url = med["url"]
            url = url + ("&" if "?" in url else "?") + "name=large" if "pbs.twimg.com" in url else url
            p = save_image(url, cand / f"x-{tw['date']}-{tw['id']}-{i}")
            if p:
                tw["local_images"].append(p.name)
                add_credit(issue, p.name, {"source": "x", "page_url": tw["url"],
                                           "credit_line": ""})  # own content: no visible credit

    totals = {k: sum(t["metrics"][k] for t in tweets) for k in ("views", "likes", "retweets", "replies")}
    weeks = {}
    for t in tweets:
        w = f"W{(int(t['date'][8:10]) - 1) // 7 + 1}"
        weeks[w] = weeks.get(w, 0) + 1
    rank = sorted(tweets, key=lambda t: (t["metrics"]["views"], t["metrics"]["likes"]), reverse=True)
    out = {"status": "ok" if tweets else "empty", "handles": handles, "month": win["key"],
           "methods": methods, "errors": errors, "count": len(tweets), "totals": totals,
           "posts_per_week": weeks, "top_ids": [t["id"] for t in rank[:7]], "tweets": tweets}
    write_json(issue / "sources" / "x.json", out)

    md = [f"source: x.com/{', x.com/'.join(handles)}\nfetched-for: {win['key']}\nchannel: twitter-cli ({', '.join(methods)})\n---\n",
          f"# X posts — {win['month_name']} {win['year']}\n\n{len(tweets)} posts · totals {totals} · per week {weeks}\n"]
    if errors:
        md.append(f"\nErrors: {errors}\n")
    md.append("\n## Top posts\n")
    for t in rank[:7]:
        md.append(f"- {t['date']} · {t['metrics']['views']} views · {t['metrics']['likes']} likes · {t['url']}\n  {t['text'][:280]}\n")
    md.append("\n## All posts\n")
    for t in tweets:
        md.append(f"- {t['date']} {t['url']} — {t['text'][:500]}  [{', '.join(t['local_images'])}]\n")
    (issue / "sources" / "x.md").write_text("".join(md), encoding="utf-8")
    print(f"X → {len(tweets)} posts ({', '.join(methods) or 'none'}) · {sum(len(t['local_images']) for t in tweets)} images"
          + (f" · errors: {errors}" if errors else ""))


if __name__ == "__main__":
    main()
