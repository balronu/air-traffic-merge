from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_SCAN_INTERVAL,
    CONF_ENABLE_TRACKING,
    CONF_TRACK_MODE,
    CONF_TRACK_CALLSIGNS,
    CONF_TRACK_REGISTRATIONS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_ENABLE_TRACKING,
    DEFAULT_TRACK_MODE,
    DEFAULT_TRACK_CALLSIGNS,
    DEFAULT_TRACK_REGISTRATIONS,
)


class AirTrafficMergeFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    # ... dein bestehender ConfigFlow bleibt wie er ist ...

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return AirTrafficMergeOptionsFlow(config_entry)


class AirTrafficMergeOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry
        self._options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        # 1. Seite: scan_interval + enable_tracking
        if user_input is not None:
            self._options.update(user_input)
            if self._options.get(CONF_ENABLE_TRACKING):
                return await self.async_step_tracking()
            # Tracking aus -> Tracking Felder entfernen
            self._options.pop(CONF_TRACK_MODE, None)
            self._options.pop(CONF_TRACK_CALLSIGNS, None)
            self._options.pop(CONF_TRACK_REGISTRATIONS, None)
            return self.async_create_entry(title="", data=self._options)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=int(self._options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_ENABLE_TRACKING,
                    default=bool(self._options.get(CONF_ENABLE_TRACKING, DEFAULT_ENABLE_TRACKING)),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_tracking(self, user_input=None):
        # 2. Seite: Tracking Mode + Werte
        if user_input is not None:
            self._options.update(user_input)

            mode = self._options.get(CONF_TRACK_MODE, DEFAULT_TRACK_MODE)
            if mode not in ("callsign", "registration", "both"):
                return self.async_show_form(
                    step_id="tracking",
                    data_schema=self._tracking_schema(),
                    errors={"base": "invalid_track_mode"},
                )

            # Felder säubern je nach Mode
            if mode not in ("callsign", "both"):
                self._options.pop(CONF_TRACK_CALLSIGNS, None)
            if mode not in ("registration", "both"):
                self._options.pop(CONF_TRACK_REGISTRATIONS, None)

            return self.async_create_entry(title="", data=self._options)

        return self.async_show_form(step_id="tracking", data_schema=self._tracking_schema())

    def _tracking_schema(self):
        return vol.Schema(
            {
                vol.Optional(
                    CONF_TRACK_MODE,
                    default=self._options.get(CONF_TRACK_MODE, DEFAULT_TRACK_MODE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"label": "Callsign (z. B. CHX16)", "value": "callsign"},
                            {"label": "Registrierung (z. B. D-HXYZ)", "value": "registration"},
                            {"label": "Beides", "value": "both"},
                        ],
                        mode="dropdown",
                    )
                ),
                vol.Optional(
                    CONF_TRACK_CALLSIGNS,
                    default=self._options.get(CONF_TRACK_CALLSIGNS, DEFAULT_TRACK_CALLSIGNS),
                ): str,
                vol.Optional(
                    CONF_TRACK_REGISTRATIONS,
                    default=self._options.get(CONF_TRACK_REGISTRATIONS, DEFAULT_TRACK_REGISTRATIONS),
                ): str,
            }
        )
