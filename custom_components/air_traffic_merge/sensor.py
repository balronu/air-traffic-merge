"""Sensor platform for Air Traffic Merge."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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
    DOMAIN,
)
from .coordinator import AirTrafficMergeCoordinator

COUNT_KEYS = {
    "medical": "medical",
    "military": "military",
    "helicopter": "helicopter",
    "business": "business",
    "general_aviation": "general_aviation",
    "civil": "civil",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AirTrafficMergeCoordinator = entry.runtime_data

    entities: list[SensorEntity] = [AirTrafficMergeMainSensor(coordinator, entry)]
    entities.extend(AirTrafficMergeCountSensor(coordinator, entry, key) for key in COUNT_KEYS)
    async_add_entities(entities)


class AirTrafficMergeBase(CoordinatorEntity[AirTrafficMergeCoordinator], SensorEntity):
    """Base sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AirTrafficMergeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Air Traffic Merge",
            manufacturer="balronu",
            model="FR24 + ADS-B Merge",
        )


class AirTrafficMergeMainSensor(AirTrafficMergeBase):
    """Main merged flights sensor."""

    _attr_name = None
    _attr_translation_key = "main"
    _attr_icon = "mdi:airplane"

    def __init__(self, coordinator: AirTrafficMergeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_main"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get(ATTR_FLIGHTS, []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            ATTR_FLIGHTS: self.coordinator.data.get(ATTR_FLIGHTS, []),
            ATTR_LAST_UPDATE: self.coordinator.data.get(ATTR_LAST_UPDATE),
            ATTR_STATUS: self.coordinator.data.get(ATTR_STATUS),
            ATTR_FR24_COUNT: self.coordinator.data.get(ATTR_FR24_COUNT, 0),
            ATTR_ADSB_COUNT: self.coordinator.data.get(ATTR_ADSB_COUNT, 0),
            ATTR_MERGED_COUNT: self.coordinator.data.get(ATTR_MERGED_COUNT, 0),
            ATTR_COUNTS: self.coordinator.data.get(ATTR_COUNTS, {}),
            ATTR_TRACKED_PRESENT: self.coordinator.data.get(ATTR_TRACKED_PRESENT, False),
            ATTR_DEBUG: self.coordinator.data.get(ATTR_DEBUG, {}),
        }


class AirTrafficMergeCountSensor(AirTrafficMergeBase):
    """Count sensor for specific category."""

    def __init__(self, coordinator: AirTrafficMergeCoordinator, entry: ConfigEntry, count_key: str) -> None:
        super().__init__(coordinator, entry)
        self._count_key = count_key
        self._attr_translation_key = f"count_{count_key}"
        self._attr_unique_id = f"{entry.entry_id}_{count_key}"
        self._attr_icon = "mdi:counter"

    @property
    def native_value(self) -> int:
        return int(self.coordinator.data.get(ATTR_COUNTS, {}).get(self._count_key, 0))
