# Air Traffic Merge

Custom Home Assistant integration that merges Flightradar24 and ADS-B (`aircraft.json`) into one sensor and classifies aircraft as medical, military, helicopter, business, GA, or civil.

## Features

- Config flow in the UI
- Reads a FR24 sensor entity and an ADS-B JSON URL
- Merges aircraft by registration first and ADS-B hex as fallback
- Robust classification for:
  - Medical: `CHX`, `ADAC`, `DRF`, `REGA`, `LIFE`, `ITH`, `RTH`
  - Military: `HERKY`, `RCH`, `REACH`, `NATO`, `GAF`, `MMF`, `DUKE`, etc.
  - Helicopters, business jets, GA, civil traffic
- Extra count sensors
- Optional tracked callsigns / registrations

## Installation via HACS

1. Add this repository as a custom repository in HACS.
2. Type: **Integration**
3. Install **Air Traffic Merge**.
4. Restart Home Assistant.
5. Add the integration in **Settings → Devices & services**.

## Setup

You need:

- A FR24 entity, for example:
  - `sensor.flightradar24_current_in_area`
- An ADS-B JSON URL, for example:
  - `http://192.168.178.186:8080/data/aircraft.json`

## Created entities

Main sensor:

- `sensor.air_traffic_merge_flights`

Count sensors:

- medical
- military
- helicopter
- business
- general aviation
- civil

The main sensor exposes these attributes:

- `flights`
- `last_update`
- `status`
- `fr24_count`
- `adsb_count`
- `merged_count`
- `counts`
- `tracked_present`
- `debug`

## Dashboard card

Use the separate card repository:

- `balronu/air-traffic-merge-card`

Example:

```yaml
type: custom:air-traffic-merge-card
entity: sensor.air_traffic_merge_flights
title: Flugzeuge
show_status: true
show_debug: false
```

## Notes

This is a custom integration intended for Home Assistant. It does not require YAML sensors.
