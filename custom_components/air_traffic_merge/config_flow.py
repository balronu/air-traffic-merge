from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
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

class AirTrafficMergeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_FR24_ENTITY]}::{user_input[CONF_ADSB_URL]}"
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Air Traffic Merge", data=user_input)

        return self.async_show_form(step_id="user", data_schema=self._schema())

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return AirTrafficMergeOptionsFlow(config_entry)

    def _schema(self, options: dict[str, Any] | None = None) -> vol.Schema:
        options = options or {}
        return vol.Schema(
            {
                vol.Required(CONF_FR24_ENTITY, default=options.get(CONF_FR24_ENTITY, "")): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_ADSB_URL, default=options.get(CONF_ADSB_URL, "")): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
                ),
                vol.Required(CONF_SCAN_INTERVAL, default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=120, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(CONF_MAX_ITEMS, default=options.get(CONF_MAX_ITEMS, DEFAULT_MAX_ITEMS)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=200, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_TRACKED_CALLSIGNS, default=options.get(CONF_TRACKED_CALLSIGNS, "")): selector.TextSelector(),
                vol.Optional(CONF_TRACKED_REGISTRATIONS, default=options.get(CONF_TRACKED_REGISTRATIONS, "")): selector.TextSelector(),
            }
        )

class AirTrafficMergeOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=120, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(CONF_MAX_ITEMS, default=defaults.get(CONF_MAX_ITEMS, DEFAULT_MAX_ITEMS)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=200, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_TRACKED_CALLSIGNS, default=defaults.get(CONF_TRACKED_CALLSIGNS, "")): selector.TextSelector(),
                vol.Optional(CONF_TRACKED_REGISTRATIONS, default=defaults.get(CONF_TRACKED_REGISTRATIONS, "")): selector.TextSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
