"""Shared helpers: project config, month windows, HTTP, HTML-to-text, image download."""
import calendar
import datetime as dt
import html
import html.parser
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/144.0 Safari/537.36 ReportStudio/1.0")
# Wikimedia (and Openverse's Wikimedia results) rate-limit browser-like agents; their policy
# asks for an identifying UA with a contact URL.
BOT_UA = "ReportStudio/1.0 (https://github.com/MANOSHRANJAN/report-studio; report generation)"
IMG_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
           "image/avif": ".avif", "image/gif": ".gif"}


def load_config(path=None) -> dict:
    """report.config.json from --config, the cwd, or any parent directory."""
    if path:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    here = pathlib.Path.cwd()
    for d in [here, *here.parents]:
        p = d / "report.config.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return {}


def month_window(month: str | None):
    """'YYYY-MM' (default: previous calendar month) -> dict with start, end (exclusive), labels."""
    if month:
        y, m = (int(x) for x in month.split("-"))
    else:
        first = dt.date.today().replace(day=1)
        prev = first - dt.timedelta(days=1)
        y, m = prev.year, prev.month
    start = dt.date(y, m, 1)
    end = dt.date(y + (m == 12), m % 12 + 1, 1)
    return {"key": f"{y}-{m:02d}", "start": start, "end": end, "year": y,
            "month_name": calendar.month_name[m], "days": (end - start).days}


def in_window(iso: str, win) -> bool:
    try:
        d = dt.date.fromisoformat(iso[:10])
    except ValueError:
        return False
    return win["start"] <= d < win["end"]


def http_get(url: str, timeout=30, headers=None):
    ua = BOT_UA if "wikimedia.org" in url or "openverse.org" in url else UA
    req = urllib.request.Request(url, headers={"User-Agent": ua, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), dict(r.headers)


def http_json(url: str, timeout=30, headers=None):
    body, hdrs = http_get(url, timeout, {"Accept": "application/json", **(headers or {})})
    return json.loads(body.decode("utf-8", "replace")), hdrs


def slugify(text: str, n=50) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:n] or "item"


class _Text(html.parser.HTMLParser):
    BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section", "blockquote"}
    SKIP = {"script", "style", "noscript", "svg"}

    def __init__(self):
        super().__init__()
        self.out, self.skip, self.imgs = [], 0, []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        if tag in self.BLOCK:
            self.out.append("\n")
        if tag == "img":
            a = dict(attrs)
            src = a.get("data-src") or a.get("src")
            if src and not src.startswith("data:"):
                self.imgs.append(src)

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def html_to_text(markup: str):
    """-> (plain text with paragraph breaks, [img src...])"""
    p = _Text()
    p.feed(markup or "")
    text = html.unescape("".join(p.out))
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return text, p.imgs


def save_image(url: str, dest_stem: pathlib.Path, min_bytes=8_000):
    """Download url to dest_stem + proper extension. Returns path or None (tiny/failed/not image)."""
    try:
        body, hdrs = http_get(url, timeout=45)
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        print(f"  ! image failed {url[:80]}: {e}", file=sys.stderr)
        return None
    ctype = (hdrs.get("Content-Type") or hdrs.get("content-type") or "").split(";")[0].strip()
    ext = IMG_EXT.get(ctype) or pathlib.Path(url.split("?")[0]).suffix.lower()
    if ext not in IMG_EXT.values() or len(body) < min_bytes:
        return None
    if ext == ".gif":
        return None
    dest = dest_stem.with_suffix(ext)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    return dest


def credits_path(issue: pathlib.Path) -> pathlib.Path:
    return issue / "images" / "credits.json"


def add_credit(issue: pathlib.Path, filename: str, entry: dict):
    p = credits_path(issue)
    data = json.loads(p.read_text()) if p.exists() else {}
    data[filename] = entry
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def write_json(path: pathlib.Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
