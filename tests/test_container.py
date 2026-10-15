# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Pure-memory parser tests; optional --original adds pinned updater roundtrips.

Run: python -B tests/test_container.py [--original path/to/official-C11.exe]
No executables are run or written and no device is accessed.
"""
import argparse
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.container import (Container, HexImage, RepackError, SOURCE_SIZE,
                             SPANS, HEX_START, HEX_END)

ORIGINAL = None


def record(kind, address=0, payload=b"", ending=b"\n"):
    raw = bytes([len(payload)]) + address.to_bytes(2, "big") + bytes([kind]) + payload
    return b":" + (raw + bytes([(-sum(raw)) & 255])).hex().upper().encode() + ending


class HexTests(unittest.TestCase):
    def setUp(self):
        self.text = (record(4, payload=b"\x00\x01", ending=b"\r\n") +
                     record(0, 0x4000, b"\x10\xab\x30", b"\r\n").lower() +
                     record(0, 0x4010, b"\xfe\x00", b"\n") + record(1, ending=b""))
        self.hex = HexImage(self.text)

    def test_sparse_noop_preserves_exact_spelling_and_endings(self):
        self.assertEqual(self.hex.replace_opaque_bytes({}).text, self.text)
        self.assertEqual(self.hex.replace_opaque_bytes({0x14001: 0xab}).text, self.text)
        self.assertEqual(self.hex.spans(), [(0x14000, 0x14003), (0x14010, 0x14012)])

    def test_sparse_edit_keeps_other_bytes_layout_and_checksum(self):
        edited = self.hex.replace_opaque_bytes({0x14001: 0xc3, 0x14011: 0x55})
        self.assertEqual(edited.layout(), self.hex.layout())
        self.assertEqual(len(edited.text), len(self.text))
        self.assertEqual(edited.spans(), self.hex.spans())
        expected = dict(self.hex.memory, **{})
        expected.update({0x14001: 0xc3, 0x14011: 0x55})
        self.assertEqual(edited.memory, expected)
        self.assertEqual(edited.records[0].original, self.hex.records[0].original)
        self.assertEqual(edited.records[-1].original, self.hex.records[-1].original)

    def test_bad_checksum_rejected(self):
        bad = record(0, 0x20, b"\x10")[:-3] + b"00\n" + record(1)
        with self.assertRaisesRegex(RepackError, "checksum"):
            HexImage(bad)

    def test_overlap_rejected_across_address_records(self):
        text = (record(4, payload=b"\x00\x01") + record(0, 0x20, b"\x01\x02") +
                record(2, payload=b"\x10\x00") + record(0, 0x21, b"\x02") + record(1))
        with self.assertRaisesRegex(RepackError, "Overlapping"):
            HexImage(text)

    def test_extra_eof_and_content_after_eof_rejected(self):
        for tail in [record(1), b"\n", record(0, 5, b"\x00")]:
            with self.subTest(tail=tail), self.assertRaises(RepackError):
                HexImage(self.text + b"\n" + tail)

    def test_gap_outside_and_invalid_values_rejected(self):
        for changes in [{0x14005: 1}, {0: 1}, {0x14000: 256}, {0x14000: -1},
                        {0x14000: True}, {True: 0}]:
            with self.subTest(changes=changes), self.assertRaises(RepackError):
                self.hex.replace_opaque_bytes(changes)

    def test_malformed_hex_rejected(self):
        cases = [b"", b":0\n", b":GG\n", b":00 000001FF\n", b":00000000\n",
                 record(0, 0xffff, b"\x00\x01") + record(1),
                 record(5, payload=b"\x00\x00\x40\x00") + record(1),
                 record(4, 1, b"\x00\x01") + record(1),
                 record(0, 1, b"\x00"), record(1),
                 record(0, 1, b"\x00") + record(1, 1)]
        for text in cases:
            with self.subTest(text=text), self.assertRaises(RepackError):
                HexImage(text)
        with self.assertRaises(RepackError):
            HexImage(self.text.decode("ascii"))

    def test_bad_official_sha_rejected(self):
        with self.assertRaisesRegex(RepackError, "pinned original"):
            Container(bytes(SOURCE_SIZE))

    def test_unpinned_mode_still_rejects_changed_outer_bytes(self):
        with self.assertRaisesRegex(RepackError, "outside"):
            Container(bytes(SOURCE_SIZE), require_vendor_pin=False)


class OfficialContainerTests(unittest.TestCase):
    def setUp(self):
        if ORIGINAL is None:
            self.skipTest("Supply --original for pinned vendor-input checks")
        self.data = ORIGINAL
        self.container = Container(self.data)

    def test_official_noop_is_byte_identical(self):
        self.assertEqual((self.container.start, self.container.end), (HEX_START, HEX_END))
        self.assertEqual(self.container.hex.spans(), SPANS)
        self.assertEqual(self.container.replace_hex(self.container.hex), self.data)

    def test_synthetic_edit_only_in_resource_and_reparse(self):
        addr = 0x4002
        edited = self.container.hex.replace_opaque_bytes({addr: self.container.hex.memory[addr] ^ 1})
        result = self.container.replace_hex(edited)
        self.assertEqual(result[:HEX_START], self.data[:HEX_START])
        self.assertEqual(result[HEX_END:], self.data[HEX_END:])
        self.assertEqual(Container(result, require_vendor_pin=False).hex.memory, edited.memory)
        with self.assertRaisesRegex(RepackError, "pinned original"):
            Container(result)

    def test_replacement_layout_change_rejected(self):
        changed = HexImage(self.container.hex_bytes.replace(b":020000040001F9", b":020000040002F8"))
        with self.assertRaisesRegex(RepackError, "layout"):
            self.container.replace_hex(changed)

    def test_same_size_outside_modification_rejected(self):
        result = bytearray(self.data)
        result[0] ^= 1
        with self.assertRaisesRegex(RepackError, "outside"):
            Container(bytes(result), require_vendor_pin=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path)
    args, unittest_args = parser.parse_known_args()
    if args.original:
        ORIGINAL = args.original.read_bytes()
    unittest.main(argv=[sys.argv[0]] + unittest_args)
