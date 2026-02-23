from __future__ import annotations

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
    """Return matched sets and list."""
    enable = bool(entry.options.get(CONF_ENABLE_TRACKING, entry.data.get(CONF_ENABLE_TRACKING, DEFAULT_ENABLE_TRACKING)))
    if not enable:
        return {"enabled": False, "matched": [], "matched_callsigns": [], "matched_registrations": []}

    mode = entry.options.get(CONF_TRACK_MODE, entry.data.get(CONF_TRACK_MODE, DEFAULT_TRACK_MODE))

    want_callsigns = set(_norm(x) for x in _split_csv(entry.options.get(CONF_TRACK_CALLSIGNS, entry.data.get(CONF_TRACK_CALLSIGNS, ""))))
    want_regs = set(_norm(x) for x in _split_csv(entry.options.get(CONF_TRACK_REGISTRATIONS, entry.data.get(CONF_TRACK_REGISTRATIONS, ""))))

    matched = []
    matched_callsigns = set()
    matched_regs = set()

    for ac in aircraft:
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
        "matched": matched,
        "matched_callsigns": sorted(matched_callsigns),
        "matched_registrations": sorted(matched_regs),
    }


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
        interval = int(self.entry.options.get(CONF_SCAN_INTERVAL, self.entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)))
        self._unsub_timer = async_track_time_interval(
            self.hass,
            self._async_update,
            timedelta(seconds=interval),
        )
        await self._async_update(None)

    async def _async_update(self, now):
        url = self.entry.data.get(CONF_ADSB_URL)
        if not url:
            return

        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        data = await resp.json()

            aircraft = data.get("aircraft", []) or []

            tracking = _compute_tracking(self.entry, aircraft)

            # store for other entities
            self.hass.data[DOMAIN][self.entry.entry_id][STORE_KEY] = {
                "aircraft": aircraft,
                "tracking": tracking,
                "raw": {"now": data.get("now"), "messages": data.get("messages")},
            }

            self._attr_native_value = len(aircraft)
            self._attr_extra_state_attributes = {
                "aircraft": aircraft,
                "messages": data.get("messages"),
                "now": data.get("now"),
                "tracking_enabled": tracking.get("enabled", False),
                "tracked_count": len(tracking.get("matched", [])),
                "matched_callsigns": tracking.get("matched_callsigns", []),
                "matched_registrations": tracking.get("matched_registrations", []),
            }

            self.async_write_ha_state()

            # Force tracked sensor to update too
            self.hass.async_create_task(
                self.hass.helpers.entity_component.async_update_entity(
                    f"sensor.air_traffic_tracked_count"
                )
            )

        except Exception as e:
            self._attr_extra_state_attributes = {"error": str(e)}
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
        store = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {}).get(STORE_KEY, {})
        tracking = store.get("tracking", {}) or {}
        matched = tracking.get("matched", []) or []

        self._attr_native_value = len(matched)
        self._attr_extra_state_attributes = {
            "tracking_enabled": tracking.get("enabled", False),
            "matched_callsigns": tracking.get("matched_callsigns", []),
            "matched_registrations": tracking.get("matched_registrations", []),
            "matched_aircraft": matched,
        }
