"""Tests for register decoding and batching (no Home Assistant needed).

Run with: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys
import unittest

COMPONENT_DIR = Path(__file__).resolve().parent.parent / "custom_components" / "anker_solix_x1"

_spec = importlib.util.spec_from_file_location("modbus_codec", COMPONENT_DIR / "modbus_codec.py")
codec = importlib.util.module_from_spec(_spec)
sys.modules["modbus_codec"] = codec
_spec.loader.exec_module(codec)


def _load_const_values() -> dict[str, object]:
    """Read literal constants from const.py without importing Home Assistant."""
    tree = ast.parse((COMPONENT_DIR / "const.py").read_text(encoding="utf-8"))
    values: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name, value = node.targets[0].id, node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name, value = node.target.id, node.value
        else:
            continue
        try:
            values[name] = ast.literal_eval(value)
        except ValueError:
            continue
    return values


CONST = _load_const_values()
SENSORS = CONST["SENSOR_DEFINITIONS"]


class DecodeTests(unittest.TestCase):
    def test_uint16_with_gain(self) -> None:
        self.assertEqual(codec.decode_register_value([2305], "uint16", 10, None), 230.5)

    def test_gain_returns_int_when_whole(self) -> None:
        value = codec.decode_register_value([5000], "uint16", 100, None)
        self.assertEqual(value, 50)
        self.assertIsInstance(value, int)

    def test_int16_negative(self) -> None:
        self.assertEqual(codec.decode_register_value([0xFFF6], "int16", 100, None), -0.1)

    def test_int32_word_swap_negative(self) -> None:
        # -1500 W as 0xFFFFFA24, low word first on the wire.
        self.assertEqual(codec.decode_register_value([0xFA24, 0xFFFF], "int32", 1, "word"), -1500)

    def test_uint32_word_swap(self) -> None:
        # 123456 = 0x0001E240 -> low word first.
        self.assertEqual(codec.decode_register_value([0xE240, 0x0001], "uint32", 100, "word"), 1234.56)

    def test_word_byte_swap(self) -> None:
        # 0x00010002 with words and bytes swapped.
        self.assertEqual(codec.decode_register_value([0x0200, 0x0100], "uint32", 1, "word_byte"), 0x00010002)

    def test_string_byte_swap_strips_padding(self) -> None:
        registers = [0x3158, 0x0000]  # "X1" with swapped bytes, then padding
        self.assertEqual(codec.decode_register_value(registers, "string", 1, "byte"), "X1")

    def test_string_without_swap(self) -> None:
        self.assertEqual(codec.decode_register_value([0x4131, 0x2000], "string", 1, None), "A1")

    def test_auto_power_uses_max_abs(self) -> None:
        value = codec.decode_register_value([0x05DC, 0x0000], "int32", 1, "auto_power", max_abs=20000)
        self.assertEqual(value, 1500)

    def test_unknown_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            codec.decode_register_value([1], "float32", 1, None)


class BlockTests(unittest.TestCase):
    def test_adjacent_sensors_share_block(self) -> None:
        defs = [
            {"key": "a", "address": 100, "count": 2},
            {"key": "b", "address": 102, "count": 1},
            {"key": "c", "address": 106, "count": 1},
        ]
        blocks = codec.build_register_blocks(defs, max_block_size=100, max_gap=8)
        self.assertEqual(len(blocks), 1)
        self.assertEqual((blocks[0].start, blocks[0].count), (100, 7))

    def test_large_gap_splits(self) -> None:
        defs = [
            {"key": "a", "address": 100, "count": 1},
            {"key": "b", "address": 200, "count": 1},
        ]
        self.assertEqual(len(codec.build_register_blocks(defs, 100, 8)), 2)

    def test_block_size_limit(self) -> None:
        defs = [{"key": f"s{i}", "address": 1000 + i * 10, "count": 10} for i in range(30)]
        blocks = codec.build_register_blocks(defs, max_block_size=100, max_gap=8)
        self.assertTrue(all(block.count <= 100 for block in blocks))
        self.assertEqual(sum(len(block.sensors) for block in blocks), 30)

    def test_slice_registers(self) -> None:
        block = codec.RegisterBlock(start=10, count=5)
        sensor = {"key": "x", "address": 12, "count": 2}
        self.assertEqual(codec.slice_registers(block, [0, 1, 2, 3, 4], sensor), [2, 3])

    def test_slice_registers_short_response(self) -> None:
        block = codec.RegisterBlock(start=10, count=5)
        with self.assertRaises(ValueError):
            codec.slice_registers(block, [0, 1], {"key": "x", "address": 12, "count": 2})


class SensorDefinitionTests(unittest.TestCase):
    def test_keys_are_unique(self) -> None:
        keys = [d["key"] for d in SENSORS]
        self.assertEqual(len(keys), len(set(keys)))

    def test_counts_match_data_types(self) -> None:
        expected = {"uint16": 1, "int16": 1, "uint32": 2, "int32": 2}
        for d in SENSORS:
            if d["data_type"] in expected:
                self.assertEqual(d["count"], expected[d["data_type"]], d["key"])

    def test_energy_sensors_are_totals(self) -> None:
        for d in SENSORS:
            if d.get("device_class") == "energy":
                self.assertIn(d.get("state_class"), ("total", "total_increasing"), d["key"])

    def test_real_definitions_cover_every_sensor(self) -> None:
        blocks = codec.build_register_blocks(SENSORS, CONST["MAX_BLOCK_SIZE"], CONST["MAX_BLOCK_GAP"])
        covered = [d["key"] for block in blocks for d in block.sensors]
        self.assertEqual(sorted(covered), sorted(d["key"] for d in SENSORS))
        self.assertLess(len(blocks), len(SENSORS) // 3)
        for block in blocks:
            self.assertLessEqual(block.count, 125)
            for d in block.sensors:
                self.assertLessEqual(d["address"] + d["count"], block.end)


if __name__ == "__main__":
    unittest.main()
