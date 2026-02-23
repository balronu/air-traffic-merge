from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_FR24_ENTITY,
    CONF_ADSB_SOURCE,
    CONF_ADSB_URL,
    CONF_ADSB_ENTITY,
    CONF_SCAN_INTERVAL,
    CONF_ENABLE_TRACKING,
    CONF_TRACK_CALLSIGNS,
    CONF_TRACK_REGISTRATIONS,
    CONF_TRACK_MODE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_ADSB_SOURCE,
    DEFAULT_ENABLE_TRACKING,
    DEFAULT_TRACK_CALLSIGNS,
    DEFAULT_TRACK_REGISTRATIONS,
    DEFAULT_TRACK_MODE,
)


def _schema(defaults: dict):
    return vol.Schema(
        {
            vol.Optional(CONF_FR24_ENTITY, default=defaults.get(CONF_FR24_ENTITY)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(CONF_ADSB_SOURCE, default=defaults.get(CONF_ADSB_SOURCE, DEFAULT_ADSB_SOURCE)): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"label": "ADS-B per URL (aircraft.json)", "value": "url"},
                        {"label": "ADS-B bestehender Sensor (attributes.aircraft)", "value": "entity"},
                    ],
                    mode="dropdown",
                )
            ),
            vol.Optional(CONF_ADSB_URL, default=defaults.get(CONF_ADSB_URL, "")): str,
            vol.Optional(CONF_ADSB_ENTITY, default=defaults.get(CONF_ADSB_ENTITY)): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional(CONF_SCAN_INTERVAL, default=int(defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))): vol.Coerce(int),

            vol.Optional(CONF_ENABLE_TRACKING, default=bool(defaults.get(CONF_ENABLE_TRACKING, DEFAULT_ENABLE_TRACKING))): bool,
            vol.Optional(CONF_TRACK_MODE, default=str(defaults.get(CONF_TRACK_MODE, DEFAULT_TRACK_MODE))): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"label": "Callsign (z. B. CHX16)", "value": "callsign"},
                        {"label": "Registrierung (z. B. D-HXYZ)", "value": "registration"},
                        {"label": "Beides", "value": "both"},
                    ],
                    mode="dropdown",
                )
            ),
            vol.Optional(CONF_TRACK_CALLSIGNS, default=str(defaults.get(CONF_TRACK_CALLSIGNS, DEFAULT_TRACK_CALLSIGNS))): str,
            vol.Optional(CONF_TRACK_REGISTRATIONS, default=str(defaults.get(CONF_TRACK_REGISTRATIONS, DEFAULT_TRACK_REGISTRATIONS))): str,
        }
    )


def _validate(user_input: dict) -> dict[str, str]:
    errors: dict[str, str] = {}
    adsb_source = user_input.get(CONF_ADSB_SOURCE, DEFAULT_ADSB_SOURCE)

    if adsb_source == "url":
        url = str(user_input.get(CONF_ADSB_URL, "")).strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            errors["base"] = "invalid_url"
        else:
            user_input.pop(CONF_ADSB_ENTITY, None)
    else:
        ent = user_input.get(CONF_ADSB_ENTITY)
        if not ent:
            errors["base"] = "missing_entity"
        else:
            user_input.pop(CONF_ADSB_URL, None)

    return errors


class AirTrafficMergeFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(title="Air Traffic Merge", data=user_input)

        defaults = {
            CONF_FR24_ENTITY: None,
            CONF_ADSB_SOURCE: DEFAULT_ADSB_SOURCE,
            CONF_ADSB_URL: "",
            CONF_ADSB_ENTITY: None,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_ENABLE_TRACKING: DEFAULT_ENABLE_TRACKING,
            CONF_TRACK_MODE: DEFAULT_TRACK_MODE,
            CONF_TRACK_CALLSIGNS: DEFAULT_TRACK_CALLSIGNS,
            CONF_TRACK_REGISTRATIONS: DEFAULT_TRACK_REGISTRATIONS,
        }

        return self.async_show_form(step_id="user", data_schema=_schema(defaults), errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return AirTrafficMergeOptionsFlow(config_entry)


class AirTrafficMergeOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}

        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        defaults = dict(self.config_entry.data)
        defaults.update(dict(self.config_entry.options or {}))
        return self.async_show_form(step_id="init", data_schema=_schema(defaults), errors=errors)
