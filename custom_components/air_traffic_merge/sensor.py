from __future__ import annotations

import time
import aiohttp
import async_timeout
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    CONF_ADSB_URL,
    CONF_SCAN_INTERVAL,
    CONF_ENABLE_TRACKING,
    CONF_TRACK_MODE,
    CONF_TRACK_CALLSIGNS,
    CONF_TRACK_REGISTRATIONS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_ENABLE_TRACKING,
    DEFAULT_TRACK_MODE,
)

STORE_KEY = "latest"


def _to_m(ft):
    try:
        return round(float(ft) * 0.3048)
    except Exception:
        return None


def _to_kmh(kn):
    try:
        return round(float(kn) * 1.852)
    except Exception:
        return None


def _safe_float(v):
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _split_csv(s: str) -> list[str]:
    return [p.strip() for p in (s or "").split(",") if p.strip()]


def _norm(s: str) -> str:
    return (s or "").strip().upper()


def _extract_callsign(ac: dict) -> str:
    # readsb aircraft.json uses "flight" for callsign (often padded)
    return (ac.get("flight") or "").strip()


def _extract_registration(ac: dict) -> str:
    # readsb aircraft.json uses "r" for registration
    return (ac.get("r") or "").strip()


def _compute_tracking(entry: ConfigEntry, aircraft: list[dict]) -> dict:
    """Return matched sets and list (aircraft dicts)."""
    enable = bool(
        entry.options.get(
            CONF_ENABLE_TRACKING,
            entry.data.get(CONF_ENABLE_TRACKING, DEFAULT_ENABLE_TRACKING),
        )
    )
    if not enable:
        return {
            "enabled": False,
            "mode": DEFAULT_TRACK_MODE,
            "want_callsigns": [],
            "want_registrations": [],
            "matched": [],
            "matched_callsigns": [],
            "matched_registrations": [],
        }

    mode = entry.options.get(CONF_TRACK_MODE, entry.data.get(CONF_TRACK_MODE, DEFAULT_TRACK_MODE))

    want_callsigns = set(
        _norm(x)
        for x in _split_csv(entry.options.get(CONF_TRACK_CALLSIGNS, entry.data.get(CONF_TRACK_CALLSIGNS, "")))
    )
    want_regs = set(
        _norm(x)
        for x in _split_csv(entry.options.get(CONF_TRACK_REGISTRATIONS, entry.data.get(CONF_TRACK_REGISTRATIONS, "")))
    )

    matched = []
    matched_callsigns = set()
    matched_regs = set()

    for ac in aircraft or []:
        cs = _norm(_extract_callsign(ac))
        reg = _norm(_extract_registration(ac))

        cs_hit = cs and cs in want_callsigns
        reg_hit = reg and reg in want_regs

        if mode == "callsign" and cs_hit:
            matched.append(ac)
            matched_callsigns.add(cs)
        elif mode == "registration" and reg_hit:
            matched.append(ac)
            matched_regs.add(reg)
        elif mode == "both" and (cs_hit or reg_hit):
            matched.append(ac)
            if cs_hit:
                matched_callsigns.add(cs)
            if reg_hit:
                matched_regs.add(reg)

    return {
        "enabled": True,
        "mode": mode,
        "want_callsigns": sorted(want_callsigns),
        "want_registrations": sorted(want_regs),
        "matched": matched,
        "matched_callsigns": sorted(matched_callsigns),
        "matched_registrations": sorted(matched_regs),
    }


def _build_flights_from_aircraft(entry: ConfigEntry, aircraft: list[dict], tracking: dict) -> list[dict]:
    """Build the 'flights' list exactly like the Lovelace card expects."""
    mode = tracking.get("mode", DEFAULT_TRACK_MODE)
    want_callsigns = set(tracking.get("want_callsigns", []) or [])
    want_regs = set(tracking.get("want_registrations", []) or [])

    flights: list[dict] = []

    for ac in aircraft or []:
        callsign_raw = _extract_callsign(ac)
        reg_raw = _extract_registration(ac)
        hx = (ac.get("hex") or "").strip()

        callsign = callsign_raw.strip()
        reg = reg_raw.strip()

        alt_m = _to_m(ac.get("alt_baro"))
        spd_kmh = _to_kmh(ac.get("gs"))
        dist_km = _safe_float(ac.get("r_dst"))
        dir_deg = _safe_float(ac.get("r_dir"))

        cs_norm = _norm(callsign)
        reg_norm = _norm(reg)

        cs_hit = cs_norm and cs_norm in want_callsigns
        reg_hit = reg_norm and reg_norm in want_regs

        is_tracked = False
        tracked_by = ""
        tracked_target = ""

        if tracking.get("enabled"):
            if mode == "callsign" and cs_hit:
                is_tracked = True
                tracked_by = "callsign"
                tracked_target = cs_norm
            elif mode == "registration" and reg_hit:
                is_tracked = True
                tracked_by = "registration"
                tracked_target = reg_norm
            elif mode == "both" and (cs_hit or reg_hit):
                is_tracked = True
                if reg_hit:
                    tracked_by = "registration"
                    tracked_target = reg_norm
                else:
                    tracked_by = "callsign"
                    tracked_target = cs_norm

        flights.append(
            {
                "registration": reg,
                "hex": hx,
                "callsign": callsign,
                "airline": "",  # ADS-B usually doesn't provide airline name
                "aircraft_model": (ac.get("t") or "").strip(),  # e.g. A320
                "source": "ADSB",
                "alt_m": alt_m,
                "spd_kmh": spd_kmh,
                "dist_km": dist_km,
                "dir_deg": dir_deg,
                "tracked": bool(is_tracked),
                "tracked_target": tracked_target,
                "tracked_by": tracked_by,
            }
        )

    return flights


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    # Ensure store dict exists
    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {}).setdefault(STORE_KEY, {})

    merged = AirTrafficMergedSensor(hass, entry)
    tracked = AirTrafficTrackedCountSensor(hass, entry)

    async_add_entities([merged, tracked])
    await merged.async_start()
    # tracked reads from shared store, no own timer needed


