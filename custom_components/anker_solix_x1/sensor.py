"""Sensor platform for Anker Solix X1."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
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
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_DEFINITIONS
from .coordinator import AnkerSolixX1ConfigEntry, AnkerSolixX1Coordinator


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
    if device_class == "energy_storage":
        return SensorDeviceClass.ENERGY_STORAGE
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
    entry: AnkerSolixX1ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data
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
        entry: AnkerSolixX1ConfigEntry,
        description: AnkerSensorDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

        data = coordinator.data or {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Anker",
            model=_text_or_none(data.get("model_name")) or "SOLIX X1",
            serial_number=_text_or_none(data.get("serial_number")),
            sw_version=_text_or_none(data.get("software_version")),
        )

    @property
    def native_value(self) -> int | float | str | None:
        """Return sensor value."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self.entity_description.key)


def _text_or_none(value: object) -> str | None:
    """Return a non-empty string or None."""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None

