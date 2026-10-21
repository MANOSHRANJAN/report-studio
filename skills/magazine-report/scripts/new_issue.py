#!/usr/bin/env python3
"""Create an issue folder with template, engine files, brand, brief skeleton.

usage:
  new_issue.py "Report title" [--masthead NAME]        general report
  new_issue.py --monthly [--month YYYY-MM]              monthly issue
Working files go to reports/.work/<slug>/ (hidden). The only deliverable is the PDF that
render.py writes to reports/<PDF name>.pdf.
options: --root DIR (project root, default cwd) · --config report.config.json · --force
"""
import argparse
import datetime as dt
import json
import pathlib
import shutil
import sys

from _common import load_config, month_window, slugify

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
ASSETS = SKILL_DIR / "assets"

BRIEF = """# {title}

_Created {date}. Fill each section during GATHER and BRIEF; keep it updated._

## What I found
| # | Source | Origin | Date | Key facts used |
|---|--------|--------|------|----------------|

## Drive inventory

## Channels that failed

## Design system (from references)

## Proposed storyline
1.

## Image plan
| Slot | Page | Ratio | Chosen image | Source / credit |
|------|------|-------|--------------|-----------------|
"""


def brand_block(cfg: dict) -> tuple[str, str | None]:
    b = cfg.get("brand") or {}
    vars_ = b.get("vars") or {}
    css = ""
    if vars_:
        body = "\n".join(f"  {k}: {v};" for k, v in vars_.items())
        css = f'<style id="brand">\n:root {{\n{body}\n}}\n</style>'
    fonts = b.get("fonts_url")
    return css, (f'<link href="{fonts}" rel="stylesheet">' if fonts else None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("title", nargs="?")
    ap.add_argument("--monthly", action="store_true")
    ap.add_argument("--month", help="YYYY-MM (monthly; default previous month)")
    ap.add_argument("--masthead")
    ap.add_argument("--root", default=".")
    ap.add_argument("--config")
    ap.add_argument("--force", action="store_true", help="overwrite report.html if it exists")
    a = ap.parse_args()

    cfg = load_config(a.config)
    today = dt.date.today()
    org = cfg.get("org", "")
    masthead = a.masthead or cfg.get("masthead") or a.title or org or "Report"
    theme_dir, theme = None, {}
    if cfg.get("theme"):
        theme_dir = ASSETS / "themes" / cfg["theme"]
        if not (theme_dir / "theme.json").exists():
            sys.exit(f"theme not found: {theme_dir}")
        theme = json.loads((theme_dir / "theme.json").read_text())
    if a.monthly:
        win = month_window(a.month)
        slug = f"{slugify(org or masthead, 30)}-{win['key']}"
        title = a.title or f"{masthead} — {win['month_name']} {win['year']}"
        template = ASSETS / "monthly-template.html"
        if theme.get("templates", {}).get("monthly"):
            template = theme_dir / theme["templates"]["monthly"]
        month_name, year = win["month_name"], str(win["year"])
    else:
        if not a.title:
            sys.exit("title required (or use --monthly)")
        slug, title, template = slugify(a.title, 60), a.title, ASSETS / "magazine-template.html"
        month_name, year = today.strftime("%B"), str(today.year)

    issue = pathlib.Path(a.root).resolve() / "reports" / ".work" / slug
    for sub in ("sources/raw", "images/candidates", "previews"):
        (issue / sub).mkdir(parents=True, exist_ok=True)
    for f in ("magazine.css", "magazine.js"):
        shutil.copy(ASSETS / f, issue / f)
    shutil.copy(ASSETS / "images-README.txt", issue / "images" / "README.txt")
    if theme_dir:
        for f in theme.get("copy", []):
            shutil.copy(theme_dir / f, issue / pathlib.Path(f).name)
        for slot, f in theme.get("slot_defaults", {}).items():  # recurring brand images
            src = theme_dir / f
            if not any((issue / "images" / f"{slot}{e}").exists() for e in (".jpg", ".jpeg", ".png", ".webp")):
                shutil.copy(src, issue / "images" / f"{slot}{src.suffix}")

    if (issue / "report.html").exists() and not a.force:
        print(f"report.html exists, kept (use --force to reset): {issue}", file=sys.stderr)
    else:
        html = template.read_text(encoding="utf-8")
        css, fonts = ("", None) if theme_dir else brand_block(cfg)  # themes carry their own fonts/colours
        if fonts:
            start, end = html.index("<!--FONTS-->"), html.index("<!--/FONTS-->") + len("<!--/FONTS-->")
            html = html[:start] + fonts + html[end:]
        site = (cfg.get("website") or {}).get("url", "")
        handle = ((cfg.get("twitter") or {}).get("handles") or [""])[0]
        repl = {"{{TITLE}}": title, "{{MASTHEAD}}": masthead, "{{ORG}}": org or masthead,
                "{{MONTH YEAR}}": f"{month_name} {year}", "{{MONTH}}": month_name, "{{YEAR}}": year,
                "{{WEBSITE}}": (cfg.get("website") or {}).get("cta_url") or site.split("//")[-1],
                "{{HANDLE}}": handle, "<!--BRAND-->": css}
        for k, v in repl.items():
            html = html.replace(k, v)
        (issue / "report.html").write_text(html, encoding="utf-8")
    if not (issue / "brief.md").exists():
        (issue / "brief.md").write_text(BRIEF.format(title=title, date=today.isoformat()), encoding="utf-8")
    edition = cfg.get("edition_name") or "Report"
    pdf_name = (f"{org or masthead} Monthly Impact Report - {month_name} {year}" if a.monthly else title)
    pdf_name = "".join(c for c in pdf_name if c not in '/\\:*?"<>|').strip() + ".pdf"
    (issue / "issue.json").write_text(json.dumps({"title": title, "pdf_name": pdf_name}, indent=2, ensure_ascii=False))
    if cfg:
        (issue / "sources" / "config.used.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
    print(issue)
    print(f"→ final PDF will be reports/{pdf_name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
