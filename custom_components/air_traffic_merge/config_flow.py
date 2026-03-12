"""Config flow for Air Traffic Merge."""
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
    """Handle a config flow for Air Traffic Merge."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_FR24_ENTITY]}::{user_input[CONF_ADSB_URL]}"
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="Air Traffic Merge",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_FR24_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_ADSB_URL): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.URL)
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=120, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_MAX_ITEMS, default=DEFAULT_MAX_ITEMS): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=200, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_TRACKED_CALLSIGNS, default=""): selector.TextSelector(),
                vol.Optional(CONF_TRACKED_REGISTRATIONS, default=""): selector.TextSelector(),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return AirTrafficMergeOptionsFlow(config_entry)


class AirTrafficMergeOptionsFlow(config_entries.OptionsFlow):
    """Handle Air Traffic Merge options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=120, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(
                    CONF_MAX_ITEMS,
                    default=options.get(CONF_MAX_ITEMS, DEFAULT_MAX_ITEMS),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=200, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Optional(
                    CONF_TRACKED_CALLSIGNS,
                    default=options.get(CONF_TRACKED_CALLSIGNS, options.get(CONF_TRACKED_CALLSIGNS, "")),
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_TRACKED_REGISTRATIONS,
                    default=options.get(CONF_TRACKED_REGISTRATIONS, options.get(CONF_TRACKED_REGISTRATIONS, "")),
                ): selector.TextSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
