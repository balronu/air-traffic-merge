from __future__ import annotations

from datetime import datetime, UTC
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
    "A139": "AgustaWestland AW139",
    "A169": "Leonardo AW169",
    "A3ST": "Airbus A330 MRTT",
    "A400": "Airbus A400M Atlas",
    "A20N": "Airbus A320neo",
    "A21N": "Airbus A321neo",
    "B38M": "Boeing 737 MAX 8",
    "BK117": "MBB/Kawasaki BK117",
    "C130": "Lockheed C-130 Hercules",
    "C30J": "Lockheed Martin C-130J-30 Super Hercules",
    "C17": "Boeing C-17 Globemaster III",
    "EC35": "Airbus H135 / EC135",
    "E3CF": "Boeing E-3 Sentry",
    "E3TF": "Boeing E-3 Sentry",
    "EUFI": "Eurofighter Typhoon",
    "F16": "F-16 Fighting Falcon",
    "F18": "F/A-18 Hornet",
    "H145": "Airbus H145",
    "H160": "Airbus H160",
    "K35R": "KC-135 Stratotanker",
    "KC46": "KC-46 Pegasus",
    "TOR": "Panavia Tornado",
    "UH60": "Sikorsky UH-60 Black Hawk",
}

FIGHTER_CODES = {"EUFI", "TOR", "F16", "F18"}
TANKER_CODES = {"A3ST", "KC46", "KC35", "K35R", "K30T"}
TRANSPORT_CODES = {"A400", "C130", "C30J", "C17"}
AWACS_CODES = {"E3TF", "E3CF"}
HELI_CODES = {"A139", "A169", "BK117", "EC35", "H145", "H160", "H64", "R44", "UH60"}
BUSINESS_CODES = {"BE40", "GLF5", "GL7T", "LJ45", "PC12"}
GA_CODES = {"C150", "C152", "C172", "DA40", "DA42"}

MEDICAL_PREFIXES = ("CHX", "CHRISTOPH", "ADAC", "DRF", "LIFE", "REGA", "NHC", "ITH", "RTH")
MILITARY_PREFIXES = (
    "GAF", "RCH", "REACH", "NATO", "DUKE", "ASCOT", "SHEPHERD", "MMF",
    "IAM", "BAF", "ADF", "HERKY", "SAM", "MC", "PAT", "QID", "RRR",
    "AME", "HKY", "CFC", "CNV", "PEGASUS", "MOOSE", "ROYAL", "NAVY",
    "LAGR", "PACK", "TABOR", "SPAR",
)
MILITARY_MODEL_KEYWORDS = (
    "AIR FORCE", "LUFTWAFFE", "ARMEE DE L AIR", "ARMÉE DE L AIR", "ROYAL AIR FORCE",
    "USAF", "NATO", "A400M", "C-130", "C130", "SUPER HERCULES", "GLOBEMASTER",
    "STRATOTANKER", "PEGASUS", "SENTRY", "AWACS", "EUROFIGHTER", "TORNADO", "BLACK HAWK",
)
HELI_MODEL_KEYWORDS = ("H145", "EC145", "EC135", "H135", "BK117", "AW139", "AW169", "HELICOPTER", "HELIKOPTER", "ROBINSON", "BLACK HAWK")

def _clean(value: Any) -> str:
    return str(value or "").strip()

def _upper(value: Any) -> str:
    return _clean(value).upper()

def _reg_key(value: Any) -> str:
    return _upper(value)

def _hex_key(value: Any) -> str:
    return _upper(value)

def _classify(callsign: str, registration: str, typecode: str, model: str, airline: str) -> tuple[str, str, int]:
    callsign_u = _upper(callsign)
    reg_u = _upper(registration)
    type_u = _upper(typecode)
    model_u = _upper(model)
    airline_u = _upper(airline)

    is_medical = callsign_u.startswith(MEDICAL_PREFIXES)
    is_military = False
    is_heli = type_u in HELI_CODES or any(word in model_u for word in HELI_MODEL_KEYWORDS)

    if callsign_u.startswith(MILITARY_PREFIXES):
        is_military = True
        reason = "Erkannt über Callsign"
    elif "+" in reg_u or ("-" in reg_u and reg_u[:2].isdigit()):
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
        reg = _reg_key(f.get("aircraft_registration"))
        fallback_key = f"fr24::{_upper(f.get('flight_number')) or _upper(f.get('aircraft_model')) or len(by_key)}"
        key = reg or fallback_key
        by_key.setdefault(key, {})["fr24"] = f

    for a in adsb_aircraft:
        reg = _reg_key(a.get("r"))
        hex_code = _hex_key(a.get("hex"))
        key = reg or hex_code or f"adsb::{_upper(a.get('flight')) or len(by_key)}"
        slot = by_key.setdefault(key, {})
        slot["adsb"] = a

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

        callsign = _clean(a.get("flight")) or _clean(f.get("flight_number"))
        registration = _upper(a.get("r")) or _upper(f.get("aircraft_registration"))
        typecode = _upper(a.get("t"))
        model = _clean(TYPE_NAMES.get(typecode)) or _clean(f.get("aircraft_model"))
        airline = _clean(f.get("airline_short"))
        name = _clean(f.get("flight_number")) or callsign or registration or _upper(a.get("hex")) or "Unbekannt"

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
            "priority": priority,
            "source_prio": source_prio,
            "tracked": tracked,
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

    flights.sort(key=lambda x: (0 if x["tracked"] else 1, x["priority"], x["source_prio"], x["dist_km"], x["name"]))
    flights = flights[:max_items]

    return {
        "flights": flights,
        "last_update": int(datetime.now(UTC).timestamp()),
        "fr24_count": len(fr24_flights),
        "adsb_count": len(adsb_aircraft),
        "merged_count": merged_count,
        "counts": counts,
        "tracked_present": tracked_present,
    }
