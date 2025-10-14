import os
import sys
import time
from bs4 import BeautifulSoup
from collections import OrderedDict
import helpers

URL = "https://browserleaks.com/javascript"

def normalizeLabel(label):
    return label.strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")

def parseBrowserleaksJavascriptHtml(html):
    soup = BeautifulSoup(html, "html.parser")
    out = OrderedDict()

    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) >= 2:
            label = tds[0].get_text(separator=" ", strip=True)
            value = tds[1].get_text(separator=" ", strip=True)
            if value.lower() in ("undefined", "none", ""):
                value = None
            out[normalizeLabel(label)] = value

    return out

def getHtmlFirefox(headless=True, wait=3):
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options

    opts = Options()
    opts.binary_location = helpers.FIREFOX_BINARY
    if headless:
        opts.add_argument("--headless")

    driver = webdriver.Firefox(options=opts)
    try:
        driver.get(URL)
        time.sleep(wait)
        ua = driver.execute_script("return navigator.userAgent;")
        html = driver.page_source
    finally:
        driver.quit()

    return html, ua

def getHtmlTorBrowser(tbb_dir, wait=5):
    from tbselenium.tbdriver import TorBrowserDriver

    display = None
    if helpers.HEADLESS_TBB:
        try:
            from pyvirtualdisplay import Display
            display = Display()
            display.start()
            print("[DEBUG] pyvirtualdisplay started for Tor Browser")
        except Exception as e:
            print(f"[WARN] Could not start pyvirtualdisplay: {e}. Trying without headless.")

    try:
        with TorBrowserDriver(tbb_dir) as driver:
            driver.get(URL)
            ua = driver.execute_script("return navigator.userAgent;")
            time.sleep(wait)
            html = driver.page_source
    finally:
        if display:
            display.stop()

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
    ts_iso = helpers.getDatetimeNow()
    ts_safe = helpers.replaceDatetimeSeparators(ts_iso)
    meta = {"browser": browser_name, "timestamp": ts_iso, "script_version": "1.2"}
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
        helpers.saveAsJson(browser_name, ts_safe, result, "javascript")
        print(f"[OK] Saved JavaScript data for {browser_name}")
        return result

    except Exception as e:
        meta["error"] = str(e)
        helpers.saveAsJson(browser_name, ts_safe, result, "javascript")
        print(f"[ERROR] during test {browser_name}: {e}", file=sys.stderr)
        return result

def main():
    print("[RUN] Running BrowserLeaks JavaScript tests")

    print("[RUN] Firefox test")
    runSelectedBrowser("Firefox", getHtmlFirefox, wait=3)

    tbb_dir = helpers.determineTorBrowserDir()
    if not tbb_dir:
        print("[WARN] Tor Browser folder not found", file=sys.stderr)
        return

    print("[RUN] Tor Browser test")
    runSelectedBrowser("TorBrowser", getHtmlTorBrowser, wait=5, tbb_dir=tbb_dir)

    print("[FIN] Finished BrowserLeaks JavaScript tests")

if __name__ == "__main__":
    main()
