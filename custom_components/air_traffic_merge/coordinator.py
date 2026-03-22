from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from aiohttp import ClientError, ClientTimeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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
    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.config_entry = entry
        options = {**entry.data, **entry.options}

        self.fr24_entity = str(options.get(CONF_FR24_ENTITY, "")).strip()
        self.adsb_url = str(options[CONF_ADSB_URL]).strip()
        self.max_items = int(options.get(CONF_MAX_ITEMS, DEFAULT_MAX_ITEMS))
        self.tracked_callsigns = str(options.get(CONF_TRACKED_CALLSIGNS, ""))
        self.tracked_registrations = str(options.get(CONF_TRACKED_REGISTRATIONS, ""))
        scan_interval = int(options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        self._unsub_state = None
        self._last_adsb_aircraft: list[dict[str, Any]] = []
        self._last_adsb_now: Any = None
        self._last_adsb_error: str | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

        if self.fr24_entity:
            self._unsub_state = async_track_state_change_event(
                hass,
                [self.fr24_entity],
                self._handle_fr24_change,
            )

    async def async_shutdown(self) -> None:
        if self._unsub_state:
            self._unsub_state()
            self._unsub_state = None

    @callback
    def _handle_fr24_change(self, event: Event[EventStateChangedData]) -> None:
        self.async_set_updated_data(self._build_data_from_current_state())

    def _build_data_from_current_state(self) -> dict[str, Any]:
        fr24_flights: list[dict[str, Any]] = []
        fr24_error = None

        if self.fr24_entity:
            fr24_state = self.hass.states.get(self.fr24_entity)
            if fr24_state is None:
                fr24_error = f"FR24 entity not found: {self.fr24_entity}"
            else:
                fr24_flights = list(fr24_state.attributes.get("flights", []))

        merged = merge_flights(
            fr24_flights,
            self._last_adsb_aircraft,
            max_items=self.max_items,
            tracked_callsigns=self.tracked_callsigns,
            tracked_registrations=self.tracked_registrations,
        )

        if not fr24_flights and not self._last_adsb_aircraft:
            status = "empty"
        elif fr24_flights and not self._last_adsb_aircraft:
            status = "fr24_only"
        elif self._last_adsb_aircraft and not fr24_flights:
            status = "adsb_only"
        else:
            status = "both"

        return {
            ATTR_FLIGHTS: merged["flights"],
            ATTR_LAST_UPDATE: self._last_adsb_now,
            ATTR_STATUS: status,
            ATTR_FR24_COUNT: merged["fr24_count"],
            ATTR_ADSB_COUNT: merged["adsb_count"],
            ATTR_MERGED_COUNT: merged["merged_count"],
            ATTR_COUNTS: merged["counts"],
            ATTR_TRACKED_PRESENT: merged["tracked_present"],
            ATTR_DEBUG: {
                "fr24_entity": self.fr24_entity,
                "fr24_error": fr24_error,
                "adsb_url": self.adsb_url,
                "adsb_now": self._last_adsb_now,
                "adsb_error": self._last_adsb_error,
                "scan_interval": int(self.update_interval.total_seconds()),
                "max_items": self.max_items,
            },
        }

    async def _async_update_data(self) -> dict[str, Any]:
        session = async_get_clientsession(self.hass)
        self._last_adsb_aircraft = []
        self._last_adsb_now = None
        self._last_adsb_error = None

        try:
            async with session.get(self.adsb_url, timeout=ClientTimeout(total=8)) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
                self._last_adsb_aircraft = list(payload.get("aircraft", []))
                self._last_adsb_now = payload.get("now")
        except (ClientError, TimeoutError, ValueError) as err:
            self._last_adsb_error = str(err)
            _LOGGER.warning("Could not fetch ADS-B data from %s: %s", self.adsb_url, err)

        data = self._build_data_from_current_state()
        if data[ATTR_STATUS] == "empty" and self._last_adsb_error:
            raise UpdateFailed(self._last_adsb_error)
        return data
