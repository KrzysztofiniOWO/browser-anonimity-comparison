from . import helpers
from .helpers import logger as log

import sys
import time
from collections import OrderedDict
from bs4 import BeautifulSoup
from pyvirtualdisplay import Display

from tbselenium.tbdriver import TorBrowserDriver
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions

URL = "https://www.deviceinfo.me/"

FIELDS_ORDER = [
    "Device Type / Model",
    "Operating System",
    "True Operating System Core",
    "Browser",
    "True Browser Core",
    "IP Address (WAN)",
    "Tor IP Address",
    "VPN IP Address",
    "Proxy IP Address",
    "Hostname",
    "Location",
    "Country",
    "Region",
    "City",
    "Latitude & Longitude",
    "Geolocation",
    "ISP",
    "Nameservers",
    "Connection Status",
    "Local Area Network (LAN) (Live)",
    "Internet Access",
    "Connection Type",
    "Wide Area Network (WAN)",
    "Date & Time",
    "System (Live)",
    "System Time Zone",
    "Local (Live)",
    "Local Time Zone",
    "Fingerprinting Resistance",
    "Canvas",
    "Canvas Fingerprinting",
    "AudioContext",
    "AudioContext Fingerprinting",
    "User Agent",
    "HTTP Request Headers",
    "Accept",
    "Accept-Encoding",
    "Accept-Language",
    "Connection",
    "Host",
    "Priority",
    "Sec-Fetch-Dest",
    "Sec-Fetch-Mode",
    "Sec-Fetch-Site",
    "Sec-Fetch-User",
    "Upgrade-Insecure-Requests",
    "User-Agent",
    "Local IP Address (LAN)",
    "Languages"
]


def parseDeviceInfoHtml(html):
    log.info("Parsing deviceinfo.me HTML content")
    soup = BeautifulSoup(html, "html.parser")
    data = OrderedDict()

    labels = soup.find_all("div", class_="gmplz")
    for label_div in labels:
        label_text = label_div.get_text(strip=True).rstrip(":")
        value_div = label_div.find_next_sibling("div", class_="czbdh")
        value_text = value_div.get_text(separator=" ", strip=True) if value_div else None
        data[label_text] = value_text

    ordered_data = OrderedDict()
    for field in FIELDS_ORDER:
        ordered_data[field] = data.get(field)

    return ordered_data


def getHtmlFirefox(headless=True, wait=10):
    log.info("Launching Firefox for deviceinfo.me")
    opts = FirefoxOptions()
    opts.binary_location = helpers.FIREFOX_BINARY
    if headless:
        opts.add_argument("--headless")

    driver = webdriver.Firefox(options=opts)
    try:
        log.info("Opening deviceinfo.me in Firefox")
        driver.get(URL)
        time.sleep(wait)
        html = driver.page_source
        log.info("Page loaded successfully (Firefox)")
    finally:
        driver.quit()
        log.info("Closed Firefox instance")

    return html


def getHtmlChrome(headless=True, wait=10):
    log.info("Launching Chrome for deviceinfo.me")

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
        log.info("Opening deviceinfo.me in Chrome")
        driver.get(URL)
        time.sleep(wait)
        html = driver.page_source
        log.info("Page loaded successfully (Chrome)")
    finally:
        driver.quit()
        log.info("Closed Chrome instance")

    return html


def getHtmlTorBrowser(tbb_dir, wait=10):
    log.info("Launching Tor Browser for deviceinfo.me")
    if TorBrowserDriver is None:
        raise RuntimeError("tbselenium is required for Tor Browser")

    display = None
    if helpers.HEADLESS_TBB:
        display = Display()
        display.start()
        log.info("Started virtual display for Tor Browser")

    driver = TorBrowserDriver(tbb_dir, headless=False)
    try:
        log.info("Opening deviceinfo.me in Tor Browser")
        driver.get(URL)
        time.sleep(wait)
        html = driver.page_source
        log.info("Page loaded successfully (Tor Browser)")
    finally:
        driver.quit()
        if display:
            display.stop()
            log.info("Stopped virtual display")

    return html


def runSelectedBrowser(browser_name, getter_fn, wait=10, tbb_dir=None):
    log.info(f"Running deviceinfo.me test for {browser_name}")
    ts_iso = helpers.getDatetimeNow()
    ts_safe = helpers.replaceDatetimeSeparators(ts_iso)
    meta = {"browser": browser_name, "timestamp": ts_iso, "script_version": "1.0"}
    result = {"meta": meta, "data": None}

    try:
        if browser_name.lower().startswith("tor"):
            if not tbb_dir:
                raise RuntimeError("No tbb_dir for Tor Browser")
            html = getter_fn(tbb_dir, wait=wait)
        else:
            html = getter_fn(headless=helpers.HEADLESS_FIREFOX, wait=wait)

        parsed = parseDeviceInfoHtml(html)
        result["data"] = parsed
        helpers.saveAsJson(browser_name, ts_safe, result, "deviceinfo")
        log.save(f"Saved DeviceInfo data for {browser_name}")

    except Exception as e:
        meta["error"] = str(e)
        log.error(f"Error while running deviceinfo.me test for {browser_name}: {e}")
        helpers.saveAsJson(browser_name, ts_safe, result, "deviceinfo")

    return result


def main():
    log.module("Starting deviceinfo.me module")

    log.info("Running Firefox test")
    runSelectedBrowser("Firefox", getHtmlFirefox, wait=10)

    log.info("Running Chrome test")
    runSelectedBrowser("Chrome", getHtmlChrome, wait=10)

    tbb_dir = helpers.determineTorBrowserDir()
    if not tbb_dir:
        log.warning("Tor Browser folder not found", file=sys.stderr)
    else:
        log.info("Running Tor Browser test")
        runSelectedBrowser("TorBrowser", getHtmlTorBrowser, wait=10, tbb_dir=tbb_dir)

    log.finish("Finished deviceinfo.me module")


if __name__ == "__main__":
    main()
