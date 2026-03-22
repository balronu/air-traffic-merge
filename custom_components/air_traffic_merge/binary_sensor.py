from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AirTrafficMergeCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AirTrafficMergeCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AirTrafficTrackedPresentBinarySensor(coordinator, entry)])


class AirTrafficTrackedPresentBinarySensor(CoordinatorEntity[AirTrafficMergeCoordinator], BinarySensorEntity):
    _attr_name = "Air Traffic Tracked Present"
    _attr_icon = "mdi:radar"

    def __init__(self, coordinator: AirTrafficMergeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_tracked_present"

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("tracked_present", False))
