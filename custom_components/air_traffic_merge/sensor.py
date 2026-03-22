from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AirTrafficMergeCoordinator


@dataclass(frozen=True, kw_only=True)
class CountSensorDescription(SensorEntityDescription):
    count_key: str


COUNT_SENSORS: tuple[CountSensorDescription, ...] = (
    CountSensorDescription(key="medical", name="Air Traffic Medical", icon="mdi:medical-bag", count_key="medical"),
    CountSensorDescription(key="military", name="Air Traffic Military", icon="mdi:shield-airplane", count_key="military"),
    CountSensorDescription(key="helicopter", name="Air Traffic Helicopter", icon="mdi:helicopter", count_key="helicopter"),
    CountSensorDescription(key="business", name="Air Traffic Business", icon="mdi:briefcase", count_key="business"),
    CountSensorDescription(key="general_aviation", name="Air Traffic General Aviation", icon="mdi:airplane-takeoff", count_key="general_aviation"),
    CountSensorDescription(key="civil", name="Air Traffic Civil", icon="mdi:airplane", count_key="civil"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = AirTrafficMergeCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()

    entities: list[SensorEntity] = [AirTrafficMergedSensor(coordinator, entry)]
    entities.extend(AirTrafficCountSensor(coordinator, entry, desc) for desc in COUNT_SENSORS)
    async_add_entities(entities)


class AirTrafficMergedSensor(CoordinatorEntity[AirTrafficMergeCoordinator], SensorEntity):
    _attr_icon = "mdi:airplane-search"

    def __init__(self, coordinator: AirTrafficMergeCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Air Traffic Merge"
        self._attr_unique_id = f"{entry.entry_id}_overview"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("flights", []))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return dict(self.coordinator.data)


class AirTrafficCountSensor(CoordinatorEntity[AirTrafficMergeCoordinator], SensorEntity):
    entity_description: CountSensorDescription

    def __init__(self, coordinator: AirTrafficMergeCoordinator, entry: ConfigEntry, description: CountSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> int:
        return int(self.coordinator.data.get("counts", {}).get(self.entity_description.count_key, 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        flights = [
            f
            for f in self.coordinator.data.get("flights", [])
            if (
                self.entity_description.count_key == "military"
                and str(f.get("category", "")).startswith("military")
            )
            or f.get("category") == self.entity_description.count_key
        ]
        return {
            "category": self.entity_description.count_key,
            "flights": flights,
            "last_update": self.coordinator.data.get("last_update"),
        }
