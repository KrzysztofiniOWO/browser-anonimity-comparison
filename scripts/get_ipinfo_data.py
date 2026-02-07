from . import helpers
from .helpers import logger as log

import json
import time
import requests
from pyvirtualdisplay import Display

from tbselenium.tbdriver import TorBrowserDriver
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService

IPINFO_URL = "https://ipinfo.io/json"
TOR_PROXY = "socks5h://127.0.0.1:9050"

def get_ipinfo_from_driver(driver, wait=3):
    try:
        driver.get(IPINFO_URL)
        time.sleep(wait)
        src = driver.page_source
        try:
            first = src.find("{")
            last = src.rfind("}")
            if first != -1 and last != -1 and last > first:
                txt = src[first:last+1]
            else:
                txt = src
            data = json.loads(txt)
        except Exception:
            try:
                js = (
                    "return fetch(arguments[0], {credentials: 'omit'}).then(r=>r.text()).then(t=>t).catch(e=>null);"
                )
                txt = driver.execute_script(js, IPINFO_URL)
                data = json.loads(txt) if txt else None
            except Exception:
                data = None

        try:
            ua = driver.execute_script("return navigator.userAgent;")
        except Exception:
            ua = None

        return data, ua
    except Exception as e:
        log.error(f"Error while fetching IP info via driver: {e}")
        return None, None


def getHtmlFirefox(headless=True, wait=3):
    log.info("Launching Firefox browser session for ipinfo")

    opts = FirefoxOptions()
    if hasattr(helpers, "FIREFOX_BINARY") and helpers.FIREFOX_BINARY:
        opts.binary_location = helpers.FIREFOX_BINARY
    if headless:
        opts.add_argument("--headless")

    driver = webdriver.Firefox(options=opts)
    try:
        data, ua = get_ipinfo_from_driver(driver, wait=wait)
        log.info("Firefox ipinfo fetch completed")
    finally:
        try:
            driver.quit()
        except:
            pass
        log.info("Closed Firefox session")
    return data, ua


def getHtmlChrome(headless=True, wait=3):
    log.info("Launching Chrome browser session for ipinfo")

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
        data, ua = get_ipinfo_from_driver(driver, wait=wait)
        log.info("Chrome ipinfo fetch completed")
    finally:
        try:
            driver.quit()
        except:
            pass
        log.info("Closed Chrome session")
    return data, ua


def getHtmlEdge(headless=True, wait=3):
    log.info("Launching Edge browser session for ipinfo")

    opts = EdgeOptions()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")

    opts.binary_location = helpers.EDGE_BINARY

    driver = webdriver.Edge(
        service=EdgeService('/usr/local/bin/msedgedriver'), 
        options=opts
    )

    try:
        data, ua = get_ipinfo_from_driver(driver, wait=wait)
        log.info("Edge ipinfo fetch completed")
    finally:
        try:
            driver.quit()
        except:
            pass
        log.info("Closed Edge session")

    return data, ua


def getHtmlBrave(headless=True, wait=3):
    log.info("Launching Brave browser session for ipinfo")

    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
        opts.add_argument("--disable-gpu")

    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--user-data-dir=/tmp/brave-ipinfo-profile")
    opts.add_argument(f"--brave-binary={helpers.BRAVE_BINARY}")

    driver = webdriver.Chrome(service=ChromeService("/usr/bin/chromedriver"), options=opts)

    try:
        data, ua = get_ipinfo_from_driver(driver, wait=wait)
        log.info("Brave ipinfo fetch completed")
    finally:
        try:
            driver.quit()
        except:
            pass
        log.info("Closed Brave session")

    return data, ua


def getHtmlTorBrowser(tbb_dir, wait=5):
    log.info("Launching Tor Browser session for ipinfo")

    display = None
    if TorBrowserDriver is None:
        log.warning("tbselenium not available, falling back to requests via Tor proxy")
        data = fetch_ipinfo(proxies={"http": TOR_PROXY, "https": TOR_PROXY})
        ua = None
        return data, ua

    if helpers.HEADLESS_TBB and Display is not None:
        try:
            display = Display()
            display.start()
            log.info("Started virtual display for Tor Browser")
        except Exception as e:
            log.warning(f"Could not start virtual display for Tor Browser: {e}. Continuing without it.")

    data = None
    ua = None
    try:
        with TorBrowserDriver(tbb_dir, headless=False) as driver:
            data, ua = get_ipinfo_from_driver(driver, wait=wait)
            log.info("Tor Browser ipinfo fetch completed")
    except Exception as e:
        log.error(f"Error launching Tor Browser via tbselenium: {e}")
        data = fetch_ipinfo(proxies={"http": TOR_PROXY, "https": TOR_PROXY})
        ua = None
    finally:
        if display:
            try:
                display.stop()
                log.info("Stopped virtual display for Tor Browser")
            except:
                pass

    return data, ua


