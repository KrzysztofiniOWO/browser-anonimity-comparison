from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
import os
import time

TOR_ROOT = os.path.expanduser("~/Magisterka/tor-browser")
TOR_FIREFOX_BIN = os.path.join(TOR_ROOT, "Browser", "firefox")
TOR_PROFILE_PATH = os.path.join(TOR_ROOT, "Browser", "TorBrowser", "Data", "Browser", "profile.default")

def start_tor_browser():
    options = FirefoxOptions()
    options.headless = True
    options.binary_location = TOR_FIREFOX_BIN
    options.set_preference("profile", TOR_PROFILE_PATH)
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    return driver

def start_regular_browser():
    options = ChromeOptions()
    options.headless = True
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def test_browser(driver, url):
    try:
        driver.get(url)
        time.sleep(5)
        print(f"Title: {driver.title}")
    except Exception as e:
        print("Błąd podczas testu:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    url_testowa = "https://browserleaks.com"

    print("=== Test Tor Browser ===")
    tor = start_tor_browser()
    test_browser(tor, url_testowa)

    print("=== Test Regular Browser ===")
    regular = start_regular_browser()
    test_browser(regular, url_testowa)
