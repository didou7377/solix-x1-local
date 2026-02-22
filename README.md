# Anker Solix X1 (Local) for Home Assistant

Lokale Home-Assistant-Integration fuer **Anker SOLIX X1** ueber **Modbus TCP**.

Die Integration liest Messwerte direkt aus deinem Geraet im lokalen Netzwerk (kein Cloud-Zwang) und erstellt daraus automatisch Sensoren in Home Assistant.

---

## Highlights

- Vollstaendige Einrichtung ueber die Home-Assistant-Oberflaeche (Config Flow)
- Lokales Polling ueber Modbus TCP (`iot_class: local_polling`)
- Konfigurierbarer Host, Port und Abfrageintervall
- Automatische Sensor-Erstellung aus `SENSOR_DEFINITIONS` in `const.py`
- Fokus auf stabile Read-Only-Messwerte (keine Schreib-/Steuerfunktionen)
- HACS Custom Repository geeignet

---

## Aktueller Funktionsumfang

Die Integration liefert derzeit **27 Sensoren** (je nach Geraet/Antworten koennen einzelne Werte `unknown` sein), unter anderem:

- **Diagnose:** Modellname, Seriennummer, Software-Version
- **Netz:** Frequenz, Phasenspannungen/-stroeme
- **PV:** aktuelle PV-Leistung, Tages-/Gesamt-PV-Erzeugung
- **Batterie:** SoC, Spannung, Leistung, Temperatur, Anzahl Packs, Kapazitaet
- **Energiezaehler:** Netzbezug/Einspeisung und Lastverbrauch (Tag/Gesamt)

Alle Sensoren entstehen zentral ueber `custom_components/anker_solix_x1/const.py`.

---

## Voraussetzungen

- Home Assistant mit `custom_components` Unterstuetzung
- Netzwerkverbindung vom Home-Assistant-Host zum X1-System
- Modbus TCP auf der Zielhardware erreichbar
- Standard-Port ist `502` (kann in der Einrichtung angepasst werden)

---

## Installation via HACS (Custom Repository)

1. In Home Assistant **HACS** oeffnen
2. **Integrations** -> Menue oben rechts -> **Custom repositories**
3. Repository URL eintragen:  
   `https://github.com/didou7377/solix-x1-local`
4. Typ: **Integration**
5. Repository hinzufuegen und **Anker Solix X1** installieren
6. Home Assistant neu starten
7. Danach: **Settings -> Devices & Services -> Add Integration**
8. Nach **Anker Solix X1** suchen und konfigurieren

---

## Manuelle Installation

1. In deiner HA-Konfiguration den Ordner `custom_components` oeffnen/erstellen
2. `custom_components/anker_solix_x1` aus diesem Repo dorthin kopieren
3. Home Assistant neu starten
4. Unter **Settings -> Devices & Services** die Integration hinzufuegen

---

## Ersteinrichtung (Config Flow)

Beim Hinzufuegen der Integration werden folgende Werte abgefragt:

- **Name** (frei waehlbar, Standard: `Anker Solix X1`)
- **Host/IP** (Pflichtfeld)
- **Port** (Standard: `502`)
- **Scan-Intervall** in Sekunden (Standard: `5`)

Die Integration testet die Erreichbarkeit waehrend der Einrichtung.

### Optionen nach der Einrichtung

Im Options-Dialog kannst du aktuell das **Scan-Intervall** aendern, ohne die Integration neu anzulegen.

---

## Technische Hinweise

- Es wird ein `DataUpdateCoordinator` verwendet, um alle Register zyklisch zu lesen.
- Die Integration nutzt `pymodbus` (aktuell `>=3.8.0,<4.0.0`).
- Unterschiedliche Endianness/Word-Swap-Varianten werden je Sensor beruecksichtigt.
- Legacy-Sensoren aus aelteren Namensschemata werden beim Setup bereinigt.

---

## Fehlerbehebung (Troubleshooting)

### Integration kann nicht verbinden

