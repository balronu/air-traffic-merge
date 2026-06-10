DOMAIN = "air_traffic_merge"

# Source selection
CONF_SOURCE_MODE = "source_mode"
SOURCE_FR24_ONLY = "fr24_only"
SOURCE_ADSB_ONLY = "adsb_only"
SOURCE_BOTH = "both"
DEFAULT_SOURCE_MODE = SOURCE_BOTH

# FR24
CONF_FR24_ENTITY = "fr24_entity"

# ADS-B
CONF_ADSB_SOURCE = "adsb_source"
DEFAULT_ADSB_SOURCE = "url"  # "url" oder "entity"

CONF_ADSB_URL = "adsb_url"
CONF_ADSB_ENTITY = "adsb_entity"

# Polling
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 10

# Tracking
CONF_ENABLE_TRACKING = "enable_tracking"
DEFAULT_ENABLE_TRACKING = False

CONF_TRACK_MODE = "track_mode"
DEFAULT_TRACK_MODE = "callsign"

CONF_TRACK_CALLSIGNS = "track_callsigns"
CONF_TRACK_REGISTRATIONS = "track_registrations"

DEFAULT_TRACK_CALLSIGNS = ""
DEFAULT_TRACK_REGISTRATIONS = ""
