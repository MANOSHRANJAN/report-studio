#!/usr/bin/env python3
"""Find and download relevant stock photos, with attribution, to fill image gaps.

usage: stock.py <issue-dir> --query "Hindu temple festival" [--n 4]
                [--orientation landscape|portrait|square] [--provider auto|pexels|unsplash|openverse]

Providers (auto = first available):
  pexels     needs PEXELS_API_KEY        free licence, credit appreciated
  unsplash   needs UNSPLASH_ACCESS_KEY   free licence, credit required by API terms
  openverse  no key                      Creative Commons (commercial + modification allowed),
                                         credit required — written to images/credits.json
Writes images/candidates/stock-<provider>-<query>-N.<ext>.
"""
import argparse
import os
import pathlib
import sys
import time
import urllib.parse

from _common import add_credit, http_json, load_config, save_image, slugify

OV_LICENSE_NAMES = {"by": "CC BY", "by-sa": "CC BY-SA", "cc0": "CC0", "pdm": "Public Domain"}


def pexels(q, n, orient):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None
    o = {"landscape": "landscape", "portrait": "portrait", "square": "square"}[orient]
    data, _ = http_json(f"https://api.pexels.com/v1/search?query={urllib.parse.quote(q)}&per_page={n}&orientation={o}",
                        headers={"Authorization": key})
    return [{"url": p["src"]["large2x"], "page_url": p["url"], "creator": p["photographer"],
             "title": p.get("alt") or q, "license": "Pexels License",
             "credit_line": f"Photo: {p['photographer']} / Pexels"} for p in data.get("photos", [])]


def unsplash(q, n, orient):
    key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not key:
        return None
    o = {"landscape": "landscape", "portrait": "portrait", "square": "squarish"}[orient]
    data, _ = http_json(f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(q)}&per_page={n}"
                        f"&orientation={o}&client_id={key}")
    out = []
    for p in data.get("results", []):
        try:  # API terms: register the download
            http_json(f"{p['links']['download_location']}&client_id={key}")
        except Exception:
            pass
        name = p["user"]["name"]
        out.append({"url": p["urls"]["regular"], "page_url": p["links"]["html"], "creator": name,
                    "title": p.get("alt_description") or q, "license": "Unsplash License",
                    "credit_line": f"Photo: {name} / Unsplash"})
    return out


def openverse(q, n, orient):
    ar = {"landscape": "wide", "portrait": "tall", "square": "square"}[orient]
    url = (f"https://api.openverse.org/v1/images/?q={urllib.parse.quote(q)}&license_type=commercial,modification"
           f"&aspect_ratio={ar}&size=large&mature=false&page_size={min(n * 3, 30)}")
    data = None
    for attempt_url in (url, url.replace("&size=large", "")):  # Openverse is sometimes slow
        try:
            data, _ = http_json(attempt_url, timeout=60)
            break
        except Exception as e:
            print(f"  openverse retry ({e})", file=sys.stderr)
    if data is None:
        raise RuntimeError("Openverse unreachable")
    out = []
    for r in data.get("results", []):
        if (r.get("width") or 0) < 900:
            continue
        lic = OV_LICENSE_NAMES.get(r.get("license"), (r.get("license") or "").upper())
        ver = r.get("license_version") or ""
        creator = r.get("creator") or ""
        out.append({"url": r["url"], "page_url": r.get("foreign_landing_url"), "creator": creator,
                    "title": r.get("title") or q, "license": f"{lic} {ver}".strip(),
                    "license_url": r.get("license_url"),
                    "credit_line": f"Photo: {creator + ' / ' if creator else ''}{r.get('source', 'Openverse').title()}, {lic} {ver}".strip()})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("issue")
    ap.add_argument("--query", required=True)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--orientation", default="landscape", choices=["landscape", "portrait", "square"])
    ap.add_argument("--provider", default="auto")
    ap.add_argument("--config")
    a = ap.parse_args()

    issue = pathlib.Path(a.issue).resolve()
    order = load_config(a.config).get("stock", {}).get("providers") or ["pexels", "unsplash", "openverse"]
    if a.provider != "auto":
        order = [a.provider]
    funcs = {"pexels": pexels, "unsplash": unsplash, "openverse": openverse}

    for name in order:
        try:
            results = funcs[name](a.query, a.n, a.orientation)
        except Exception as e:
            print(f"! {name}: {e}", file=sys.stderr)
            continue
        if results is None:  # no API key
            continue
        saved = 0
        for r in results:
            if saved >= a.n:
                break
            stem = issue / "images" / "candidates" / f"stock-{name}-{slugify(a.query, 24)}-{saved + 1}"
            time.sleep(1)  # be polite to image hosts
            p = save_image(r["url"], stem, min_bytes=30_000)
            if not p:
                continue
            saved += 1
            add_credit(issue, p.name, {"source": name, **{k: v for k, v in r.items() if k != "url"}})
            print(f"{p.name}  ·  {r['credit_line']}")
        if saved:
            return
        print(f"! {name}: nothing usable for '{a.query}'", file=sys.stderr)
    sys.exit("no stock images found — try a broader query or set PEXELS_API_KEY / UNSPLASH_ACCESS_KEY")


if __name__ == "__main__":
    main()
