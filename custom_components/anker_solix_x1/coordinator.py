"""DataUpdateCoordinator for Anker Solix X1."""

from __future__ import annotations

from datetime import timedelta
import logging

from pymodbus.client import AsyncModbusTcpClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_ID,
    DOMAIN,
    MODBUS_ADDRESS_OFFSET,
    SENSOR_DEFINITIONS,
)

_LOGGER = logging.getLogger(__name__)


async def _read_input_registers_compat(
    client: AsyncModbusTcpClient,
    address: int,
    count: int,
    unit_id: int,
):
    """Read input registers across pymodbus API variants.

    Different pymodbus versions use different keyword names for unit id
    (e.g. device_id, unit, slave). Try the known variants in order.
    """
    try:
        return await client.read_input_registers(
            address=address,
            count=count,
            device_id=unit_id,
        )
    except TypeError:
        pass

    try:
        return await client.read_input_registers(
            address=address,
            count=count,
            unit=unit_id,
        )
    except TypeError:
        return await client.read_input_registers(
            address=address,
            count=count,
            slave=unit_id,
        )


class AnkerSolixX1Coordinator(DataUpdateCoordinator[dict[str, int | float | str | None]]):
    """Coordinator to fetch Anker Solix X1 data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
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
            update_interval=timedelta(seconds=scan_interval_seconds),
        )

    def _decode_register_value(
        self,
        registers: list[int],
        data_type: str,
        gain: int,
        swap: str | None,
        max_abs: float | None = None,
    ) -> int | float | str:
        """Decode Modbus registers and apply gain."""
        normalized_data_type = data_type.strip().lower()
        registers_local = registers.copy()

        if normalized_data_type == "string":
            chars = bytearray()
            for register in registers:
                high = (register >> 8) & 0xFF
                low = register & 0xFF
                if swap == "byte":
                    chars.append(low)
                    chars.append(high)
                else:
                    chars.append(high)
                    chars.append(low)

            decoded = chars.decode("utf-8", errors="ignore")
            return decoded.replace("\x00", "").strip()

        if normalized_data_type == "int32" and swap == "auto_power" and len(registers_local) >= 2:
            def _byte_swap(reg: int) -> int:
                return ((reg & 0xFF) << 8) | ((reg >> 8) & 0xFF)

            def _to_int32(regs: list[int]) -> int:
                value = (regs[0] << 16) | regs[1]
                if value > 0x7FFFFFFF:
                    value -= 0x100000000
                return value

            candidate_regs: list[list[int]] = [
                [_byte_swap(registers_local[0]), _byte_swap(registers_local[1])],  # byte
                [registers_local[1], registers_local[0]],  # word
                [_byte_swap(registers_local[1]), _byte_swap(registers_local[0])],  # word_byte
                [registers_local[0], registers_local[1]],  # none
            ]

            candidates: list[int | float] = []
            for regs in candidate_regs:
                raw = _to_int32(regs)
                scaled = raw if gain <= 1 else raw / gain
                if isinstance(scaled, float) and scaled.is_integer():
                    scaled = int(scaled)
                candidates.append(scaled)

            if max_abs is not None:
                plausible = [
                    value for value in candidates if isinstance(value, (int, float)) and abs(value) <= max_abs
                ]
                if plausible:
                    return plausible[0]

            return min(candidates, key=lambda value: abs(float(value)))

        if swap == "word" and len(registers_local) >= 2:
            registers_local = [registers_local[1], registers_local[0], *registers_local[2:]]
        elif swap == "byte":
            registers_local = [((reg & 0xFF) << 8) | ((reg >> 8) & 0xFF) for reg in registers_local]
        elif swap == "word_byte" and len(registers_local) >= 2:
            registers_local = [registers_local[1], registers_local[0], *registers_local[2:]]
            registers_local = [
                ((reg & 0xFF) << 8) | ((reg >> 8) & 0xFF) for reg in registers_local
            ]

        if normalized_data_type == "uint16":
            raw_value = registers_local[0]
        elif normalized_data_type == "int16":
            raw_value = registers_local[0]
            if raw_value > 0x7FFF:
                raw_value -= 0x10000
        elif normalized_data_type == "uint32":
            raw_value = (registers_local[0] << 16) | registers_local[1]
        elif normalized_data_type == "int32":
            raw_value = (registers_local[0] << 16) | registers_local[1]
            if raw_value > 0x7FFFFFFF:
                raw_value -= 0x100000000
        else:
            raise ValueError(f"Unsupported data_type: {data_type}")

        if gain <= 1:
            return raw_value

        scaled = raw_value / gain
        if isinstance(scaled, float) and scaled.is_integer():
            return int(scaled)
        return scaled

    async def _async_update_data(self) -> dict[str, int | float | str | None]:
        """Fetch data from inverter via Modbus TCP."""
        client = AsyncModbusTcpClient(host=self.host, port=self.port)
        connected = await client.connect()
        if not connected:
            raise UpdateFailed(f"Verbindung fehlgeschlagen: {self.host}:{self.port}")

        data: dict[str, int | float | str | None] = {}

        try:
            for sensor_def in SENSOR_DEFINITIONS:
                key = str(sensor_def["key"])
                address = int(sensor_def["address"])
                count = int(sensor_def["count"])
                data_type = str(sensor_def["data_type"])
                gain = int(sensor_def["gain"])
                swap = sensor_def.get("swap")
                max_abs = sensor_def.get("max_abs")
                if swap is not None:
                    swap = str(swap).strip().lower()
                if max_abs is not None:
                    max_abs = float(max_abs)

                result = await _read_input_registers_compat(
                    client=client,
                    address=address + MODBUS_ADDRESS_OFFSET,
                    count=count,
                    unit_id=self.unit_id,
                )
                if result.isError():
                    _LOGGER.debug("Modbus-Fehler auf Register %s (%s)", address, key)
                    data[key] = None
                    continue

                data[key] = self._decode_register_value(
                    result.registers, data_type, gain, swap, max_abs
                )

            return data
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Datenabfrage fehlgeschlagen: {err}") from err
        finally:
            client.close()

