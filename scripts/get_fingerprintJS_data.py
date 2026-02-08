from . import helpers
from .helpers import logger as log

import time
import json
from bs4 import BeautifulSoup
from collections import OrderedDict
from pyvirtualdisplay import Display

from tbselenium.tbdriver import TorBrowserDriver
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService

URL = "https://fingerprintjs.github.io/fingerprintjs/"

def parseFingerprintJsHtml(html):
    """Parsuje HTML FingerprintJS i zwraca słownik z wynikami"""
    log.info("Parsing FingerprintJS HTML content")
    soup = BeautifulSoup(html, "html.parser")
    out = {}

    section = soup.find("section", class_="output")
    if not section:
        return out

    vid = section.find("pre", class_="giant")
    if vid:
        out["visitor_id"] = vid.get_text(strip=True)

    time_elem = section.find_all("pre", class_="big")
    if time_elem:
        if len(time_elem) > 0:
            out["time_taken_ms"] = int(time_elem[0].get_text(strip=True).replace("ms",""))
        if len(time_elem) > 1:
            try:
                out["confidence_score"] = float(time_elem[1].get_text(strip=True))
            except:
                out["confidence_score"] = None

    ua_elem = section.find("pre", text=lambda x: x and "Mozilla" in x)
    if ua_elem:
        out["user_agent"] = ua_elem.get_text(strip=True)

    entropy_elem = section.find("pre", text=lambda x: x and x.strip().startswith("{"))
    if entropy_elem:
        try:
            out["entropy_components"] = json.loads(entropy_elem.get_text(strip=True))
        except Exception as e:
            log.warning(f"Could not parse entropy JSON: {e}")
            out["entropy_components"] = None

    return out


def getHtmlFirefox(headless=False, wait=3):
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
    finally:
        driver.quit()
    return html, ua


def getHtmlChrome(headless=False, wait=3):
    log.info("Launching Chrome browser session")
    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")

    if hasattr(helpers, "CHROME_BINARY") and helpers.CHROME_BINARY:
        opts.binary_location = helpers.CHROME_BINARY

    driver = webdriver.Chrome(options=opts)
    try:
        driver.get(URL)
        time.sleep(wait)
        html = driver.page_source
        ua = driver.execute_script("return navigator.userAgent;")
    finally:
        driver.quit()
    return html, ua


def getHtmlEdge(headless=False, wait=3):
    log.info("Launching Edge browser session")
    opts = EdgeOptions()
    opts.binary_location = helpers.EDGE_BINARY
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")

    driver = webdriver.Edge(service=EdgeService(helpers.MSEDGEDRIVER), options=opts)
    try:
        driver.get(URL)
        time.sleep(wait)
        html = driver.page_source
        ua = driver.execute_script("return navigator.userAgent;")
        log.info("Edge page loaded successfully")
    finally:
        driver.quit()
        log.info("Closed Edge session")

    return html, ua


def getHtmlBrave(headless=False, wait=3):
    log.info("Launching Brave browser session")
    opts = ChromeOptions()
    opts.add_argument(f"--brave-binary={helpers.BRAVE_BINARY}")
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=ChromeService(helpers.CHROMEDRIVER), options=opts)
    try:
        driver.get(URL)
        time.sleep(wait)
        html = driver.page_source
        ua = driver.execute_script("return navigator.userAgent;")
    finally:
        driver.quit()
    return html, ua


def getHtmlTorBrowser(tbb_dir, wait=5):
    log.info("Launching Tor Browser session")
    display = None
    if helpers.HEADLESS_TBB:
        try:
            display = Display()
            display.start()
        except Exception as e:
            log.warning(f"Could not start pyvirtualdisplay: {e}")

    try:
        with TorBrowserDriver(tbb_dir) as driver:
            driver.get(URL)
            time.sleep(wait)
            html = driver.page_source
            ua = driver.execute_script("return navigator.userAgent;")
    finally:
        if display:
            display.stop()
    return html, ua


def runSelectedBrowser(browser_name, getter_fn, wait=4, tbb_dir=None):
    log.info(f"Running FingerprintJS test for {browser_name}")

    ts_iso = helpers.getDatetimeNow()
    meta = {"browser": browser_name, "timestamp": ts_iso, "script_version": "1.0"}
    result = {"meta": meta, "data": None}

    try:
        if browser_name.lower().startswith("tor"):
            if not tbb_dir:
                raise RuntimeError("No tbb_dir for Tor Browser")
            html, ua = getter_fn(tbb_dir, wait=wait)
        else:
            html, ua = getter_fn(headless=helpers.HEADLESS, wait=wait)

        parsed = parseFingerprintJsHtml(html)
        meta["user_agent"] = ua
        result["data"] = parsed

        helpers.saveAsJson(browser_name, result, "fingerprintjs")
        log.save(f"Saved FingerprintJS data for {browser_name}")
    except Exception as e:
        meta["error"] = str(e)
        helpers.saveAsJson(browser_name, result, "fingerprintjs")
        log.error(f"Error during {browser_name} test: {e}")

    return result


def main():
    log.module("Starting FingerprintJS module")

    log.info("Firefox test started")
    runSelectedBrowser("Firefox", getHtmlFirefox, wait=3)

    log.info("Chrome test started")
    runSelectedBrowser("Chrome", getHtmlChrome, wait=3)

    log.info("Edge test started")
    runSelectedBrowser("Edge", getHtmlEdge, wait=3)

    log.info("Brave test started")
    runSelectedBrowser("Brave", getHtmlBrave, wait=3)

    tbb_dir = helpers.determineTorBrowserDir()
    if tbb_dir:
        log.info("Tor Browser test started")
        runSelectedBrowser("TorBrowser", getHtmlTorBrowser, wait=5, tbb_dir=tbb_dir)
    else:
        log.warning("Tor Browser folder not found")

    log.finish("FingerprintJS module completed")


if __name__ == "__main__":
    main()
