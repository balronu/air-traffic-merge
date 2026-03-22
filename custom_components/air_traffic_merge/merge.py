from __future__ import annotations

from typing import Any

from .const import (
    CATEGORY_BUSINESS,
    CATEGORY_CIVIL,
    CATEGORY_GA,
    CATEGORY_HELI,
    CATEGORY_MEDICAL,
    CATEGORY_MILITARY,
    CATEGORY_MILITARY_FIGHTER,
    CATEGORY_MILITARY_HELI,
    CATEGORY_MILITARY_ISR,
    CATEGORY_MILITARY_TANKER,
    CATEGORY_MILITARY_TRANSPORT,
)

TYPE_NAMES = {
    "A321": "Airbus A321",
    "A319": "Airbus A319",
    "A20N": "Airbus A320neo",
    "A21N": "Airbus A321neo",
    "A359": "Airbus A350-900",
    "A333": "Airbus A330-300",
    "A332": "Airbus A330-200",
    "B738": "Boeing 737-800",
    "B38M": "Boeing 737 MAX 8",
    "B789": "Boeing 787-9",
    "DH8D": "De Havilland Dash 8 Q400",
    "E190": "Embraer 190",
    "FA7X": "Dassault Falcon 7X",
    "EC35": "Eurocopter EC135/145",
    "H145": "Airbus H145",
    "LJ45": "Learjet 45",
    "LJ35": "Learjet 35A",
    "GLF6": "Gulfstream G650",
    "GLF5": "Gulfstream G550",
    "PC24": "Pilatus PC-24",
    "C130": "Lockheed C-130 Hercules",
    "A400": "Airbus A400M",
    "KC35R": "Boeing KC-135R",
    "E3TF": "Boeing E-3 Sentry",
}

FIGHTER_CODES = {"EUFI", "F16", "F18", "TOR", "RAPT"}
TANKER_CODES = {"KC35R", "K35R", "A330", "KC46"}
TRANSPORT_CODES = {"C130", "A400", "C17", "C27J", "C160"}
AWACS_CODES = {"E3TF", "E3CF", "P8", "R135", "U2"}
HELI_CODES = {"EC35", "H145", "BK17", "A109", "R44", "B06", "AS32", "EC45", "EC55"}
BUSINESS_CODES = {"FA7X", "E55P", "GLF5", "GLF6", "LJ35", "LJ45", "PC24", "C25A", "C25B", "C25C"}
GA_CODES = {"C150", "C152", "C172", "DA40", "DA42", "P28A", "SR22"}

MEDICAL_PREFIXES = ("CHX", "CHRISTOPH", "ADAC", "DRF", "LIFE", "REGA", "NHC", "ITH", "RTH")
MILITARY_PREFIXES = (
    "GAF", "RCH", "REACH", "NATO", "DUKE", "ASCOT", "SHEPHERD", "MMF", "IAM", "BAF", "ADF",
    "HERKY", "SAM", "MC", "PAT", "QID", "RRR", "AME", "HKY", "CFC", "CNV", "PEGASUS", "MOOSE",
    "ROYAL", "NAVY", "LAGR", "PACK", "TABOR", "SPAR",
)
MILITARY_MODEL_KEYWORDS = (
    "AIR FORCE", "LUFTWAFFE", "ARMEE DE L AIR", "ARMÉE DE L AIR", "ROYAL AIR FORCE", "USAF", "NATO",
    "A400M", "C-130", "C130", "SUPER HERCULES", "GLOBEMASTER", "STRATOTANKER", "PEGASUS", "SENTRY",
    "AWACS", "EUROFIGHTER", "TORNADO", "BLACK HAWK",
)
HELI_MODEL_KEYWORDS = ("H145", "EC145", "EC135", "H135", "BK117", "AW139", "AW169", "HELICOPTER", "HELIKOPTER", "ROBINSON", "BLACK HAWK")


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _upper(value: Any) -> str:
    return _clean(value).upper()


