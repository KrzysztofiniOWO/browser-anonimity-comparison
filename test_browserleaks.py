import requests
import re
from bs4 import BeautifulSoup

URL = "https://browserleaks.com/ip"
TOR_PROXY = "socks5h://127.0.0.1:9050"
TIMEOUT = 10

def extract_ip(text):
    m = re.search(r'id=["\']client-ipv4["\'][^>]*data-ip=["\']([^"\']+)["\']', text)
    if m:
        return m.group(1).strip()
    m2 = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})', text)
    if m2:
        return m2.group(1)
    return ""

def extract_region(text):
    soup = BeautifulSoup(text, "html.parser")
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) >= 2 and tds[0].get_text(strip=True) == "State/Region":
            return tds[1].get_text(strip=True)
    return ""

def get_ip_normal():
    try:
        r = requests.get(URL, timeout=TIMEOUT)
        r.raise_for_status()
        return extract_ip(r.text), extract_region(r.text)
    except requests.RequestException:
        return "", ""

def get_ip_tor():
    proxies = {"http": TOR_PROXY, "https": TOR_PROXY}
    try:
        r = requests.get(URL, proxies=proxies, timeout=TIMEOUT)
        r.raise_for_status()
        return extract_ip(r.text), extract_region(r.text)
    except requests.RequestException:
        return "", ""

if __name__ == "__main__":
    ip_normal, region_normal = get_ip_normal()
    ip_tor, region_tor = get_ip_tor()

    print(ip_normal)
    print(region_normal)
    print(ip_tor)
    print(region_tor)