def fetch_ipinfo(url=IPINFO_URL, proxies=None):

    mode = "Tor" if proxies else "Direct"
    log.info(f"Fetching IP info ({mode} mode) from {url} [requests fallback]")

    try:
        resp = requests.get(url, headers={"Accept": "application/json"}, timeout=15, proxies=proxies)
        resp.raise_for_status()
        log.info(f"Successfully received IP info ({mode})")
        return resp.json()
    except requests.exceptions.RequestException as e:
        log.error(f"Network error during IP info fetch ({mode}): {e}")
    except Exception as e:
        log.error(f"Unexpected error fetching IP info ({mode}): {e}")

    return None

def save_data(browser_name, data, ua=None, category="ipinfo"):
    ts_iso = helpers.getDatetimeNow()
    ts_safe = helpers.replaceDatetimeSeparators(ts_iso)
    out = {"meta_ts": ts_iso, "user_agent": ua, "data": data}
    helpers.saveAsJson(browser_name, out, category)
    log.save(f"Saved IP info data for {browser_name}")
    return True


def main():
    log.module("Running ipinfo test (browser-driven)")

    log.info("Starting Firefox IP info test (browser-driven)")
    try:
        data, ua = getHtmlFirefox(headless=helpers.HEADLESS, wait=4)
        if not data:
            log.warning("Firefox webdriver did not return data, falling back to requests")
            data = fetch_ipinfo()
        save_data("firefox", data, ua)
    except Exception as e:
        log.error(f"Unhandled error in Firefox ipinfo test: {e}")

    log.info("Starting Chrome IP info test (browser-driven)")
    try:
        data, ua = getHtmlChrome(headless=helpers.HEADLESS, wait=4)
        if not data:
            log.warning("Chrome webdriver did not return data, falling back to requests")
            data = fetch_ipinfo()
        save_data("chrome", data, ua)
    except Exception as e:
        log.error(f"Unhandled error in Chrome ipinfo test: {e}")

    log.info("Starting Edge IP info test (browser-driven)")
    try:
        data, ua = getHtmlEdge(headless=helpers.HEADLESS, wait=4)
        if not data:
            log.warning("Edge webdriver did not return data, falling back to requests")
            data = fetch_ipinfo()
        save_data("edge", data, ua)
    except Exception as e:
        log.error(f"Unhandled error in edge ipinfo test: {e}")

    log.info("Starting Brave IP info test (browser-driven)")
    try:
        data, ua = getHtmlBrave(headless=helpers.HEADLESS, wait=4)
        if not data:
            log.warning("Brave webdriver did not return data, falling back to requests")
            data = fetch_ipinfo()
        save_data("brave", data, ua)
    except Exception as e:
        log.error(f"Unhandled error in Brave ipinfo test: {e}")

    log.info("Starting Tor Browser IP info test (browser-driven / tor proxy fallback)")
    tbb_dir = None
    try:
        tbb_dir = helpers.determineTorBrowserDir()
    except Exception:
        tbb_dir = None

    if tbb_dir:
        data, ua = getHtmlTorBrowser(tbb_dir=tbb_dir, wait=5)
        if not data:
            log.warning("Tor Browser fetch failed, falling back to requests via Tor proxy")
            data = fetch_ipinfo(proxies={"http": TOR_PROXY, "https": TOR_PROXY})
        save_data("torbrowser", data, ua)
    else:
        log.warning("Tor Browser folder not found; using requests via Tor proxy")
        data = fetch_ipinfo(proxies={"http": TOR_PROXY, "https": TOR_PROXY})
        save_data("torbrowser", data, ua=None)

    log.finish("Finished ipinfo test (browser-driven)")

if __name__ == "__main__":
    main()
