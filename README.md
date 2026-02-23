# Air Traffic Merge (FR24 + ADS-B) — Home Assistant Custom Integration + Custom Card

This repository contains:

- **Custom Integration** (`custom_components/air_traffic_merge/`)
  - Lets users pick their **FR24 sensor entity** and set an **ADS-B JSON URL**
  - Creates two sensors:
    - `sensor.air_traffic_status` (counts + last update)
    - `sensor.air_traffic_merged` (merged list in attribute `flights`)
- **Custom Lovelace Card** (`www/air-traffic-merge-card.js`)
  - Renders a clean, mobile-friendly flight list
  - Highlights **CHX16**
  - Shows whether data is from **FR24**, **ADS-B**, or **both**

## Install (HACS)

### Integration
1. Add this repo to HACS as a **Custom Repository** (Integration).
2. Install **Air Traffic Merge (FR24 + ADS-B)**.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration → Air Traffic Merge**.
5. Select your FR24 sensor entity (must have attribute `flights`) and enter your ADS-B JSON URL:
   - Example: `http://<your-adsb-host>:8080/data/aircraft.json`

### Card
1. Add this repo to HACS as a **Custom Repository** (Frontend) *or* copy `www/air-traffic-merge-card.js` to your `/config/www/`.
2. Add as a Lovelace resource (Settings → Dashboards → Resources):
   - URL: `/local/air-traffic-merge-card.js`
   - Type: `JavaScript Module`

## Usage

### Basic card
```yaml
type: custom:air-traffic-merge-card
entity: sensor.air_traffic_merged
status_entity: sensor.air_traffic_status
title: Flugzeuge
highlight_callsign: CHX16
max_items: 30
show_debug: false
```

### Minimal card (no status header)
```yaml
type: custom:air-traffic-merge-card
entity: sensor.air_traffic_merged
title: Flugzeuge
```

## Data sources

### FR24
The selected FR24 sensor must expose a list under attribute `flights`. Each flight should include (typical FR24 integration):
- `aircraft_registration`
- `flight_number`
- `airline_short`
- `aircraft_model`

### ADS-B
The ADS-B URL should return JSON compatible with readsb/dump1090 style feeds (as used by adsb.im), containing:
- `now` (unix timestamp)
- `aircraft` (list)
  - `r` (registration, optional)
  - `hex` (icao hex)
  - `flight` (callsign, optional)
  - `alt_baro` (feet, optional)
  - `gs` (knots, optional)
  - `r_dst` (km, optional)
  - `r_dir` (degrees, optional)
  - `t` (type, optional)

## Notes
- The integration **deduplicates** ADS-B by using **registration** when present; **hex** is only used if registration is missing.
- Callsign fallback order: `FR24 flight_number` → `ADS-B flight` → `registration` → `HEX <hex>`.

## License
MIT


## HACS: zero-manual install (recommended)

This repo supports **HACS download/install** (no copying files manually).

### Add repository to HACS
1. Open **HACS → Integrations → ⋮ → Custom repositories**
2. Add the GitHub repo URL and choose category **Integration**
3. Repeat once more and choose category **Lovelace** (Frontend)

> HACS currently treats Integrations and Lovelace cards as separate installables, so you add the same repo in both categories.  
> Installation is still one-click and **no manual file copying**.

### Install
- In **HACS → Integrations**, install **Air Traffic Merge (FR24 + ADS-B)** and restart Home Assistant.
- In **HACS → Frontend**, install **Air Traffic Merge Card**.
- The card resource will be offered for auto-add; if not, add a resource:
  - URL: `/hacsfiles/air-traffic-merge/air-traffic-merge-card.js`
  - Type: `JavaScript Module`



## ADS-B source options
During setup you can choose:
- **URL**: the integration will fetch `aircraft.json` directly
- **Entity**: pick an existing HA sensor entity that provides attributes `aircraft` and optionally `now`

## Tracking (e.g., CHX16)
During setup you can enable tracking and provide a comma-separated list of callsigns (e.g. `CHX16, HEMS1`).
The integration exposes:
- `sensor.air_traffic_tracked` (state = number currently active)
- `sensor.air_traffic_status` attributes:
  - `tracked_callsigns`
  - `tracked_active`
  - `tracked_active_count`

The custom card will automatically show a **🎯 Tracked** chip when tracking is enabled.


## Options (change settings later)
After installing, open the integration in **Settings → Devices & services → Air Traffic Merge → Configure** to change:
- ADS-B source (URL / Entity)
- scan interval
- tracking enable + callsigns

No need to delete/re-add the integration.

## Per-callsign binary sensors
If tracking is enabled and callsigns are provided, the integration creates a **binary sensor per callsign**, e.g.:
- `binary_sensor.tracked_chx16`

This is great for automations/notifications.


## Tracking by callsign and/or registration
In the integration setup (or Options) you can select a **tracking mode**:
- callsign
- registration
- both

Then provide:
- `track_callsigns` (comma separated, e.g. `CHX16, HEMS1`)
- `track_registrations` (comma separated, e.g. `D-HXYZ`)

### Entities created
- `sensor.air_traffic_tracked` (count currently active)
- One binary sensor per tracked target (depending on mode), e.g.
  - `binary_sensor.tracked_chx16`
  - `binary_sensor.tracked_d_hxyz`

## Card options
```yaml
type: custom:air-traffic-merge-card
entity: sensor.air_traffic_merged
status_entity: sensor.air_traffic_status
title: Flugzeuge
highlight_callsign: CHX16
prioritize_tracked: true
tracked_icons:
  CHX16: "🚑🚁"
  HEMS1: "🚑🚁"
max_items: 30
show_debug: false
```


## Events (automations / Node-RED)
When tracking is enabled, the integration fires events when a tracked target appears/disappears:

- Event type: `air_traffic_merge_tracked`
- Payload:
  - `action`: `appeared` | `disappeared`
  - `target`: callsign or registration (uppercase)
  - `last_update`: unix timestamp
  - `track_mode`: callsign | registration | both

Example automation trigger:
```yaml
trigger:
  - platform: event
    event_type: air_traffic_merge_tracked
```

## Card: separate icon maps
```yaml
type: custom:air-traffic-merge-card
entity: sensor.air_traffic_merged
status_entity: sensor.air_traffic_status
tracked_icons_callsign:
  CHX16: "🚑🚁"
tracked_icons_registration:
  D-HXYZ: "🚑🚁"
```
