from . import helpers
from .helpers import logger as log

import time
import re
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

URL = "https://browserleaks.com/dns"

def parseBrowserleaksDNSHtml(html):
    log.info("Parsing BrowserLeaks DNS HTML content")

    soup = BeautifulSoup(html, "html.parser")

    out = {
        "dns_servers": []
    }

    page_text = soup.get_text(" ", strip=True)

    m = re.search(r"IP Address\s+([\d\.]+)", page_text)
    if m:
        out["ip_address"] = m.group(1)

    m = re.search(r"ISP\s+([A-Za-z0-9\.\- ]+)", page_text)
    if m:
        out["isp"] = m.group(1).strip()

    m = re.search(r"Location\s+([A-Za-z ]+),\s*([A-Za-z ]+)", page_text)
    if m:
        out["location"] = {
            "country": m.group(1).strip(),
            "city": m.group(2).strip()
        }

    m = re.search(
        r"Found\s+(\d+)\s+Servers,\s+(\d+)\s+ISP,\s+(\d+)\s+Location",
        page_text
    )
    if m:
        out["dns_test_summary"] = {
            "servers_found": int(m.group(1)),
            "isp_count": int(m.group(2)),
            "location_count": int(m.group(3))
        }

    dns_tbody = soup.find("tbody", id="dns-list")
    if not dns_tbody:
        log.warning("DNS list table not found")
        return out

    for row in dns_tbody.find_all("tr"):
        ip_cell = row.find("td", class_="dns-col-ip")
        isp_cell = row.find("td", class_="dns-col-isp")
        loc_cell = row.find("td", class_="n-740")

        if not (ip_cell and isp_cell and loc_cell):
            continue

        ip = ip_cell.get_text(strip=True)

        if not re.match(r"^(\d{1,3}(\.\d{1,3}){3}|[a-fA-F0-9:]{4,})$", ip):
            continue

        isp = isp_cell.get_text(strip=True)
        location = loc_cell.get_text(strip=True)

        country, city = None, None
        if "," in location:
            country, city = [x.strip() for x in location.split(",", 1)]

        out["dns_servers"].append({
            "ip": ip,
            "ip_version": "ipv6" if ":" in ip else "ipv4",
            "isp": isp,
            "country": country,
            "city": city
        })

    out["dns_server_count"] = len(out["dns_servers"])

    return out


def getHtmlFirefox(headless=False, wait=4):
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


def getHtmlChrome(headless=False, wait=4):
    log.info("Launching Chrome browser session")
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


def getHtmlEdge(headless=False, wait=4):
    log.info("Launching Edge browser session")
    opts = EdgeOptions()
    opts.binary_location = helpers.EDGE_BINARY
    if headless:
        opts.add_argument("--headless=new")

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


def getHtmlBrave(headless=False, wait=4):
    log.info("Launching Brave browser session")
    opts = ChromeOptions()
    opts.add_argument(f"--brave-binary={helpers.BRAVE_BINARY}")
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-blink-features=AutomationControlled")

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

def getHtmlTorBrowser(tbb_dir, wait=6):
    log.info("Launching Tor Browser session")

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

def runSelectedBrowser(browser_name, getter_fn, wait=4, tbb_dir=None):
    log.info(f"Running BrowserLeaks DNS test for {browser_name}")

    ts_iso = helpers.getDatetimeNow()
    meta = {"browser": browser_name, "timestamp": ts_iso, "script_version": "1.0"}
    result = {"meta": meta, "data": None}

    try:
        if browser_name.lower().startswith("tor"):
            html, ua = getter_fn(tbb_dir, wait=wait)
        else:
            html, ua = getter_fn(headless=helpers.HEADLESS, wait=wait)

        parsed = parseBrowserleaksDNSHtml(html)
        meta["user_agent"] = ua
        result["data"] = parsed

        helpers.saveAsJson(browser_name, result, "browserleaks_dns")
        log.save(f"Saved BrowserLeaks DNS data for {browser_name}")

    except Exception as e:
        meta["error"] = str(e)
        helpers.saveAsJson(browser_name, result, "browserleaks_dns")
        log.error(f"Error during {browser_name} DNS test: {e}")

    return result

def main():
    log.module("Starting BrowserLeaks DNS module")

    log.info("Firefox test started")
    runSelectedBrowser("Firefox", getHtmlFirefox)

    log.info("Chrome test started")
    runSelectedBrowser("Chrome", getHtmlChrome)

    log.info("Edge test started")
    runSelectedBrowser("Edge", getHtmlEdge)

    log.info("Brave test started")
    runSelectedBrowser("Brave", getHtmlBrave)

    tbb_dir = helpers.determineTorBrowserDir()
    if tbb_dir:
        runSelectedBrowser("TorBrowser", getHtmlTorBrowser, tbb_dir=tbb_dir)
    else:
        log.warning("Tor Browser folder not found")

    log.finish("BrowserLeaks DNS module completed")


if __name__ == "__main__":
    main()


