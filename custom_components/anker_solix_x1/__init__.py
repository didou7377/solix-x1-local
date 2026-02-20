"""Anker Solix X1 integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, PLATFORMS
from .coordinator import AnkerSolixX1Coordinator

AnkerSolixX1ConfigEntry = ConfigEntry

_LEGACY_SENSOR_KEYS_TO_REMOVE = {
    "grid_voltage_uab",
    "grid_voltage_ubc",
    "grid_voltage_uca",
    "daily_charge_energy",
    "daily_discharge_energy",
    "total_charge_energy",
    "total_discharge_energy",
}


def _remove_legacy_entities(hass: HomeAssistant, entry: AnkerSolixX1ConfigEntry) -> None:
    """Remove old sensor entities that are no longer part of this integration."""
    entity_registry = er.async_get(hass)
    prefix = f"{entry.entry_id}_"

    for entity in list(entity_registry.entities.values()):
        if entity.config_entry_id != entry.entry_id or entity.domain != "sensor":
            continue
        if entity.unique_id is None or not entity.unique_id.startswith(prefix):
            continue

        legacy_key = entity.unique_id[len(prefix) :]
        if legacy_key in _LEGACY_SENSOR_KEYS_TO_REMOVE:
            entity_registry.async_remove(entity.entity_id)


async def async_setup_entry(hass: HomeAssistant, entry: AnkerSolixX1ConfigEntry) -> bool:
    """Set up Anker Solix X1 from a config entry."""
    coordinator = AnkerSolixX1Coordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    _remove_legacy_entities(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AnkerSolixX1ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok

