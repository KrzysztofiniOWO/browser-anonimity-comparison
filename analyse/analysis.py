import json
import pathlib
import pandas as pd
import re
import sys
import math

try:
    from .analysis_helper import get_config
except (ImportError, ValueError):
    from analysis_helper import get_config

# REMOVED None from the tuple to avoid 'in <string>' errors
EMPTY = (
    "no value", "not supported", "unknown", "none", "unspecified", 
    "blocked", "detection disabled", "could not detect", 
    "detection blocked", "not detected", ""
)

def load_data(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["data"]

def is_present(v):
    if v is None: 
        return False
    s = str(v).strip().lower()
    if s == "":
        return False
    for phrase in EMPTY:
        # phrase is now always a string, so this won't crash
        if phrase in s:
            return False
    return True

def extract_number(text):
    if not is_present(text): 
        return 0
    s_text = str(text)
    match = re.search(r'\d+', s_text)
    return int(match.group()) if match else 0

def count_elements(text):
    if not is_present(text): return 0
    if isinstance(text, list): return len(text)
    elements = [e for e in re.split(r'[,\n]', str(text)) if e.strip()]
    return len(elements)

def get_nested(data, key):
    for part in key.split('.'):
        if isinstance(data, dict):
            data = data.get(part)
        else:
            return None
    return data

def get_penalty(val, tor_val, weight):
    v_pres = is_present(val)
    t_pres = is_present(tor_val)
    
    v_str = str(val).strip().lower() if val is not None else ""
    t_str = str(tor_val).strip().lower() if tor_val is not None else ""

    if v_str == t_str:
        return 0.0

    if not t_pres and v_pres:
        return 1.2 * weight
    
    if t_pres and v_pres:
        return 1.0 * weight
        
    if t_pres and not v_pres:
        return 0.5 * weight
        
    return 0.2 * weight

def get_header_penalty(val, tor_val, weight):
    if not is_present(val) or not is_present(tor_val):
        return get_penalty(val, tor_val, weight)
    
    v_keys = set(re.findall(r'^([\w-]+):', str(val), re.MULTILINE))
    t_keys = set(re.findall(r'^([\w-]+):', str(tor_val), re.MULTILINE))
    
    extra_headers = v_keys - t_keys
    penalty = len(extra_headers) * 0.5 * weight
    
    if v_keys == t_keys and str(val) != str(tor_val):
        penalty += 0.5 * weight
        
    return min(penalty, weight * 1.5)

def get_base_score(data, tor_data, fields, weight):
    total = 0
    for f in fields:
        val = get_nested(data, f)
        t_val = get_nested(tor_data, f)
        
        if any(x in f.lower() for x in ["header", "accept", "sec-"]):
            total += get_header_penalty(val, t_val, weight)
        else:
            total += get_penalty(val, t_val, weight)
    return total

def get_list_log_penalty(data, tor_data, key_variants, weight, factor):
    for k in key_variants:
        v = get_nested(data, k)
        t = get_nested(tor_data, k)
        if v is not None and t is not None:
            diff = abs(count_elements(v) - count_elements(t))
            if diff > 0:
                return math.log2(diff + 1) * factor * weight
    return 0

def analyze_browser(browser_name, data, tor_data, conf):
    score_crit = get_base_score(data, tor_data, conf.get("critical", []), 10.0)
    score_high = get_base_score(data, tor_data, conf.get("high", []), 7.0)
    score_med  = get_base_score(data, tor_data, conf.get("medium", []), 4.0)
    score_low  = get_base_score(data, tor_data, conf.get("low", []), 2.0)

    score_crit += get_list_log_penalty(data, tor_data, ["webgl_parameters", "WebGL Challenge.parameters"], 10.0, 1.2)
    score_high += get_list_log_penalty(data, tor_data, ["list_of_fonts_js", "fonts_list", "Fonts.Fonts"], 7.0, 1.0)
    score_high += get_list_log_penalty(data, tor_data, ["list_of_plugins", "plugins_information.Name"], 7.0, 1.5)

    total_index = (score_crit * 0.50) + (score_high * 0.25) + (score_med * 0.15) + (score_low * 0.10)

    privacy_pct = round(max(0, 100 - (total_index * 2.2)), 2)

    return {
        "Browser": browser_name,
        "Score_Critical": round(score_crit, 2),
        "Score_High": round(score_high, 2),
        "Score_Medium": round(score_med, 2),
        "Score_Low": round(score_low, 2),
        "Fingerprint_Intensity": round(total_index, 2),
        "Privacy_Score_Pct": privacy_pct
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
            print(f"Error: Tor baseline missing at {files['tor']}")
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
        
        print(f"\n--- ANALYSIS COMPLETED: {source_site.upper()} ---")
        print(df.to_string())
        print(f"\n[OK] Results saved to: {output_path}")

    except Exception as e:
        print(f"[ERROR] Error during analysis: {e}")

if __name__ == "__main__":
    main()