- Host/IP pruefen (Ping vom HA-System)
- Port pruefen (`502` bzw. dein konfigurierter Port)
- Modbus TCP am Zielsystem aktiv/erreichbar
- Firewall/VLAN-Regeln pruefen

### Sensoren bleiben auf `unknown` oder `unavailable`

- Erreichbarkeit und Stabilitaet der Verbindung pruefen
- Scan-Intervall testweise erhoehen (z. B. 10-15 Sekunden)
- Pruefen, ob dein Geraet die entsprechenden Register wirklich liefert

### Werte wirken unplausibel

- Registerdefinitionen (`address`, `count`, `data_type`, `gain`, `swap`) in `const.py` kontrollieren
- Modell-/Firmware-Unterschiede koennen abweichende Registerbelegungen verursachen

---

## Erweiterung eigener Sensoren

Neue Sensoren fuegst du in `custom_components/anker_solix_x1/const.py` in `SENSOR_DEFINITIONS` hinzu.

Typische Felder:

- `key`, `name`
- `address`, `count`
- `data_type` (`uint16`, `int16`, `uint32`, `int32`, `string`)
- `gain`, optional `swap`
- optional HA-Metadaten (`unit`, `device_class`, `state_class`, `entity_category`)

Nach Anpassungen:

1. Dateien speichern
2. Home Assistant neu starten
3. Integration neu laden (oder komplett neu starten)

---

## Projektstatus

- Version: `0.1.3`
- Fokus: Lokales, robustes Auslesen von X1-Daten
- Geplanter Ausbau: schrittweise neue Register/Sensoren je nach Testbasis

### Neu in 0.1.3

- Korrektur:
  - `Akku1 Rate Capacity` Skalierung angepasst (`gain` von `10` auf `100`)
  - Ziel: korrekte Darstellung der Nennkapazitaet (z. B. `5.00 kWh` statt `50.00 kWh`)

### Neu in 0.1.2

- Sensoren hinzugefuegt (Leistungswerte):
  - Haus Verbrauch
  - Akku Leistung
  - Power Load
  - Power Grid
- Sensoren hinzugefuegt (Backup-Phasenstroeme):
  - Backup/Phase A Strom
  - Backup Phase B Strom
  - Backup Phase C Strom
- Sensoren hinzugefuegt (Akku1 Block):
  - Akku1 Modellname
  - Akku1 Seriennummer
  - Akku1 Software Version
  - Akku1 Hardware Version
  - Akku1 Rate Capacity
  - Akku1 Status
  - Akku1 Spannung
  - Akku1 Leistung
  - Akku1 SoC
  - Akku1 SoH
  - Akku1 Gesamt-Entladeenergie
  - Akku1 Max Temperatur
  - Akku1 Min Temperatur

### Neu in 0.1.1

- Sensoren hinzugefuegt:
  - PV1 Strom
  - PV1 Spannung
  - PV2 Strom
  - PV2 Spannung

---

## Entwicklung / Releases

Minimaler Release-Ablauf:

1. `manifest.json` Version anheben
2. Aenderungen committen und auf `main` pushen
3. GitHub Release/Tag erstellen (z. B. `v0.1.1`)
4. In HACS nach Updates suchen

---

## Support via PayPal

Wenn dir dieses Projekt hilft und du meine Arbeit unterstuetzen moechtest:

<a href="https://paypal.me/jahnouni/2" target="_blank" rel="noopener noreferrer">
  <img src="https://img.shields.io/badge/PayPal-2%E2%82%AC-00457C?logo=paypal&logoColor=white" alt="PayPal 2 EUR">
</a>
<a href="https://paypal.me/jahnouni/5" target="_blank" rel="noopener noreferrer">
  <img src="https://img.shields.io/badge/PayPal-5%E2%82%AC-00457C?logo=paypal&logoColor=white" alt="PayPal 5 EUR">
</a>
<a href="https://paypal.me/jahnouni/10" target="_blank" rel="noopener noreferrer">
  <img src="https://img.shields.io/badge/PayPal-10%E2%82%AC-00457C?logo=paypal&logoColor=white" alt="PayPal 10 EUR">
</a>

