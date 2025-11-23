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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://www.browserscan.net/"


def acceptConsent(driver, timeout=10):
    try:
        consent_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.fc-cta-consent"))
        )
        consent_btn.click()
        log.info("Consent button clicked")
    except:
        log.info("No Consent button found or already accepted")


def getHtmlFirefox(headless=False, wait=50):
    log.info("Launching Firefox for BrowserScan test")
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

    profile = FirefoxProfile()
    profile.set_preference("webgl.disabled", False)
    profile.set_preference("javascript.enabled", True)
    profile.set_preference("media.navigator.enabled", True)
    profile.set_preference("dom.webrtc.enabled", True)

    opts = FirefoxOptions()
    opts.binary_location = helpers.FIREFOX_BINARY
    opts.headless = headless
    opts.profile = profile

    driver = webdriver.Firefox(options=opts)
    driver.get(URL)

    acceptConsent(driver)

    log.info(f"Waiting {wait}s for BrowserScan to load...")
    time.sleep(wait)
    return driver


def getHtmlChrome(headless=False, wait=50):
    log.info("Launching Chrome for BrowserScan test")

    opts = ChromeOptions()
    opts.headless = headless
    opts.add_argument("--start-maximized")
    opts.add_argument("--use-gl=desktop")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    
    if hasattr(helpers, "CHROME_BINARY") and helpers.CHROME_BINARY:
        opts.binary_location = helpers.CHROME_BINARY
    else:
        opts.binary_location = "/usr/bin/chromium-browser"

    driver = webdriver.Chrome(options=opts)
    driver.get(URL)

    acceptConsent(driver)

    log.info(f"Waiting {wait}s for BrowserScan to load...")
    time.sleep(wait)
    return driver


def getHtmlTorBrowser(tbb_dir, wait=70):
    log.info("Launching Tor Browser for BrowserScan test")

    display = None
    if helpers.HEADLESS_TBB:
        display = Display()
        display.start()

    driver = TorBrowserDriver(tbb_dir, headless=False)
    driver.get(URL)

    log.info(f"Waiting {wait}s for BrowserScan to load...")
    time.sleep(wait)

    return driver, display


def parseBrowserScan(driver):
    data = {}

    blocks = driver.find_elements(By.CSS_SELECTOR, "div._kwexxy")
    for block in blocks:
        try:
            key_el = block.find_element(By.TAG_NAME, "h3")
            key = key_el.text.strip().replace(":", "").lower().replace(" ", "_")
            try:
                val_el = block.find_element(By.CSS_SELECTOR, "div._1lcvjee, p._1lcvjee")
                value = val_el.text.strip().split("\n")[0]
            except:
                value = ""
            if key and value:
                data[key] = value
        except:
            continue

    table_blocks = driver.find_elements(By.CSS_SELECTOR, "div._11xj7yu")
    for tb in table_blocks:
        try:
            key_el = tb.find_element(By.CSS_SELECTOR, "div._to28ap h3")
            key = key_el.text.strip().lower().replace(" ", "_")

            try:
                val_el = tb.find_element(By.CSS_SELECTOR, "div._gtrg9a")
                lis = val_el.find_elements(By.TAG_NAME, "li")
                if lis:
                    value = [li.text.strip() for li in lis if li.text.strip()]
                else:
                    value = val_el.text.strip()
            except:
                value = ""

            if key and value:
                data[key] = value
        except:
            continue

    return data


def runSelectedBrowser(browser_name, getter_fn, wait=50, tbb_dir=None):
    log.info(f"Running BrowserScan test for {browser_name}")

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

        parsed = parseBrowserScan(driver)
        result["data"] = parsed

        helpers.saveAsJson(browser_name, ts_safe, result, "browserscan")
        log.save(f"Saved BrowserScan data for {browser_name}")

    except Exception as e:
        meta["error"] = str(e)
        log.error(f"Error during BrowserScan test ({browser_name}): {e}")
        helpers.saveAsJson(browser_name, ts_safe, result, "browserscan")

    finally:
        try:
            driver.quit()
        except:
            pass
        if display:
            display.stop()

    return result


def main():
    log.module("Starting BrowserScan module")

    log.info("Firefox test started")
    runSelectedBrowser("Firefox", getHtmlFirefox, wait=15)

    log.info("Chrome test started")
    runSelectedBrowser("Chrome", getHtmlChrome, wait=15)

    tbb_dir = helpers.determineTorBrowserDir()
    if tbb_dir:
        log.info("Tor Browser test started")
        runSelectedBrowser("TorBrowser", getHtmlTorBrowser, wait=15, tbb_dir=tbb_dir)
    else:
        log.warning("Tor Browser folder not found")

    log.finish("BrowserScan module completed")


if __name__ == "__main__":
    main()
