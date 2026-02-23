# Changelog

Alle nennenswerten Aenderungen an diesem Projekt werden hier dokumentiert.

Das Format orientiert sich an Keep a Changelog und Semantic Versioning.

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

