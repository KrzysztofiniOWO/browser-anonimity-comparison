import os
import sys
import time
import json
import re
from collections import OrderedDict
import helpers
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
try:
    from tbselenium.tbdriver import TorBrowserDriver
except ImportError:
    TorBrowserDriver = None

URL = "https://amiunique.org/fingerprint"

def normalize_key(label):
    key = label.split(" - ", 1)[-1].strip().lower()
    key = re.sub(r'[()\s]+', '_', key)
    key = re.sub(r'_+', '_', key)
    key = key.strip('_')
    return key

def extract_cell_value(cell):
    try:
        spans = cell.find_elements(By.CSS_SELECTOR, "span, div")
        text_values = [s.text.strip() for s in spans if s.text.strip()]
        if text_values:
            return "\n".join(text_values)
    except:
        pass

    try:
        svg_spans = cell.find_elements(By.CSS_SELECTOR, "span.v-icon")
        for svg_span in svg_spans:
            cls = svg_span.get_attribute("class") or ""
            if "red--text" in cls:
                return "No value"
            elif "green--text" in cls:
                return "Yes"
        return "Unknown"
    except:
        return "Unknown"


def clean_multiline(value):
    lines = [line.strip() for line in value.split("\n") if line.strip()]
    return "\n".join(list(dict.fromkeys(lines)))

def getHtmlFirefox(headless=True, wait=30):
    opts = Options()
    opts.binary_location = helpers.FIREFOX_BINARY
    if headless:
        opts.add_argument("--headless")
    driver = webdriver.Firefox(options=opts)
    driver.get(URL)
    print(f"[DEBUG] Waiting {wait}s for full JS rendering...")
    time.sleep(wait)
    return driver

def getHtmlTorBrowser(tbb_dir, wait=30):
    if TorBrowserDriver is None:
        raise RuntimeError("tbselenium is required for Tor Browser")
    from pyvirtualdisplay import Display
    display = None
    if helpers.HEADLESS_TBB:
        display = Display()
        display.start()
        print("[DEBUG] pyvirtualdisplay started for Tor Browser")
    driver = TorBrowserDriver(tbb_dir, headless=False)
    driver.get(URL)
    print(f"[DEBUG] Waiting {wait}s for full page rendering (Tor Browser)...")
    time.sleep(wait)
    return driver, display

def get_dynamic_values(driver):
    out = {}
    try:
        out['cookies_enabled'] = driver.execute_script("return navigator.cookieEnabled ? 'Yes' : 'No';")
    except:
        out['cookies_enabled'] = 'Unknown'

    try:
        out['use_of_local_storage'] = driver.execute_script("return typeof localStorage !== 'undefined' ? 'Yes' : 'No';")
    except:
        out['use_of_local_storage'] = 'Unknown'

    try:
        out['use_of_session_storage'] = driver.execute_script("return typeof sessionStorage !== 'undefined' ? 'Yes' : 'No';")
    except:
        out['use_of_session_storage'] = 'Unknown'

    try:
        out['use_of_indexeddb'] = driver.execute_script("return typeof indexedDB !== 'undefined' ? 'Yes' : 'No';")
    except:
        out['use_of_indexeddb'] = 'Unknown'

    try:
        out['do_not_track'] = driver.execute_script("return navigator.doNotTrack || 'No value';")
    except:
        out['do_not_track'] = 'Unknown'

    try:
        out['use_of_adblock'] = driver.execute_script("""
            let bait = document.createElement('div');
            bait.className = 'adsbox';
            bait.style.height='1px';
            document.body.appendChild(bait);
            let blocked = window.getComputedStyle(bait).display === 'none';
            document.body.removeChild(bait);
            return blocked ? 'Yes' : 'No value';
        """)
    except:
        out['use_of_adblock'] = 'Unknown'

    return out

def parseAmiUniqueHtml(driver):
    data = {}
    rows = driver.find_elements(By.CSS_SELECTOR, "tr")
    for row in rows:
        try:
            label_cell = row.find_element(By.CSS_SELECTOR, "td:first-child")
            value_cell = row.find_element(By.CSS_SELECTOR, "td:last-child")
            key = normalize_key(label_cell.text)
            value = extract_cell_value(value_cell)
            value = clean_multiline(value)
            data[key] = value
        except:
            continue
    data.update(get_dynamic_values(driver))
    return data

def runSelectedBrowser(browser_name, getter_fn, wait=30, tbb_dir=None):
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
            driver = getter_fn(headless=helpers.HEADLESS_FIREFOX, wait=wait)

        parsed = parseAmiUniqueHtml(driver)
        result["data"] = parsed
        helpers.saveAsJson(browser_name, ts_safe, result, "amiunique_summary")
        print(f"[OK] Saved AmiUnique data for {browser_name}")

    except Exception as e:
        meta["error"] = str(e)
        helpers.saveAsJson(browser_name, ts_safe, result, "amiunique_summary")
        print(f"[ERROR] during test {browser_name}: {e}", file=sys.stderr)

    finally:
        try:
            driver.quit()
        except:
            pass
        if display:
            display.stop()

    return result

def main():
    print("[RUN] Running AmiUnique fingerprint tests")

    print("[RUN] Firefox test")
    runSelectedBrowser("Firefox", getHtmlFirefox, wait=30)

    tbb_dir = helpers.determineTorBrowserDir()
    if not tbb_dir:
        print("[WARN] Tor Browser folder not found", file=sys.stderr)
    else:
        print("[RUN] Tor Browser test")
        runSelectedBrowser("TorBrowser", getHtmlTorBrowser, wait=30, tbb_dir=tbb_dir)

    print("[FIN] Finished AmiUnique fingerprint tests")

if __name__ == "__main__":
    main()
