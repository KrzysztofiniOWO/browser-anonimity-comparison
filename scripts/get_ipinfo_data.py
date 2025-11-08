from . import helpers
from .helpers import logger as log

import requests

IPINFO_URL = "https://ipinfo.io/json"
TOR_PROXY = "socks5h://127.0.0.1:9050"


def fetch_ipinfo(url=IPINFO_URL, proxies=None):
    mode = "Tor" if proxies else "Direct"
    log.info(f"Fetching IP info ({mode} mode) from {url}")

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


def save_data(browser_name, data, category="ipinfo"):
    ts_iso = helpers.getDatetimeNow()
    ts_safe = helpers.replaceDatetimeSeparators(ts_iso)
    helpers.saveAsJson(browser_name, ts_safe, data, category)
    log.save(f"Saved IP info data for {browser_name}")
    return True


def main():
    log.module("Running ipinfo test")

    log.info("Starting Firefox IP info test")
    firefox_data = fetch_ipinfo()
    if firefox_data:
        save_data("firefox", firefox_data)
    else:
        log.warning("No data fetched for Firefox")

    log.info("Starting Tor Browser IP info test")
    tor_data = fetch_ipinfo(proxies={"http": TOR_PROXY, "https": TOR_PROXY})
    if tor_data:
        save_data("torbrowser", tor_data)
    else:
        log.warning("No data fetched for Tor Browser")

    log.finish("Finished ipinfo test")


if __name__ == "__main__":
    main()
