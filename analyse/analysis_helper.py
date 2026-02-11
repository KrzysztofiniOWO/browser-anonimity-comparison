CONFIG = {
    "amiunique": {
        "critical": ["webgl_renderer", "webgl_vendor", "canvas", "frequency_analyser"],
        "high": ["use_of_local_storage", "use_of_indexeddb", "audio_context", "permissions"],
        "medium": ["screen_width", "screen_height", "timezone", "hardware_concurrency", "device_memory", "platform"],
        "low": ["user_agent", "accept", "content_language", "do_not_track"]
    },
    "browserleaks_ip": {
        "critical": ["ip", "ipv6", "coordinates", "network"],
        "high": ["isp", "organization", "hostname"],
        "medium": ["timezone", "state_region", "city"],
        "low": ["user-agent", "accept-language", "accept-encoding", "upgrade-insecure_requests"]
    }
}

def get_config(source_site):
    return CONFIG.get(source_site)