from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

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
    DEFAULT_ADSB_SOURCE,
    DEFAULT_ENABLE_TRACKING,
    DEFAULT_TRACK_CALLSIGNS,
    DEFAULT_TRACK_REGISTRATIONS,
    DEFAULT_TRACK_MODE,
    DEFAULT_SCAN_INTERVAL,
)


def _s(v: Any) -> str:
    return str(v).strip() if v is not None else ""


def _feet_to_m(feet: Any) -> Optional[float]:
    try:
        return round(int(feet) * 0.3048, 0)
    except Exception:
        return None


def _knots_to_kmh(knots: Any) -> Optional[float]:
    try:
        return round(float(knots) * 1.852, 0)
    except Exception:
        return None


def _parse_list(s: str) -> list[str]:
    parts = [p.strip() for p in (s or "").split(",")]
    return [p for p in parts if p]


def _parse_callsigns(s: str) -> list[str]:
    return [p.upper() for p in _parse_list(s)]


def _parse_regs(s: str) -> list[str]:
    # registrations are typically case-insensitive, keep upper
    return [p.upper() for p in _parse_list(s)]


def _sanitize_id(s: str) -> str:
    # for unique_id / entity ids
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in s).strip("_")


@dataclass
class MergedFlight:
    key: str
    registration: str
    hex: str
    callsign: str
    source: str  # "FR24" | "ADSB" | "BOTH"
    aircraft_model: str
    airline: str
    alt_m: Optional[float]
    spd_kmh: Optional[float]
    dist_km: Optional[float]
    dir_deg: Optional[float]
    tracked: bool = False
    tracked_by: str = ""   # "callsign" | "registration"
    tracked_target: str = ""


