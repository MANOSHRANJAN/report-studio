#!/usr/bin/env python3
"""Collect everything a website published in one month.

usage: fetch_web.py <issue-dir> [--month YYYY-MM] [--site URL] [--types posts,events,...]
                    [--modified] [--max-images 60] [--config report.config.json]

Strategy (first that works):
  1. WordPress REST API  /wp-json/wp/v2/<type>?after=..&before=..  (posts + custom post types)
  2. Sitemaps            <lastmod> inside the month
  3. RSS/Atom feed       <pubDate> inside the month
Writes sources/web.json, sources/web.md, and images/candidates/web-*.{jpg,png,webp}.
"""
import argparse
import html
import pathlib
import re
import sys
import urllib.error
import xml.etree.ElementTree as ET

from _common import (add_credit, html_to_text, http_get, http_json, in_window, load_config,
                     month_window, save_image, slugify, write_json)

WP_INTERNAL = {"page", "attachment", "nav_menu_item", "wp_block", "wp_template", "wp_template_part",
               "wp_global_styles", "wp_navigation", "wp_font_family", "wp_font_face",
               "elementor_library", "elementor_snippet", "e-floating-buttons", "jp_search_overlay",
               "feedback", "jetpack_form", "jp_act_log_event", "jp_pay_order", "jp_pay_product",
               "wp_knowledge", "pending-events"}


def wp_types(site):
    try:
        types, _ = http_json(f"{site}/wp-json/wp/v2/types")
    except Exception:
        return None
    return {k: v.get("rest_base") for k, v in types.items()
            if v.get("rest_base") and k not in WP_INTERNAL and "(?P<" not in v["rest_base"]}


def wp_collect(site, bases, win, modified):
    items = []
    s, e = f"{win['start']}T00:00:00", f"{win['end']}T00:00:00"
    for base in bases:
        modes = [("published", f"after={s}&before={e}")]
        if modified:
            modes.append(("updated", f"modified_after={s}&modified_before={e}"))
        seen = set()
        for status, q in modes:
            page = 1
            while True:
                url = (f"{site}/wp-json/wp/v2/{base}?{q}&per_page=100&page={page}"
                       f"&orderby=date&order=asc&_embed=wp:featuredmedia")
                try:
                    data, hdrs = http_json(url, timeout=40)
                except urllib.error.HTTPError as err:
                    if err.code != 400:  # 400 = page past the end
                        print(f"  ! {base}: HTTP {err.code}", file=sys.stderr)
                    break
                except Exception as err:
                    print(f"  ! {base}: {err}", file=sys.stderr)
                    break
                if not isinstance(data, list) or not data:
                    break
                for p in data:
                    if p["id"] in seen:
                        continue
                    seen.add(p["id"])
                    text, imgs = html_to_text((p.get("content") or {}).get("rendered", ""))
                    excerpt, _ = html_to_text((p.get("excerpt") or {}).get("rendered", ""))
                    feat = None
                    for m in (p.get("_embedded") or {}).get("wp:featuredmedia", []) or []:
                        sizes = (m.get("media_details") or {}).get("sizes") or {}
                        feat = (sizes.get("large") or sizes.get("full") or {}).get("source_url") or m.get("source_url")
                    items.append({
                        "type": base, "status": status, "id": p["id"],
                        "date": p.get("date", "")[:10], "modified": p.get("modified", "")[:10],
                        "title": html.unescape((p.get("title") or {}).get("rendered", "")).strip(),
                        "link": p.get("link"), "excerpt": excerpt[:600], "text": text[:8000],
                        "featured_image": feat, "content_images": imgs[:6],
                    })
                total_pages = int(hdrs.get("X-WP-TotalPages") or hdrs.get("x-wp-totalpages") or 1)
                if page >= total_pages:
                    break
                page += 1
        n = sum(1 for i in items if i["type"] == base)
        print(f"  {base:<24} {n} item(s)")
    return items


def sitemap_urls(site, win):
    out, queue, seen = [], [f"{site}/sitemap_index.xml", f"{site}/sitemap.xml"], set()
    while queue:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        try:
            body, _ = http_get(sm, timeout=30)
            root = ET.fromstring(body)
        except Exception:
            continue
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for node in root.findall("s:sitemap", ns):
            queue.append(node.findtext("s:loc", default="", namespaces=ns))
        for node in root.findall("s:url", ns):
            loc = node.findtext("s:loc", default="", namespaces=ns)
            lastmod = node.findtext("s:lastmod", default="", namespaces=ns)
            if lastmod and in_window(lastmod, win):
                out.append((loc, lastmod[:10]))
    return out


