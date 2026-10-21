#!/usr/bin/env python3
"""Turn Google Drive connector downloads into image files.

The Drive connector's download_file_content returns {content: <base64>, id, mimeType, title}.
For photos the result is too large for the conversation, so Claude Code saves it to a
tool-results/*.txt file and prints that path. Pass those paths here — the base64 never has
to enter the context.

usage: drive_save.py <issue-dir> <saved-result.txt> [...] [--max-px 2400]
Writes images/candidates/drive-<title>.<ext> and a credits entry per file.
"""
import argparse
import base64
import json
import pathlib
import shutil
import subprocess
import sys

from _common import IMG_EXT, add_credit, slugify


def shrink(path: pathlib.Path, max_px: int):
    """Downscale big photos so PDFs stay small. Uses sips (macOS) or Pillow if present."""
    if shutil.which("sips"):
        subprocess.run(["sips", "-Z", str(max_px), str(path)], capture_output=True)
        return
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return
    with Image.open(path) as im:
        if max(im.size) > max_px:
            im.thumbnail((max_px, max_px))
            im.save(path, quality=88)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("issue")
    ap.add_argument("results", nargs="+")
    ap.add_argument("--max-px", type=int, default=2400)
    a = ap.parse_args()
    issue = pathlib.Path(a.issue).resolve()
    out = issue / "images" / "candidates"
    out.mkdir(parents=True, exist_ok=True)

    for res in a.results:
        try:
            d = json.loads(pathlib.Path(res).expanduser().read_text())
            if isinstance(d, list):  # some clients wrap the payload as [{type:text,text:"{...}"}]
                d = json.loads(d[0]["text"])
            blob = base64.b64decode(d["content"])
        except Exception as e:
            print(f"! {res}: not a Drive download result ({e})", file=sys.stderr)
            continue
        mime = d.get("mimeType", "")
        ext = IMG_EXT.get(mime)
        if not ext or ext == ".gif":
            print(f"! {d.get('title')}: {mime} is not a usable image, skipped", file=sys.stderr)
            continue
        title = d.get("title") or d.get("id")
        stem = slugify(pathlib.Path(title).stem, 50)
        dest = out / f"drive-{stem}{ext}"
        n = 2
        while dest.exists():
            dest = out / f"drive-{stem}-{n}{ext}"
            n += 1
        dest.write_bytes(blob)
        shrink(dest, a.max_px)
        add_credit(issue, dest.name, {"source": "google-drive", "drive_id": d.get("id"),
                                      "title": title, "credit_line": ""})
        print(f"{dest.name}  ({len(blob) // 1024} KB original)")


if __name__ == "__main__":
    main()
