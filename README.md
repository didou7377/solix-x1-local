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
- Gebuendeltes Lesen ueber eine dauerhafte Verbindung (8 Anfragen pro Zyklus)
- HACS Custom Repository geeignet, Updates direkt in Home Assistant

---

## So funktioniert es

### Wie die Daten in Home Assistant kommen

Home Assistant fragt den X1 regelmaessig selbst ab (Polling). Der X1 meldet sich nicht von sich aus.

```
X1 (Wechselrichter)  <-- Modbus TCP, Port 502 --  Home Assistant
```

Ablauf pro Zyklus (Standard: alle 5 Sekunden):

1. **Coordinator** (`coordinator.py`): Ein Timer von Home Assistant startet die Abfrage.
2. **Modbus-Anfrage**: Ueber die offene TCP-Verbindung werden zusammenhaengende Registerbereiche gelesen, z. B. 34 Register ab Adresse `10002`. Der X1 antwortet mit rohen 16-Bit-Werten.
3. **Dekodieren** (`modbus_codec.py`): Anhand von `const.py` werden daraus echte Werte (Byte-/Wort-Reihenfolge, Vorzeichen, Teilung durch `gain`), z. B. `[0xFA24, 0xFFFF]` -> `-1500 W`.
4. **Sensoren** (`sensor.py`): Alle Sensoren haengen am Coordinator und werden automatisch benachrichtigt, sobald neue Daten da sind. Home Assistant speichert die Werte in seiner Datenbank.

Faellt die Verbindung aus, zeigen die Sensoren `unavailable`. Beim naechsten Zyklus wird automatisch neu verbunden.

### Wie Home Assistant von neuen Versionen erfaehrt

Das uebernimmt **HACS**:

1. HACS kennt dieses Repository als Custom Repository.
2. Es prueft regelmaessig, ob es auf GitHub ein neues **Release** gibt (z. B. `v0.2.0`).
3. Ist das Release neuer als die installierte Version, erscheint unter **Einstellungen -> Updates** ein Update.
4. Installieren und Home Assistant neu starten.

---

## Aktueller Funktionsumfang

Die Integration liefert derzeit **56 Sensoren** (je nach Geraet/Antworten koennen einzelne Werte `unknown` sein), unter anderem:

- **Diagnose:** Modellname, Seriennummer, Software-Version
- **Netz:** Frequenz, Phasenspannungen/-stroeme
- **PV:** aktuelle PV-Leistung, Tages-/Gesamt-PV-Erzeugung
- **Batterie:** SoC, Spannung, Leistung, Temperatur, Anzahl Packs, Kapazitaet
- **Energiezaehler:** Netzbezug/Einspeisung und Lastverbrauch (Tag/Gesamt)

Alle Sensoren entstehen zentral ueber `custom_components/anker_solix_x1/const.py`.

---

## Voraussetzungen

- Home Assistant **2024.12** oder neuer mit `custom_components` Unterstuetzung
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

Im Options-Dialog kannst du das **Scan-Intervall** aendern, ohne die Integration neu anzulegen. Die Integration wird danach automatisch neu geladen, das neue Intervall gilt sofort.

---

## Technische Hinweise

- Es wird ein `DataUpdateCoordinator` verwendet, um alle Register zyklisch zu lesen.
- Die Modbus-Verbindung bleibt zwischen den Abfragen offen und wird nur bei Fehlern neu aufgebaut.
- Benachbarte Register werden gebuendelt gelesen (`MAX_BLOCK_SIZE`, `MAX_BLOCK_GAP` in `const.py`): statt 56 Einzelabfragen sind es pro Zyklus nur noch 8. Lehnt das Geraet einen Block ab, werden dessen Register automatisch einzeln gelesen.
- Jede Anfrage hat ein Timeout (`MODBUS_TIMEOUT`, Standard 5 s).
- Die Dekodierung liegt in `modbus_codec.py` (ohne Home-Assistant-Abhaengigkeit) und ist durch Tests in `tests/` abgedeckt.
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
- Debug-Log einschalten (siehe unten) und nach `Modbus-Fehler auf Register` suchen

### Debug-Log einschalten

In `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.anker_solix_x1: debug
```

Nach dem Neustart steht im Log u. a. `56 Sensoren werden in 8 Modbus-Anfragen gelesen`.

### Meldung `Block ... abgelehnt, lese Register einzeln`

Das Geraet hat eine gebuendelte Abfrage abgelehnt, meist weil der Bereich ein Register enthaelt, das die Firmware nicht kennt. Die Integration liest diese Register dann einzeln weiter, die Werte stimmen also. Taucht die Meldung bei jedem Zyklus auf, `MAX_BLOCK_GAP` in `const.py` verkleinern (z. B. auf `0`), damit nur direkt aneinanderliegende Register zusammengefasst werden.

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
- `gain` (Teiler, `10` bedeutet Rohwert / 10)
- optional `swap`: `word` (Wortreihenfolge tauschen), `byte`, `word_byte`
- optional HA-Metadaten (`unit`, `device_class`, `state_class`, `entity_category`)

