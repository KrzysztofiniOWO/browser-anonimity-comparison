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
    return len([line for line in str(text).split('\n') if line.strip()])

def get_penalty(val, tor_val, weight):
    v_str, t_str = str(val).strip(), str(tor_val).strip()
    if v_str == t_str: return 0.0
    if not is_present(tor_val) and is_present(val): return 1.0 * weight
    return 0.5 * weight

def analyze_browser(browser_name, data, tor_data, conf):
    score_crit = sum(get_penalty(data.get(f), tor_data.get(f), 10.0) for f in conf.get("critical", []))
    score_high = sum(get_penalty(data.get(f), tor_data.get(f), 7.0) for f in conf.get("high", []))
    score_med = sum(get_penalty(data.get(f), tor_data.get(f), 4.0) for f in conf.get("medium", []))
    score_low = sum(get_penalty(data.get(f), tor_data.get(f), 2.0) for f in conf.get("low", []))

    if "webgl_parameters" in data:
        w_diff = abs(extract_number(data.get("webgl_parameters")) - extract_number(tor_data.get("webgl_parameters")))
        score_crit += (w_diff * 0.5)

    if "list_of_fonts_js" in data:
        f_diff = abs(extract_number(data.get("list_of_fonts_js")) - extract_number(tor_data.get("list_of_fonts_js")))
        score_high += (f_diff * 0.3)
    
    if "list_of_plugins" in data:
        p_diff = abs(count_elements(data.get("list_of_plugins")) - count_elements(tor_data.get("list_of_plugins")))
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
            print("Użycie: python analysis.py <nazwa_strony>")
            return
        source_site = sys.argv[1]

    conf = get_config(source_site)

    if not conf:
        print(f"Błąd: Brak konfiguracji dla strony '{source_site}'")
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
            print(f"Błąd: Brak pliku wzorcowego Tor dla {source_site} w {files['tor']}")
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
        
        print(f"\n--- WYNIKI DLA: {source_site.upper()} ---")
        print(df.to_string())
        print(f"\n[OK] Zapisano w: {output_path}")

    except Exception as e:
        print(f"[ERROR] Wystąpił błąd podczas analizy: {e}")

if __name__ == "__main__":
    main()