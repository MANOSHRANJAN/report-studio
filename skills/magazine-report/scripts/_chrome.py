"""Headless Chrome helpers shared by render.py and candidates.py."""
import glob
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
import time


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
