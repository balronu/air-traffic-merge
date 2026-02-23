from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import AirTrafficCoordinator


def _sanitize(s: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in s).strip("_")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator: AirTrafficCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_refresh()

    entities = []
    if coordinator.tracking_enabled:
        mode = coordinator.track_mode
        if mode in ("callsign", "both"):
            for cs in sorted(set(coordinator.tracked_callsigns)):
                entities.append(TrackedBinarySensor(coordinator, entry.entry_id, "callsign", cs))
        if mode in ("registration", "both"):
            for reg in sorted(set(coordinator.tracked_regs)):
                entities.append(TrackedBinarySensor(coordinator, entry.entry_id, "registration", reg))

    async_add_entities(entities, update_before_add=True)


class TrackedBinarySensor(BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: AirTrafficCoordinator, entry_id: str, kind: str, target: str) -> None:
        self.coordinator = coordinator
        self.kind = kind  # callsign|registration
        self.target = target.upper().strip()
        self._attr_name = f"Tracked {self.target}"
        self._attr_unique_id = f"{entry_id}_tracked_{kind}_{_sanitize(self.target)}"
        self._unsub = None
        self._attr_icon = "mdi:target"

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

    @property
    def is_on(self) -> bool:
        # tracked_active contains matched targets (callsign or registration, uppercase)
        return self.target in (t.upper() for t in self.coordinator.tracked_active)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"kind": self.kind, "target": self.target, "last_update": self.coordinator.last_update_ts}
