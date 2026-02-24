def get_config(source_site):
    return CONFIG.get(source_site)

CONFIG = {
    "amiunique": {
        "critical": [
            "webgl_renderer", 
            "webgl_vendor", 
            "canvas", 
            "frequency_analyser"
        ],
        "high": [
            "use_of_local_storage", 
            "use_of_indexeddb", 
            "audio_context", 
            "permissions"
        ],
        "medium": [
            "screen_width", 
            "screen_height", 
            "timezone", 
            "hardware_concurrency", 
            "device_memory", 
            "platform"
        ],
        "low": [
            "user_agent", 
            "accept", 
            "content_language", 
            "do_not_track"
        ]
    },
    "browserleaks_dns": {
        "critical": [
            "ip_address",
            "isp",
            "location.city",
            "location.country"
        ],
        "high": [
            "dns_server_count",
            "dns_test_summary.isp_count",
            "dns_test_summary.location_count"
        ],
        "medium": [
            "dns_test_summary.servers_found"
        ],
        "low": [
            "user_agent"
        ]
    },
    "browserleaks_ip": {
        "critical": [
            "ip", 
            "ipv6", 
            "coordinates", 
            "network", 
            "hostname"
        ],
        "high": [
            "isp", 
            "organization", 
            "city", 
            "relays"
        ],
        "medium": [
            "timezone", 
            "state_region", 
            "country", 
            "usage_type", 
            "local_time"
        ],
        "low": [
            "user-agent", 
            "accept", 
            "accept-language", 
            "accept-encoding", 
            "upgrade-insecure-requests", 
            "request", 
            "host", 
            "sec-fetch-dest", 
            "sec-fetch-mode", 
            "priority"
        ]
    },
    "browserleaks_javascript": {
        "critical": [
            "screen_resolution",
            "timezone",
            "system_time",
            "datetimeformat",
            "tolocalestring"
        ],
        "high": [
            "hardwareconcurrency",
            "devicememory",
            "vendor",
            "buildid",
            "oscpu",
            "platform",
            "webdriver"
        ],
        "medium": [
            "locale",
            "language",
            "languages",
            "cookieenabled",
            "pdfviewerenabled",
            "globalprivacycontrol"
        ],
        "low": [
            "useragent",
            "appversion",
            "appname",
            "product",
            "productsub",
            "javascript_enabled",
            "inline_scripts",
            "same_origin_scripts",
            "third_party_scripts",
            "donottrack",
            "document_referrer"
        ]
    },
    "browserscan": {
        "critical": [
            "ip",
            "webrtc",
            "webrtc_stun",
            "canvas",
            "audio",
            "fonts",
            "visitor_id",
            "location",
            "latitude",
            "longitude"
        ],
        "high": [
            "isp",
            "proxy",
            "dns_leak",
            "bot_detection",
            "webgl_report",
            "client_rects",
            "screen_resolution",
            "available_screen_size",
            "hardware_concurrency",
            "time_zone",
            "time_from_javascript"
        ],
        "medium": [
            "country",
            "region",
            "city",
            "postal_code",
            "ip_time_zone",
            "time_zone_based_on_ip",
            "device_memory",
            "color_depth",
            "fonts_list"
        ],
        "low": [
            "browser",
            "browser_version",
            "os",
            "platform",
            "header",
            "language",
            "languages",
            "accept-language_header",
            "incognito_mode",
            "do_not_track",
            "pdf_viewer",
            "cookie"
        ]
    },
    "creepjs": {
        "critical": [
            "workerScope.$hash",
            "navigator.$hash",
            "windowFeatures.$hash",
            "headless.$hash",
            "offlineAudioContext.$hash",
            "canvasWebgl.$hash",
            "workerScope.timezoneLocation",
            "workerScope.webglRenderer",
            "workerScope.gpu.compressedGPU"
        ],
        "high": [
            "headless.headlessRating",
            "headless.likeHeadlessRating",
            "headless.stealthRating",
            "navigator.lied",
            "workerScope.lied",
            "screen.lied",
            "lies.totalLies",
            "offlineAudioContext.totalUniqueSamples",
            "navigator.hardwareConcurrency",
            "navigator.deviceMemory"
        ],
        "medium": [
            "intl.dateTimeFormat",
            "intl.locale",
            "workerScope.locale",
            "workerScope.timezoneOffset",
            "screen.width",
            "screen.height",
            "cssMedia.mediaCSS.device-aspect-ratio",
            "navigator.platform",
            "navigator.oscpu"
        ],
        "low": [
            "workerScope.userAgentEngine",
            "workerScope.system",
            "workerScope.device",
            "navigator.userAgentParsed",
            "navigator.vendor",
            "navigator.webdriver",
            "navigator.doNotTrack",
            "navigator.globalPrivacyControl"
        ]
    },
    "deviceinfo": {
        "critical": [
            "IP Address (WAN)",
            "Hostname",
            "Latitude & Longitude",
            "ISP",
            "Nameservers",
            "Local IP Address (LAN)"
        ],
        "high": [
            "True Operating System Core",
            "True Browser Core",
            "Tor IP Address",
            "VPN IP Address",
            "Proxy IP Address",
            "Canvas Fingerprinting",
            "AudioContext Fingerprinting",
            "System Time Zone",
            "Local Time Zone"
        ],
        "medium": [
            "Device Type / Model",
            "Operating System",
            "Browser",
            "Country",
            "Region",
            "City",
            "Wide Area Network (WAN)",
            "System (Live)",
            "Local (Live)"
        ],
        "low": [
            "User Agent",
            "Languages",
            "Fingerprinting Resistance",
            "Canvas",
            "AudioContext",
            "HTTP Request Headers",
            "Local Area Network (LAN) (Live)"
        ]
    },
    "fingerprint_scan": {
        "critical": [
            "IP Address Information.IP Address",
            "IP Address Information.ASN",
            "IP Address Information.Timezone",
            "Canvas.Canvas",
            "Math Constants.hash",
            "WebGL Challenge.challenge",
            "WebGL Challenge.parameters",
            "Fonts.Fonts",
            "Keyboard Layout.layout"
        ],
        "high": [
            "Generic Bot Tests.WebDriver",
            "Generic Bot Tests.CDP Check",
            "General Device Information.Hardware Concurrency",
            "General Device Information.Device Memory",
            "General Device Information.Timezone",
            "Screen.Width",
            "Screen.Height",
            "Screen.devicePixelRatio",
            "Screen.innerWidth",
            "Screen.innerHeight",
            "Multimedia Devices.speakers",
            "Multimedia Devices.micros",
            "Multimedia Devices.webcams",
            "Worker Data.Hardware Concurrency",
            "Worker Data.User Agent"
        ],
        "medium": [
            "IP Address Information.Country",
            "IP Address Information.City",
            "IP Address Information.Region",
            "IP Address Information.AS Organization",
            "Network Information.HTTP Protocol",
            "Network Information.TLS Version",
            "Network Information.TLS Cipher",
            "General Device Information.Locale Date",
            "Plugins Information.Number",
            "Mime Types.Number",
            "Media Capabilities.Number",
            "Speech Synthesis Voices.Number of Voices",
            "Fonts.Number"
        ],
        "low": [
            "HTTP Headers.user-agent",
            "HTTP Headers.accept",
            "HTTP Headers.accept-language",
            "HTTP Headers.priority",
            "HTTP Headers.sec-ch-ua",
            "General Device Information.Platform",
            "General Device Information.Is Brave Browser",
            "General Device Information.Has Default Chrome Extension",
            "Screen.colorDepth",
            "Screen.screenOrientationType",
            "Scrollbar.Width",
            "Scrollbar.Height",
            "Audio Codecs.mp3",
            "Audio Codecs.aac",
            "Video Codecs.h264",
            "Video Codecs.webm",
            "Iframe Information.Iframe Overridden",
            "High Entropy Values.architecture",
            "High Entropy Values.bitness"
        ]
    },
    "fingerprintjs": {
        "critical": [
            "visitor_id",
            "entropy_components.canvas.value.geometry",
            "entropy_components.canvas.value.text",
            "entropy_components.audio.value",
            "entropy_components.webGlBasics.value.renderer",
            "entropy_components.webGlBasics.value.vendor",
            "entropy_components.webGlBasics.value.shadingLanguageVersion",
            "entropy_components.fonts.value"
        ],
        "high": [
            "confidence_score",
            "entropy_components.fontPreferences.value.default",
            "entropy_components.fontPreferences.value.apple",
            "entropy_components.fontPreferences.value.serif",
            "entropy_components.fontPreferences.value.sans",
            "entropy_components.fontPreferences.value.mono",
            "entropy_components.fontPreferences.value.system",
            "entropy_components.hardwareConcurrency.value",
            "entropy_components.deviceMemory.value",
            "entropy_components.screenResolution.value",
            "entropy_components.osCpu.value",
            "entropy_components.platform.value",
            "entropy_components.webGlExtensions.value.parameters"
        ],
        "medium": [
            "entropy_components.timezone.value",
            "entropy_components.languages.value",
            "entropy_components.math.value.acos",
            "entropy_components.math.value.acosh",
            "entropy_components.math.value.asin",
            "entropy_components.math.value.asinh",
            "entropy_components.math.value.atanh",
            "entropy_components.math.value.cosh",
            "entropy_components.math.value.sinh",
            "entropy_components.math.value.tanh",
            "entropy_components.math.value.exp",
            "entropy_components.math.value.powPI",
            "entropy_components.plugins.value",
            "entropy_components.vendor.value",
            "entropy_components.vendorFlavors.value",
            "entropy_components.colorGamut.value",
            "entropy_components.dateTimeLocale.value"
        ],
        "low": [
            "user_agent",
            "entropy_components.cookiesEnabled.value",
            "entropy_components.sessionStorage.value",
            "entropy_components.localStorage.value",
            "entropy_components.indexedDB.value",
            "entropy_components.pdfViewerEnabled.value",
            "entropy_components.touchSupport.value.maxTouchPoints",
            "entropy_components.touchSupport.value.touchEvent",
            "entropy_components.forcedColors.value",
            "entropy_components.reducedMotion.value",
            "entropy_components.contrast.value",
            "entropy_components.monochrome.value",
            "entropy_components.hdr.value",
            "entropy_components.audioBaseLatency.value",
            "entropy_components.architecture.value"
        ]
    },
    "ipinfo": {
        "critical": [
            "ip",
            "hostname",
            "loc",
            "org"
        ],
        "high": [
            "city",
            "postal",
            "timezone"
        ],
        "medium": [
            "region",
            "country"
        ],
        "low": [
            "readme"
        ]
    },
    "ipleak": {
        "critical": [
            "ip_address",
            "webrtc_ips",
            "your_ip_addresses.IP",
            "your_ip_addresses.ISP",
            "your_ip_addresses.ASN",
            "your_ip_addresses.Latitude &amp; Longitude",
            "dns_servers"
        ],
        "high": [
            "your_ip_addresses.City",
            "your_ip_addresses.Region",
            "your_ip_addresses.Time Zone",
            "detected_information.Your User Agent",
            "screen_information.Your screen",
            "screen_information.Available screen",
            "http_request_headers.User-Agent"
        ],
        "medium": [
            "your_ip_addresses.Country",
            "detected_information.What language you can accept",
            "detected_information.What document you can accept",
            "system_information.Platform",
            "system_information.Online",
            "plugins_information.Name",
            "mime-types_information.Mime Type"
        ],
        "low": [
            "detected_information.What encoding you can accept",
            "system_information.Cookie enabled",
            "system_information.Java enabled",
            "system_information.Taint enabled",
            "screen_information.Color depth",
            "screen_information.Pixel depth",
            "http_request_headers.Accept-Language",
            "http_request_headers.Sec-Ch-Ua",
            "http_request_headers.Sec-Ch-Ua-Platform",
            "http_request_headers.Sec-Gpc",
            "http_request_headers.Upgrade-Insecure-Requests"
        ]
    },
    "pixelscan": {
        "critical": [
            "webrtc_address.Public IP",
            "ip_address.ISP",
            "webgl_hash.WebGL unmasked vendor",
            "webgl_hash.WebGL unmasked renderer",
            "ip_location.Latitude",
            "ip_location.Longitude"
        ],
        "high": [
            "time.Timezone from Javascript",
            "time.Time from Javascript",
            "time.Time from IP",
            "ip_address.User Type by IP",
            "webgl_hash.WebGL version"
        ],
        "medium": [
            "ip_address.Country",
            "ip_address.City",
            "languages.Languages from Javascript",
            "languages.Accept-Language header"
        ],
        "low": [
            "time.Daylight savings time"
        ]
    }
}