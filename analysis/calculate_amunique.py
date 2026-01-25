import json
import pathlib
import pandas as pd
import math

EMPTY = ("No value", "Not supported", "Unknown", None)

def load_browser_data(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return raw["data"]

def is_present(value):
    return value not in EMPTY and str(value).strip() != ""

def parse_multiline(value):
    if not is_present(value):
        return []
    return [v.strip() for v in value.split("\n") if v.strip()]

def http_metrics(data):
    headers = [
        "user_agent", "accept", "content_encoding",
        "content_language", "upgrade_insecure_requests", "do_not_track"
    ]

    ua = data.get("user_agent")

    return {
        "http_header_count": sum(is_present(data.get(h)) for h in headers),
        "user_agent_length": len(ua) if is_present(ua) else 0,
        "user_agent_standardized": int(is_present(ua) and "Tor Browser" in ua)
    }

def score_http_A(m):
    return (
        m["http_header_count"] * 1.0 +
        m["user_agent_length"] * 0.01 -
        m["user_agent_standardized"] * 3.0
    )

def navigator_metrics(data):
    hw_features = ["hardware_concurrency", "device_memory"]
    binary_features = ["java_enabled"]

    nav_props = data.get("navigator_properties", "")

    return {
        "navigator_property_count": int(nav_props.split()[0]) if nav_props else 0,
        "hardware_feature_count": sum(is_present(data.get(f)) for f in hw_features),
        "binary_feature_count": sum(is_present(data.get(f)) for f in binary_features)
    }

def score_navigator_B(m):
    return (
        m["navigator_property_count"] * 0.1 +
        m["hardware_feature_count"] * 1.5 +
        m["binary_feature_count"] * 0.5
    )

def graphics_metrics(data):
    webgl_params = parse_multiline(data.get("webgl_parameters"))
    renderer = data.get("webgl_renderer", "")

    software_renderer = int(
        is_present(renderer) and any(x in renderer.lower() for x in ["swiftshader", "llvmpipe", "software"])
    )

    return {
        "webgl_field_count": sum(is_present(data.get(k)) for k in ["canvas", "webgl_vendor", "webgl_renderer"]),
        "webgl_extension_count": len(webgl_params),
        "software_renderer": software_renderer
    }

def score_graphics_C(m):
    return (
        m["webgl_field_count"] * 2.0 +
        m["webgl_extension_count"] * 0.3 -
        m["software_renderer"] * 2.0
    )

def audio_metrics(data):
    audio_formats = parse_multiline(data.get("audio_formats"))
    audio_context = parse_multiline(data.get("audio_context"))

    return {
        "audio_format_count": len(audio_formats),
        "audio_context_param_count": len(audio_context),
        "audio_api_available": int(is_present(data.get("audio_context")))
    }

def score_audio_D(m):
    return (
        m["audio_format_count"] * 0.5 +
        m["audio_context_param_count"] * 0.2 +
        m["audio_api_available"] * 2.0
    )

def screen_metrics(data):
    try:
        width = int(data.get("screen_width", 0))
        height = int(data.get("screen_height", 0))
        area = width * height
    except Exception:
        area = 0

    timezone = data.get("timezone", "")

    return {
        "screen_area": area,
        "screen_depth": int(data.get("screen_depth", 0)) if is_present(data.get("screen_depth")) else 0,
        "timezone_non_utc": int(is_present(timezone) and "UTC" not in timezone)
    }

def score_screen_E(m):
    return (
        (m["screen_area"] / 1_000_000) +
        m["screen_depth"] * 0.2 +
        m["timezone_non_utc"] * 1.0
    )

def storage_metrics(data):
    storage_flags = [
        data.get("cookies_enabled"),
        data.get("use_of_local_storage"),
        data.get("use_of_session_storage"),
        data.get("use_of_indexeddb")
    ]

    count = sum(v == "Yes" for v in storage_flags)

    return {
        "storage_mechanism_count": count,
        "fingerprint_persistence_potential": int(count >= 2)
    }

def score_storage_F(m):
    return (
        m["storage_mechanism_count"] * 1.5 +
        m["fingerprint_persistence_potential"] * 2.0
    )

def permission_metrics(data):
    permissions = parse_multiline(data.get("permissions"))
    granted = [p for p in permissions if "granted" in p]

    sensors = ["accelerometer", "gyroscope", "battery", "connection"]

    return {
        "permission_count": len(permissions),
        "granted_permission_count": len(granted),
        "sensor_api_count": sum(is_present(data.get(s)) for s in sensors)
    }

def score_permissions_G(m):
    return (
        m["permission_count"] * 0.2 +
        m["granted_permission_count"] * 0.5 +
        m["sensor_api_count"] * 1.5
    )

def extract_all_metrics(browser, data):
    metrics = {"browser": browser}

    metrics.update(http_metrics(data))
    metrics.update(navigator_metrics(data))
    metrics.update(graphics_metrics(data))
    metrics.update(audio_metrics(data))
    metrics.update(screen_metrics(data))
    metrics.update(storage_metrics(data))
    metrics.update(permission_metrics(data))

    metrics["score_A_http"] = score_http_A(metrics)
    metrics["score_B_js"] = score_navigator_B(metrics)
    metrics["score_C_graphics"] = score_graphics_C(metrics)
    metrics["score_D_audio"] = score_audio_D(metrics)
    metrics["score_E_screen"] = score_screen_E(metrics)
    metrics["score_F_storage"] = score_storage_F(metrics)
    metrics["score_G_permissions"] = score_permissions_G(metrics)

    metrics["overall_fingerprinting_score"] = (
        metrics["score_A_http"] * 0.10 +
        metrics["score_B_js"] * 0.15 +
        metrics["score_C_graphics"] * 0.25 +
        metrics["score_D_audio"] * 0.15 +
        metrics["score_E_screen"] * 0.10 +
        metrics["score_F_storage"] * 0.10 +
        metrics["score_G_permissions"] * 0.15
    )

    return metrics

browser_files = {
    "chrome": pathlib.Path("data/amiunique/chrome/Chrome.json"),
    "firefox": pathlib.Path("data/amiunique/firefox/Firefox.json"),
    "tor": pathlib.Path("data/amiunique/torbrowser/TorBrowser.json"),
}

results = []
for browser, path in browser_files.items():
    data = load_browser_data(path)
    results.append(extract_all_metrics(browser, data))

df = pd.DataFrame(results).set_index("browser")
print(df)

output_dir = pathlib.Path("results")
output_dir.mkdir(exist_ok=True)

output_path = output_dir / "amiunique_metrics.csv"
df.to_csv(output_path)

print(f"[OK] Wyniki zapisane do: {output_path.resolve()}")
