DOMAIN = "air_traffic_merge"

CONF_FR24_ENTITY = "fr24_entity"

CONF_ADSB_SOURCE = "adsb_source"   # "url" | "entity"
CONF_ADSB_URL = "adsb_url"
CONF_ADSB_ENTITY = "adsb_entity"

CONF_SCAN_INTERVAL = "scan_interval"

CONF_ENABLE_TRACKING = "enable_tracking"
CONF_TRACK_CALLSIGNS = "track_callsigns"        # comma-separated string
CONF_TRACK_REGISTRATIONS = "track_registrations" # comma-separated string
CONF_TRACK_MODE = "track_mode"                  # "callsign" | "registration" | "both"

DEFAULT_SCAN_INTERVAL = 10  # seconds
DEFAULT_ADSB_SOURCE = "url"
DEFAULT_ENABLE_TRACKING = True
DEFAULT_TRACK_CALLSIGNS = "CHX16"
DEFAULT_TRACK_REGISTRATIONS = ""
DEFAULT_TRACK_MODE = "callsign"
