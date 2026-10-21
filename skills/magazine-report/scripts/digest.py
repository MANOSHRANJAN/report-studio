#!/usr/bin/env python3
"""Merge the month's sources into one digest for the BRIEF and the numbers / timeline pages.

usage: digest.py <issue-dir>
Reads sources/web.json, sources/x.json (either may be missing) and writes:
  sources/month.json  — counts, X totals, top posts, merged dated timeline
  sources/digest.md   — the same, readable; paste the key parts into brief.md
"""
import argparse
import json
import pathlib

from _common import write_json


def load(p):
    return json.loads(p.read_text()) if p.exists() else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("issue")
    a = ap.parse_args()
    issue = pathlib.Path(a.issue).resolve()
    web = load(issue / "sources" / "web.json")
    x = load(issue / "sources" / "x.json")
    month = web.get("month") or x.get("month")

    timeline = []
    for it in web.get("items", []):
        timeline.append({"date": it["date"], "src": it["type"], "title": it["title"], "link": it["link"],
                         "images": it.get("local_images", [])})
    tweets = x.get("tweets", [])
    top = [t for t in tweets if t["id"] in set(x.get("top_ids", []))]
    top.sort(key=lambda t: (t["metrics"]["views"], t["metrics"]["likes"]), reverse=True)
    for t in tweets:
        timeline.append({"date": t["date"], "src": "x", "title": t["text"][:140].replace("\n", " "),
                         "link": t["url"], "images": t.get("local_images", []),
                         "views": t["metrics"]["views"], "likes": t["metrics"]["likes"]})
    timeline.sort(key=lambda e: (e["date"], e["src"]))

    data = {
        "month": month,
        "website": {"site": web.get("site"), "method": web.get("method"), "count": web.get("count", 0),
                    "by_type": web.get("by_type", {})},
        "x": {"status": x.get("status", "missing"), "handles": x.get("handles"), "count": x.get("count", 0),
              "totals": x.get("totals", {}), "posts_per_week": x.get("posts_per_week", {}),
              "errors": x.get("errors", [])},
        "top_posts": [{k: t[k] for k in ("date", "url", "text", "metrics", "local_images")} for t in top],
        "timeline": timeline,
    }
    write_json(issue / "sources" / "month.json", data)

    w, xs = data["website"], data["x"]
    lines = [f"# Month digest — {month}\n",
             f"\n## Website ({w['site']}, via {w['method']})\n{w['count']} items · {w['by_type']}\n",
             f"\n## X ({', '.join('@' + h for h in xs['handles'] or [])})\n"]
    if xs["status"] in ("ok", "empty"):
        lines.append(f"{xs['count']} posts · totals {xs['totals']} · per week {xs['posts_per_week']}\n")
    else:
        lines.append(f"NOT AVAILABLE ({xs['status']}). Drop the On-X page or fill it from tweet URLs "
                     f"the user provides (syndication fallback).\n")
    if xs["errors"]:
        lines.append(f"errors: {xs['errors']}\n")
    if data["top_posts"]:
        lines.append("\n## Top posts\n")
        for t in data["top_posts"]:
            lines.append(f"- {t['date']} · {t['metrics']['views']:,} views · {t['metrics']['likes']:,} likes · "
                         f"{t['url']}\n  {t['text'][:240]}\n")
    lines.append("\n## Timeline\n")
    for e in timeline:
        img = f"  [{len(e['images'])} img]" if e["images"] else ""
        lines.append(f"- {e['date']} · {e['src']:<10} {e['title'][:110]}{img}\n")
    (issue / "sources" / "digest.md").write_text("".join(lines), encoding="utf-8")
    print("".join(lines[:4]).strip())
    print(f"→ sources/month.json, sources/digest.md ({len(timeline)} timeline entries)")


if __name__ == "__main__":
    main()
