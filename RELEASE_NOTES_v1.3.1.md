# v1.3.1

Built from the working Home Assistant `/config/custom_components/air_traffic_merge` setup.

## Fixed

- Removed the Home Assistant 2026 runtime error caused by `hass.helpers.entity_component.async_update_entity`.
- Refreshed `sensor.air_traffic_tracked_count` directly from the shared in-memory store.
- Updated HACS/GitHub metadata for `balronu/air-traffic-merge`.

## Added

- Validation workflow for Python compilation and JSON syntax.
- English translation file from the installed Home Assistant copy.

## Notes

This release keeps compatibility with the current config flow and entities:

- `sensor.air_traffic_merged`
- `sensor.air_traffic_tracked_count`
- `binary_sensor.air_traffic_tracked_present`
