import json
import pathlib
import pandas as pd
import ipaddress

EMPTY = ("No value", "Not supported", "Unknown", None)

def load_data(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return raw["data"]

def is_present(value):
    return value not in EMPTY and str(value).strip() != ""

def ip_metrics(data):
    ipv4 = data.get("ip")
    ipv6 = data.get("ipv6")

    return {
        "ipv4_present": int(is_present(ipv4)),
        "ipv6_present": int(is_present(ipv6)),
        "dual_stack": int(is_present(ipv4) and is_present(ipv6))
    }

def score_ip_A(m):
    return (
        m["ipv4_present"] * 2.0 +
        m["ipv6_present"] * 2.0 +
        m["dual_stack"] * 2.0
    )

def geo_metrics(data):
    fields = ["country", "state_region", "city", "coordinates"]

    return {
        "geo_field_count": sum(is_present(data.get(f)) for f in fields),
        "coordinates_present": int(is_present(data.get("coordinates")))
    }

def score_geo_B(m):
    return (
        m["geo_field_count"] * 1.5 +
        m["coordinates_present"] * 2.0
    )

def network_metrics(data):
    fields = ["isp", "organization", "network", "usage_type"]

    tor_indicator = data.get("network", "").lower()

    return {
        "network_field_count": sum(is_present(data.get(f)) for f in fields),
        "tor_indicator": int("tor" in tor_indicator)
    }

def score_network_C(m):
    return (
        m["network_field_count"] * 1.5 -
        m["tor_indicator"] * 3.0
    )

def http_metrics(data):
    headers = [
        "user-agent", "accept", "accept-language", "accept-encoding",
        "upgrade-insecure-requests", "sec-fetch-dest",
        "sec-fetch-mode", "sec-fetch-user", "priority"
    ]

    return {
        "http_header_count": sum(is_present(data.get(h)) for h in headers),
        "user_agent_length": len(data.get("user-agent", "")) if is_present(data.get("user-agent")) else 0
    }

def score_http_D(m):
    return (
        m["http_header_count"] * 1.0 +
        m["user_agent_length"] * 0.01
    )

def time_metrics(data):
    return {
        "timezone_present": int(is_present(data.get("timezone"))),
        "local_time_present": int(is_present(data.get("local_time")))
    }

def score_time_E(m):
    return (
        m["timezone_present"] * 1.5 +
        m["local_time_present"] * 1.5
    )

def request_metrics(data):
    fields = ["host", "request", "relays"]

    return {
        "request_field_count": sum(is_present(data.get(f)) for f in fields),
        "tor_relay_flag": int("not identified" not in str(data.get("relays", "")).lower())
    }

def score_request_F(m):
    return (
        m["request_field_count"] * 1.0 +
        m["tor_relay_flag"] * 2.0
    )

def extract_all_metrics(browser, data):
    metrics = {"browser": browser}

    metrics.update(ip_metrics(data))
    metrics.update(geo_metrics(data))
    metrics.update(network_metrics(data))
    metrics.update(http_metrics(data))
    metrics.update(time_metrics(data))
    metrics.update(request_metrics(data))

    metrics["score_A_ip"] = score_ip_A(metrics)
    metrics["score_B_geo"] = score_geo_B(metrics)
    metrics["score_C_network"] = score_network_C(metrics)
    metrics["score_D_http"] = score_http_D(metrics)
    metrics["score_E_time"] = score_time_E(metrics)
    metrics["score_F_request"] = score_request_F(metrics)

    metrics["overall_network_fingerprinting_score"] = (
        metrics["score_A_ip"] * 0.20 +
        metrics["score_B_geo"] * 0.25 +
        metrics["score_C_network"] * 0.20 +
        metrics["score_D_http"] * 0.15 +
        metrics["score_E_time"] * 0.10 +
        metrics["score_F_request"] * 0.10
    )

    return metrics

# ---------- MAIN ----------
browser_files = {
    "chrome": pathlib.Path("data/browserleaks_ip/chrome/Chrome.json"),
    "firefox": pathlib.Path("data/browserleaks_ip/firefox/Firefox.json"),
    "tor": pathlib.Path("data/browserleaks_ip/torbrowser/TorBrowser.json"),
}

results = []
for browser, path in browser_files.items():
    data = load_data(path)
    results.append(extract_all_metrics(browser, data))

df = pd.DataFrame(results).set_index("browser")
print(df)

output_dir = pathlib.Path("results")
output_dir.mkdir(exist_ok=True)

output_path = output_dir / "browserleaks_ip_metrics.csv"
df.to_csv(output_path)

print(f"[OK] Wyniki zapisane do: {output_path.resolve()}")
