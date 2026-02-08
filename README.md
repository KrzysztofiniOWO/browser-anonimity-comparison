## Browser Fingerprinting Data Collection

This project collects and aggregates browser fingerprinting and device information from multiple online services. It allows researchers and developers to analyze how different browsers and environments reveal information about a user. The collected data includes HTTP headers, IP information, JavaScript fingerprinting, device characteristics, media capabilities, WebGL details, fonts, canvas hashes, and more.

By running these scripts, you can obtain structured JSON data per browser and per service, which can be used for security research, anonymity evaluation, or testing anti-fingerprinting measures.

## Supported fingerprinting services

The project automatically collects browser fingerprinting and network-related data from the following services.

### AmIUnique  
Provides an analysis of browser uniqueness based on device characteristics, system configuration, and JavaScript-exposed attributes.

### BrowserLeaks DNS  
Detects DNS leaks and analyzes the DNS resolvers used by the browser.

### BrowserLeaks IP  
Collects information about the public IP address, connection protocol, and potential network leaks.

### BrowserLeaks JavaScript  
Gathers data exposed via JavaScript APIs, including WebGL, Canvas, AudioContext, and environment properties.

### BrowserScan  
Performs a comprehensive browser fingerprint analysis covering hardware, software, network properties, and bot-detection tests.

### CreepJS  
Conducts advanced browser fingerprinting with a focus on consistency, entropy, and resistance to spoofing techniques.

### DeviceInfo  
Provides basic information about the device and operating system as detected from the client side.

### Fingerprint Scan  
Generates a detailed browser fingerprint including HTTP headers, WebGL, media capabilities, fonts, canvas, and bot-detection indicators.

### FingerprintJS  
Generates a browser identifier and analyzes entropy components used for fingerprinting.

### IPInfo  
Retrieves geolocation and network metadata associated with the public IP address.

### IPLeak  
Tests for potential IP leaks, including WebRTC and DNS-based disclosures.

### PixelScan  
Analyzes pixel-level rendering behavior to detect subtle fingerprinting differences across browsers and systems.

### How to Launch and Set Paths

To run the project You need to set paths for browsers and drivers according to your installation. I run the script on Ubuntu virtual machine for reference. 

To use the script you can either use main.py and select tests you want to run there or run each module fron scripts directory separately. 

```python
from pathlib import Path
import os

# Project directories
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Headless mode (default enabled, can be disabled via environment variables)
HEADLESS = os.environ.get("HEADLESS", "1") != "0"
HEADLESS_TBB = os.environ.get("HEADLESS_TBB", "1") != "0"

# Browser paths (change if installed elsewhere)
TOR_BROWSER_DIR = os.environ.get("TOR_BROWSER_DIR", None)
TOR_BROWSER_BINARY = os.environ.get("TOR_BROWSER_BINARY", "/home/kali/Magisterka/tor-browser/Browser/firefox")
FIREFOX_BINARY = os.environ.get("FIREFOX_BINARY", "/usr/bin/firefox")
CHROME_BINARY = os.environ.get("CHROME_BINARY", "/usr/bin/chromium-browser")
EDGE_BINARY = os.environ.get("EDGE_BINARY", "/usr/bin/microsoft-edge")
BRAVE_BINARY = os.environ.get("BRAVE_BINARY", "/usr/bin/brave-browser")

# WebDriver paths
CHROMEDRIVER = "/usr/bin/chromedriver"
MSEDGEDRIVER = "/usr/local/bin/msedgedriver"
```

### Output Structure

After running the scripts, all data is saved inside the `data` folder at the root of the repository. Each service or website test creates its own subfolder under `data` according to the category:

- `data/fingerprintjs/<browser>/` contains JSON files with FingerprintJS results for each browser.
- `data/fingerprint_scan/<browser>/` contains JSON files with fingerprint-scan.com results.
- `data/amiunique/`, `data/browserleaks/`, `data/creepjs/`, `data/deviceinfo/`, `data/ipleak/`, `data/pixelscan/`, `data/ipinfo/` contain JSON files structured per browser or test type.

Each JSON file stores a dictionary with `meta` information (timestamp, browser, user agent) and `data` with the scraped or collected values. Logs are saved in `logs/app.log` for tracking the execution of each script.

