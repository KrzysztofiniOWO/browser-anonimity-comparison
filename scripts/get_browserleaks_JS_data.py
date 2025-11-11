from . import helpers
from .helpers import logger as log

import sys
import time
from bs4 import BeautifulSoup
from collections import OrderedDict
from pyvirtualdisplay import Display

from tbselenium.tbdriver import TorBrowserDriver
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions

URL = "https://browserleaks.com/javascript"


def parseBrowserleaksJavascriptHtml(html):
    log.info("Parsing BrowserLeaks JavaScript data")
    soup = BeautifulSoup(html, "html.parser")
    out = OrderedDict()

    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) >= 2:
            label = tds[0].get_text(separator=" ", strip=True)
            value = tds[1].get_text(separator=" ", strip=True)
            key = helpers.normalizeLabel(label)
            if value.lower() in ("undefined", "none", ""):
                value = None
            out[key] = value

    return out


def getHtmlFirefox(headless=True, wait=3):
    log.info("Launching Firefox for JS test")

    opts = FirefoxOptions()
    opts.binary_location = helpers.FIREFOX_BINARY
    if headless:
        opts.add_argument("--headless")

    driver = webdriver.Firefox(options=opts)
    try:
        driver.get(URL)
        log.info("Loaded BrowserLeaks JS page in Firefox")
        time.sleep(wait)
        ua = driver.execute_script("return navigator.userAgent;")
        html = driver.page_source
    finally:
        driver.quit()
        log.info("Closed Firefox browser")

    return html, ua


def getHtmlChrome(headless=True, wait=3):
    log.info("Launching Chrome for JS test")

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
        log.info("Loaded BrowserLeaks JS page in Chrome")
        time.sleep(wait)
        ua = driver.execute_script("return navigator.userAgent;")
        html = driver.page_source
    finally:
        driver.quit()
        log.info("Closed Chrome browser")

    return html, ua


def getHtmlTorBrowser(tbb_dir, wait=5):
    log.info("Launching Tor Browser for JS test")

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
            log.info("Loaded BrowserLeaks JS page in Tor Browser")
            ua = driver.execute_script("return navigator.userAgent;")
            time.sleep(wait)
            html = driver.page_source
    finally:
        if display:
            display.stop()
            log.info("Stopped virtual display for Tor")

    return html, ua


def filterOnlyImportantJS(data: OrderedDict) -> OrderedDict:
    ordered_keys = [
        "javascript_enabled", "inline_scripts", "same_origin_scripts", "third_party_scripts",
        "document_referrer", "document_character_set", "document_title", "screen_resolution",
        "available_resolution", "color_depth", "pixel_depth",
        "system_time", "tolocalestring", "datetimeformat", "locale", "timezone",
        "useragent", "appversion", "appname", "appcodename",
        "product", "productsub", "vendor", "buildid", "platform", "oscpu",
        "hardwareconcurrency", "devicememory", "language", "languages",
        "donottrack", "cookieenabled", "webdriver", "pdfviewerenabled", "globalprivacycontrol"
    ]
    return OrderedDict((k, data[k]) for k in ordered_keys if k in data)


def runSelectedBrowser(browser_name, getter_fn, wait=4, tbb_dir=None):
    log.info(f"Running BrowserLeaks JS test for {browser_name}")
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

        parsed = parseBrowserleaksJavascriptHtml(html)
        meta["user_agent"] = ua
        result["data"] = filterOnlyImportantJS(parsed)

        helpers.saveAsJson(browser_name, ts_safe, result, "browserleaks_javascript")
        log.save(f"Saved JavaScript results for {browser_name}")
        return result

    except Exception as e:
        meta["error"] = str(e)
        log.error(f"Error during {browser_name} JS test: {e}")
        helpers.saveAsJson(browser_name, ts_safe, result, "browserleaks_javascript")
        return result


def main():
    log.module("Starting BrowserLeaks JavaScript module")

    log.info("Firefox JS test started")
    runSelectedBrowser("Firefox", getHtmlFirefox, wait=3)

    log.info("Chrome JS test started")
    runSelectedBrowser("Chrome", getHtmlChrome, wait=3)

    tbb_dir = helpers.determineTorBrowserDir()
    if not tbb_dir:
        log.warning("Tor Browser folder not found", file=sys.stderr)
        log.finish("Module finished with missing Tor path")
        return

    log.info("Tor Browser JS test started")
    runSelectedBrowser("TorBrowser", getHtmlTorBrowser, wait=5, tbb_dir=tbb_dir)

    log.finish("BrowserLeaks JavaScript module completed")


if __name__ == "__main__":
    main()
