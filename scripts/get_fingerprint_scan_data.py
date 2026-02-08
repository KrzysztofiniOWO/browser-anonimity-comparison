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

URL = "https://fingerprint-scan.com/"

def parseFingerprintScanHtml(html):
    """
    Parsuje fingerprint-scan.com i zwraca strukturę:
    {
        "Section Name": {
            "key": value,
            ...
        }
    }
    """
    log.info("Parsing fingerprint-scan HTML content")
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("tbody")
    if not table:
        log.warning("No tbody found")
        return {}

    result = OrderedDict()
    current_section = None

    for tr in table.find_all("tr"):
        header = tr.find("td", class_="object-header")
        if header:
            current_section = header.get_text(strip=True)
            result[current_section] = OrderedDict()
            continue

        cells = tr.find_all("td", class_="data-cell")
        if len(cells) == 2 and current_section:
            key = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)

            # próba JSON
            if value.startswith("[") or value.startswith("{"):
                try:
                    value = json.loads(value)
                except:
                    pass

            result[current_section][key] = value

    return result


def getHtmlFirefox(headless=False, wait=6):
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


def getHtmlChrome(headless=False, wait=6):
    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")

    if helpers.CHROME_BINARY:
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


def getHtmlEdge(headless=False, wait=6):
    opts = EdgeOptions()
    opts.binary_location = helpers.EDGE_BINARY
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")

    driver = webdriver.Edge(
        service=EdgeService(helpers.MSEDGEDRIVER),
        options=opts
    )
    try:
        driver.get(URL)
        time.sleep(wait)
        html = driver.page_source
        ua = driver.execute_script("return navigator.userAgent;")
    finally:
        driver.quit()
    return html, ua


def getHtmlBrave(headless=False, wait=6):
    opts = ChromeOptions()
    opts.add_argument(f"--brave-binary={helpers.BRAVE_BINARY}")
    opts.add_argument("--disable-blink-features=AutomationControlled")

    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")

    driver = webdriver.Chrome(
        service=ChromeService(helpers.CHROMEDRIVER),
        options=opts
    )
    try:
        driver.get(URL)
        time.sleep(wait)
        html = driver.page_source
        ua = driver.execute_script("return navigator.userAgent;")
    finally:
        driver.quit()
    return html, ua


def getHtmlTorBrowser(tbb_dir, wait=8):
    display = None
    if helpers.HEADLESS_TBB:
        display = Display()
        display.start()

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


def runSelectedBrowser(browser_name, getter_fn, wait=6, tbb_dir=None):
    log.info(f"Running fingerprint-scan test for {browser_name}")

    meta = {
        "browser": browser_name,
        "timestamp": helpers.getDatetimeNow(),
        "script": "fingerprint_scan",
        "version": "1.0"
    }

    result = {"meta": meta, "data": None}

    try:
        if browser_name.lower().startswith("tor"):
            html, ua = getter_fn(tbb_dir, wait)
        else:
            html, ua = getter_fn(headless=helpers.HEADLESS, wait=wait)

        meta["user_agent"] = ua
        result["data"] = parseFingerprintScanHtml(html)

        helpers.saveAsJson(browser_name, result, "fingerprint_scan")
        log.save(f"Saved fingerprint-scan data for {browser_name}")

    except Exception as e:
        meta["error"] = str(e)
        helpers.saveAsJson(browser_name, result, "fingerprint_scan")
        log.error(f"{browser_name} failed: {e}")

    return result


def main():
    log.module("Starting fingerprint-scan module")

    runSelectedBrowser("Firefox", getHtmlFirefox)
    runSelectedBrowser("Chrome", getHtmlChrome)
    runSelectedBrowser("Edge", getHtmlEdge)
    runSelectedBrowser("Brave", getHtmlBrave)

    tbb_dir = helpers.determineTorBrowserDir()
    if tbb_dir:
        runSelectedBrowser("TorBrowser", getHtmlTorBrowser, tbb_dir=tbb_dir)

    log.finish("fingerprint-scan module completed")


if __name__ == "__main__":
    main()
