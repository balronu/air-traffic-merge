from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    # Mode
    CONF_MODE,
    MODE_FR24,
    MODE_ADSB,
    MODE_BOTH,
    DEFAULT_MODE,
    # FR24
    CONF_FR24_ENTITY,
    # ADSB
    CONF_ADSB_SOURCE,
    ADSB_SOURCE_URL,
    ADSB_SOURCE_ENTITY,
    DEFAULT_ADSB_SOURCE,
    CONF_ADSB_URL,
    CONF_ADSB_ENTITY,
    # Misc
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    # Tracking
    CONF_ENABLE_TRACKING,
    DEFAULT_ENABLE_TRACKING,
    CONF_TRACK_MODE,
    TRACK_MODE_CALLSIGN,
    TRACK_MODE_REGISTRATION,
    TRACK_MODE_BOTH,
    DEFAULT_TRACK_MODE,
    CONF_TRACK_CALLSIGNS,
    CONF_TRACK_REGISTRATIONS,
    DEFAULT_TRACK_CALLSIGNS,
    DEFAULT_TRACK_REGISTRATIONS,
)


def _is_http_url(url: str) -> bool:
    u = (url or "").strip().lower()
    return u.startswith("http://") or u.startswith("https://")


def _looks_like_aircraft_json(url: str) -> bool:
    u = (url or "").strip().lower()
    # Wir wollen nur einen Hinweis geben, kein Hard-Fail.
    return u.endswith("/aircraft.json") or u.endswith("aircraft.json")


def _entity_selector_optional(default: str | None = None):
    # NIE default=None an EntitySelector geben!
    if default:
        return vol.Optional(default=default)
    return vol.Optional


class AirTrafficMergeFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Step 1: Grundmodus wählen."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.update(user_input)

            # Routing je nach Modus
            mode = self._data.get(CONF_MODE, DEFAULT_MODE)
            if mode in (MODE_FR24, MODE_BOTH):
                return await self.async_step_fr24()
            return await self.async_step_adsb()

        schema = vol.Schema(
            {
                vol.Required(CONF_MODE, default=self._data.get(CONF_MODE, DEFAULT_MODE)): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"label": "Nur Flightradar24 (FR24)", "value": MODE_FR24},
                            {"label": "Nur ADS-B (lokal)", "value": MODE_ADSB},
                            {"label": "FR24 + ADS-B (zusammenführen)", "value": MODE_BOTH},
                        ],
                        mode="dropdown",
                    )
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_fr24(self, user_input: dict[str, Any] | None = None):
        """Step 2 (optional): FR24 Sensor auswählen."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # FR24 Entity optional, aber wenn Mode FR24/BOTH dann sinnvollerweise required
            fr24 = user_input.get(CONF_FR24_ENTITY)
            mode = self._data.get(CONF_MODE, DEFAULT_MODE)

            if mode in (MODE_FR24, MODE_BOTH) and not fr24:
                errors[CONF_FR24_ENTITY] = "missing_entity"
            else:
                self._data.update(user_input)
                return await self.async_step_adsb() if mode in (MODE_ADSB, MODE_BOTH) else await self.async_step_tracking_gate()

        fr24_default = self._data.get(CONF_FR24_ENTITY)
        schema = vol.Schema(
            {
                vol.Required(CONF_FR24_ENTITY, default=fr24_default) if fr24_default else vol.Required(CONF_FR24_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                )
            }
        )

        return self.async_show_form(step_id="fr24", data_schema=schema, errors=errors)

    async def async_step_adsb(self, user_input: dict[str, Any] | None = None):
        """Step 3 (optional): ADS-B Quelle wählen."""
        errors: dict[str, str] = {}

        mode = self._data.get(CONF_MODE, DEFAULT_MODE)
        if mode == MODE_FR24:
            return await self.async_step_tracking_gate()

        if user_input is not None:
            adsb_source = user_input.get(CONF_ADSB_SOURCE, DEFAULT_ADSB_SOURCE)
            self._data.update(user_input)

            if adsb_source == ADSB_SOURCE_URL:
                return await self.async_step_adsb_url()
            return await self.async_step_adsb_entity()

        schema = vol.Schema(
            {
                vol.Required(CONF_ADSB_SOURCE, default=self._data.get(CONF_ADSB_SOURCE, DEFAULT_ADSB_SOURCE)): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"label": "ADS-B per URL (aircraft.json)", "value": ADSB_SOURCE_URL},
                            {"label": "ADS-B über bestehenden Sensor (attributes.aircraft)", "value": ADSB_SOURCE_ENTITY},
                        ],
                        mode="dropdown",
                    )
                ),
                vol.Optional(CONF_SCAN_INTERVAL, default=int(self._data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))): vol.Coerce(int),
            }
        )
        return self.async_show_form(step_id="adsb", data_schema=schema, errors=errors)

    async def async_step_adsb_url(self, user_input: dict[str, Any] | None = None):
        """Step 4a: ADS-B URL eingeben."""
        errors: dict[str, str] = {}
        placeholders = {
            # Hinweistext wird in translations unter description_placeholders genutzt
            "example_url": "http://<ip>:8080/data/aircraft.json"
        }

        if user_input is not None:
            url = str(user_input.get(CONF_ADSB_URL, "") or "").strip()
            if not _is_http_url(url):
                errors[CONF_ADSB_URL] = "invalid_url"
            else:
                # Optional: Warnung wenn nicht nach aircraft.json aussieht
                # (kein Fehler — nur Hinweis, siehe strings/translation)
                self._data.update({CONF_ADSB_URL: url})
                # sicherstellen: entity nicht speichern
                self._data.pop(CONF_ADSB_ENTITY, None)
                return await self.async_step_tracking_gate()

        url_default = self._data.get(CONF_ADSB_URL, "")
        schema = vol.Schema(
            {
                vol.Required(CONF_ADSB_URL, default=url_default): str,
            }
        )

        return self.async_show_form(
            step_id="adsb_url",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_adsb_entity(self, user_input: dict[str, Any] | None = None):
        """Step 4b: ADS-B Entity auswählen."""
        errors: dict[str, str] = {}

        if user_input is not None:
            ent = user_input.get(CONF_ADSB_ENTITY)
            if not ent:
                errors[CONF_ADSB_ENTITY] = "missing_entity"
            else:
                self._data.update({CONF_ADSB_ENTITY: ent})
                # sicherstellen: url nicht speichern
                self._data.pop(CONF_ADSB_URL, None)
                return await self.async_step_tracking_gate()

        ent_default = self._data.get(CONF_ADSB_ENTITY)

        schema = vol.Schema(
            {
                (vol.Required(CONF_ADSB_ENTITY, default=ent_default) if ent_default else vol.Required(CONF_ADSB_ENTITY)): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                )
            }
        )

        return self.async_show_form(step_id="adsb_entity", data_schema=schema, errors=errors)

    async def async_step_tracking_gate(self, user_input: dict[str, Any] | None = None):
        """Step 5: Tracking aktivieren? (default: aus)"""
        errors: dict[str, str] = {}

        if user_input is not None:
            enable = bool(user_input.get(CONF_ENABLE_TRACKING, False))
            self._data[CONF_ENABLE_TRACKING] = enable
            if enable:
                return await self.async_step_tracking()
            return await self._finish()

        schema = vol.Schema(
            {
                vol.Required(CONF_ENABLE_TRACKING, default=bool(self._data.get(CONF_ENABLE_TRACKING, DEFAULT_ENABLE_TRACKING))): bool
            }
        )
        return self.async_show_form(step_id="tracking_gate", data_schema=schema, errors=errors)

    async def async_step_tracking(self, user_input: dict[str, Any] | None = None):
        """Step 6: Tracking Details (nur wenn aktiviert)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # (Optional) leichte Normalisierung: Strings trimmen
            user_input[CONF_TRACK_CALLSIGNS] = str(user_input.get(CONF_TRACK_CALLSIGNS, "") or "").strip()
            user_input[CONF_TRACK_REGISTRATIONS] = str(user_input.get(CONF_TRACK_REGISTRATIONS, "") or "").strip()

            self._data.update(user_input)
            return await self._finish()

        schema = vol.Schema(
            {
                vol.Required(CONF_TRACK_MODE, default=str(self._data.get(CONF_TRACK_MODE, DEFAULT_TRACK_MODE))): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"label": "Callsign (z. B. CHX16)", "value": TRACK_MODE_CALLSIGN},
                            {"label": "Registrierung (z. B. D-HXYZ)", "value": TRACK_MODE_REGISTRATION},
                            {"label": "Beides", "value": TRACK_MODE_BOTH},
                        ],
                        mode="dropdown",
                    )
                ),
                vol.Optional(CONF_TRACK_CALLSIGNS, default=str(self._data.get(CONF_TRACK_CALLSIGNS, DEFAULT_TRACK_CALLSIGNS))): str,
                vol.Optional(CONF_TRACK_REGISTRATIONS, default=str(self._data.get(CONF_TRACK_REGISTRATIONS, DEFAULT_TRACK_REGISTRATIONS))): str,
            }
        )

        return self.async_show_form(step_id="tracking", data_schema=schema, errors=errors)

    async def _finish(self):
        """Create final entry (nur die relevanten Keys speichern)."""
        mode = self._data.get(CONF_MODE, DEFAULT_MODE)

        data: dict[str, Any] = {
            CONF_MODE: mode,
            CONF_SCAN_INTERVAL: int(self._data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
            CONF_ENABLE_TRACKING: bool(self._data.get(CONF_ENABLE_TRACKING, DEFAULT_ENABLE_TRACKING)),
        }

        # FR24
        if mode in (MODE_FR24, MODE_BOTH):
            data[CONF_FR24_ENTITY] = self._data.get(CONF_FR24_ENTITY)

        # ADSB
        if mode in (MODE_ADSB, MODE_BOTH):
            data[CONF_ADSB_SOURCE] = self._data.get(CONF_ADSB_SOURCE, DEFAULT_ADSB_SOURCE)
            if data[CONF_ADSB_SOURCE] == ADSB_SOURCE_URL:
                data[CONF_ADSB_URL] = self._data.get(CONF_ADSB_URL, "")
            else:
                data[CONF_ADSB_ENTITY] = self._data.get(CONF_ADSB_ENTITY)

        # Tracking
        if data[CONF_ENABLE_TRACKING]:
            data[CONF_TRACK_MODE] = self._data.get(CONF_TRACK_MODE, DEFAULT_TRACK_MODE)
            data[CONF_TRACK_CALLSIGNS] = self._data.get(CONF_TRACK_CALLSIGNS, "")
            data[CONF_TRACK_REGISTRATIONS] = self._data.get(CONF_TRACK_REGISTRATIONS, "")

        return self.async_create_entry(title="Air Traffic Merge", data=data)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return AirTrafficMergeOptionsFlow(config_entry)


class AirTrafficMergeOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry
        self._data: dict[str, Any] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        # Options nutzt denselben Wizard — wir starten mit User-Step,
        # aber mit Defaults aus entry.data + entry.options
        if not self._data:
            defaults = dict(self.config_entry.data)
            defaults.update(dict(self.config_entry.options or {}))
            self._data.update(defaults)
        flow = AirTrafficMergeFlow()
        flow._data = dict(self._data)  # seed

        # OptionsFlow muss eigenständig laufen -> wir spiegeln die Steps minimal:
        # Wir springen direkt zum "user"-Step, aber mit defaults.
        # (HA ruft nur async_step_init auf)
        return await self._step_user(flow, user_input=None)

    async def _step_user(self, flow: AirTrafficMergeFlow, user_input: dict[str, Any] | None):
        # Im Options-Flow lassen wir dich erneut konfigurieren.
        return await flow.async_step_user(user_input)

    # Home Assistant erwartet OptionsFlow mit async_step_init -> done
    # Das Speichern erfolgt automatisch, weil ConfigFlow create_entry macht.
