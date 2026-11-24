"""DataUpdateCoordinator for Anker Solix X1."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusIOException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_ID,
    DOMAIN,
    MAX_BLOCK_GAP,
    MAX_BLOCK_SIZE,
    MODBUS_ADDRESS_OFFSET,
    MODBUS_RETRIES,
    MODBUS_TIMEOUT,
    SENSOR_DEFINITIONS,
)
from .modbus_codec import (
    RegisterBlock,
    SensorDefinition,
    build_register_blocks,
    decode_sensor,
    slice_registers,
)

_LOGGER = logging.getLogger(__name__)

type AnkerSolixX1ConfigEntry = ConfigEntry[AnkerSolixX1Coordinator]
SensorData = dict[str, int | float | str | None]


async def _read_input_registers_compat(
    client: AsyncModbusTcpClient,
    address: int,
    count: int,
    unit_id: int,
) -> Any:
    """Read input registers across pymodbus API variants.

    Different pymodbus versions use different keyword names for the unit id
    (device_id, slave, unit). Try the known variants in order.
    """
    for keyword in ("device_id", "slave", "unit"):
        try:
            return await client.read_input_registers(
                address=address, count=count, **{keyword: unit_id}
            )
        except TypeError:
            continue
    raise UpdateFailed("Keine kompatible pymodbus-Version gefunden")


class AnkerSolixX1Coordinator(DataUpdateCoordinator[SensorData]):
    """Coordinator to fetch Anker Solix X1 data."""

    config_entry: AnkerSolixX1ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: AnkerSolixX1ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.host: str = entry.data[CONF_HOST]
        self.port: int = entry.data[CONF_PORT]
        self.unit_id: int = entry.data.get("unit_id", DEFAULT_UNIT_ID)
        scan_interval_seconds = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=scan_interval_seconds),
        )

        self._client: AsyncModbusTcpClient | None = None
        self._blocks: list[RegisterBlock] = build_register_blocks(
            SENSOR_DEFINITIONS, MAX_BLOCK_SIZE, MAX_BLOCK_GAP
        )
        _LOGGER.debug(
            "%s Sensoren werden in %s Modbus-Anfragen gelesen",
            len(SENSOR_DEFINITIONS),
            len(self._blocks),
        )

    async def _async_get_client(self) -> AsyncModbusTcpClient:
        """Return a connected client, reusing the open connection."""
        if self._client is not None and self._client.connected:
            return self._client

        self._close_client()
        client = AsyncModbusTcpClient(
            host=self.host,
            port=self.port,
            timeout=MODBUS_TIMEOUT,
            retries=MODBUS_RETRIES,
        )
        if not await client.connect():
            client.close()
            raise UpdateFailed(f"Verbindung fehlgeschlagen: {self.host}:{self.port}")
        self._client = client
        return client

    def _close_client(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    async def async_shutdown(self) -> None:
        """Close the Modbus connection when the entry is unloaded."""
        await super().async_shutdown()
        self._close_client()

    async def _read(self, client: AsyncModbusTcpClient, address: int, count: int) -> list[int] | None:
        """Read registers, returning None when the device answers with an error."""
        result = await _read_input_registers_compat(
            client, address + MODBUS_ADDRESS_OFFSET, count, self.unit_id
        )
        if result.isError():
            return None
        return list(result.registers)

    def _decode_into(self, data: SensorData, sensor_def: SensorDefinition, registers: list[int]) -> None:
        key = str(sensor_def["key"])
        try:
            data[key] = decode_sensor(sensor_def, registers)
        except (ValueError, IndexError) as err:
            _LOGGER.debug("Wert fuer %s nicht dekodierbar: %s", key, err)
            data[key] = None

    async def _read_block(self, client: AsyncModbusTcpClient, block: RegisterBlock, data: SensorData) -> None:
        """Read one block; fall back to single reads if the device rejects it."""
        registers = await self._read(client, block.start, block.count)
        if registers is not None:
            for sensor_def in block.sensors:
                try:
                    chunk = slice_registers(block, registers, sensor_def)
                except ValueError as err:
                    _LOGGER.debug("%s", err)
                    data[str(sensor_def["key"])] = None
                    continue
                self._decode_into(data, sensor_def, chunk)
            return

        if len(block.sensors) > 1:
            _LOGGER.debug(
                "Block %s-%s abgelehnt, lese Register einzeln", block.start, block.end - 1
            )
        for sensor_def in block.sensors:
            key = str(sensor_def["key"])
            single = await self._read(client, int(sensor_def["address"]), int(sensor_def["count"]))
            if single is None:
                _LOGGER.debug("Modbus-Fehler auf Register %s (%s)", sensor_def["address"], key)
                data[key] = None
                continue
            self._decode_into(data, sensor_def, single)

    async def _async_update_data(self) -> SensorData:
        """Fetch data from the inverter via Modbus TCP."""
        client = await self._async_get_client()
        data: SensorData = {}

        try:
            for block in self._blocks:
                await self._read_block(client, block, data)
        except (ConnectionException, ModbusIOException, TimeoutError, OSError) as err:
            self._close_client()
            raise UpdateFailed(f"Datenabfrage fehlgeschlagen: {err}") from err

        if all(value is None for value in data.values()):
            raise UpdateFailed("Das Geraet hat auf keine Registerabfrage geantwortet")

        return data
