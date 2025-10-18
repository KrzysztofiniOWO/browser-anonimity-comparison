import os
import sys
import time
import re
from bs4 import BeautifulSoup
from collections import OrderedDict

import helpers

URL = "https://browserleaks.com/ip"

IP_MAPPING = {
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

def parseBrowserleaksIPHtml(html):
    soup = BeautifulSoup(html, "html.parser")
    out = {}

    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) >= 2:
            label = tds[0].get_text(separator=" ", strip=True)
            value = tds[1].get_text(separator=" ", strip=True)
            key = helpers.normalizeLabel(label, IP_MAPPING)
            if value.lower() in ("n/a", "none", ""):
                value = None
            out[key] = value

    if "country" in out and out["country"]:
        m = re.match(r"^(.*)\s+\((\w{2})\)\s*$", out["country"])
        if m:
            out["country_name"] = m.group(1).strip()
            out["country_code"] = m.group(2).strip()

    if "coordinates" in out and out["coordinates"]:
        coords = out["coordinates"].replace(" ", "")
        try:
            lat, lon = coords.split(",", 1)
            out["latitude"] = float(lat)
            out["longitude"] = float(lon)
        except Exception:
            out["latitude"] = None
            out["longitude"] = None

    return out

def extractIP(text):
    m = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})', text)
    return m.group(1) if m else None

def getHtmlFirefox(headless=True, wait=3):
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options

    opts = Options()
    opts.binary_location = helpers.FIREFOX_BINARY
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
    if helpers.HEADLESS_TBB:
        try:
            from pyvirtualdisplay import Display
            display = Display()
            display.start()
            print("[DEBUG] pyvirtualdisplay started for Tor Browser")
        except Exception as e:
            print(f"[WARN] Could not start pyvirtualdisplay: {e}. Trying without headless.")

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

def filterOnlyImportantIP(data: dict) -> OrderedDict:
    ordered_keys = [
        "ip", "hostname", "country", "state_region", "city",
        "isp", "organization", "network", "usage_type",
        "timezone", "local_time", "coordinates", "ipv6",
        "request", "user-agent", "accept", "accept-language", "accept-encoding",
        "referer", "upgrade-insecure-requests", "sec-fetch-dest", "sec-fetch-mode",
        "sec-fetch-site", "sec-fetch-user", "priority", "te", "host", "relays",
    ]
    return OrderedDict((k, data[k]) for k in ordered_keys if k in data)

def runSelectedBrowser(browser_name, getter_fn, wait=4, tbb_dir=None):
    ts_iso = helpers.getDatetimeNow()
    ts_safe = helpers.replaceDatetimeSeparators(ts_iso)
    meta = {"browser": browser_name, "timestamp": ts_iso, "script_version": "1.3"}
    result = {"meta": meta, "data": None}

    try:
        if browser_name.lower().startswith("tor"):
            if not tbb_dir:
                raise RuntimeError("No tbb_dir for Tor Browser")
            html, ua = getter_fn(tbb_dir, wait=wait)
        else:
            html, ua = getter_fn(headless=helpers.HEADLESS_FIREFOX, wait=wait)

        parsed = parseBrowserleaksIPHtml(html)
        if not parsed.get("ip"):
            parsed["ip"] = extractIP(html)

        meta["user_agent"] = ua
        result["data"] = filterOnlyImportantIP(parsed)
        helpers.saveAsJson(browser_name, ts_safe, result, "ip")
        print(f"[OK] Saved IP data for {browser_name}")
        return result

    except Exception as e:
        meta["error"] = str(e)
        helpers.saveAsJson(browser_name, ts_safe, result, "ip")
        print(f"[ERROR] during test {browser_name}: {e}", file=sys.stderr)
        return result

def main():
    print("[RUN] Running BrowserLeaks IP tests")

    print("[RUN] Firefox test")
    runSelectedBrowser("Firefox", getHtmlFirefox, wait=3)

    tbb_dir = helpers.determineTorBrowserDir()
    if not tbb_dir:
        print("[WARN] Tor Browser folder not found", file=sys.stderr)
        return

    print("[RUN] Tor Browser test")
    runSelectedBrowser("TorBrowser", getHtmlTorBrowser, wait=5, tbb_dir=tbb_dir)

    print("[FIN] Finished BrowserLeaks IP tests")

if __name__ == "__main__":
    main()
