#!/usr/bin/env python3
"""List and fill the image slots of a magazine report.

usage:
  slots.py list <issue-dir> [--json]
  slots.py fill <issue-dir> [--assign SLOT=PATH ...]

A slot is <figure class="slot" data-slot="ID" data-ratio=".." data-hint="..">.
It is filled by images/<ID>.<jpg|jpeg|png|webp|avif>.
"""
import argparse
import html
import html.parser
import json
import pathlib
import re
import shutil
import sys

EXTS = (".jpg", ".jpeg", ".png", ".webp", ".avif")


class SlotParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.slots, self._page, self._pages = [], 0, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag == "section" and "page" in classes:
            self._pages += 1
            self._page = self._pages
        if tag == "figure" and "slot" in classes and a.get("data-slot"):
            self.slots.append({"slot": a["data-slot"], "page": self._page,
                               "ratio": a.get("data-ratio", ""), "hint": a.get("data-hint", "")})


def find_image(images: pathlib.Path, slot: str):
    for ext in EXTS:
        p = images / f"{slot}{ext}"
        if p.exists():
            return p
    return None


def load(issue: pathlib.Path):
    html_path = issue / "report.html"
    if not html_path.exists():
        sys.exit(f"no report.html in {issue}")
    parser = SlotParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    for s in parser.slots:
        img = find_image(issue / "images", s["slot"])
        s["file"] = img.name if img else None
    return html_path, parser.slots


def cmd_list(issue, as_json):
    _, slots = load(issue)
    if as_json:
        print(json.dumps(slots, indent=2))
        return
    known = {s["slot"] for s in slots}
    w = max([len(s["slot"]) for s in slots] + [4])
    fw = max([len(s["file"] or "EMPTY") for s in slots] + [6])
    print(f"{'SLOT':<{w}}  PG  RATIO     {'STATUS':<{fw}}  WHAT GOES THERE")
    for s in slots:
        status = s["file"] or "EMPTY"
        print(f"{s['slot']:<{w}}  {s['page']:>2}  {s['ratio']:<8}  {status:<{fw}}  {s['hint']}")
    filled = sum(1 for s in slots if s["file"])
    print(f"\n{filled}/{len(slots)} slots filled. Drop files into {issue / 'images'}/<SLOT>.jpg")
    stray = [p.name for p in sorted((issue / "images").glob("*"))
             if p.suffix.lower() in EXTS and p.stem not in known]
    if stray:
        print("Images not matching any slot (rename or --assign):", ", ".join(stray))


def set_credit(text, slot, line):
    """Put the credit line into the slot's caption (stock / X / website photos must be credited)."""
    m = re.search(r'<figure[^>]*data-slot="' + re.escape(slot) + r'"[^>]*>.*?</figure>', text, re.S)
    if not m:
        return text
    fig, cred = m.group(0), f'<span class="credit">{html.escape(line)}</span>'
    if 'class="credit"' in fig:
        new = re.sub(r'<span class="credit">.*?</span>', cred, fig, count=1, flags=re.S)
    elif "</figcaption>" in fig:
        new = fig.replace("</figcaption>", f" {cred}</figcaption>", 1)
    else:
        new = fig.replace("</figure>", f'<figcaption class="caption">{cred}</figcaption></figure>', 1)
    return text[:m.start()] + new + text[m.end():]


def cmd_fill(issue, assigns):
    images = issue / "images"
    images.mkdir(exist_ok=True)
    credits_file = images / "credits.json"
    credits = json.loads(credits_file.read_text()) if credits_file.exists() else {}
    for pair in assigns or []:
        slot, _, src = pair.partition("=")
        src_path = pathlib.Path(src).expanduser()
        if not src_path.is_file() and (issue / src).is_file():  # path relative to the issue
            src_path = issue / src
        if not slot or not src_path.is_file() or src_path.suffix.lower() not in EXTS:
            sys.exit(f"bad --assign {pair!r} (need SLOT=/path/to/image{{{','.join(EXTS)}}})")
        for ext in EXTS:  # one file per slot
            (images / f"{slot}{ext}").unlink(missing_ok=True)
            credits.pop(f"{slot}{ext}", None)
        dest = f"{slot}{src_path.suffix.lower()}"
        shutil.copy(src_path, images / dest)
        if src_path.name in credits:  # carry attribution with the file
            credits[dest] = {**credits[src_path.name], "from_candidate": src_path.name}
        print(f"assigned {src_path.name} -> {slot}")
    if credits:
        credits_file.write_text(json.dumps(credits, indent=2, ensure_ascii=False))

    html_path, slots = load(issue)
    text = html_path.read_text(encoding="utf-8")
    changed = 0
    for s in slots:
        if not s["file"]:
            continue
        pattern = re.compile(r'(src=")images/' + re.escape(s["slot"]) + r'\.[a-zA-Z0-9]+(")')
        new, n = pattern.subn(r"\g<1>images/" + s["file"] + r"\g<2>", text)
        if n and new != text:
            text, changed = new, changed + 1
        line = (credits.get(s["file"]) or {}).get("credit_line")
        if line:
            text = set_credit(text, s["slot"], line)
    html_path.write_text(text, encoding="utf-8")
    print(f"updated {changed} image paths; credits applied where known")
    cmd_list(issue, False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "fill"])
    ap.add_argument("issue")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--assign", action="append", metavar="SLOT=PATH")
    a = ap.parse_args()
    issue = pathlib.Path(a.issue).resolve()
    if a.cmd == "list":
        cmd_list(issue, a.json)
    else:
        cmd_fill(issue, a.assign)


if __name__ == "__main__":
    main()
