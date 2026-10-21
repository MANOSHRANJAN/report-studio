#!/usr/bin/env python3
"""Render a magazine issue to PDF + PNG previews with headless Chrome, and report
overflowing pages and empty image slots.

usage: render.py <issue-dir> [--html report.html] [--no-previews]

Deliverable: reports/<PDF name>.pdf (name from issue.json) — the only file meant for the user.
Working outputs stay in the hidden issue folder: report.pdf, previews/page-NN.png, previews/contact.png
Chrome is found via $CHROME_PATH, standard install paths, or the Playwright cache.
"""
import argparse
import html.parser
import json
import pathlib
import shutil
import subprocess
import sys

from _chrome import chrome, find_chrome

BUDGET_MS = "10000"  # virtual time for fonts/images to load


def png_size(path):
    """(width, height) from a PNG header — no imaging library needed."""
    with open(path, "rb") as f:
        head = f.read(24)
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


class PageScan(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.pages, self.empty, self.pending = [], [], []
        self._page, self._skip = 0, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag == "section" and "page" in classes:
            if "hidden" in a:  # pending page, not printed
                self.pending.append((a.get("data-type", ""), a.get("data-pending", "")))
                self._skip = True
                return
            self._skip = False
            self._page += 1
            self.pages.append((self._page, a.get("data-type", ""), a.get("data-overflow")))
        if tag == "figure" and "slot" in classes and a.get("data-filled") == "no" and not self._skip:
            self.empty.append((self._page, a.get("data-slot")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("issue")
    ap.add_argument("--html", default="report.html")
    ap.add_argument("--no-previews", action="store_true")
    a = ap.parse_args()

    issue = pathlib.Path(a.issue).resolve()
    src = issue / a.html
    if not src.exists():
        sys.exit(f"missing {src}")
    url = src.as_uri()
    binary = find_chrome()

    # 1. layout check (scripts in the template flag overflow + empty slots in the DOM)
    dom = chrome(binary, f"--virtual-time-budget={BUDGET_MS}", "--window-size=900,1200", "--dump-dom", url)
    scan = PageScan()
    scan.feed(dom)
    if not scan.pages:
        sys.exit("render failed: no .page sections found in rendered DOM")

    # 2. PDF
    pdf = issue / "report.pdf"
    chrome(binary, f"--virtual-time-budget={BUDGET_MS}", "--no-pdf-header-footer",
           f"--print-to-pdf={pdf}", url, out_file=pdf)
    if not pdf.exists():
        sys.exit("PDF was not produced")

    # 3. previews
    prev = issue / "previews"
    if not a.no_previews:
        prev.mkdir(exist_ok=True)
        for old in prev.glob("page-*.png"):
            old.unlink()
        if shutil.which("pdftoppm"):
            subprocess.run(["pdftoppm", "-png", "-r", "80", str(pdf), str(prev / "page")], check=True)
            for p in prev.glob("page-*.png"):  # normalise page-1.png / page-01.png
                n = int(p.stem.split("-")[-1])
                p.rename(prev / f"page-{n:02d}.png")
        else:
            for n, _, _ in scan.pages:
                shot = prev / f"page-{n:02d}.png"
                chrome(binary, f"--virtual-time-budget={BUDGET_MS}", "--window-size=794,1123",
                       f"--screenshot={shot}", f"{url}#page={n}", out_file=shot)
        pngs = sorted(prev.glob("page-*.png"))
        if pngs:
            cells = "".join(f'<figure><img src="{p.name}"><figcaption>{p.stem[5:]}</figcaption></figure>' for p in pngs)
            sheet = prev / "contact.html"
            sheet.write_text(
                "<style>body{margin:0;background:#777;display:grid;grid-template-columns:repeat(4,1fr);"
                "gap:16px;padding:16px;font:12px sans-serif;color:#fff}figure{margin:0}"
                "img{width:100%;display:block;box-shadow:0 2px 8px #0006}</style>" + cells, encoding="utf-8")
            rows = (len(pngs) + 3) // 4
            w, h = png_size(pngs[0])
            cell_h = int(((1600 - 32 - 48) / 4) * h / w) + 40  # 4 columns, keep page aspect
            chrome(binary, "--virtual-time-budget=3000", f"--window-size=1600,{rows * cell_h + 40}",
                   f"--screenshot={prev / 'contact.png'}", sheet.as_uri(), out_file=prev / "contact.png")
            sheet.unlink()

    # 4. publish the PDF — the one deliverable — next to the hidden working folder
    final = pdf
    meta = issue / "issue.json"
    if meta.exists():
        name = json.loads(meta.read_text()).get("pdf_name") or "report.pdf"
        out_dir = issue.parent.parent if issue.parent.name == ".work" else issue.parent
        final = out_dir / name
        shutil.copy(pdf, final)

    # 5. report
    print(f"PDF       {final}  ({final.stat().st_size // 1024} KB, {len(scan.pages)} pages)")
    if not a.no_previews:
        print(f"Previews  {prev}/page-NN.png  ·  overview: {prev / 'contact.png'}")
    over = [f"p{n} ({t})" for n, t, o in scan.pages if o == "yes"]
    print("Overflow  " + (", ".join(over) + "  ← cut copy or resize, then re-render" if over else "none"))
    print("Empty     " + (", ".join(f"{s} (p{n})" for n, s in scan.empty) if scan.empty else "all image slots filled"))
    for t, why in scan.pending:
        print(f"Pending   {t}: {why}")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
