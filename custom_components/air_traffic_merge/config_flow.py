from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_SOURCE_MODE,
    CONF_FR24_ENTITY,
    CONF_ADSB_SOURCE,
    CONF_ADSB_URL,
    CONF_ADSB_ENTITY,
    CONF_SCAN_INTERVAL,
    CONF_ENABLE_TRACKING,
    CONF_TRACK_MODE,
    CONF_TRACK_CALLSIGNS,
    CONF_TRACK_REGISTRATIONS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_ADSB_SOURCE,
    DEFAULT_ENABLE_TRACKING,
    DEFAULT_TRACK_MODE,
    DEFAULT_TRACK_CALLSIGNS,
    DEFAULT_TRACK_REGISTRATIONS,
)

SOURCE_FR24_ONLY = "fr24_only"
SOURCE_ADSB_ONLY = "adsb_only"
SOURCE_BOTH = "both"


def _normalize_adsb_url(url: str) -> str:
    """Accept either full aircraft.json URL or a base URL and normalize.

    Examples:
    - http://1.2.3.4:8080/data/aircraft.json  (kept)
    - http://1.2.3.4:8080                    (-> /data/aircraft.json)
    - http://1.2.3.4:8080/                   (-> /data/aircraft.json)
    - http://1.2.3.4:8080/data               (-> /data/aircraft.json)
    """
    u = (url or "").strip()
    if not u:
        return u
    if not (u.startswith("http://") or u.startswith("https://")):
        return u

    # If user already provided aircraft.json, keep as-is
    if "aircraft.json" in u:
        return u

    # If they gave a base URL or folder URL, append standard path
    u = u.rstrip("/")
    return f"{u}/data/aircraft.json"


class AirTrafficMergeFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(self, user_input=None):
        """Step 1: Choose which sources to use."""
        errors = {}

        if user_input is not None:
            self._data.update(user_input)

            source_mode = self._data.get(CONF_SOURCE_MODE, SOURCE_BOTH)
            enable_tracking = bool(self._data.get(CONF_ENABLE_TRACKING, DEFAULT_ENABLE_TRACKING))
            self._data[CONF_ENABLE_TRACKING] = enable_tracking

            # Next step based on chosen sources
            if source_mode in (SOURCE_FR24_ONLY, SOURCE_BOTH):
                return await self.async_step_fr24()

            if source_mode in (SOURCE_ADSB_ONLY,):
                return await self.async_step_adsb_source()

            errors["base"] = "invalid_source_mode"

        schema = vol.Schema(
            {
                vol.Required(CONF_SOURCE_MODE, default=SOURCE_BOTH): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"label": "Beides (FR24 + ADS-B)", "value": SOURCE_BOTH},
                            {"label": "Nur Flightradar24 (FR24)", "value": SOURCE_FR24_ONLY},
                            {"label": "Nur ADS-B (lokal)", "value": SOURCE_ADSB_ONLY},
                        ],
                        mode="dropdown",
                    )
                ),
                vol.Optional(CONF_ENABLE_TRACKING, default=DEFAULT_ENABLE_TRACKING): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_fr24(self, user_input=None):
        """Step 2 (optional): FR24 entity selection."""
        errors = {}

        if user_input is not None:
            fr24_entity = user_input.get(CONF_FR24_ENTITY)
            if not fr24_entity:
                errors[CONF_FR24_ENTITY] = "missing_entity"
            else:
                self._data.update(user_input)

                source_mode = self._data.get(CONF_SOURCE_MODE, SOURCE_BOTH)
                if source_mode == SOURCE_FR24_ONLY:
                    # If tracking enabled -> go to tracking, else finish
                    if self._data.get(CONF_ENABLE_TRACKING):
                        return await self.async_step_tracking_mode()
                    return self._create_entry()

                return await self.async_step_adsb_source()

        schema = vol.Schema(
            {
                vol.Required(CONF_FR24_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                )
            }
        )

        return self.async_show_form(
            step_id="fr24",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_adsb_source(self, user_input=None):
        """Step 3: Choose ADS-B input method."""
        errors = {}

        if user_input is not None:
            self._data.update(user_input)

            adsb_source = self._data.get(CONF_ADSB_SOURCE, DEFAULT_ADSB_SOURCE)
            if adsb_source == "url":
                return await self.async_step_adsb_url()
            return await self.async_step_adsb_entity()

        schema = vol.Schema(
            {
                vol.Required(CONF_ADSB_SOURCE, default=self._data.get(CONF_ADSB_SOURCE, DEFAULT_ADSB_SOURCE)): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"label": "ADS-B per URL (aircraft.json)", "value": "url"},
                            {"label": "ADS-B bestehender Sensor (attributes.aircraft)", "value": "entity"},
                        ],
                        mode="dropdown",
                    )
                ),
                vol.Optional(CONF_SCAN_INTERVAL, default=int(self._data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))): vol.Coerce(int),
            }
        )

        return self.async_show_form(
            step_id="adsb_source",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "url_hint": "Hinweis: Du kannst entweder die komplette URL inkl. /data/aircraft.json angeben – oder nur die Basis-URL (z.B. http://192.168.178.186:8080). Die Integration ergänzt /data/aircraft.json automatisch."
            },
        )

    async def async_step_adsb_url(self, user_input=None):
        """Step 4a: ADS-B URL."""
        errors = {}

        if user_input is not None:
            url_raw = str(user_input.get(CONF_ADSB_URL, "") or "").strip()
            url = _normalize_adsb_url(url_raw)

            if not (url.startswith("http://") or url.startswith("https://")):
                errors[CONF_ADSB_URL] = "invalid_url"
            else:
                # Save normalized URL and ensure we do NOT keep entity fields
                self._data[CONF_ADSB_URL] = url
                self._data.pop(CONF_ADSB_ENTITY, None)

                # Tracking?
                if self._data.get(CONF_ENABLE_TRACKING):
                    return await self.async_step_tracking_mode()
                return self._create_entry()

        schema = vol.Schema(
            {
                vol.Required(CONF_ADSB_URL, default=self._data.get(CONF_ADSB_URL, "")): str,
            }
        )

        return self.async_show_form(
            step_id="adsb_url",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "url_hint": "Beispiel: http://192.168.178.186:8080/data/aircraft.json  (oder nur http://192.168.178.186:8080)"
            },
        )

    async def async_step_adsb_entity(self, user_input=None):
        """Step 4b: Existing ADS-B sensor entity."""
        errors = {}

        if user_input is not None:
            ent = user_input.get(CONF_ADSB_ENTITY)
            if not ent:
                errors[CONF_ADSB_ENTITY] = "missing_entity"
            else:
                self._data[CONF_ADSB_ENTITY] = ent
                self._data.pop(CONF_ADSB_URL, None)

                if self._data.get(CONF_ENABLE_TRACKING):
                    return await self.async_step_tracking_mode()
                return self._create_entry()

        schema = vol.Schema(
            {
                vol.Required(CONF_ADSB_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                )
            }
        )

        return self.async_show_form(
            step_id="adsb_entity",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_tracking_mode(self, user_input=None):
        """Step 5: Tracking mode (only if enabled)."""
        errors = {}

        if user_input is not None:
            self._data.update(user_input)
            mode = self._data.get(CONF_TRACK_MODE, DEFAULT_TRACK_MODE)

            if mode not in ("callsign", "registration", "both"):
                errors["base"] = "invalid_track_mode"
            else:
                return await self.async_step_tracking_values()

        schema = vol.Schema(
            {
                vol.Required(CONF_TRACK_MODE, default=self._data.get(CONF_TRACK_MODE, DEFAULT_TRACK_MODE)): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"label": "Callsign (z. B. CHX16)", "value": "callsign"},
                            {"label": "Registrierung (z. B. D-HXYZ)", "value": "registration"},
                            {"label": "Beides", "value": "both"},
                        ],
                        mode="dropdown",
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="tracking_mode",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_tracking_values(self, user_input=None):
        """Step 6: Tracking values depending on mode."""
        errors = {}
        mode = self._data.get(CONF_TRACK_MODE, DEFAULT_TRACK_MODE)

        if user_input is not None:
            # Store values depending on mode
            if mode in ("callsign", "both"):
                self._data[CONF_TRACK_CALLSIGNS] = str(user_input.get(CONF_TRACK_CALLSIGNS, "") or "")
            else:
                self._data.pop(CONF_TRACK_CALLSIGNS, None)

            if mode in ("registration", "both"):
                self._data[CONF_TRACK_REGISTRATIONS] = str(user_input.get(CONF_TRACK_REGISTRATIONS, "") or "")
            else:
                self._data.pop(CONF_TRACK_REGISTRATIONS, None)

            return self._create_entry()

        fields = {}

        if mode in ("callsign", "both"):
            fields[vol.Optional(CONF_TRACK_CALLSIGNS, default=self._data.get(CONF_TRACK_CALLSIGNS, DEFAULT_TRACK_CALLSIGNS))] = str
        if mode in ("registration", "both"):
            fields[vol.Optional(CONF_TRACK_REGISTRATIONS, default=self._data.get(CONF_TRACK_REGISTRATIONS, DEFAULT_TRACK_REGISTRATIONS))] = str

        schema = vol.Schema(fields)

        return self.async_show_form(
            step_id="tracking_values",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "hint": "Mehrere Werte mit Komma trennen, z. B. CHX16,CHX18 oder D-HXYZ,D-ABCD."
            },
        )

    @callback
    def _create_entry(self):
        """Create entry with clean data according to selected mode."""
        data = dict(self._data)

        # Clean data depending on source mode
        source_mode = data.get(CONF_SOURCE_MODE, SOURCE_BOTH)

        if source_mode == SOURCE_ADSB_ONLY:
            data.pop(CONF_FR24_ENTITY, None)
        elif source_mode == SOURCE_FR24_ONLY:
            data.pop(CONF_ADSB_SOURCE, None)
            data.pop(CONF_ADSB_URL, None)
            data.pop(CONF_ADSB_ENTITY, None)
            data.pop(CONF_SCAN_INTERVAL, None)

        # Clean tracking if disabled
        if not data.get(CONF_ENABLE_TRACKING, False):
            data.pop(CONF_TRACK_MODE, None)
            data.pop(CONF_TRACK_CALLSIGNS, None)
            data.pop(CONF_TRACK_REGISTRATIONS, None)

        # Ensure scan_interval exists if ADS-B is used
        if source_mode in (SOURCE_ADSB_ONLY, SOURCE_BOTH):
            data[CONF_SCAN_INTERVAL] = int(data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

        return self.async_create_entry(title="Air Traffic Merge", data=data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return AirTrafficMergeOptionsFlow(config_entry)


class AirTrafficMergeOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry
        self._data: dict = dict(config_entry.data)
        self._data.update(dict(config_entry.options or {}))

    async def async_step_init(self, user_input=None):
        # Start in the same step as user step
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        flow = AirTrafficMergeFlow()
        flow.hass = self.hass  # type: ignore
        flow._data = dict(self._data)  # reuse saved values
        return await flow.async_step_user(user_input)

    async def async_step_fr24(self, user_input=None):
        flow = AirTrafficMergeFlow()
        flow.hass = self.hass  # type: ignore
        flow._data = dict(self._data)
        result = await flow.async_step_fr24(user_input)
        if result.get("type") == "create_entry":
            return self.async_create_entry(title="", data=result["data"])
        return result

    async def async_step_adsb_source(self, user_input=None):
        flow = AirTrafficMergeFlow()
        flow.hass = self.hass  # type: ignore
        flow._data = dict(self._data)
        result = await flow.async_step_adsb_source(user_input)
        if result.get("type") == "create_entry":
            return self.async_create_entry(title="", data=result["data"])
        return result

    async def async_step_adsb_url(self, user_input=None):
        flow = AirTrafficMergeFlow()
        flow.hass = self.hass  # type: ignore
        flow._data = dict(self._data)
        result = await flow.async_step_adsb_url(user_input)
        if result.get("type") == "create_entry":
            return self.async_create_entry(title="", data=result["data"])
        return result

    async def async_step_adsb_entity(self, user_input=None):
        flow = AirTrafficMergeFlow()
        flow.hass = self.hass  # type: ignore
        flow._data = dict(self._data)
        result = await flow.async_step_adsb_entity(user_input)
        if result.get("type") == "create_entry":
            return self.async_create_entry(title="", data=result["data"])
        return result

    async def async_step_tracking_mode(self, user_input=None):
        flow = AirTrafficMergeFlow()
        flow.hass = self.hass  # type: ignore
        flow._data = dict(self._data)
        result = await flow.async_step_tracking_mode(user_input)
        if result.get("type") == "create_entry":
            return self.async_create_entry(title="", data=result["data"])
        return result

    async def async_step_tracking_values(self, user_input=None):
        flow = AirTrafficMergeFlow()
        flow.hass = self.hass  # type: ignore
        flow._data = dict(self._data)
        result = await flow.async_step_tracking_values(user_input)
        if result.get("type") == "create_entry":
            return self.async_create_entry(title="", data=result["data"])
        return result
