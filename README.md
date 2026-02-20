# Anker Solix X1 Home Assistant Integration

Custom Home Assistant integration for reading Anker SOLIX X1 data locally via Modbus TCP.

## Features

- UI-based setup (Config Flow)
- Configurable:
  - Name
  - IP address
  - Port (default: `502`)
  - Polling interval (default: `5` seconds)
- Local polling over Modbus TCP
- Automatic sensor creation from `SENSOR_DEFINITIONS` in `const.py`
- HACS custom repository ready

## Installation via HACS (Custom Repository)

1. Open HACS in Home Assistant.
2. Go to **HACS -> Integrations -> top right menu -> Custom repositories**.
3. Add repository URL: `https://github.com/didou7377/solix-x1-local`
4. Category: **Integration**
5. Install **Anker Solix X1**
6. Restart Home Assistant.
7. Go to **Settings -> Devices & Services -> Add Integration** and search for **Anker Solix X1**.

## Manual Installation

1. Copy `custom_components/anker_solix_x1` into your Home Assistant `custom_components` folder.
2. Restart Home Assistant.
3. Add the integration in **Settings -> Devices & Services**.

## Supported Data

Current implementation includes system info, battery, grid and energy-related sensors for supported Modbus registers.
Additional sensors can be added by extending `SENSOR_DEFINITIONS` in `const.py`.

## Release Checklist

- Update `manifest.json` version
- Commit and push to `main`
- Create a GitHub tag/release (for example `v0.1.0`)
- In Home Assistant HACS, click **Check for updates**

