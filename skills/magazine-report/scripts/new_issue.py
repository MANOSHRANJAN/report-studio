#!/usr/bin/env python3
"""Create reports/<slug>/ with the magazine template, a brief skeleton and folders.

usage: new_issue.py "Report title" [--masthead NAME] [--root DIR]
"""
import argparse
import datetime as dt
import pathlib
import re
import shutil
import sys

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "assets" / "magazine-template.html"

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
| Slot | Page | Ratio | What goes there |
|------|------|-------|-----------------|
"""


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "report"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("--masthead", help="name on the cover (default: title)")
    ap.add_argument("--root", default=".", help="project root holding reports/")
    a = ap.parse_args()

    issue = pathlib.Path(a.root).resolve() / "reports" / slugify(a.title)
    if (issue / "report.html").exists():
        print(f"exists, not overwriting: {issue}", file=sys.stderr)
        print(issue)
        return 0
    for sub in ("sources/raw", "images", "previews"):
        (issue / sub).mkdir(parents=True, exist_ok=True)

    today = dt.date.today()
    html = TEMPLATE.read_text(encoding="utf-8")
    html = (html.replace("{{TITLE}}", a.title)
                .replace("{{MASTHEAD}}", a.masthead or a.title)
                .replace("{{MONTH YEAR}}", today.strftime("%B %Y")))
    (issue / "report.html").write_text(html, encoding="utf-8")
    (issue / "brief.md").write_text(BRIEF.format(title=a.title, date=today.isoformat()), encoding="utf-8")
    shutil.copy(SKILL_DIR / "assets" / "images-README.txt", issue / "images" / "README.txt")
    print(issue)
    return 0


if __name__ == "__main__":
    sys.exit(main())
