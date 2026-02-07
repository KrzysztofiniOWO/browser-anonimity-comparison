from . import helpers
from .helpers import logger as log

import time
import json
from pyvirtualdisplay import Display

from tbselenium.tbdriver import TorBrowserDriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService

URL = "https://abrahamjuliot.github.io/creepjs/"


def getHtmlFirefox(headless=True, wait=60):
    log.info("Launching Firefox for CreepJS test")
    opts = FirefoxOptions()
    opts.binary_location = helpers.FIREFOX_BINARY
    if headless:
        opts.add_argument("--headless")

    driver = webdriver.Firefox(options=opts)
    driver.get(URL)

    log.info(f"Waiting {wait}s for CreepJS to fully render...")
    time.sleep(wait)

    return driver


def getHtmlChrome(headless=True, wait=60):
    log.info("Launching Chrome for CreepJS test")

    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")

    if hasattr(helpers, "CHROME_BINARY") and helpers.CHROME_BINARY:
        opts.binary_location = helpers.CHROME_BINARY

    driver = webdriver.Chrome(options=opts)
    driver.get(URL)

    log.info(f"Waiting {wait}s for CreepJS to fully render...")
    time.sleep(wait)

    return driver


def getHtmlEdge(headless=True, wait=60):
    log.info("Launching Edge for CreepJS test")

    opts = EdgeOptions()
    if headless:
        opts.add_argument("--headless=new")

    opts.add_argument("--disable-gpu")

    opts.binary_location = helpers.EDGE_BINARY

    driver = webdriver.Edge(
        service=EdgeService(helpers.MSEDGEDRIVER), 
        options=opts
    )

    driver.get(URL)

    log.info(f"Waiting {wait}s for CreepJS to fully render...")
    time.sleep(wait)

    return driver


def getHtmlBrave(headless=True, wait=60):
    log.info("Launching Brave for CreepJS test")

    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")

    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(f"--brave-binary={helpers.BRAVE_BINARY}")

    driver = webdriver.Chrome(service=ChromeService(helpers.CHROMEDRIVER), options=opts)
    driver.get(URL)

    log.info(f"Waiting {wait}s for CreepJS to fully render...")
    time.sleep(wait)

    return driver


def getHtmlTorBrowser(tbb_dir, wait=90):
    log.info("Launching Tor Browser for CreepJS test")

    display = None
    if helpers.HEADLESS_TBB:
        display = Display()
        display.start()

    driver = TorBrowserDriver(tbb_dir, headless=False)
    driver.get(URL)

    log.info(f"Waiting {wait}s for CreepJS to fully render...")
    time.sleep(wait)

    return driver, display


def parseCreepJS(driver):
    log.info("Trying to read CreepJS fingerprint object...")

    js = """
        try {
            return JSON.stringify(window.Fingerprint || window.fp || null);
        } catch (e) { return null; }
    """
    raw = driver.execute_script(js)

    if not raw:
        log.error("Fingerprint object NOT FOUND")
        return {}

    try:
        parsed = json.loads(raw)
        log.info("Fingerprint parsed successfully")
        return parsed
    except Exception as e:
        log.error(f"JSON decode error: {e}")
        return {"raw": raw}


def runSelectedBrowser(browser_name, getter_fn, wait=60, tbb_dir=None):
    log.info(f"Running CreepJS test for {browser_name}")

    ts_iso = helpers.getDatetimeNow()
    ts_safe = helpers.replaceDatetimeSeparators(ts_iso)
    meta = {"browser": browser_name, "timestamp": ts_iso, "script_version": "1.0"}
    result = {"meta": meta, "data": None}

    display = None
    try:
        if browser_name.lower().startswith("tor"):
            if not tbb_dir:
                raise RuntimeError("No tbb_dir for Tor Browser")
            driver, display = getter_fn(tbb_dir, wait=wait)
        else:
            driver = getter_fn(headless=helpers.HEADLESS, wait=wait)

        parsed = parseCreepJS(driver)
        result["data"] = parsed

        helpers.saveAsJson(browser_name, result, "creepjs")
        log.save(f"Saved CreepJS data for {browser_name}")

    except Exception as e:
        meta["error"] = str(e)
        log.error(f"Error during {browser_name} CreepJS test: {e}")
        helpers.saveAsJson(browser_name, result, "creepjs")

    finally:
        try:
            driver.quit()
        except:
            pass
        if display:
            display.stop()

    return result


def main():
    log.module("Starting CreepJS module")

    log.info("Firefox test started")
    runSelectedBrowser("Firefox", getHtmlFirefox, wait=10)

    log.info("Chrome test started")
    runSelectedBrowser("Chrome", getHtmlChrome, wait=10)

    log.info("Edge test started")
    runSelectedBrowser("Edge", getHtmlEdge, wait=10)

    log.info("Brave test started")
    runSelectedBrowser("Brave", getHtmlBrave, wait=10)

    tbb_dir = helpers.determineTorBrowserDir()
    if not tbb_dir:
        log.warning("Tor Browser folder not found")
    else:
        log.info("Tor Browser test started")
        runSelectedBrowser("TorBrowser", getHtmlTorBrowser, wait=10, tbb_dir=tbb_dir)

    log.finish("CreepJS module completed")


if __name__ == "__main__":
    main()