def _fr24_callsign(f: dict[str, Any]) -> str:
    return _clean(f.get("flight_number") or f.get("callsign") or f.get("flight"))


def _fr24_registration(f: dict[str, Any]) -> str:
    return _upper(f.get("aircraft_registration") or f.get("registration") or f.get("reg"))


def _fr24_model(f: dict[str, Any]) -> str:
    return _clean(f.get("aircraft_model") or f.get("model") or f.get("aircraft_type"))


def _fr24_airline(f: dict[str, Any]) -> str:
    return _clean(f.get("airline_short") or f.get("airline") or f.get("operator"))


def _classify(callsign: str, registration: str, typecode: str, model: str, airline: str) -> tuple[str, str, int]:
    callsign_u = _upper(callsign)
    reg_u = _upper(registration)
    type_u = _upper(typecode)
    model_u = _upper(model)
    airline_u = _upper(airline)

    is_medical = callsign_u.startswith(MEDICAL_PREFIXES)
    is_heli = type_u in HELI_CODES or any(word in model_u for word in HELI_MODEL_KEYWORDS)

    is_military = False
    if callsign_u.startswith(MILITARY_PREFIXES):
        is_military = True
        reason = "Erkannt über Callsign"
    elif "+" in reg_u or ("-" in reg_u and len(reg_u) > 1 and reg_u[:2].isdigit()):
        is_military = True
        reason = "Erkannt über militärische Registrierung"
    elif any(word in model_u or word in airline_u for word in MILITARY_MODEL_KEYWORDS):
        is_military = True
        reason = "Erkannt über Modell/Betreiber"
    else:
        reason = "Standard-Fallback"

    if is_medical:
        return CATEGORY_MEDICAL, "Erkannt über Callsign", 1
    if type_u in FIGHTER_CODES:
        return CATEGORY_MILITARY_FIGHTER, "Erkannt über Typecode", 3
    if type_u in TANKER_CODES:
        return CATEGORY_MILITARY_TANKER, "Erkannt über Typecode", 4
    if type_u in TRANSPORT_CODES:
        return CATEGORY_MILITARY_TRANSPORT, "Erkannt über Typecode", 5
    if type_u in AWACS_CODES:
        return CATEGORY_MILITARY_ISR, "Erkannt über Typecode", 6
    if is_military and is_heli:
        return CATEGORY_MILITARY_HELI, reason, 7
    if is_military:
        return CATEGORY_MILITARY, reason, 8
    if is_heli:
        return CATEGORY_HELI, "Erkannt über Typecode/Modell", 10
    if type_u in BUSINESS_CODES:
        return CATEGORY_BUSINESS, "Erkannt über Typecode", 20
    if type_u in GA_CODES:
        return CATEGORY_GA, "Erkannt über Typecode", 30
    return CATEGORY_CIVIL, "Standard-Fallback", 50


def _source_text(has_fr24: bool, has_adsb: bool) -> tuple[str, int]:
    if has_fr24 and has_adsb:
        return "✅ FR24 + ADS-B verfügbar", 0
    if has_fr24:
        return "⚠️ Nur FR24 verfügbar", 1
    return "📡 Nur ADS-B empfangen", 2


def _tracked(callsign: str, registration: str, tracked_callsigns: set[str], tracked_regs: set[str]) -> bool:
    return _upper(callsign) in tracked_callsigns or _upper(registration) in tracked_regs


