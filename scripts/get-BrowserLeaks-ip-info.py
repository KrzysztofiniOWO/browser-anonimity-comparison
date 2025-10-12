import os
import sys
import time
import json
import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from collections import OrderedDict

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

URL = "https://browserleaks.com/ip"

TOR_BROWSER_DIR = os.environ.get("TOR_BROWSER_DIR", None)
TOR_BROWSER_BINARY = os.environ.get("TOR_BROWSER_BINARY", "/home/kali/Magisterka/tor-browser/Browser/firefox")
FIREFOX_BINARY = os.environ.get("FIREFOX_BINARY", "/usr/bin/firefox")
HEADLESS_FIREFOX = os.environ.get("HEADLESS_FIREFOX", "1") != "0"
HEADLESS_TBB = os.environ.get("HEADLESS_TBB", "1") != "0"

def getDatetimeNow():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds")

def replaceDatetimeSeparators(ts_iso):
    return ts_iso.replace(":", "-")

def saveAsJson(browser_name, timestamp_iso, data):
    folder = (DATA_DIR / browser_name.lower()).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    fname = folder / f"{timestamp_iso}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[SAVE] JSON saved to: {fname}")
    return str(fname)

def normalizeData(label):
    mapping = {
        "IP Address": "ip",
        "Hostname": "hostname",
        "Country": "country",
        "State/Region": "state_region",
        "City": "city",
        "ISP": "isp",
        "Organization": "organization",
        "Network": "network",
        "Usage Type": "usage_type",
        "Timezone": "timezone",
        "Local Time": "local_time",
        "Coordinates": "coordinates",
        "IPv6 Address": "ipv6",
        "Local IP Address": "webrtc_local_ip",
        "Public IP Address": "webrtc_public_ip",
        "Request": "request",
        "User-Agent": "user-agent",
        "Accept": "accept",
        "Accept-Language": "accept-language",
        "Accept-Encoding": "accept-encoding",
        "Referer": "referer",
        "Upgrade-Insecure-Requests": "upgrade-insecure-requests",
        "Sec-Fetch-Dest": "sec-fetch-dest",
        "Sec-Fetch-Mode": "sec-fetch-mode",
        "Sec-Fetch-Site": "sec-fetch-site",
        "Sec-Fetch-User": "sec-fetch-user",
        "Priority": "priority",
        "TE": "te",
        "Host": "host",
        "Relays": "relays",
    }
    return mapping.get(label.strip(), label.strip().lower().replace(" ", "_"))

def parseBrowserleaksHtml(html):
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) >= 2:
            label = tds[0].get_text(separator=" ", strip=True)
            value = tds[1].get_text(separator=" ", strip=True)
            key = normalizeData(label)
            if value.lower() in ("n/a", "none", ""):
                value = None
            out[key] = value

    if "country" in out and out["country"]:
        import re
        m = re.match(r"^(.*)\s+\((\w{2})\)\s*$", out["country"])
        if m:
            out["country_name"] = m.group(1).strip()
            out["country_code"] = m.group(2).strip()
        else:
            out["country_name"] = out["country"]

    if "coordinates" in out and out["coordinates"]:
        coords = out["coordinates"].replace(" ", "")
        try:
            lat_str, lon_str = coords.split(",", 1)
            out["latitude"] = float(lat_str)
            out["longitude"] = float(lon_str)
        except Exception:
            out["latitude"] = None
            out["longitude"] = None

    return out

def extractIP(text):
    import re
    m = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})', text)
    return m.group(1) if m else None


def getHtmlFirefox(headless=True, wait=3):
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options

    opts = Options()
    opts.binary_location = FIREFOX_BINARY
    if headless:
        opts.add_argument("--headless")
    driver = webdriver.Firefox(options=opts)
    try:
        driver.get(URL)
        time.sleep(wait)
        ua = driver.execute_script("return navigator.userAgent;")
        html = driver.page_source
    finally:
        driver.quit()
    return html, ua

def getHtmlTorBrowser(tbb_dir, wait=5):
    from tbselenium.tbdriver import TorBrowserDriver

    display = None
    if HEADLESS_TBB:
        try:
            from pyvirtualdisplay import Display
            display = Display()
            display.start()
            print("[DEBUG] pyvirtualdisplay started for TBB")
        except Exception as e:
            print(f"[WARN] Nie udało się uruchomić pyvirtualdisplay: {e}. Spróbuję bez headless.")

    try:
        with TorBrowserDriver(tbb_dir) as driver:
            driver.get(URL)
            ua = driver.execute_script("return navigator.userAgent;")
            time.sleep(wait)
            html = driver.page_source
    finally:
        if display:
            display.stop()

    return html, ua

def determineTorBrowserDir():
    if TOR_BROWSER_DIR and os.path.isdir(TOR_BROWSER_DIR):
        return TOR_BROWSER_DIR
    if TOR_BROWSER_BINARY and os.path.isfile(TOR_BROWSER_BINARY):
        cand = os.path.dirname(os.path.dirname(TOR_BROWSER_BINARY))
        if os.path.isdir(cand):
            return cand
    return None

def filterOnlyImportantData(data: dict) -> OrderedDict:
    ordered_keys = [
        "ip", "hostname",
        "country", "state_region", "city",
        "isp", "organization", "network", "usage_type",
        "timezone", "local_time", "coordinates", "ipv6",
        "request", "user-agent", "accept", "accept-language", "accept-encoding",
        "referer", "upgrade-insecure-requests", "sec-fetch-dest", "sec-fetch-mode",
        "sec-fetch-site", "sec-fetch-user", "priority", "te", "host",
        "relays",
    ]
    return OrderedDict((k, data[k]) for k in ordered_keys if k in data)

def runSelectedBrowser(browser_name, getter_fn, wait=4, tbb_dir=None):
    ts_iso = getDatetimeNow()
    ts_safe = replaceDatetimeSeparators(ts_iso)
    meta = {"browser": browser_name, "timestamp": ts_iso, "script_version": "1.2"}

    result = {"meta": meta, "data": None}
    try:
        if browser_name.lower().startswith("tor"):
            if not tbb_dir:
                raise RuntimeError("Brak tbb_dir dla Tor Browser")
            html, ua = getter_fn(tbb_dir, wait=wait)
        else:
            html, ua = getter_fn(headless=HEADLESS_FIREFOX, wait=wait)

        parsed = parseBrowserleaksHtml(html)
        if not parsed.get("ip"):
            parsed["ip"] = extractIP(html)

        meta["user_agent"] = ua

        result["data"] = filterOnlyImportantData(parsed)

        saveAsJson(browser_name, ts_safe, result)
        print(f"[OK] zapisano dane dla {browser_name}")
        return result
    except Exception as e:
        meta["error"] = str(e)
        result["data"] = None
        saveAsJson(browser_name, ts_safe, result)
        print(f"[ERROR] podczas testu {browser_name}: {e}", file=sys.stderr)
        return result

def main():
    print("[RUN] Running tests")

    # Firefox
    print("[RUN] Running Firefox tests")
    runSelectedBrowser("Firefox", getHtmlFirefox, wait=3)

    # Tor Browser
    tbb_dir = determineTorBrowserDir()
    if not tbb_dir:
        print("Tor Browser folder not found", file=sys.stderr)
        return
    print("[RUN] Running Tor Browser tests")
    runSelectedBrowser("TorBrowser", getHtmlTorBrowser, wait=5, tbb_dir=tbb_dir)

if __name__ == "__main__":
    main()
