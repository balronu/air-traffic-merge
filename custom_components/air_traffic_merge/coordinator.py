"""Coordinator for Air Traffic Merge."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_ADSB_COUNT,
    ATTR_COUNTS,
    ATTR_DEBUG,
    ATTR_FLIGHTS,
    ATTR_FR24_COUNT,
    ATTR_LAST_UPDATE,
    ATTR_MERGED_COUNT,
    ATTR_STATUS,
    ATTR_TRACKED_PRESENT,
    CONF_ADSB_URL,
    CONF_FR24_ENTITY,
    CONF_MAX_ITEMS,
    CONF_SCAN_INTERVAL,
    CONF_TRACKED_CALLSIGNS,
    CONF_TRACKED_REGISTRATIONS,
    DEFAULT_MAX_ITEMS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .merge import merge_flights

_LOGGER = logging.getLogger(__name__)


class AirTrafficMergeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Handle fetching and merging flight data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.config_entry = entry
        self.fr24_entity = entry.data[CONF_FR24_ENTITY]
        self.adsb_url = entry.data[CONF_ADSB_URL]
        options = {**entry.data, **entry.options}
        scan_interval = int(options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        self.max_items = int(options.get(CONF_MAX_ITEMS, DEFAULT_MAX_ITEMS))
        self.tracked_callsigns = str(options.get(CONF_TRACKED_CALLSIGNS, ""))
        self.tracked_registrations = str(options.get(CONF_TRACKED_REGISTRATIONS, ""))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

        self._unsubscribe_state = async_track_state_change_event(
            hass, [self.fr24_entity], self._handle_fr24_change
        )

    async def _handle_fr24_change(self, event) -> None:
        """Refresh quickly when FR24 entity changes."""
        self.async_set_updated_data(await self._async_update_data())

    async def async_shutdown(self) -> None:
        if self._unsubscribe_state:
            self._unsubscribe_state()

    async def _async_update_data(self) -> dict[str, Any]:
        fr24_state = self.hass.states.get(self.fr24_entity)
        if fr24_state is None:
            raise UpdateFailed(f"FR24 entity not found: {self.fr24_entity}")

        fr24_flights = list(fr24_state.attributes.get("flights", []))
        adsb_aircraft: list[dict[str, Any]] = []
        adsb_error = None

        try:
            session = aiohttp.ClientSession()
            try:
                async with session.get(self.adsb_url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                    response.raise_for_status()
                    payload = await response.json()
            finally:
                await session.close()
            adsb_aircraft = list(payload.get("aircraft", []))
            adsb_now = payload.get("now")
        except Exception as err:  # noqa: BLE001
            adsb_error = str(err)
            _LOGGER.warning("Could not fetch ADS-B data from %s: %s", self.adsb_url, err)
            adsb_now = None

        merged = merge_flights(
            fr24_flights,
            adsb_aircraft,
            max_items=self.max_items,
            tracked_callsigns=self.tracked_callsigns,
            tracked_registrations=self.tracked_registrations,
        )

        status = "ok"
        if not fr24_flights and not adsb_aircraft:
            status = "empty"
        elif fr24_flights and not adsb_aircraft:
            status = "fr24_only"
        elif adsb_aircraft and not fr24_flights:
            status = "adsb_only"
        elif fr24_flights and adsb_aircraft:
            status = "both"

        return {
            ATTR_FLIGHTS: merged["flights"],
            ATTR_LAST_UPDATE: merged["last_update"],
            ATTR_STATUS: status,
            ATTR_FR24_COUNT: merged["fr24_count"],
            ATTR_ADSB_COUNT: merged["adsb_count"],
            ATTR_MERGED_COUNT: merged["merged_count"],
            ATTR_COUNTS: merged["counts"],
            ATTR_TRACKED_PRESENT: merged["tracked_present"],
            ATTR_DEBUG: {
                "fr24_entity": self.fr24_entity,
                "adsb_url": self.adsb_url,
                "adsb_now": adsb_now,
                "adsb_error": adsb_error,
                "scan_interval": int(self.update_interval.total_seconds()),
                "max_items": self.max_items,
            },
        }
