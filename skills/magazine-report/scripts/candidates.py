#!/usr/bin/env python3
"""Contact sheet of every candidate image, so Claude (or you) can pick photos for slots.

usage: candidates.py <issue-dir>
Writes previews/candidates-N.png (24 images per sheet) and images/candidates/index.json.
Each tile shows #, filename, pixel size, orientation and source (drive / x / website / stock).
"""
import argparse
import html
import json
import pathlib

from _chrome import chrome, find_chrome

PER_SHEET = 24
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("issue")
    a = ap.parse_args()
    issue = pathlib.Path(a.issue).resolve()
    cand = issue / "images" / "candidates"
    files = sorted(p for p in cand.glob("*") if p.suffix.lower() in EXTS)
    if not files:
        raise SystemExit(f"no candidates in {cand}")
    credits_file = issue / "images" / "credits.json"
    credits = json.loads(credits_file.read_text()) if credits_file.exists() else {}
    order = {"google-drive": 0, "x": 1, "website": 2}
    files.sort(key=lambda p: (order.get(credits.get(p.name, {}).get("source"), 3), p.name))

    index = [{"n": i + 1, "file": p.name, "source": credits.get(p.name, {}).get("source", "?"),
              "credit_line": credits.get(p.name, {}).get("credit_line", "")} for i, p in enumerate(files)]
    (cand / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False))

    binary = find_chrome()
    (issue / "previews").mkdir(exist_ok=True)
    sheets = []
    for s in range(0, len(files), PER_SHEET):
        chunk = list(enumerate(files[s:s + PER_SHEET], start=s + 1))
        tiles = "".join(
            f'<figure><div><img src="{p.as_uri()}"></div><figcaption><b>#{n}</b> '
            f'<span class="src {html.escape(credits.get(p.name, {}).get("source", "?"))}">'
            f'{html.escape(credits.get(p.name, {}).get("source", "?"))}</span> <span class="dim"></span>'
            f'<br>{html.escape(p.name[:46])}</figcaption></figure>' for n, p in chunk)
        page = issue / "previews" / "_candidates.html"
        page.write_text(
            "<style>body{margin:0;padding:14px;background:#1d1d1d;color:#eee;font:11px/1.35 ui-monospace,monospace;"
            "display:grid;grid-template-columns:repeat(6,1fr);gap:12px}figure{margin:0}"
            "figure div{aspect-ratio:1;background:#333;display:flex;align-items:center;justify-content:center}"
            "img{max-width:100%;max-height:100%;object-fit:contain}figcaption{margin-top:4px}"
            ".src{padding:0 4px;border-radius:2px;background:#555}.google-drive{background:#1a7f37}"
            ".x{background:#333;outline:1px solid #888}.website{background:#9a6700}"
            ".openverse,.pexels,.unsplash{background:#8250df}</style>" + tiles +
            "<script>document.querySelectorAll('figure').forEach(f=>{const i=f.querySelector('img');"
            "const set=()=>{f.querySelector('.dim').textContent=i.naturalWidth+'×'+i.naturalHeight+' '+"
            "(i.naturalWidth>i.naturalHeight*1.15?'land':i.naturalHeight>i.naturalWidth*1.15?'port':'sq')};"
            "i.complete?set():i.onload=set})</script>", encoding="utf-8")
        out = issue / "previews" / f"candidates-{s // PER_SHEET + 1}.png"
        rows = (len(chunk) + 5) // 6
        chrome(binary, "--virtual-time-budget=6000", f"--window-size=1500,{rows * 330 + 60}",
               f"--screenshot={out}", page.as_uri(), out_file=out)
        page.unlink()
        sheets.append(out)
    by_src = {}
    for i in index:
        by_src[i["source"]] = by_src.get(i["source"], 0) + 1
    print(f"{len(files)} candidates {by_src}")
    for sh in sheets:
        print(f"sheet  {sh}")
    print(f"index  {cand / 'index.json'}  (#n → filename; assign with slots.py fill --assign SLOT=images/candidates/<file>)")


if __name__ == "__main__":
    main()
