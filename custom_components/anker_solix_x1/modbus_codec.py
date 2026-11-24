"""Register decoding and request batching for Anker Solix X1.

This module has no Home Assistant or pymodbus imports so it can be tested
on its own.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

SensorDefinition = Mapping[str, Any]


@dataclass
class RegisterBlock:
    """A contiguous register range read in a single Modbus request."""

    start: int
    count: int
    sensors: list[SensorDefinition] = field(default_factory=list)

    @property
    def end(self) -> int:
        """Return the first address after this block."""
        return self.start + self.count


def build_register_blocks(
    sensor_definitions: Iterable[SensorDefinition],
    max_block_size: int,
    max_gap: int,
) -> list[RegisterBlock]:
    """Group sensor definitions into as few register blocks as possible.

    Sensors are joined into one block when the unused gap between them is at
    most ``max_gap`` registers and the block stays within ``max_block_size``.
    """
    ordered = sorted(sensor_definitions, key=lambda d: int(d["address"]))
    blocks: list[RegisterBlock] = []

    for sensor_def in ordered:
        address = int(sensor_def["address"])
        count = int(sensor_def["count"])
        sensor_end = address + count

        if blocks:
            block = blocks[-1]
            gap = address - block.end
            new_end = max(block.end, sensor_end)
            if gap <= max_gap and new_end - block.start <= max_block_size:
                block.count = new_end - block.start
                block.sensors.append(sensor_def)
                continue

        blocks.append(RegisterBlock(start=address, count=count, sensors=[sensor_def]))

    return blocks


def slice_registers(block: RegisterBlock, registers: list[int], sensor_def: SensorDefinition) -> list[int]:
    """Return the registers belonging to one sensor inside a block read."""
    offset = int(sensor_def["address"]) - block.start
    count = int(sensor_def["count"])
    chunk = registers[offset : offset + count]
    if len(chunk) != count:
        raise ValueError(
            f"Expected {count} registers for {sensor_def['key']}, got {len(chunk)}"
        )
    return chunk


def _byte_swap(reg: int) -> int:
    return ((reg & 0xFF) << 8) | ((reg >> 8) & 0xFF)


def _to_int32(regs: list[int]) -> int:
    value = (regs[0] << 16) | regs[1]
    if value > 0x7FFFFFFF:
        value -= 0x100000000
    return value


def _apply_gain(raw_value: int, gain: int) -> int | float:
    if gain <= 1:
        return raw_value
    scaled = raw_value / gain
    if scaled.is_integer():
        return int(scaled)
    return scaled


def decode_register_value(
    registers: list[int],
    data_type: str,
    gain: int,
    swap: str | None,
    max_abs: float | None = None,
) -> int | float | str:
    """Decode Modbus registers and apply the gain divisor."""
    normalized_data_type = data_type.strip().lower()
    swap = swap.strip().lower() if isinstance(swap, str) else None
    registers_local = list(registers)

    if normalized_data_type == "string":
        chars = bytearray()
        for register in registers_local:
            high = (register >> 8) & 0xFF
            low = register & 0xFF
            if swap == "byte":
                chars.extend((low, high))
            else:
                chars.extend((high, low))
        return chars.decode("utf-8", errors="ignore").replace("\x00", "").strip()

    if normalized_data_type == "int32" and swap == "auto_power" and len(registers_local) >= 2:
        # Legacy heuristic for custom definitions: try every byte/word order
        # and keep the first plausible result.
        first, second = registers_local[0], registers_local[1]
        candidate_regs = [
            [_byte_swap(first), _byte_swap(second)],
            [second, first],
            [_byte_swap(second), _byte_swap(first)],
            [first, second],
        ]
        candidates = [_apply_gain(_to_int32(regs), gain) for regs in candidate_regs]
        if max_abs is not None:
            plausible = [value for value in candidates if abs(value) <= max_abs]
            if plausible:
                return plausible[0]
        return min(candidates, key=lambda value: abs(float(value)))

    if swap in ("word", "word_byte") and len(registers_local) >= 2:
        registers_local = [registers_local[1], registers_local[0], *registers_local[2:]]
    if swap in ("byte", "word_byte"):
        registers_local = [_byte_swap(reg) for reg in registers_local]

    if normalized_data_type == "uint16":
        raw_value = registers_local[0]
    elif normalized_data_type == "int16":
        raw_value = registers_local[0]
        if raw_value > 0x7FFF:
            raw_value -= 0x10000
    elif normalized_data_type == "uint32":
        raw_value = (registers_local[0] << 16) | registers_local[1]
    elif normalized_data_type == "int32":
        raw_value = _to_int32(registers_local)
    else:
        raise ValueError(f"Unsupported data_type: {data_type}")

    return _apply_gain(raw_value, gain)


def decode_sensor(sensor_def: SensorDefinition, registers: list[int]) -> int | float | str:
    """Decode the value of one sensor definition from its own registers."""
    max_abs = sensor_def.get("max_abs")
    return decode_register_value(
        registers,
        str(sensor_def["data_type"]),
        int(sensor_def["gain"]),
        sensor_def.get("swap"),
        float(max_abs) if max_abs is not None else None,
    )
