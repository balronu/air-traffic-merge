"""Constants for Air Traffic Merge."""
from __future__ import annotations

DOMAIN = "air_traffic_merge"
PLATFORMS = ["sensor"]

CONF_FR24_ENTITY = "fr24_entity"
CONF_ADSB_URL = "adsb_url"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MAX_ITEMS = "max_items"
CONF_TRACKED_CALLSIGNS = "tracked_callsigns"
CONF_TRACKED_REGISTRATIONS = "tracked_registrations"

DEFAULT_SCAN_INTERVAL = 10
DEFAULT_MAX_ITEMS = 50

ATTR_FLIGHTS = "flights"
ATTR_LAST_UPDATE = "last_update"
ATTR_STATUS = "status"
ATTR_FR24_COUNT = "fr24_count"
ATTR_ADSB_COUNT = "adsb_count"
ATTR_MERGED_COUNT = "merged_count"
ATTR_COUNTS = "counts"
ATTR_DEBUG = "debug"
ATTR_TRACKED_PRESENT = "tracked_present"

CATEGORY_MEDICAL = "🚑 Medical"
CATEGORY_MILITARY = "🪖 Militär"
CATEGORY_MILITARY_FIGHTER = "⚔️ Militär – Fighter"
CATEGORY_MILITARY_TANKER = "⛽ Militär – Tanker"
CATEGORY_MILITARY_TRANSPORT = "📦 Militär – Transport"
CATEGORY_MILITARY_ISR = "📡 Militär – Aufklärung"
CATEGORY_MILITARY_HELI = "🪖 Militär – Helikopter"
CATEGORY_HELI = "🚁 Helikopter"
CATEGORY_BUSINESS = "💼 Business Jet"
CATEGORY_GA = "🛩️ General Aviation"
CATEGORY_CIVIL = "✈️ Zivil"
