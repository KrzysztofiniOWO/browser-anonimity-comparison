import json
import pathlib
import pandas as pd
import re
import sys

try:
    from .analysis_helper import get_config
except (ImportError, ValueError):
    from analysis_helper import get_config

EMPTY = ("No value", "Not supported", "Unknown", "None", "unspecified", None, "")

def load_data(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["data"]

def is_present(v):
    return v not in EMPTY and str(v).strip() != ""

def extract_number(text):
    if not is_present(text): return 0
    match = re.search(r'\d+', str(text))
    return int(match.group()) if match else 0

def count_elements(text):
    if not is_present(text): return 0
    if isinstance(text, list): return len(text)
    return len([line for line in str(text).split('\n') if line.strip()])

def get_nested(data, key):
    for part in key.split('.'):
        if isinstance(data, dict):
            data = data.get(part)
        else:
            return None
    return data

def get_penalty(val, tor_val, weight):
    if isinstance(val, (list, dict)) or isinstance(tor_val, (list, dict)):
        v_str, t_str = str(val), str(tor_val)
    else:
        v_str, t_str = str(val).strip(), str(tor_val).strip()
    
    if v_str == t_str: return 0.0
    if not is_present(tor_val) and is_present(val): return 1.0 * weight
    return 0.5 * weight

def analyze_browser(browser_name, data, tor_data, conf):
    score_crit = sum(get_penalty(get_nested(data, f), get_nested(tor_data, f), 10.0) for f in conf.get("critical", []))
    score_high = sum(get_penalty(get_nested(data, f), get_nested(tor_data, f), 7.0) for f in conf.get("high", []))
    score_med = sum(get_penalty(get_nested(data, f), get_nested(tor_data, f), 4.0) for f in conf.get("medium", []))
    score_low = sum(get_penalty(get_nested(data, f), get_nested(tor_data, f), 2.0) for f in conf.get("low", []))

    if get_nested(data, "webgl_parameters"):
        w_diff = abs(extract_number(get_nested(data, "webgl_parameters")) - extract_number(get_nested(tor_data, "webgl_parameters")))
        score_crit += (w_diff * 0.5)

    if get_nested(data, "list_of_fonts_js"):
        f_diff = abs(extract_number(get_nested(data, "list_of_fonts_js")) - extract_number(get_nested(tor_data, "list_of_fonts_js")))
        score_high += (f_diff * 0.3)
    
    if get_nested(data, "list_of_plugins"):
        p_diff = abs(count_elements(get_nested(data, "list_of_plugins")) - count_elements(get_nested(tor_data, "list_of_plugins")))
        score_high += (p_diff * 1.0)

    total_index = (score_crit * 0.40) + (score_high * 0.30) + (score_med * 0.20) + (score_low * 0.10)

    return {
        "Browser": browser_name,
        "Score_Critical": round(score_crit, 2),
        "Score_High": round(score_high, 2),
        "Score_Medium": round(score_med, 2),
        "Score_Low": round(score_low, 2),
        "Fingerprint_Intensity": round(total_index, 2),
        "Privacy_Score_Pct": round(max(0, 100 - (total_index / 2)), 2)
    }

def main(source_site=None):
    if source_site is None:
        if len(sys.argv) < 2:
            print("Usage: python analysis.py <site_name>")
            return
        source_site = sys.argv[1]

    conf = get_config(source_site)

    if not conf:
        print(f"Error: Configuration for site '{source_site}' not found.")
        return

    base_path = pathlib.Path(__file__).parent.parent / "data" / source_site
    
    files = {
        "chrome":  base_path / "chrome" / "Chrome.json",
        "firefox": base_path / "firefox" / "Firefox.json",
        "edge":    base_path / "edge" / "Edge.json",
        "brave":   base_path / "brave" / "Brave.json",
        "tor":     base_path / "torbrowser" / "TorBrowser.json",
    }

    try:
        if not files["tor"].exists():
            print(f"Error: Tor baseline file for {source_site} not found at {files['tor']}")
            return

        tor_baseline = load_data(files["tor"])
        results = []

        for name, path in files.items():
            if path.exists():
                results.append(analyze_browser(name, load_data(path), tor_baseline, conf))

        df = pd.DataFrame(results).set_index("Browser")
        output_dir = pathlib.Path(__file__).parent.parent / "results"
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / f"results_{source_site}.csv"
        df.to_csv(output_path)
        
        print(f"\n--- ANALYSIS RESULTS: {source_site.upper()} ---")
        print(df.to_string())
        print(f"\n[OK] Results saved to: {output_path}")

    except Exception as e:
        print(f"[ERROR] An exception occurred during analysis: {e}")

if __name__ == "__main__":
    main()