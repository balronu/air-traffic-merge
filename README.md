# Air Traffic Merge

Home Assistant Custom Integration zum Zusammenführen von:

- Flightradar24 Entity
- ADS-B JSON Quelle (z. B. readsb `aircraft.json`)

## Funktionen

- Merge von FR24 + ADS-B
- Kategorien:
  - Medical
  - Militär
  - Militär – Fighter / Tanker / Transport / Aufklärung / Helikopter
  - Helikopter
  - Business Jet
  - General Aviation
  - Zivil
- Tracking über Callsigns und Registrierungen
- zusätzliche Count-Sensoren

## Installation

### HACS
1. Dieses Repository als **Custom Repository** in HACS hinzufügen
2. Typ: **Integration**
3. Installation starten
4. Home Assistant neu starten

### Manuell
Den Ordner `custom_components/air_traffic_merge` nach `/config/custom_components/` kopieren.

## Einrichtung

Nach dem Neustart:

- **Einstellungen**
- **Geräte & Dienste**
- **Integration hinzufügen**
- **Air Traffic Merge**

Einzugeben sind:

- FR24 Entity, z. B. `sensor.flightradar24_current_in_area`
- ADS-B URL, z. B. `http://192.168.178.186:8080/data/aircraft.json`

## Sensoren

Hauptsensor:
- `sensor.air_traffic_merge`

Zusätzliche Count-Sensoren:
- `sensor.air_traffic_merge_medical`
- `sensor.air_traffic_merge_military`
- `sensor.air_traffic_merge_helicopter`
- `sensor.air_traffic_merge_business`
- `sensor.air_traffic_merge_general_aviation`
- `sensor.air_traffic_merge_civil`
