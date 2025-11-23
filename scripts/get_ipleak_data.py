from . import helpers
from .helpers import logger as log

import re
import time
from pyvirtualdisplay import Display

from tbselenium.tbdriver import TorBrowserDriver
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions

URL = "https://ipleak.net/"


def getHtmlFirefox(headless=True, wait=45):
    log.info("Launching Firefox for IPLeak test")
    opts = FirefoxOptions()
    opts.binary_location = helpers.FIREFOX_BINARY
    if headless:
        opts.add_argument("--headless")

    driver = webdriver.Firefox(options=opts)
    driver.get(URL)
    log.info(f"Waiting {wait}s for full JS load...")
    time.sleep(wait)
    log.info("Firefox page loaded successfully")
    return driver


def getHtmlChrome(headless=True, wait=45):
    log.info("Launching Chrome for IPLeak test")

    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    if hasattr(helpers, "CHROME_BINARY") and helpers.CHROME_BINARY:
        opts.binary_location = helpers.CHROME_BINARY

    driver = webdriver.Chrome(options=opts)
    driver.get(URL)
    log.info(f"Waiting {wait}s for full JS load...")
    time.sleep(wait)
    log.info("Chrome page loaded successfully")
    return driver


def getHtmlTorBrowser(tbb_dir, wait=45):
    log.info("Launching Tor Browser for IPLeak test")
    if TorBrowserDriver is None:
        raise RuntimeError("tbselenium is required for Tor Browser")

    display = None
    if helpers.HEADLESS_TBB:
        display = Display()
        display.start()

    driver = TorBrowserDriver(tbb_dir, headless=False)
    driver.get(URL)
    log.info(f"Waiting {wait}s for full JS load...")
    time.sleep(wait)
    log.info("Tor Browser page loaded successfully")
    return driver, display


def parseIpLeakHtml(driver):
    log.info("Parsing IPLeak HTML content")
    html = driver.page_source
    data = {}

    ip_match = re.search(r"Your IP address.*?(\d{1,3}(?:\.\d{1,3}){3})", html, re.S)
    if ip_match:
        data["ip_address"] = ip_match.group(1)

    ipv6_match = re.search(r"IPv6 Address.*?([a-f0-9:]+)", html, re.I | re.S)
    if ipv6_match:
        data["ipv6_address"] = ipv6_match.group(1).strip()

    dns_entries = re.findall(r"DNS Address.*?(\d{1,3}(?:\.\d{1,3}){3})", html, re.S)
    if dns_entries:
        data["dns_servers"] = list(set(dns_entries))

    webrtc_matches = re.findall(r"(\d{1,3}(?:\.\d{1,3}){3}).*?WebRTC", html, re.S)
    if webrtc_matches:
        data["webrtc_ips"] = list(set(webrtc_matches))

    sections = re.findall(
        r'<div class="title">\s*([^<]+?)\s*</div>.*?<table[^>]*class="properties details"[^>]*>(.*?)</table>',
        html, re.S | re.I
    )

    for title, table_html in sections:
        title_key = title.strip().lower().replace(" ", "_")
        rows = re.findall(r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>", table_html, re.S)
        section_data = {}
        for label, value in rows:
            clean_label = re.sub(r"<.*?>", "", label).strip().rstrip(":")
            clean_value = re.sub(r"<.*?>", "", value).strip()
            if clean_label and clean_value:
                section_data[clean_label] = clean_value
        if section_data:
            data[title_key] = section_data

    headers_block = re.search(r"HTTP Request Headers.*?<table[^>]*>(.*?)</table>", html, re.S | re.I)
    if headers_block:
        headers = re.findall(r"<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>", headers_block.group(1), re.S)
        http_headers = {}
        for key, val in headers:
            k = re.sub(r"<.*?>", "", key).strip().rstrip(":")
            v = re.sub(r"<.*?>", "", val).strip()
            http_headers[k] = v
        if http_headers:
            data["http_request_headers"] = http_headers

    log.info(f"Parsed {len(data)} sections from IPLeak HTML")
    return data


def runSelectedBrowser(browser_name, getter_fn, wait=45, tbb_dir=None):
    log.info(f"Running IPLeak test for {browser_name}")
    ts_iso = helpers.getDatetimeNow()
    ts_safe = helpers.replaceDatetimeSeparators(ts_iso)
    meta = {"browser": browser_name, "timestamp": ts_iso, "script_version": "1.1"}
    result = {"meta": meta, "data": None}

    display = None
    try:
        if browser_name.lower().startswith("tor"):
            if not tbb_dir:
                raise RuntimeError("No tbb_dir for Tor Browser")
            driver, display = getter_fn(tbb_dir, wait=wait)
        else:
            driver = getter_fn(headless=helpers.HEADLESS, wait=wait)

        parsed = parseIpLeakHtml(driver)
        result["data"] = parsed
        helpers.saveAsJson(browser_name, ts_safe, result, "ipleak")
        log.save(f"Saved IPLeak data for {browser_name}")

    except Exception as e:
        meta["error"] = str(e)
        log.error(f"Error during {browser_name} IPLeak test: {e}")
        helpers.saveAsJson(browser_name, ts_safe, result, "ipleak")

    finally:
        try:
            driver.quit()
            log.info(f"Closed {browser_name} session")
        except:
            pass
        if display:
            display.stop()
            log.info("Stopped virtual display for Tor Browser")

    return result


def main():
    log.module("Starting IPLeak module")

    log.info("Firefox test started")
    runSelectedBrowser("Firefox", getHtmlFirefox, wait=5)

    log.info("Chrome test started")
    runSelectedBrowser("Chrome", getHtmlChrome, wait=5)

    tbb_dir = helpers.determineTorBrowserDir()
    if not tbb_dir:
        log.warning("Tor Browser folder not found")
    else:
        log.info("Tor Browser test started")
        runSelectedBrowser("TorBrowser", getHtmlTorBrowser, wait=5, tbb_dir=tbb_dir)

    log.finish("IPLeak module completed")


if __name__ == "__main__":
    main()
