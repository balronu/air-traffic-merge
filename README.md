# Air Traffic Merge Local

Home Assistant Custom Integration für lokales ADS-B mit optionalem FR24-Merge.

Diese Version ist auf `adsb.im` / `readsb` / `tar1090` JSON im Format von `aircraft.json` angepasst.

## Fixes in dieser Version

- korrektes Mapping für `adsb.im`-Felder wie `r`, `t`, `desc`, `ownOp`, `flight`
- kein Zugriff über `hass.helpers`
- sauberer Config Flow ohne YAML
- Hauptsensor `sensor.air_traffic_merged`
- zusätzliche Kategorie-Sensoren

## Einrichtung

1. Ordner `custom_components/air_traffic_merge` nach `/config/custom_components/` kopieren
2. Home Assistant neu starten
3. Integration hinzufügen: **Air Traffic Merge Local**
4. ADS-B URL eintragen, z. B. `http://192.168.178.186:8080/data/aircraft.json`
5. FR24 Entity optional setzen

## Sensoren

- `sensor.air_traffic_merged`
- `sensor.air_traffic_medical`
- `sensor.air_traffic_military`
- `sensor.air_traffic_helicopter`
- `sensor.air_traffic_business`
- `sensor.air_traffic_general_aviation`
- `sensor.air_traffic_civil`
- `binary_sensor.air_traffic_tracked_present`

## Beispiel für die Karte

```yaml
type: custom:air-traffic-merge-card
entity: sensor.air_traffic_merged
```
