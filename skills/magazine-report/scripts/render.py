#!/usr/bin/env python3
"""Render a magazine issue to PDF + PNG previews with headless Chrome, and report
overflowing pages and empty image slots.

usage: render.py <issue-dir> [--html report.html] [--no-previews]

Outputs in <issue-dir>: report.pdf, previews/page-NN.png, previews/contact.png
Chrome is found via $CHROME_PATH, standard install paths, or the Playwright cache.
"""
import argparse
import glob
import html.parser
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
import time

BUDGET_MS = "10000"  # virtual time for fonts/images to load


def find_chrome() -> str:
    env = os.environ.get("CHROME_PATH") or os.environ.get("PUPPETEER_EXECUTABLE_PATH")
    candidates = [env] if env else []
    candidates += [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        if shutil.which(name):
            candidates.append(shutil.which(name))
    home = pathlib.Path.home()
    for pat in ("~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome",
                "~/Library/Caches/ms-playwright/chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium",
                "~/Library/Caches/ms-playwright/chromium-*/chrome-mac*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"):
        candidates += sorted(glob.glob(os.path.expanduser(pat)), reverse=True)
    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    sys.exit("No Chrome/Chromium found. Install one or set CHROME_PATH "
             "(cloud: npx -y playwright install chromium).")


def chrome(binary, *args, out_file=None, timeout=90):
    """Run headless Chrome once. Some Chrome builds never exit after --dump-dom /
    --print-to-pdf / --screenshot, so we stop it as soon as the output is complete:
    stdout ends with </html>, or out_file exists and its size stopped changing."""
    profile = tempfile.mkdtemp(prefix="mag-chrome-")
    cmd = [binary, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
           "--no-default-browser-check", "--allow-file-access-from-files",
           "--disable-background-networking", "--disable-sync", "--disable-component-update",
           "--disable-extensions", "--no-service-autorun", "--use-mock-keychain",
           "--password-store=basic", f"--user-data-dir={profile}"]
    if platform.system() == "Linux":
        cmd += ["--no-sandbox", "--disable-dev-shm-usage"]
    if out_file:
        pathlib.Path(out_file).unlink(missing_ok=True)
    stdout_path = pathlib.Path(profile) / "stdout.html"
    with open(stdout_path, "wb") as so:
        proc = subprocess.Popen(cmd + list(args), stdout=so, stderr=subprocess.DEVNULL)
        deadline, last_size, stable = time.time() + timeout, -1, 0
        while time.time() < deadline and proc.poll() is None:
            time.sleep(0.5)
            if out_file:
                p = pathlib.Path(out_file)
                size = p.stat().st_size if p.exists() else -1
                stable = stable + 1 if size > 0 and size == last_size else 0
                last_size = size
                if stable >= 2:
                    break
            elif stdout_path.read_bytes().rstrip().endswith(b"</html>"):
                break
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(5)
            except subprocess.TimeoutExpired:
                proc.kill()
    out = stdout_path.read_text(encoding="utf-8", errors="replace")
    shutil.rmtree(profile, ignore_errors=True)
    return out


class PageScan(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.pages, self.empty = [], []
        self._page = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag == "section" and "page" in classes:
            self._page += 1
            self.pages.append((self._page, a.get("data-type", ""), a.get("data-overflow")))
        if tag == "figure" and "slot" in classes and a.get("data-filled") == "no":
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
            chrome(binary, "--virtual-time-budget=3000", f"--window-size=1600,{rows * 610 + 40}",
                   f"--screenshot={prev / 'contact.png'}", sheet.as_uri(), out_file=prev / "contact.png")
            sheet.unlink()

    # 4. report
    print(f"PDF       {pdf}  ({pdf.stat().st_size // 1024} KB, {len(scan.pages)} pages)")
    if not a.no_previews:
        print(f"Previews  {prev}/page-NN.png  ·  overview: {prev / 'contact.png'}")
    over = [f"p{n} ({t})" for n, t, o in scan.pages if o == "yes"]
    print("Overflow  " + (", ".join(over) + "  ← cut copy or resize, then re-render" if over else "none"))
    print("Empty     " + (", ".join(f"{s} (p{n})" for n, s in scan.empty) if scan.empty else "all image slots filled"))
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
