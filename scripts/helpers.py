import datetime
from pathlib import Path
import json
import os

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
HEADLESS_FIREFOX = os.environ.get("HEADLESS_FIREFOX", "1") != "0"
HEADLESS_TBB = os.environ.get("HEADLESS_TBB", "1") != "0"

TOR_BROWSER_DIR = os.environ.get("TOR_BROWSER_DIR", None)
TOR_BROWSER_BINARY = os.environ.get("TOR_BROWSER_BINARY", "/home/kali/Magisterka/tor-browser/Browser/firefox")
FIREFOX_BINARY = os.environ.get("FIREFOX_BINARY", "/usr/bin/firefox")

def getDatetimeNow():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds")

def replaceDatetimeSeparators(ts_iso):
    return ts_iso.replace(":", "-")

def saveAsJson(browser_name, timestamp_iso, data, category):
    folder = (DATA_DIR / category / browser_name.lower()).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    fname = folder / f"{timestamp_iso}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[SAVE] JSON saved to: {fname}")
    return str(fname)

def determineTorBrowserDir():
    if TOR_BROWSER_DIR and os.path.isdir(TOR_BROWSER_DIR):
        return TOR_BROWSER_DIR
    if TOR_BROWSER_BINARY and os.path.isfile(TOR_BROWSER_BINARY):
        cand = os.path.dirname(os.path.dirname(TOR_BROWSER_BINARY))
        if os.path.isdir(cand):
            return cand
    return None