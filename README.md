# Air Traffic Merge Local

Home Assistant custom integration for merging **local ADS-B data** from `readsb` / `adsb.im` with **optional** Flightradar24 data.

This repo is structured so you can upload it to GitHub as-is and add it to HACS as a custom repository.

## Highlights

- ADS-B-first design for `adsb.im` / `readsb`
- FR24 entity is optional
- UI setup through Config Flow
- Main sensor with merged flights, counts, status and debug attributes
- Extra count sensors for:
  - Medical
  - Military
  - Helicopter
  - Business
  - General Aviation
  - Civil
- Binary sensor for tracked-aircraft presence

## Repository structure

```text
custom_components/air_traffic_merge/
hacs.json
README.md
LICENSE
.gitignore
```

## Install with HACS

1. Create a new GitHub repository, for example `air-traffic-merge-local`
2. Upload the contents of this repo
3. In HACS, open **Custom repositories**
4. Add your GitHub repo URL
5. Choose **Integration**
6. Install **Air Traffic Merge Local**
7. Restart Home Assistant

## Manual install

Copy this folder:

```text
custom_components/air_traffic_merge
```

into:

```text
/config/custom_components/air_traffic_merge
```

Then restart Home Assistant.

## Setup

After restart:

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **Air Traffic Merge Local**
4. Enter your ADS-B JSON URL, for example:

```text
http://YOUR-PI:8080/data/aircraft.json
```

5. Optionally add your FR24 entity, for example:

```text
sensor.flightradar24_current_in_area
```

## Created entities

Main sensor:

- `sensor.air_traffic_merge`

Additional sensors:

- `sensor.air_traffic_merge_medical`
- `sensor.air_traffic_merge_military`
- `sensor.air_traffic_merge_helicopter`
- `sensor.air_traffic_merge_business`
- `sensor.air_traffic_merge_general_aviation`
- `sensor.air_traffic_merge_civil`

Binary sensor:

- `binary_sensor.air_traffic_tracked_present`

## Notes

- Best fit for local feeds like `adsb.im` or `readsb`
- The original idea and base structure come from `balronu/air-traffic-merge`
- This package is cleaned up so you can publish it directly as your own repo
