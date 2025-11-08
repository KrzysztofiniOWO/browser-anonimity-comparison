from . import helpers
from .helpers import logger as log

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
try:
    from tbselenium.tbdriver import TorBrowserDriver
except ImportError:
    TorBrowserDriver = None


URL = "https://pixelscan.net/fingerprint-check"


def getHtmlFirefox(headless=True, wait=50):
    log.info("Launching Firefox for PixelScan test")
    opts = Options()
    opts.binary_location = helpers.FIREFOX_BINARY
    if headless:
        opts.add_argument("--headless")

    driver = webdriver.Firefox(options=opts)
    driver.get(URL)
    log.info(f"Waiting {wait}s for full JS load...")
    time.sleep(wait)
    log.info("Firefox page loaded successfully")
    return driver


def getHtmlTorBrowser(tbb_dir, wait=50):
    log.info("Launching Tor Browser for PixelScan test")
    if TorBrowserDriver is None:
        raise RuntimeError("tbselenium is required for Tor Browser")

    from pyvirtualdisplay import Display
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


def parsePixelScanHtml(driver):
    log.info("Parsing PixelScan HTML content")
    data = {}

    sections = driver.find_elements(By.CSS_SELECTOR, ".pxlscn-card-body__section")
    for section in sections:
        try:
            title_elem = section.find_element(By.CSS_SELECTOR, ".pxlscn-card-body__section__title")
            section_title = title_elem.text.strip().lower().replace(" ", "_")

            records = section.find_elements(By.CSS_SELECTOR, ".pxlscn-card-body__section__body__record")
            section_data = {}
            for rec in records:
                try:
                    key_elem = rec.find_element(By.CSS_SELECTOR, ".pxlscn-card-body__section__body__record__title")
                    val_elem = rec.find_element(By.CSS_SELECTOR, ".pxlscn-card-body__section__body__record__value")
                    key = key_elem.text.strip()
                    val = val_elem.text.strip()
                    if key:
                        section_data[key] = val
                except:
                    continue

            if section_data:
                data[section_title] = section_data
        except:
            continue

    log.info(f"Parsed {len(data)} PixelScan sections")
    return data


def runSelectedBrowser(browser_name, getter_fn, wait=50, tbb_dir=None):
    log.info(f"Running PixelScan test for {browser_name}")
    ts_iso = helpers.getDatetimeNow()
    ts_safe = helpers.replaceDatetimeSeparators(ts_iso)
    meta = {"browser": browser_name, "timestamp": ts_iso, "script_version": "2.0"}
    result = {"meta": meta, "data": None}

    display = None
    try:
        if browser_name.lower().startswith("tor"):
            if not tbb_dir:
                raise RuntimeError("No tbb_dir for Tor Browser")
            driver, display = getter_fn(tbb_dir, wait=wait)
        else:
            driver = getter_fn(headless=helpers.HEADLESS_FIREFOX, wait=wait)

        parsed = parsePixelScanHtml(driver)
        result["data"] = parsed
        helpers.saveAsJson(browser_name, ts_safe, result, "pixelscan")
        log.save(f"Saved PixelScan data for {browser_name}")

    except Exception as e:
        meta["error"] = str(e)
        log.error(f"Error during {browser_name} PixelScan test: {e}")
        helpers.saveAsJson(browser_name, ts_safe, result, "pixelscan")

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
    log.module("Starting PixelScan module")

    log.info("Firefox test started")
    runSelectedBrowser("Firefox", getHtmlFirefox, wait=50)

    tbb_dir = helpers.determineTorBrowserDir()
    if not tbb_dir:
        log.warning("Tor Browser folder not found")
    else:
        log.info("Tor Browser test started")
        runSelectedBrowser("TorBrowser", getHtmlTorBrowser, wait=80, tbb_dir=tbb_dir)

    log.finish("PixelScan module completed")


if __name__ == "__main__":
    main()
