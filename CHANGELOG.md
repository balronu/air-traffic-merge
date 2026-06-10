# Changelog

## v1.3.1
- aus dem aktuell funktionierenden Home-Assistant-Stand unter `/config/custom_components/air_traffic_merge` neu aufgebaut
- Runtime-Fehler durch `hass.helpers.entity_component.async_update_entity` entfernt
- Tracking-Count-Sensor wird direkt aus dem gemeinsamen Store aktualisiert
- echte GitHub-/HACS-Metadaten für `balronu/air-traffic-merge`
- Validierungs-Workflow für Python- und JSON-Dateien ergänzt

## v1.3.0
- HACS-/GitHub-Repo bereinigt
- keine `__pycache__`-Dateien mehr im Repo
- README für direkte GitHub-/HACS-Nutzung ergänzt
- `adsb.im`-Feldmapping für `aircraft.json`
- kein Zugriff über `hass.helpers`
