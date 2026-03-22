from __future__ import annotations

DOMAIN = "air_traffic_merge"
PLATFORMS: list[str] = ["sensor", "binary_sensor"]

CONF_ADSB_URL = "adsb_url"
CONF_FR24_ENTITY = "fr24_entity"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MAX_ITEMS = "max_items"
CONF_TRACKED_CALLSIGNS = "tracked_callsigns"
CONF_TRACKED_REGISTRATIONS = "tracked_registrations"

DEFAULT_SCAN_INTERVAL = 15
DEFAULT_MAX_ITEMS = 50

ATTR_FLIGHTS = "flights"
ATTR_COUNTS = "counts"
ATTR_STATUS = "status"
ATTR_LAST_UPDATE = "last_update"
ATTR_FR24_COUNT = "fr24_count"
ATTR_ADSB_COUNT = "adsb_count"
ATTR_MERGED_COUNT = "merged_count"
ATTR_TRACKED_PRESENT = "tracked_present"
ATTR_DEBUG = "debug"

CATEGORY_MEDICAL = "medical"
CATEGORY_MILITARY = "military"
CATEGORY_MILITARY_FIGHTER = "military_fighter"
CATEGORY_MILITARY_TANKER = "military_tanker"
CATEGORY_MILITARY_TRANSPORT = "military_transport"
CATEGORY_MILITARY_ISR = "military_isr"
CATEGORY_MILITARY_HELI = "military_helicopter"
CATEGORY_HELI = "helicopter"
CATEGORY_BUSINESS = "business"
CATEGORY_GA = "general_aviation"
CATEGORY_CIVIL = "civil"
