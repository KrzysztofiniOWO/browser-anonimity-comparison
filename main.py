from scripts import (
    get_amiunique_data,
    get_browserleaks_DNS_data,
    get_browserleaks_IP_data,
    get_browserleaks_JS_data,
    get_browserscan_data,
    get_creepjs_data,
    get_deviceinfo_data,
    get_fingerprint_scan_data,
    get_fingerprintJS_data,
    get_ipinfo_data,
    get_ipleak_data,
    get_pixelscan_data
)

from analyse import (
    analysis
)

def main():
    # Funtions to scrap data for every webpage
    # get_amiunique_data.main()
    # get_browserleaks_DNS_data.main()
    # get_browserleaks_IP_data.main()
    # get_browserleaks_JS_data.main()
    # get_browserscan_data.main()
    # get_creepjs_data.main()
    # get_deviceinfo_data.main()
    # get_fingerprint_scan_data.main()
    # get_fingerprintJS_data.main()
    # get_ipinfo_data.main()
    # get_ipleak_data.main()
    # get_pixelscan_data.main()

    #Functions to analyze data for every webpage
    analysis.main("amiunique")
    analysis.main("browserleaks_dns")
    analysis.main("browserleaks_ip")
    analysis.main("browserleaks_javascript")
    analysis.main("browserscan")
    analysis.main("creepjs")
    analysis.main("deviceinfo")
    analysis.main("fingerprint_scan")
    analysis.main("fingerprintjs")
    analysis.main("ipinfo")
    analysis.main("ipleak")
    analysis.main("pixelscan")

if __name__ == "__main__":
    main()