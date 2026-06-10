from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

STORE_KEY = "latest"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    async_add_entities([AirTrafficTrackedPresentBinarySensor(hass, entry)])


class AirTrafficTrackedPresentBinarySensor(BinarySensorEntity):
    _attr_name = "Air Traffic Tracked Present"
    _attr_icon = "mdi:radar"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_tracked_present"
        self._attr_is_on = False
        self._attr_extra_state_attributes = {}

    async def async_update(self):
        store = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {}).get(STORE_KEY, {})
        tracking = store.get("tracking", {}) or {}
        matched = tracking.get("matched", []) or []

        self._attr_is_on = len(matched) > 0
        self._attr_extra_state_attributes = {
            "tracking_enabled": tracking.get("enabled", False),
            "matched_callsigns": tracking.get("matched_callsigns", []),
            "matched_registrations": tracking.get("matched_registrations", []),
        }
