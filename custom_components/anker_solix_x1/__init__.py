"""Anker Solix X1 integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import AnkerSolixX1ConfigEntry, AnkerSolixX1Coordinator
from .services import async_setup_services

# Setup happens only through the UI; required because async_setup is defined.
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_LEGACY_SENSOR_KEYS_TO_REMOVE = {
    "grid_voltage_uab",
    "grid_voltage_ubc",
    "grid_voltage_uca",
    "daily_charge_energy",
    "daily_discharge_energy",
    "total_charge_energy",
    "total_discharge_energy",
    # Renamed to structured akku_* keys.
    "battery_health",
    "battery_soc",
    "battery_number_of_packs",
    "battery_rated_capacity",
    "battery_status",
    "battery_voltage",
    "battery_power",
    # Removed duplicate/incorrect power entity.
    "akku_power",
}


def _remove_legacy_entities(hass: HomeAssistant, entry: AnkerSolixX1ConfigEntry) -> None:
    """Remove old sensor entities that are no longer part of this integration."""
    entity_registry = er.async_get(hass)
    prefix = f"{entry.entry_id}_"

    for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity.domain != "sensor" or not entity.unique_id.startswith(prefix):
            continue
        if entity.unique_id[len(prefix) :] in _LEGACY_SENSOR_KEYS_TO_REMOVE:
            entity_registry.async_remove(entity.entity_id)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register integration-wide actions."""
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: AnkerSolixX1ConfigEntry) -> bool:
    """Set up Anker Solix X1 from a config entry."""
    coordinator = AnkerSolixX1Coordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    _remove_legacy_entities(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: AnkerSolixX1ConfigEntry) -> None:
    """Reload the entry so changed options (scan interval) take effect."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: AnkerSolixX1ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