def page_item(url, date, status):
    try:
        body, _ = http_get(url, timeout=40)
    except Exception as err:
        print(f"  ! {url}: {err}", file=sys.stderr)
        return None
    raw = body.decode("utf-8", "replace")
    title = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    og = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', raw, re.I)
    main = re.search(r"<(article|main)[^>]*>(.*?)</\1>", raw, re.S | re.I)
    text, imgs = html_to_text(main.group(2) if main else raw)
    return {"type": "page", "status": status, "date": date, "title": html.unescape(title.group(1).strip()) if title else url,
            "link": url, "excerpt": text[:600], "text": text[:8000],
            "featured_image": og.group(1) if og else None, "content_images": imgs[:6]}


def rss_items(site, win):
    for feed in (f"{site}/feed/", f"{site}/rss.xml", f"{site}/atom.xml", f"{site}/feed.xml"):
        try:
            body, _ = http_get(feed, timeout=30)
            root = ET.fromstring(body)
        except Exception:
            continue
        out = []
        import email.utils
        for it in root.iter("item"):
            pub = it.findtext("pubDate") or ""
            try:
                d = email.utils.parsedate_to_datetime(pub).date().isoformat()
            except Exception:
                continue
            if in_window(d, win):
                out.append((it.findtext("link"), d))
        return out
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("issue")
    ap.add_argument("--month")
    ap.add_argument("--site")
    ap.add_argument("--types", help="comma-separated WP rest bases (default: config or all public)")
    ap.add_argument("--modified", action="store_true", help="also include items only updated in the month")
    ap.add_argument("--max-images", type=int, default=60)
    ap.add_argument("--config")
    a = ap.parse_args()

    cfg = load_config(a.config).get("website", {})
    site = (a.site or cfg.get("url") or "").rstrip("/")
    if not site:
        sys.exit("no site: pass --site or set website.url in report.config.json")
    win = month_window(a.month)
    issue = pathlib.Path(a.issue).resolve()
    modified = a.modified or cfg.get("include_modified", False)
    print(f"Website {site} · {win['month_name']} {win['year']}")

    method, items = None, []
    types = wp_types(site)
    if types is not None:
        method = "wordpress-rest"
        wanted = (a.types.split(",") if a.types else cfg.get("wp_types")) or sorted(set(types.values()))
        items = wp_collect(site, wanted, win, modified)
    if not items:
        urls = sitemap_urls(site, win)
        if urls:
            method = "sitemap-lastmod"
        else:
            urls, method = rss_items(site, win), "rss"
        for url, d in urls[:80]:
            it = page_item(url, d, "published-or-updated")
            if it:
                items.append(it)

    # page builders (Elementor, ACF fields) often keep content out of the REST body:
    # read the rendered page when the API text is thin
    for it in items:
        if len(it.get("text", "")) < 300 and it.get("link"):
            page = page_item(it["link"], it["date"], it["status"])
            if page and len(page["text"]) > len(it.get("text", "")):
                it["text"], it["excerpt"] = page["text"], page["excerpt"]
                it["featured_image"] = it.get("featured_image") or page["featured_image"]
                it["content_images"] = it.get("content_images") or page["content_images"]

    # images: featured first, then content images, de-duplicated
    cand = issue / "images" / "candidates"
    got, seen = 0, set()
    for it in items:
        it["local_images"] = []
        for src in [it.get("featured_image"), *it.get("content_images", [])]:
            if not src or src in seen or got >= a.max_images:
                continue
            seen.add(src)
            stem = cand / f"web-{it['date']}-{slugify(it['title'], 30)}-{len(it['local_images']) + 1}"
            p = save_image(src, stem, min_bytes=15_000)
            if p:
                it["local_images"].append(p.name)
                add_credit(issue, p.name, {"source": "website", "page_url": it["link"],
                                           "credit_line": ""})  # own content: no visible credit
                got += 1

    items.sort(key=lambda i: (i["date"], i["type"]))
    by_type = {}
    for it in items:
        by_type[it["type"]] = by_type.get(it["type"], 0) + 1
    out = {"site": site, "month": win["key"], "method": method, "count": len(items),
           "by_type": by_type, "items": items}
    write_json(issue / "sources" / "web.json", out)

    md = [f"source: {site}\nfetched-for: {win['key']}\nchannel: {method}\n---\n",
          f"# {site} — {win['month_name']} {win['year']}\n", f"{len(items)} items: {by_type}\n"]
    for it in items:
        md.append(f"\n## {it['date']} · [{it['type']}] {it['title']}\n{it['link']}\n"
                  f"images: {', '.join(it['local_images']) or '—'}\n\n{it['text'][:3000]}\n")
    (issue / "sources" / "web.md").write_text("".join(md), encoding="utf-8")
    print(f"→ {len(items)} items via {method} · {got} images in images/candidates/ · sources/web.json")


if __name__ == "__main__":
    main()