class AirTrafficMergedSensor(SensorEntity):
    _attr_name = "Air Traffic Merged"
    _attr_icon = "mdi:airplane"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_merged"
        self._attr_native_value = 0
        self._attr_extra_state_attributes = {}
        self._unsub_timer = None

    async def async_start(self):
        interval = int(
            self.entry.options.get(
                CONF_SCAN_INTERVAL,
                self.entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            )
        )
        self._unsub_timer = async_track_time_interval(
            self.hass,
            self._async_update,
            timedelta(seconds=interval),
        )
        await self._async_update(None)

    async def _async_update(self, now):
        url = self.entry.data.get(CONF_ADSB_URL)
        if not url:
            # no URL configured (ADS-B URL mode required for now)
            return

        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        data = await resp.json()

            aircraft = data.get("aircraft", []) or []

            tracking = _compute_tracking(self.entry, aircraft)

            # Build flights for the Lovelace card
            flights = _build_flights_from_aircraft(self.entry, aircraft, tracking)

            # Store for other entities/platforms
            self.hass.data[DOMAIN][self.entry.entry_id][STORE_KEY] = {
                "aircraft": aircraft,
                "flights": flights,
                "tracking": tracking,
                "raw": {"now": data.get("now"), "messages": data.get("messages")},
            }

            # Sensor state = number of flights
            self._attr_native_value = len(flights)

            # Card expects: attributes.flights + attributes.last_update
            tracked_active = tracking.get("matched_callsigns") or tracking.get("matched_registrations") or []
            tracked_active_count = len(tracking.get("matched", []) or [])

            self._attr_extra_state_attributes = {
                "last_update": int(time.time()),
                "flights": flights,

                # optional debug/raw
                "aircraft": aircraft,
                "messages": data.get("messages"),
                "now": data.get("now"),

                # tracking info (used by card chips if status_entity is provided;
                # still useful for debug)
                "tracking_enabled": bool(tracking.get("enabled", False)),
                "tracked_active_count": tracked_active_count,
                "tracked_active": tracked_active,
                "matched_callsigns": tracking.get("matched_callsigns", []),
                "matched_registrations": tracking.get("matched_registrations", []),
            }

            self.async_write_ha_state()

            # Force tracked-count sensor update
            self.hass.async_create_task(
                self.hass.helpers.entity_component.async_update_entity("sensor.air_traffic_tracked_count")
            )

        except Exception as e:
            self._attr_extra_state_attributes = {
                "last_update": int(time.time()),
                "error": str(e),
            }
            self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        if self._unsub_timer:
            self._unsub_timer()


class AirTrafficTrackedCountSensor(SensorEntity):
    _attr_name = "Air Traffic Tracked Count"
    _attr_icon = "mdi:radar"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_tracked_count"
        self._attr_native_value = 0
        self._attr_extra_state_attributes = {}

    @property
    def entity_id(self):
        # stable entity_id for update_entity call above
        return "sensor.air_traffic_tracked_count"

    async def async_update(self):
        store = (
            self.hass.data.get(DOMAIN, {})
            .get(self.entry.entry_id, {})
            .get(STORE_KEY, {})
        )
        tracking = store.get("tracking", {}) or {}
        matched = tracking.get("matched", []) or []

        self._attr_native_value = len(matched)
        self._attr_extra_state_attributes = {
            "tracking_enabled": bool(tracking.get("enabled", False)),
            "mode": tracking.get("mode", DEFAULT_TRACK_MODE),
            "matched_callsigns": tracking.get("matched_callsigns", []),
            "matched_registrations": tracking.get("matched_registrations", []),
            "matched_aircraft": matched,
        }
