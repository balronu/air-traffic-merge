# Air Traffic Merge Local

Home Assistant Custom Integration für lokales ADS-B mit optionalem FR24-Merge.

Diese Version ist auf `adsb.im` / `readsb` / `tar1090` JSON im Format von `aircraft.json` angepasst und für die Installation **direkt über HACS aus einem GitHub-Repository** vorbereitet.

## Highlights

- Config Flow, also **keine YAML-Konfiguration nötig**
- korrektes Mapping für `adsb.im`-Felder wie `r`, `t`, `desc`, `ownOp`, `flight`
- optionales FR24-Merge
- Hauptsensor `sensor.air_traffic_merged`
- zusätzliche Kategorie-Sensoren
- HACS-kompatible Repo-Struktur

## Für HACS vorbereiten

1. Neues GitHub-Repository anlegen, z. B. `air-traffic-merge-local`
2. Den Inhalt dieses ZIPs in das Root des Repos hochladen
3. Auf GitHub einen Release anlegen, z. B. `v1.3.0`
4. In HACS `Benutzerdefinierte Repositories` öffnen
5. Repository-URL eintragen und Typ **Integration** wählen
6. Integration über HACS installieren und Home Assistant neu starten

## Einrichtung in Home Assistant

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. **Air Traffic Merge Local** auswählen
3. ADS-B URL eintragen, z. B. `http://192.168.178.186:8080/data/aircraft.json`
4. FR24-Entity optional setzen

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

## Hinweis zu Updates über HACS

HACS erkennt Updates über GitHub, wenn du nach dem Upload neue Releases erzeugst und die `version` in `custom_components/air_traffic_merge/manifest.json` mitziehst.
