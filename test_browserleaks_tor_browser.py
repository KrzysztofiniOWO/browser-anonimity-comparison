import os
import time
import re
import sys
from bs4 import BeautifulSoup

URL = "https://browserleaks.com/ip"

TOR_BROWSER_BINARY = os.environ.get("TOR_BROWSER_BINARY", "/home/kali/Magisterka/tor-browser/Browser/firefox")
FIREFOX_BINARY = "/usr/bin/firefox"
HEADLESS_TBB = os.environ.get("HEADLESS_TBB", "") != ""

def extract_ip(text):
    import re
    m = re.search(r'id=["\']client-ipv4["\'][^>]*data-ip=["\']([^"\']+)["\']', text)
    if m:
        return m.group(1).strip()
    m2 = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})', text)
    if m2:
        return m2.group(1)
    return ""

def extract_region(text):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, "html.parser")
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) >= 2 and tds[0].get_text(strip=True) == "State/Region":
            return tds[1].get_text(strip=True)
    return ""

def get_with_firefox(headless=True, wait=3):
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options

    opts = Options()
    opts.binary_location = FIREFOX_BINARY
    if headless:
        opts.add_argument("--headless")

    driver = webdriver.Firefox(options=opts)
    try:
        driver.get(URL)
        time.sleep(wait)
        html = driver.page_source
    finally:
        driver.quit()
    return extract_ip(html), extract_region(html)

def get_with_tor_browser(tbb_dir, wait=5):
    try:
        from tbselenium.tbdriver import TorBrowserDriver
    except Exception as e:
        raise RuntimeError("Missing tbselenium.") from e

    display = None
    if HEADLESS_TBB:
        from pyvirtualdisplay import Display
        display = Display()
        display.start()

    try:
        with TorBrowserDriver(tbb_dir) as driver:
            driver.get(URL)
            ua = driver.execute_script("return navigator.userAgent;")
            print(f"[DEBUG] Tor Browser user agent: {ua}")

            time.sleep(wait)
            html = driver.page_source
    finally:
        if display:
            display.stop()

    return extract_ip(html), extract_region(html)

if __name__ == "__main__":
    try:
        ip_normal, region_normal = get_with_firefox(headless=True, wait=3)
    except Exception as e:
        print(f"# ERROR: nie udało się uruchomić Firefoxa: {e}", file=sys.stderr)
        sys.exit(1)

    if os.path.isfile(TOR_BROWSER_BINARY):
        tbb_dir = os.path.dirname(os.path.dirname(TOR_BROWSER_BINARY))
    else:
        print(f"# ERROR: Nie znaleziono pliku Tor Browser binary: {TOR_BROWSER_BINARY}", file=sys.stderr)
        sys.exit(2)

    try:
        ip_tor, region_tor = get_with_tor_browser(tbb_dir, wait=5)
    except Exception as e:
        print(f"# ERROR: Nie udało się uruchomić Tor Browsera przez tbselenium: {e}", file=sys.stderr)
        sys.exit(3)

    print(ip_normal)
    print(region_normal)
    print(ip_tor)
    print(region_tor)
