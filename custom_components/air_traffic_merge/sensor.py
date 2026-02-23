from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import AirTrafficCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator: AirTrafficCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_refresh()

    entities = [
        AirTrafficStatusSensor(coordinator, entry.entry_id),
        AirTrafficMergedSensor(coordinator, entry.entry_id),
    ]
    if coordinator.tracking_enabled:
        entities.append(AirTrafficTrackedSensor(coordinator, entry.entry_id))

    async_add_entities(entities, update_before_add=True)


class _BaseSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: AirTrafficCoordinator) -> None:
        self.coordinator = coordinator
        self._unsub = None

    async def async_added_to_hass(self) -> None:
        async def _tick(_now):
            await self.coordinator.async_refresh()
            self.async_write_ha_state()

        self._unsub = async_track_time_interval(
            self.hass, _tick, dt_util.timedelta(seconds=self.coordinator.scan_interval)
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None


class AirTrafficStatusSensor(_BaseSensor):
    _attr_name = "Air Traffic Status"
    _attr_icon = "mdi:radar"

    def __init__(self, coordinator: AirTrafficCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_status"

    @property
    def native_value(self) -> str:
        fr24 = self.coordinator.fr24_count
        adsb = self.coordinator.adsb_count
        if fr24 == 0 and adsb == 0:
            return "none"
        if fr24 == 0:
            return "adsb_only"
        if adsb == 0:
            return "fr24_only"
        return "both"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "last_update": self.coordinator.last_update_ts,
            "fr24_count": self.coordinator.fr24_count,
            "adsb_count": self.coordinator.adsb_count,
            "merged_count": len(self.coordinator.merged),
            "adsb_source": self.coordinator.adsb_source,
            "tracking_enabled": self.coordinator.tracking_enabled,
            "track_mode": self.coordinator.track_mode,
            "tracked_callsigns": self.coordinator.tracked_callsigns,
            "tracked_registrations": self.coordinator.tracked_regs,
            "tracked_active": self.coordinator.tracked_active,
            "tracked_active_count": self.coordinator.tracked_active_count,
        }


class AirTrafficMergedSensor(_BaseSensor):
    _attr_name = "Air Traffic Merged"
    _attr_icon = "mdi:airplane"

    def __init__(self, coordinator: AirTrafficCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_merged"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.merged)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        flights = []
        for m in self.coordinator.merged:
            flights.append(
                {
                    "registration": m.registration,
                    "hex": m.hex,
                    "callsign": m.callsign,
                    "source": m.source,
                    "airline": m.airline,
                    "aircraft_model": m.aircraft_model,
                    "alt_m": m.alt_m,
                    "spd_kmh": m.spd_kmh,
                    "dist_km": m.dist_km,
                    "dir_deg": m.dir_deg,
                    "tracked": m.tracked,
                    "tracked_by": m.tracked_by,
                    "tracked_target": m.tracked_target,
                }
            )
        return {"last_update": self.coordinator.last_update_ts, "flights": flights}


class AirTrafficTrackedSensor(_BaseSensor):
    _attr_name = "Air Traffic Tracked"
    _attr_icon = "mdi:target"

    def __init__(self, coordinator: AirTrafficCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_tracked"

    @property
    def native_value(self) -> int:
        return self.coordinator.tracked_active_count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "tracked_active": self.coordinator.tracked_active,
            "tracked_callsigns": self.coordinator.tracked_callsigns,
            "tracked_registrations": self.coordinator.tracked_regs,
            "track_mode": self.coordinator.track_mode,
            "last_update": self.coordinator.last_update_ts,
        }
