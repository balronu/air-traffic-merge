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


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_ADSB_URL, default=defaults.get(CONF_ADSB_URL, "http://127.0.0.1:8080/data/aircraft.json")): str,
            vol.Optional(CONF_FR24_ENTITY, default=defaults.get(CONF_FR24_ENTITY, "")): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=False)
            ),
            vol.Required(CONF_SCAN_INTERVAL, default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=300, mode=selector.NumberSelectorMode.BOX, step=1)
            ),
            vol.Required(CONF_MAX_ITEMS, default=defaults.get(CONF_MAX_ITEMS, DEFAULT_MAX_ITEMS)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=250, mode=selector.NumberSelectorMode.BOX, step=1)
            ),
            vol.Optional(CONF_TRACKED_CALLSIGNS, default=defaults.get(CONF_TRACKED_CALLSIGNS, "")): str,
            vol.Optional(CONF_TRACKED_REGISTRATIONS, default=defaults.get(CONF_TRACKED_REGISTRATIONS, "")): str,
        }
    )


class AirTrafficMergeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(f"atm::{user_input[CONF_ADSB_URL]}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Air Traffic Merge", data=user_input)

        return self.async_show_form(step_id="user", data_schema=_schema({}))

    @staticmethod
    def async_get_options_flow(config_entry):
        return AirTrafficMergeOptionsFlow(config_entry)


class AirTrafficMergeOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(defaults))
