#!/usr/bin/env python3
"""Turn a Google Sheet exported via the Drive connector into one CSV per tab.

Use the Drive connector's download_file_content with
  exportMimeType = application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
(read_file_content only returns a sample row per tab). Claude Code saves the large result to a
tool-results/*.txt file; pass that path here. Standard library only (no openpyxl needed).

usage: sheet_extract.py <saved-result.txt | file.xlsx> <out-dir> [--sheet NAME ...]
       → <out-dir>/<sheet-name>.csv   (cached formula values, as shown in the sheet)
"""
import argparse
import base64
import csv
import io
import json
import pathlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "rel": "http://schemas.openxmlformats.org/package/2006/relationships"}


def col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def load_xlsx(src: pathlib.Path) -> bytes:
    if src.suffix.lower() == ".xlsx":
        return src.read_bytes()
    d = json.loads(src.read_text())
    if isinstance(d, list):
        d = json.loads(d[0]["text"])
    return base64.b64decode(d["content"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--sheet", action="append", help="only these tab names")
    a = ap.parse_args()
    z = zipfile.ZipFile(io.BytesIO(load_xlsx(pathlib.Path(a.src).expanduser())))

    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
    rels = {r.get("Id"): r.get("Target") for r in
            ET.fromstring(z.read("xl/_rels/workbook.xml.rels")).findall("rel:Relationship", NS)}
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for sh in wb.find("m:sheets", NS):
        name = sh.get("name")
        if a.sheet and name.strip() not in [s.strip() for s in a.sheet]:
            continue
        target = rels[sh.get(f"{{{NS['r']}}}id")].lstrip("/")
        path = target if target.startswith("xl/") else f"xl/{target}"
        rows = []
        for row in ET.fromstring(z.read(path)).iter(f"{{{NS['m']}}}row"):
            cells = {}
            for c in row.findall("m:c", NS):
                v = c.find("m:v", NS)
                t = c.get("t")
                if t == "s" and v is not None:
                    val = shared[int(v.text)]
                elif t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter(f"{{{NS['m']}}}t"))
                else:
                    val = v.text if v is not None else ""
                cells[col_index(c.get("r"))] = val
            if cells:
                width = max(cells) + 1
                rows.append([cells.get(i, "") for i in range(width)])
        fname = re.sub(r"[^\w.-]+", "_", name.strip()) + ".csv"
        with open(out / fname, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)
        print(f"{fname:<34} {len(rows)} rows")


if __name__ == "__main__":
    sys.exit(main())
