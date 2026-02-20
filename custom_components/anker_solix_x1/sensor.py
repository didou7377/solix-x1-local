"""Sensor platform for Anker Solix X1."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_DEFINITIONS
from .coordinator import AnkerSolixX1Coordinator


def _map_device_class(device_class: str | None) -> SensorDeviceClass | None:
    if device_class == "power":
        return SensorDeviceClass.POWER
    if device_class == "voltage":
        return SensorDeviceClass.VOLTAGE
    if device_class == "current":
        return SensorDeviceClass.CURRENT
    if device_class == "temperature":
        return SensorDeviceClass.TEMPERATURE
    if device_class == "battery":
        return SensorDeviceClass.BATTERY
    if device_class == "frequency":
        return SensorDeviceClass.FREQUENCY
    if device_class == "energy":
        return SensorDeviceClass.ENERGY
    return None


def _map_state_class(state_class: str | None) -> SensorStateClass | None:
    if state_class == "measurement":
        return SensorStateClass.MEASUREMENT
    if state_class == "total_increasing":
        return SensorStateClass.TOTAL_INCREASING
    return None


def _map_unit(unit: str | None):
    if unit in (None, "", "/"):
        return None
    if unit == "V":
        return UnitOfElectricPotential.VOLT
    if unit == "A":
        return UnitOfElectricCurrent.AMPERE
    if unit == "W":
        return UnitOfPower.WATT
    if unit == "kW":
        return UnitOfPower.KILO_WATT
    if unit == "Hz":
        return UnitOfFrequency.HERTZ
    if unit == "°C":
        return UnitOfTemperature.CELSIUS
    if unit == "%":
        return PERCENTAGE
    if unit == "kWh":
        return UnitOfEnergy.KILO_WATT_HOUR
    return unit


def _map_entity_category(category: str | None) -> EntityCategory | None:
    if category == "diagnostic":
        return EntityCategory.DIAGNOSTIC
    return None


@dataclass(frozen=True, kw_only=True)
class AnkerSensorDescription(SensorEntityDescription):
    """Sensor description for register based entities."""

    key: str


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: AnkerSolixX1Coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []
    for sensor_def in SENSOR_DEFINITIONS:
        sensors.append(
            AnkerSolixX1Sensor(
                coordinator=coordinator,
                entry=entry,
                description=AnkerSensorDescription(
                    key=str(sensor_def["key"]),
                    name=str(sensor_def["name"]),
                    device_class=_map_device_class(sensor_def.get("device_class")),
                    state_class=_map_state_class(sensor_def.get("state_class")),
                    native_unit_of_measurement=_map_unit(sensor_def.get("unit")),
                    entity_category=_map_entity_category(sensor_def.get("entity_category")),
                ),
            )
        )
    async_add_entities(sensors)


class AnkerSolixX1Sensor(CoordinatorEntity[AnkerSolixX1Coordinator], SensorEntity):
    """Generic sensor entity for register-based values."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AnkerSolixX1Coordinator,
        entry: ConfigEntry,
        description: AnkerSensorDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Anker",
            "model": "SOLIX X1",
        }

    @property
    def native_value(self) -> int | float | str | None:
        """Return sensor value."""
        return self.coordinator.data.get(self.entity_description.key)

