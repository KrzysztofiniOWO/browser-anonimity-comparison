import os
import sys
import time
from collections import OrderedDict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
try:
    from tbselenium.tbdriver import TorBrowserDriver
except ImportError:
    TorBrowserDriver = None

from . import helpers

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
    opts = Options()
    opts.binary_location = helpers.FIREFOX_BINARY
    if headless:
        opts.add_argument("--headless")

    driver = webdriver.Firefox(options=opts)
    try:
        driver.get(URL)
        time.sleep(wait)
        html = driver.page_source
    finally:
        driver.quit()
    return html

def getHtmlTorBrowser(tbb_dir, wait=10):
    if TorBrowserDriver is None:
        raise RuntimeError("tbselenium is required for Tor Browser")
    from pyvirtualdisplay import Display
    display = None
    if helpers.HEADLESS_TBB:
        display = Display()
        display.start()

    driver = TorBrowserDriver(tbb_dir, headless=False)
    try:
        driver.get(URL)
        time.sleep(wait)
        html = driver.page_source
    finally:
        driver.quit()
        if display:
            display.stop()
    return html

def runSelectedBrowser(browser_name, getter_fn, wait=10, tbb_dir=None):
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
        print(f"[SAVE] Saved DeviceInfo data for {browser_name}")

    except Exception as e:
        meta["error"] = str(e)
        helpers.saveAsJson(browser_name, ts_safe, result, "deviceinfo")

    return result

def main():
    print("[MODULE] Running deviceinfo.me tests")

    print("[RUN] Firefox test")
    runSelectedBrowser("Firefox", getHtmlFirefox, wait=10)

    tbb_dir = helpers.determineTorBrowserDir()
    if not tbb_dir:
        print("[WARN] Tor Browser folder not found", file=sys.stderr)
    else:
        print("[RUN] Tor Browser test")
        runSelectedBrowser("TorBrowser", getHtmlTorBrowser, wait=10, tbb_dir=tbb_dir)

    print("[FIN] Finished deviceinfo.me tests")

if __name__ == "__main__":
    main()
