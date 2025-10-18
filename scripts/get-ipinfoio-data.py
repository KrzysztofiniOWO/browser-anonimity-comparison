import os
import json
import requests
from pathlib import Path

import helpers

IPINFO_URL = "https://ipinfo.io/json"
TOR_PROXY = "socks5h://127.0.0.1:9050"

def fetch_ipinfo(url=IPINFO_URL, proxies=None):
    try:
        resp = requests.get(url, headers={"Accept": "application/json"}, timeout=15, proxies=proxies)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[WARN] Request failed: {e}")
        return None

def save_data(browser_name, data, category="ipinfo"):
    ts_iso = helpers.getDatetimeNow()
    ts_safe = helpers.replaceDatetimeSeparators(ts_iso)
    return helpers.saveAsJson(browser_name, ts_safe, data, category)

def main():
    print("[RUN] Firefox")
    firefox_data = fetch_ipinfo()
    if firefox_data:
        save_data("firefox", firefox_data)
        print("[OK] Firefox done\n")

    print("[RUN] TorBrowser")
    tor_data = fetch_ipinfo(proxies={"http": TOR_PROXY, "https": TOR_PROXY})
    if tor_data:
        save_data("torbrowser", tor_data)
        print("[OK] TorBrowser done\n")
    else:
        print("[WARN] TorBrowser data not available\n")

if __name__ == "__main__":
    main()