def merge_flights(
    fr24_flights: list[dict[str, Any]],
    adsb_aircraft: list[dict[str, Any]],
    *,
    max_items: int,
    tracked_callsigns: str,
    tracked_registrations: str,
) -> dict[str, Any]:
    tracked_cs = {_upper(v) for v in tracked_callsigns.split(",") if _clean(v)}
    tracked_regs = {_upper(v) for v in tracked_registrations.split(",") if _clean(v)}

    by_key: dict[str, dict[str, Any]] = {}

    for f in fr24_flights:
        reg = _fr24_registration(f)
        fallback_key = f"fr24::{_upper(_fr24_callsign(f)) or _upper(_fr24_model(f)) or len(by_key)}"
        key = reg or fallback_key
        by_key.setdefault(key, {})["fr24"] = f

    for a in adsb_aircraft:
        reg = _upper(a.get("r") or a.get("registration"))
        hex_code = _upper(a.get("hex"))
        key = reg or hex_code or f"adsb::{_upper(a.get('flight')) or len(by_key)}"
        by_key.setdefault(key, {})["adsb"] = a

    flights: list[dict[str, Any]] = []
    counts = {
        "medical": 0,
        "military": 0,
        "helicopter": 0,
        "business": 0,
        "general_aviation": 0,
        "civil": 0,
    }
    merged_count = 0
    tracked_present = False

    for item in by_key.values():
        f = item.get("fr24", {})
        a = item.get("adsb", {})

        callsign = _clean(a.get("flight")) or _fr24_callsign(f)
        registration = _upper(a.get("r") or a.get("registration")) or _fr24_registration(f)
        typecode = _upper(a.get("t") or a.get("typecode") or a.get("aircraft_type"))
        model = _clean(a.get("desc") or TYPE_NAMES.get(typecode) or _fr24_model(f))
        airline = _clean(a.get("ownOp") or a.get("op") or _fr24_airline(f))
        name = _fr24_callsign(f) or callsign or registration or _upper(a.get("hex")) or "Unbekannt"

        category, reason, priority = _classify(callsign, registration, typecode, model, airline)
        source_text, source_prio = _source_text(bool(f), bool(a))
        tracked = _tracked(callsign, registration, tracked_cs, tracked_regs)
        tracked_present = tracked_present or tracked

        if f and a:
            merged_count += 1

        flight = {
            "name": name,
            "callsign": callsign,
            "registration": registration or "unbekannt",
            "hex": _upper(a.get("hex")) or "—",
            "typecode": typecode or "—",
            "type_name": model,
            "airline": airline,
            "category": category,
            "reason": reason,
            "source_text": source_text,
            "dist_km": float(a.get("r_dst", 9999) or 9999),
            "dir_deg": round(float(a.get("r_dir", 0) or 0)),
            "alt_m": round(float(a.get("alt_baro", 0) or 0) * 0.3048) if a else None,
            "spd_kmh": round(float(a.get("gs", 0) or 0) * 1.852) if a else None,
            "tracked": tracked,
            "priority": priority,
            "source_prio": source_prio,
        }
        flights.append(flight)

        if category == CATEGORY_MEDICAL:
            counts["medical"] += 1
        elif category in {
            CATEGORY_MILITARY,
            CATEGORY_MILITARY_FIGHTER,
            CATEGORY_MILITARY_TANKER,
            CATEGORY_MILITARY_TRANSPORT,
            CATEGORY_MILITARY_ISR,
            CATEGORY_MILITARY_HELI,
        }:
            counts["military"] += 1
        elif category == CATEGORY_HELI:
            counts["helicopter"] += 1
        elif category == CATEGORY_BUSINESS:
            counts["business"] += 1
        elif category == CATEGORY_GA:
            counts["general_aviation"] += 1
        else:
            counts["civil"] += 1

    flights.sort(key=lambda x: (bool(x["tracked"]) is False, x["priority"], x["source_prio"], x["dist_km"]))
    flights = flights[:max_items]

    last_update = None
    if adsb_aircraft:
        last_update = adsb_aircraft[0].get("seen")

    return {
        "flights": flights,
        "counts": counts,
        "fr24_count": len(fr24_flights),
        "adsb_count": len(adsb_aircraft),
        "merged_count": merged_count,
        "tracked_present": tracked_present,
        "last_update": last_update,
    }