class AirTrafficCoordinator:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.session = async_get_clientsession(hass)

        self.last_update_ts: float = 0.0
        self.fr24_count: int = 0
        self.adsb_count: int = 0
        self.merged: list[MergedFlight] = []

        self.tracking_enabled: bool = False
        self.track_mode: str = DEFAULT_TRACK_MODE
        self.tracked_callsigns: list[str] = []
        self.tracked_regs: list[str] = []
        self.tracked_active: list[str] = []
        self.tracked_active_count: int = 0
        self._prev_tracked_active: set[str] = set()

        self.reload_from_entry()

    def reload_from_entry(self) -> None:
        data = dict(self.entry.data)
        opts = dict(self.entry.options or {})

        self.fr24_entity = opts.get(CONF_FR24_ENTITY, data.get(CONF_FR24_ENTITY))

        self.adsb_source = opts.get(CONF_ADSB_SOURCE, data.get(CONF_ADSB_SOURCE, DEFAULT_ADSB_SOURCE))
        self.adsb_url = opts.get(CONF_ADSB_URL, data.get(CONF_ADSB_URL))
        self.adsb_entity = opts.get(CONF_ADSB_ENTITY, data.get(CONF_ADSB_ENTITY))

        self.scan_interval = int(opts.get(CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)))

        self.tracking_enabled = bool(opts.get(CONF_ENABLE_TRACKING, data.get(CONF_ENABLE_TRACKING, DEFAULT_ENABLE_TRACKING)))
        self.track_mode = str(opts.get(CONF_TRACK_MODE, data.get(CONF_TRACK_MODE, DEFAULT_TRACK_MODE)))

        self.tracked_callsigns = _parse_callsigns(opts.get(CONF_TRACK_CALLSIGNS, data.get(CONF_TRACK_CALLSIGNS, DEFAULT_TRACK_CALLSIGNS)))
        self.tracked_regs = _parse_regs(opts.get(CONF_TRACK_REGISTRATIONS, data.get(CONF_TRACK_REGISTRATIONS, DEFAULT_TRACK_REGISTRATIONS)))

    async def async_refresh(self) -> None:
        self.reload_from_entry()

        fr24_state = self.hass.states.get(self.fr24_entity) if self.fr24_entity else None
        fr24_flights = []
        if fr24_state and isinstance(fr24_state.attributes, dict):
            fr24_flights = fr24_state.attributes.get("flights") or []
        if not isinstance(fr24_flights, list):
            fr24_flights = []

        adsb_aircraft = []
        now_ts = 0

        if self.adsb_source == "entity":
            ent = self.hass.states.get(self.adsb_entity) if self.adsb_entity else None
            if ent and isinstance(ent.attributes, dict):
                adsb_aircraft = ent.attributes.get("aircraft") or []
                now_ts = ent.attributes.get("now") or 0
            if not isinstance(adsb_aircraft, list):
                adsb_aircraft = []
        else:
            adsb_json = await self._fetch_adsb_json()
            adsb_aircraft = (adsb_json or {}).get("aircraft") or []
            now_ts = (adsb_json or {}).get("now") or 0
            if not isinstance(adsb_aircraft, list):
                adsb_aircraft = []

        self.last_update_ts = float(now_ts or dt_util.utcnow().timestamp())
        self.fr24_count = len(fr24_flights)
        self.adsb_count = len(adsb_aircraft)

        self.merged = self._merge(fr24_flights, adsb_aircraft)

        # tracking active list
        active_targets: list[str] = []
        for m in self.merged:
            if m.tracked and m.tracked_target:
                active_targets.append(m.tracked_target)

        seen = set()
        self.tracked_active = []
        for t in active_targets:
            if t not in seen:
                seen.add(t)
                self.tracked_active.append(t)
        self.tracked_active_count = len(self.tracked_active)

        # Fire events for tracked targets appearing/disappearing
        try:
            current = set(self.tracked_active)
            prev = set(self._prev_tracked_active)
            appeared = sorted(list(current - prev))
            disappeared = sorted(list(prev - current))

            for t in appeared:
                self.hass.bus.async_fire(
                    f"{DOMAIN}_tracked",
                    {
                        "action": "appeared",
                        "target": t,
                        "last_update": self.last_update_ts,
                        "track_mode": self.track_mode,
                    },
                )
            for t in disappeared:
                self.hass.bus.async_fire(
                    f"{DOMAIN}_tracked",
                    {
                        "action": "disappeared",
                        "target": t,
                        "last_update": self.last_update_ts,
                        "track_mode": self.track_mode,
                    },
                )

            self._prev_tracked_active = current
        except Exception:
            # Never break updates due to event logic
            pass

    async def _fetch_adsb_json(self) -> dict[str, Any] | None:
        if not self.adsb_url:
            return None
        try:
            async with asyncio.timeout(8):
                resp = await self.session.get(self.adsb_url)
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except Exception:
            return None

    def _is_tracked(self, callsign: str, reg: str) -> tuple[bool, str, str]:
        if not self.tracking_enabled:
            return (False, "", "")
        cs = _s(callsign).upper()
        rg = _s(reg).upper()

        mode = self.track_mode
        if mode not in ("callsign", "registration", "both"):
            mode = "callsign"

        if mode in ("callsign", "both") and cs and cs in set(self.tracked_callsigns):
            return (True, "callsign", cs)
        if mode in ("registration", "both") and rg and rg in set(self.tracked_regs):
            return (True, "registration", rg)
        return (False, "", "")

    def _merge(self, fr24: list[dict[str, Any]], adsb: list[dict[str, Any]]) -> list[MergedFlight]:
        adsb_by_reg: dict[str, dict[str, Any]] = {}
        adsb_by_hex_only: dict[str, dict[str, Any]] = {}

        for a in adsb:
            if not isinstance(a, dict):
                continue
            reg = _s(a.get("r"))
            hx = _s(a.get("hex"))
            if reg:
                adsb_by_reg[reg] = a
            elif hx:
                adsb_by_hex_only[hx] = a

        fr24_by_reg: dict[str, dict[str, Any]] = {}
        for f in fr24:
            if not isinstance(f, dict):
                continue
            reg = _s(f.get("aircraft_registration"))
            if reg:
                fr24_by_reg[reg] = f

        keys: list[str] = []
        keys.extend(fr24_by_reg.keys())
        keys.extend(adsb_by_reg.keys())
        keys.extend(adsb_by_hex_only.keys())

        seen: set[str] = set()
        uniq_keys: list[str] = []
        for k in keys:
            if k and k not in seen:
                seen.add(k)
                uniq_keys.append(k)

        merged: list[MergedFlight] = []
        for key in uniq_keys:
            f = fr24_by_reg.get(key)
            a = adsb_by_reg.get(key) or adsb_by_hex_only.get(key)

            reg = _s(a.get("r")) if a else (_s(f.get("aircraft_registration")) if f else "")
            hx = _s(a.get("hex")) if a else ""
            fn = _s(f.get("flight_number")) if f else ""
            cs = _s(a.get("flight")) if a else ""

            callsign = fn or cs or reg or (f"HEX {hx}" if hx else "—")

            airline = _s(f.get("airline_short")) if f else ""
            model = _s(f.get("aircraft_model")) if f else ""

            alt_m = _feet_to_m(a.get("alt_baro")) if a else None
            spd_kmh = _knots_to_kmh(a.get("gs")) if a else None

            dist_km = None
            dir_deg = None
            try:
                dist_km = round(float(a.get("r_dst")), 1) if a and a.get("r_dst") is not None else None
            except Exception:
                pass
            try:
                dir_deg = round(float(a.get("r_dir")), 0) if a and a.get("r_dir") is not None else None
            except Exception:
                pass

            if f and a:
                source = "BOTH"
            elif f:
                source = "FR24"
            else:
                source = "ADSB"

            tracked, tracked_by, tracked_target = self._is_tracked(fn or cs, reg)

            merged.append(
                MergedFlight(
                    key=key,
                    registration=reg,
                    hex=hx,
                    callsign=callsign,
                    source=source,
                    aircraft_model=model,
                    airline=airline,
                    alt_m=alt_m,
                    spd_kmh=spd_kmh,
                    dist_km=dist_km,
                    dir_deg=dir_deg,
                    tracked=tracked,
                    tracked_by=tracked_by,
                    tracked_target=tracked_target,
                )
            )

        def _sort_key(m: MergedFlight):
            tracked_rank = 0 if m.tracked else 1
            src_rank = {"BOTH": 0, "ADSB": 1, "FR24": 2}.get(m.source, 9)
            dist = m.dist_km if m.dist_km is not None else 9999
            return (tracked_rank, src_rank, dist, m.registration or m.hex or m.key)

        merged.sort(key=_sort_key)
        return merged
