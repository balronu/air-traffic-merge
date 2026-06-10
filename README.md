# Air Traffic Merge

Home Assistant custom integration for merging Flightradar24 data with local ADS-B data from `readsb`, `tar1090`, or `adsb.im`.

This repository is the HACS-installable version of the working local setup. It supports FR24-only, ADS-B-only, and combined FR24 + ADS-B modes.

## Features

- Config flow, no YAML setup required
- Source selection: FR24 sensor, local ADS-B URL, or ADS-B entity
- Automatic `aircraft.json` URL normalization
- Tracking by callsign, registration, or both
- Main sensor: `sensor.air_traffic_merged`
- Tracking helper sensor: `sensor.air_traffic_tracked_count`
- Tracking binary sensor: `binary_sensor.air_traffic_tracked_present`
- Events when tracked targets appear or disappear: `air_traffic_merge_tracked`
- HACS-compatible repository structure

## Install with HACS

1. Open HACS.
2. Add this repository as a custom repository:

   ```text
   https://github.com/balronu/air-traffic-merge
   ```

3. Choose category `Integration`.
4. Install `Air Traffic Merge`.
5. Restart Home Assistant.
6. Add the integration from Settings -> Devices & services.

## Configuration

The setup flow asks for:

- Source mode: FR24 only, ADS-B only, or both
- Optional FR24 sensor with a `flights` attribute
- ADS-B source as URL or entity
- Polling interval in seconds
- Optional tracking configuration

Example ADS-B URL:

```text
http://192.168.178.186:8080/data/aircraft.json
```

If you enter only the base URL, the integration appends `/data/aircraft.json`.

## Entities

- `sensor.air_traffic_merged`
- `sensor.air_traffic_tracked_count`
- `binary_sensor.air_traffic_tracked_present`

The main sensor exposes a `flights` attribute for dashboard cards.

## Card Example

Use this with the matching dashboard card from `balronu/air-traffic-merge-card`:

```yaml
type: custom:air-traffic-merge-card
entity: sensor.air_traffic_merged
title: Flugzeuge
show_status: true
max_items: 25
```

## Release Notes

### v1.3.1

- Built from the working Home Assistant `/config/custom_components/air_traffic_merge` setup.
- Fixes the Home Assistant 2026 runtime error caused by `hass.helpers.entity_component.async_update_entity`.
- Keeps the existing setup flow and entity model compatible with current installations.
- Updates HACS metadata and GitHub links for `balronu/air-traffic-merge`.
