from . import helpers
from .helpers import logger as log

import time
import re
from bs4 import BeautifulSoup
from collections import OrderedDict
from pyvirtualdisplay import Display

from tbselenium.tbdriver import TorBrowserDriver
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions

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
    log.info("Parsing BrowserLeaks HTML content")
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

    log.info("Launching Firefox browser session")
    opts = FirefoxOptions()
    opts.binary_location = helpers.FIREFOX_BINARY
    if headless:
        opts.add_argument("--headless")

    driver = webdriver.Firefox(options=opts)
    try:
        driver.get(URL)
        time.sleep(wait)
        html = driver.page_source
        ua = driver.execute_script("return navigator.userAgent;")
        log.info("Firefox page loaded successfully")
    finally:
        driver.quit()
        log.info("Closed Firefox session")

    return html, ua


def getHtmlChrome(headless=True, wait=3):

    log.info("Launching Chrome browser session")
    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    if hasattr(helpers, "CHROME_BINARY") and helpers.CHROME_BINARY:
        opts.binary_location = helpers.CHROME_BINARY

    driver = webdriver.Chrome(options=opts)
    try:
        driver.get(URL)
        time.sleep(wait)
        html = driver.page_source
        ua = driver.execute_script("return navigator.userAgent;")
        log.info("Chrome page loaded successfully")
    finally:
        driver.quit()
        log.info("Closed Chrome session")

    return html, ua


def getHtmlTorBrowser(tbb_dir, wait=5):
    log.info("Launching Tor Browser session")

    display = None
    if helpers.HEADLESS_TBB:
        try:
            display = Display()
            display.start()
        except Exception as e:
            log.warning(f"Could not start pyvirtualdisplay: {e}. Trying without headless.")

    try:
        with TorBrowserDriver(tbb_dir) as driver:
            driver.get(URL)
            time.sleep(wait)
            html = driver.page_source
            ua = driver.execute_script("return navigator.userAgent;")
            log.info("Tor Browser page loaded successfully")
    finally:
        if display:
            display.stop()
            log.info("Stopped virtual display for Tor Browser")

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
    log.info(f"Running BrowserLeaks IP test for {browser_name}")

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
            html, ua = getter_fn(headless=helpers.HEADLESS, wait=wait)

        parsed = parseBrowserleaksIPHtml(html)
        if not parsed.get("ip"):
            parsed["ip"] = extractIP(html)

        meta["user_agent"] = ua
        filtered = filterOnlyImportantIP(parsed)
        result["data"] = filtered

        helpers.saveAsJson(browser_name, result, "browserleaks_ip")

        log.save(f"Saved BrowserLeaks IP data for {browser_name}")
    except Exception as e:
        meta["error"] = str(e)
        helpers.saveAsJson(browser_name, result, "browserleaks_ip")
        log.error(f"Error during {browser_name} test: {e}")

    return result


def main():
    log.module("Starting BrowserLeaks IP module")

    log.info("Firefox test started")
    runSelectedBrowser("Firefox", getHtmlFirefox, wait=3)

    log.info("Chrome test started")
    runSelectedBrowser("Chrome", getHtmlChrome, wait=3)

    tbb_dir = helpers.determineTorBrowserDir()
    if not tbb_dir:
        log.warning("Tor Browser folder not found")
    else:
        log.info("Tor Browser test started")
        runSelectedBrowser("TorBrowser", getHtmlTorBrowser, wait=5, tbb_dir=tbb_dir)

    log.finish("BrowserLeaks IP module completed")


if __name__ == "__main__":
    main()
