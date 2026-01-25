import datetime
from pathlib import Path
import json
import os
import logging

#----------PATHS-----------

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
HEADLESS = os.environ.get("HEADLESS", "1") != "0"
HEADLESS_TBB = os.environ.get("HEADLESS_TBB", "1") != "0"

TOR_BROWSER_DIR = os.environ.get("TOR_BROWSER_DIR", None)
TOR_BROWSER_BINARY = os.environ.get("TOR_BROWSER_BINARY", "/home/kali/Magisterka/tor-browser/Browser/firefox")
FIREFOX_BINARY = os.environ.get("FIREFOX_BINARY", "/usr/bin/firefox")
CHROME_BINARY = os.environ.get("CHROME_BINARY", "/usr/bin/chromium-browser")

#----------LOGGING-----------

MODULE_LEVEL = 25
SAVE_LEVEL = 26
FINISH_LEVEL = 27

logging.addLevelName(MODULE_LEVEL, "MODULE")
logging.addLevelName(SAVE_LEVEL, "SAVE")
logging.addLevelName(FINISH_LEVEL, "FINISH")

def module(self, message, *args, **kwargs):
    if self.isEnabledFor(MODULE_LEVEL):
        self._log(MODULE_LEVEL, message, args, **kwargs)

def save(self, message, *args, **kwargs):
    if self.isEnabledFor(SAVE_LEVEL):
        self._log(SAVE_LEVEL, message, args, **kwargs)

def finish(self, message, *args, **kwargs):
    if self.isEnabledFor(FINISH_LEVEL):
        self._log(FINISH_LEVEL, message, args, **kwargs)

logging.Logger.module = module
logging.Logger.save = save
logging.Logger.finish = finish

def setup_logger(level=logging.INFO, log_file="logs/app.log"):

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("project_logger")

    if not logger.handlers:
        logger.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

logger = setup_logger()

#----------HELPER FUNCTIONS----------

def getDatetimeNow():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds")

def replaceDatetimeSeparators(ts_iso):
    return ts_iso.replace(":", "-")

def saveAsJson(browser_name, data, category):
    folder = (DATA_DIR / category / browser_name.lower()).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    fname = folder / f"{browser_name}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.save(f"JSON saved to: {fname}")
    return str(fname)

def determineTorBrowserDir():
    if TOR_BROWSER_DIR and os.path.isdir(TOR_BROWSER_DIR):
        return TOR_BROWSER_DIR
    if TOR_BROWSER_BINARY and os.path.isfile(TOR_BROWSER_BINARY):
        cand = os.path.dirname(os.path.dirname(TOR_BROWSER_BINARY))
        if os.path.isdir(cand):
            return cand
    return None

def normalizeLabel(label: str, mapping: dict = None) -> str:
    label = label.strip()

    if mapping and label in mapping:
        return mapping[label]

    return (
        label.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
    )