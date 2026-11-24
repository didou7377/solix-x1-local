# Changelog

Alle nennenswerten Aenderungen an diesem Projekt werden hier dokumentiert.

Das Format orientiert sich an Keep a Changelog und Semantic Versioning.

## [0.2.0] - 2026-11-24
### Changed
- Modbus-Register werden in zusammenhaengenden Bloecken gelesen statt einzeln (56 -> 8 Anfragen pro Zyklus). Lehnt das Geraet einen Block ab, wird auf Einzelabfragen zurueckgefallen.
- Die TCP-Verbindung bleibt zwischen den Zyklen offen und wird nur nach Fehlern neu aufgebaut; sie wird beim Entladen der Integration geschlossen.
- Timeout (5 s) und eine Wiederholung pro Anfrage.
- Dekodierung in `modbus_codec.py` ausgelagert und mit Tests abgedeckt.
- `entry.runtime_data` statt `hass.data`.
- `akku_rated_capacity` und `akku1_rate_capacity` nutzen `energy_storage` statt `energy` (die Kombination `energy` + `measurement` ist in HA ungueltig).
- `akku_status` und `akku1_status` ohne `state_class` (Statuscodes sind keine Messwerte).
- Geraeteinfo enthaelt Modell, Seriennummer und Software-Version aus den Registern.
- Mindestversion Home Assistant 2024.12.
### Fixed
- Ein geaendertes Scan-Intervall wird sofort uebernommen (Options-Listener fehlte).
- OptionsFlow setzt `config_entry` nicht mehr selbst (in neueren HA-Versionen ein Fehler).
- Widerspruechliche Kommentare zur Adressierung in `const.py` bereinigt.
- Die Pruefung auf doppelte Einrichtung laeuft vor dem Verbindungstest.

## [0.1.7] - 2026-02-22
### Changed
- Akku-Kapazitaetswert angepasst: `akku_rated_capacity` (`10250`) liest nun mit `swap: "word"`.

## [0.1.6] - 2026-02-22
### Added
- Akku-Uebersicht erweitert (mit `akku_`-Praefix) gemaess Batterietabelle:
  - `akku_number_of_packs` (`10249`)
  - `akku_rated_capacity` (`10250`)
  - `akku_status` (`10252`)
  - `akku_voltage` (`10253`)
  - `akku_power` (`10254`)
  - `akku_soc` (`10256`)
  - `akku_soh` (`10257`)
  - `akku_daily_charge_energy` (`10258`)
  - `akku_daily_discharge_energy` (`10260`)
  - `akku_total_charge_energy` (`10262`)
  - `akku_total_discharge_energy` (`10264`)
### Changed
- `akku1_total_discharge_energy` Skalierung angepasst (`gain` von `10` auf `100`).
- Alte `battery_*` Keys werden beim Setup aus der Entity Registry bereinigt.

## [0.1.5] - 2026-02-22
### Added
- Neuer Sensor `Akku Gesundheit` (`battery_health`, Register `10015`, `UINT16`, `%`).
### Changed
- Akku-Daten in `const.py` als klare Sektion gekennzeichnet:
  - **Akku Uebersicht** = Systemakku (gesamt)
  - **Akku1 Block** = einzelner Akku-Pack

## [0.1.4] - 2026-02-22
### Added
- `CHANGELOG.md` eingefuehrt als zentrale Versions- und Aenderungshistorie.

## [0.1.3] - 2026-02-22
### Fixed
- Skalierung von `Akku1 Rate Capacity` korrigiert (`gain` von `10` auf `100`), damit die Nennkapazitaet korrekt dargestellt wird.

## [0.1.2] - 2026-02-22
### Added
- Neue Leistungs-Sensoren:
  - Haus Verbrauch (`active_power_pcs_ac_side`, Register `10006`)
  - Akku Leistung (`battery_power_pcs`, Register `10008`)
  - Power Load (`load_power`, Register `10010`)
  - Power Grid (`grid_power`, Register `10012`)
- Neue Backup-Phasenstrom-Sensoren:
  - Backup/Phase A Strom (`10230`)
  - Backup Phase B Strom (`10231`)
  - Backup Phase C Strom (`10232`)
- Neuer Akku1-Block (`akku1_*`) mit:
  - Modellname, Seriennummer, Software-/Hardware-Version
  - Rate Capacity, Status, Spannung, Leistung
  - SoC, SoH, Gesamt-Entladeenergie
  - Max/Min Temperatur

## [0.1.1] - 2026-02-22
### Added
- PV-String-Sensoren:
  - PV1 Spannung (`10167`)
  - PV1 Strom (`10168`)
  - PV2 Spannung (`10169`)
  - PV2 Strom (`10170`)

## [0.1.0] - 2026-02-22
### Added
- Initiale HACS-faehige Anker Solix X1 Integration
- Lokales Modbus-TCP-Polling
- Config Flow + Optionen
- Basis-Sensoren fuer PV, Batterie, Netz und Energiezaehler

