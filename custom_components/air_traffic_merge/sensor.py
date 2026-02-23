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
    DEFAULT_SCAN_INTERVAL,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    sensor = AirTrafficMergedSensor(hass, entry)
    async_add_entities([sensor])
    await sensor.async_start()


class AirTrafficMergedSensor(SensorEntity):
    _attr_name = "Air Traffic Merged"
    _attr_icon = "mdi:airplane"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_native_value = 0
        self._attr_extra_state_attributes = {}
        self._unsub_timer = None

    async def async_start(self):
        interval = int(
            self.entry.data.get(
                CONF_SCAN_INTERVAL,
                DEFAULT_SCAN_INTERVAL,
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
            return

        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        data = await resp.json()

            aircraft = data.get("aircraft", [])
            self._attr_native_value = len(aircraft)
            self._attr_extra_state_attributes = {
                "aircraft": aircraft,
                "messages": data.get("messages"),
                "now": data.get("now"),
            }

            self.async_write_ha_state()

        except Exception as e:
            self._attr_extra_state_attributes = {
                "error": str(e),
            }
            self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        if self._unsub_timer:
            self._unsub_timer()
