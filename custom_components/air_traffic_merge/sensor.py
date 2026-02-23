from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    async_add_entities([AirTrafficMergedSensor()])


class AirTrafficMergedSensor(SensorEntity):
    _attr_name = "Air Traffic Merged"
    _attr_unique_id = "air_traffic_merged_test"
    _attr_native_value = 0