Regeln fuer die HA-Metadaten:

- Zaehler (`device_class: energy`) brauchen `state_class: total_increasing`
- Gespeicherte Energie wie Akku-Kapazitaet: `device_class: energy_storage` mit `state_class: measurement`
- Statuscodes und Texte: `state_class: None`, sonst legt HA unnoetige Langzeitstatistiken an

Neue Sensoren werden automatisch in die gebuendelten Abfragen einsortiert, dafuer ist nichts weiter zu tun.

Nach Anpassungen:

1. Tests ausfuehren (siehe unten), sie pruefen u. a. doppelte Keys und falsche `count`-Werte
2. Home Assistant neu starten
3. Integration neu laden (oder komplett neu starten)

---

## X1-Dashboard

Das optionale Dashboard nutzt native Home-Assistant-Karten für Solarleistung,
Hausverbrauch, Netz, Akku, Tagesenergie und den Leistungsverlauf der letzten 24 Stunden.

1. Öffne **Entwicklerwerkzeuge → Aktionen** und führe **X1-Dashboard erzeugen**
   (`anker_solix_x1.generate_dashboard`) aus. Bei mehreren X1-Anlagen wähle eine aus.
2. Kopiere den Inhalt des Antwortfelds `yaml` (ab `views:`).
3. Erstelle unter **Einstellungen → Dashboards** ein neues Dashboard. Öffne es,
   gehe in den Bearbeitungsmodus und öffne im Menü den **Rohkonfigurationseditor**.
   Füge dort den kopierten Inhalt ein und speichere.

Die Aktion verwendet die aktuellen Entitäts-IDs deiner Anlage und berücksichtigt
auch umbenannte Sensoren. Bei späteren Umbenennungen kannst du die Konfiguration
erneut erzeugen. Das Diagramm nutzt den vorhandenen Verlauf von Home Assistant.

## Projektstatus

- Version: `0.2.1`
- Fokus: Lokales, robustes Auslesen von X1-Daten
- Geplanter Ausbau: schrittweise neue Register/Sensoren je nach Testbasis
- Vollstaendige Aenderungshistorie: siehe `CHANGELOG.md`

### Neu in 0.2.0

- Register werden gebuendelt gelesen, die Verbindung bleibt offen: deutlich weniger Last fuer den X1
- Timeout pro Anfrage; faellt die Verbindung aus, wird sie beim naechsten Zyklus neu aufgebaut
- Ein geaendertes Scan-Intervall gilt sofort (vorher erst nach Neustart)
- Geraeteinfo zeigt Modell, Seriennummer und Software-Version
- Kapazitaetssensoren als `energy_storage` (beseitigt HA-Warnungen), Statussensoren ohne Langzeitstatistik
- Mindestversion Home Assistant 2024.12

### Neu in 0.1.7

- Akku-Kapazitaetswert angepasst:
  - `Akku Nennkapazitaet` (`10250`) nutzt jetzt `swap: word`

### Neu in 0.1.6

- Akku-Uebersicht strukturiert mit `akku_`-Praefix (nicht zu verwechseln mit `akku1_` als einzelner Pack).
- Weitere Akku-Register aus der Batterietabelle hinzugefuegt:
  - SoH, Daily Charge/Discharge, Total Charge/Discharge
- Korrektur:
  - `akku1_total_discharge_energy` Skalierung angepasst (`gain: 100`)

### Neu in 0.1.5

- Sensor hinzugefuegt:
  - Akku Gesundheit (`10015`, `UINT16`, `%`)
- Struktur verbessert:
  - Akku-Daten sind jetzt als **Akku Uebersicht** markiert
  - klar getrennt vom **Akku1**-Block (einzelner Pack)

### Neu in 0.1.4

- `CHANGELOG.md` hinzugefuegt (Version-zu-Version Historie).

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

### Projektaufbau

| Datei | Aufgabe |
|---|---|
| `__init__.py` | Setup, Entladen, Neuladen bei geaenderten Optionen |
| `config_flow.py` | Einrichtungs- und Options-Dialog |
| `coordinator.py` | Modbus-Verbindung und zyklische Abfrage |
| `modbus_codec.py` | Dekodierung und Bildung der Abfrage-Bloecke (ohne HA-Abhaengigkeit) |
| `sensor.py` | Sensor-Entities und Geraeteinfo |
| `const.py` | Konstanten und `SENSOR_DEFINITIONS` |

### Tests

Die Tests brauchen kein Home Assistant:

```bash
python3 -m unittest discover -s tests -v
```

Die GitHub Action fuehrt bei jedem Push die Tests, `hassfest` und die HACS-Pruefung aus.

### Release-Ablauf

1. Version in `manifest.json` anheben
2. `CHANGELOG.md` und den Abschnitt "Neu in ..." in dieser README ergaenzen
3. Tests ausfuehren
4. Aenderungen committen und auf `main` pushen
5. GitHub Release mit Tag erstellen (z. B. `v0.2.0`), erst dann sieht HACS die neue Version
6. In HACS nach Updates suchen

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

