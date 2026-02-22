# Changelog

Alle nennenswerten Aenderungen an diesem Projekt werden hier dokumentiert.

Das Format orientiert sich an Keep a Changelog und Semantic Versioning.

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

