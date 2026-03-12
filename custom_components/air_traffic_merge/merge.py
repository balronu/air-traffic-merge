"""Merge and classify FR24 + ADS-B data."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
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
    "A20N": "Airbus A320neo",
    "A21N": "Airbus A321neo",
    "A220": "Airbus A220",
    "A319": "Airbus A319",
    "A320": "Airbus A320",
    "A321": "Airbus A321",
    "A333": "Airbus A330-300",
    "A359": "Airbus A350-900",
    "A388": "Airbus A380-800",
    "A400": "Airbus A400M Atlas",
    "A3ST": "Airbus A330 MRTT",
    "B38M": "Boeing 737 MAX 8",
    "B39M": "Boeing 737 MAX 9",
    "B737": "Boeing 737",
    "B738": "Boeing 737-800",
    "B744": "Boeing 747-400",
    "B752": "Boeing 757-200",
    "B763": "Boeing 767-300",
    "B77L": "Boeing 777-200LR",
    "B788": "Boeing 787-8",
    "B789": "Boeing 787-9",
    "BE40": "Beechcraft Premier I",
    "BK117": "MBB/Kawasaki BK117",
    "C130": "Lockheed C-130 Hercules",
    "C30J": "Lockheed Martin C-130J-30 Super Hercules",
    "C150": "Cessna 150",
    "C152": "Cessna 152",
    "C172": "Cessna 172",
    "C17": "Boeing C-17 Globemaster III",
    "CRJ9": "Bombardier CRJ900",
    "DA40": "Diamond DA40",
    "DA42": "Diamond DA42",
    "DH8D": "De Havilland Dash 8 Q400",
    "E190": "Embraer 190",
    "E195": "Embraer 195",
    "EC35": "Airbus H135 / EC135",
    "E3CF": "Boeing E-3 Sentry",
    "E3TF": "Boeing E-3 Sentry",
    "EUFI": "Eurofighter Typhoon",
    "F16": "F-16 Fighting Falcon",
    "F18": "F/A-18 Hornet",
    "GLF5": "Gulfstream V",
    "GL7T": "Gulfstream G700",
    "H145": "Airbus H145",
    "H160": "Airbus H160",
    "H64": "Eurocopter EC145 / H145",
    "K35R": "KC-135 Stratotanker",
    "KC46": "KC-46 Pegasus",
    "LJ45": "Learjet 45",
    "PC12": "Pilatus PC-12",
    "R44": "Robinson R44",
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
MEDICAL_CALLSIGNS = {"CHX", "CHRISTOPH", "ADAC", "DRF", "LIFE", "REGA", "NHC", "ITH", "RTH"}
MILITARY_CALLSIGNS = {
    "GAF", "RCH", "REACH", "NATO", "DUKE", "ASCOT", "SHEPHERD",
    "MMF", "IAM", "BAF", "ADF", "HERKY", "SAM", "MC", "PAT",
    "QID", "RRR", "AME", "HKY", "CFC", "CNV", "PEGASUS", "MOOSE",
    "ROYAL", "NAVY", "LAGR", "PACK", "TABOR", "SPAR"
}
MILITARY_MODEL_KEYWORDS = {
    "AIR FORCE", "LUFTWAFFE", "ARMEE DE L AIR", "ARMÉE DE L AIR",
    "ROYAL AIR FORCE", "USAF", "NATO", "AIRBUS A400M", "C-130", "C130",
    "SUPER HERCULES", "GLOBEMASTER", "STRATOTANKER", "PEGASUS", "SENTRY",
    "AWACS", "EUROFIGHTER", "TORNADO", "BLACK HAWK"
}
HELI_MODEL_KEYWORDS = {
    "H145", "EC145", "EC135", "H135", "BK117", "AW139", "AW169",
    "HELICOPTER", "HELIKOPTER", "ROBINSON", "BLACK HAWK"
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _upper(value: Any) -> str:
    return _clean(value).upper()


def _float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _split_csv(text: str) -> set[str]:
    return {part.strip().upper() for part in text.split(",") if part.strip()}


def _starts_with_any(value: str, prefixes: Iterable[str]) -> bool:
    return any(value.startswith(prefix) for prefix in prefixes)


def _contains_any(value: str, keywords: Iterable[str]) -> bool:
    return any(keyword in value for keyword in keywords)


def _build_adsb_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "registration": _upper(item.get("r")),
        "hex": _upper(item.get("hex")),
        "callsign": _upper(item.get("flight")),
        "typecode": _upper(item.get("t")),
        "distance_km": _float(item.get("r_dst"), 9999.0),
        "direction_deg": round(_float(item.get("r_dir"), 0.0) or 0.0),
        "alt_m": round((_float(item.get("alt_baro"), 0.0) or 0.0) * 0.3048),
        "speed_kmh": round((_float(item.get("gs"), 0.0) or 0.0) * 1.852),
        "raw": item,
    }


def _build_fr24_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "registration": _upper(item.get("aircraft_registration")),
        "hex": _upper(item.get("aircraft_hex")),
        "callsign": _upper(item.get("callsign") or item.get("flight_number")),
        "flight_number": _clean(item.get("flight_number")),
        "model": _clean(item.get("aircraft_model")),
        "airline": _clean(item.get("airline_short")),
        "raw": item,
    }


def _pick_name(fr24: dict[str, Any] | None, adsb: dict[str, Any] | None, key: str) -> str:
    for candidate in (
        _clean(fr24.get("flight_number")) if fr24 else "",
        _clean(adsb.get("callsign")) if adsb else "",
        _clean(fr24.get("registration")) if fr24 else "",
        _clean(adsb.get("registration")) if adsb else "",
        f"HEX: {adsb.get('hex')}" if adsb and adsb.get("hex") else "",
        key,
    ):
        if candidate:
            return candidate
    return "unbekannt"


def classify_flight(*, callsign: str, registration: str, typecode: str, model: str, airline: str) -> tuple[str, str, str, int]:
    callsign_u = _upper(callsign)
    reg_u = _upper(registration)
    type_u = _upper(typecode)
    model_u = _upper(model)
    airline_u = _upper(airline)

    is_medical = _starts_with_any(callsign_u, MEDICAL_CALLSIGNS)
    is_military = False
    is_heli = type_u in HELI_CODES or _contains_any(model_u, HELI_MODEL_KEYWORDS)

    mil_reason = ""
    if _starts_with_any(callsign_u, MILITARY_CALLSIGNS):
        is_military = True
        mil_reason = "Erkannt über Callsign"
    elif "+" in reg_u:
        is_military = True
        mil_reason = "Erkannt über militärische Kennung"
    elif "-" in reg_u and reg_u[:2].isdigit():
        is_military = True
        mil_reason = "Erkannt über militärische Registrierung"
    elif _contains_any(model_u, MILITARY_MODEL_KEYWORDS) or _contains_any(airline_u, MILITARY_MODEL_KEYWORDS):
        is_military = True
        mil_reason = "Erkannt über Modell/Betreiber"

    if is_medical:
        return (CATEGORY_MEDICAL, "🚑🚁" if is_heli else "🚑✈️", "Erkannt über Callsign", 1)
    if type_u in FIGHTER_CODES:
        return (CATEGORY_MILITARY_FIGHTER, "⚔️", "Erkannt über Typecode", 3)
    if type_u in TANKER_CODES:
        return (CATEGORY_MILITARY_TANKER, "⛽", "Erkannt über Typecode", 4)
    if type_u in TRANSPORT_CODES:
        return (CATEGORY_MILITARY_TRANSPORT, "📦", "Erkannt über Typecode", 5)
    if type_u in AWACS_CODES:
        return (CATEGORY_MILITARY_ISR, "📡", "Erkannt über Typecode", 6)
    if is_military and is_heli:
        return (CATEGORY_MILITARY_HELI, "🪖🚁", mil_reason or "Erkannt über Kennung/Modell", 7)
    if is_military:
        return (CATEGORY_MILITARY, "🪖", mil_reason or "Erkannt über Kennung/Modell", 8)
    if is_heli:
        return (CATEGORY_HELI, "🚁", "Erkannt über Typecode/Modell", 10)
    if type_u in BUSINESS_CODES:
        return (CATEGORY_BUSINESS, "💼", "Erkannt über Typecode", 20)
    if type_u in GA_CODES:
        return (CATEGORY_GA, "🛩️", "Erkannt über Typecode", 30)
    return (CATEGORY_CIVIL, "✈️", "Standard-Fallback", 50)


def merge_flights(
    fr24_flights: list[dict[str, Any]],
    adsb_aircraft: list[dict[str, Any]],
    *,
    max_items: int,
    tracked_callsigns: str = "",
    tracked_registrations: str = "",
) -> dict[str, Any]:
    fr24_items = [_build_fr24_item(item) for item in fr24_flights]
    adsb_items = [_build_adsb_item(item) for item in adsb_aircraft]

    fr24_by_reg = {item["registration"]: item for item in fr24_items if item["registration"]}
    adsb_by_reg = {item["registration"]: item for item in adsb_items if item["registration"]}
    adsb_by_hex = {item["hex"]: item for item in adsb_items if item["hex"]}

    keys: list[str] = []
    for key in list(fr24_by_reg) + list(adsb_by_reg) + list(adsb_by_hex):
        if key and key not in keys:
            keys.append(key)

    tracked_callsigns_set = _split_csv(tracked_callsigns)
    tracked_regs_set = _split_csv(tracked_registrations)

    results: list[dict[str, Any]] = []
    count_medical = 0
    count_military = 0
    count_heli = 0
    count_business = 0
    count_ga = 0
    count_civil = 0
    merged_count = 0
    tracked_present = False

    for key in keys:
        fr24 = fr24_by_reg.get(key)
        adsb = adsb_by_reg.get(key) or adsb_by_hex.get(key)
        if fr24 and adsb:
            merged_count += 1

        registration = (adsb or fr24 or {}).get("registration", "")
        hex_code = (adsb or fr24 or {}).get("hex", "")
        callsign = (adsb or fr24 or {}).get("callsign", "")
        flight_number = fr24.get("flight_number", "") if fr24 else ""
        typecode = adsb.get("typecode", "") if adsb else ""
        model = fr24.get("model", "") if fr24 else TYPE_NAMES.get(typecode, "")
        airline = fr24.get("airline", "") if fr24 else ""

        category, icon, reason, priority = classify_flight(
            callsign=callsign or flight_number,
            registration=registration,
            typecode=typecode,
            model=model,
            airline=airline,
        )

        source_text = (
            "✅ FR24 + ADS-B verfügbar" if fr24 and adsb
            else "⚠️ Nur FR24 verfügbar" if fr24
            else "📡 Nur ADS-B empfangen"
        )
        source_prio = 0 if fr24 and adsb else 1 if fr24 else 2

        tracked = False
        if _upper(callsign) in tracked_callsigns_set or _upper(flight_number) in tracked_callsigns_set:
            tracked = True
        if _upper(registration) in tracked_regs_set:
            tracked = True
        tracked_present = tracked_present or tracked

        if category == CATEGORY_MEDICAL:
            count_medical += 1
        elif category in {CATEGORY_MILITARY, CATEGORY_MILITARY_FIGHTER, CATEGORY_MILITARY_TANKER, CATEGORY_MILITARY_TRANSPORT, CATEGORY_MILITARY_ISR, CATEGORY_MILITARY_HELI}:
            count_military += 1
        elif category in {CATEGORY_HELI, CATEGORY_MILITARY_HELI}:
            count_heli += 1
        elif category == CATEGORY_BUSINESS:
            count_business += 1
        elif category == CATEGORY_GA:
            count_ga += 1
        else:
            count_civil += 1

        results.append(
            {
                "name": _pick_name(fr24, adsb, key),
                "registration": registration or "unbekannt",
                "hex": hex_code or "—",
                "callsign": callsign or flight_number,
                "typecode": typecode or "—",
                "type_name": TYPE_NAMES.get(typecode, model) or model,
                "airline": airline,
                "category": category,
                "icon": icon,
                "reason": reason,
                "distance_km": adsb.get("distance_km", 9999.0) if adsb else 9999.0,
                "direction_deg": adsb.get("direction_deg") if adsb else None,
                "alt_m": adsb.get("alt_m") if adsb else None,
                "speed_kmh": adsb.get("speed_kmh") if adsb else None,
                "priority": priority,
                "source_prio": source_prio,
                "source_text": source_text,
                "tracked": tracked,
                "source": "both" if fr24 and adsb else "fr24" if fr24 else "adsb",
            }
        )

    results.sort(key=lambda item: (0 if item["tracked"] else 1, item["priority"], item["source_prio"], item["distance_km"], item["name"]))
    results = results[:max_items]

    return {
        "flights": results,
        "counts": {
            "medical": count_medical,
            "military": count_military,
            "helicopter": count_heli,
            "business": count_business,
            "general_aviation": count_ga,
            "civil": count_civil,
        },
        "fr24_count": len(fr24_flights),
        "adsb_count": len(adsb_aircraft),
        "merged_count": merged_count,
        "tracked_present": tracked_present,
        "last_update": datetime.now(timezone.utc).isoformat(),
    }
