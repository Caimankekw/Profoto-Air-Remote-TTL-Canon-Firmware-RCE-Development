# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Self-contained codec tests; no vendor executable, captures or USB needed."""
from pathlib import Path
import hashlib
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("standalone_reference_codec", ROOT / "tools/reference_codec.py")
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)


class ReferenceCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.codec = C.ReferenceCodec()

    def test_primitive_all_values_and_masks(self):
        for mask in range(16):
            for value in range(256):
                self.assertEqual(C.swap_pairs(C.swap_pairs(value, mask), mask), value)

    def test_table_dimensions_and_hash(self):
        raw = (ROOT / "reference/c11_offset_transform.bin").read_bytes()
        self.assertEqual(len(raw), 73725)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), C.TABLE_SHA256)
        self.assertEqual(len(self.codec._keys), 49150)
        self.assertEqual(len(self.codec._masks), 49150)
        self.assertTrue(all(mask < 16 for mask in self.codec._masks))

    def test_every_address_roundtrip_with_varied_values(self):
        count = C.ENCODABLE_END - C.ENCODABLE_START
        data = bytes((i * 73 + 91) & 255 for i in range(count))
        opaque = self.codec.encode(C.ENCODABLE_START, data)
        self.assertEqual(self.codec.decode(C.ENCODABLE_START, opaque), data)

    def test_unaligned_slice_matches_whole_transform(self):
        plain = bytes(range(256))
        whole = self.codec.encode(0x8000, plain)
        self.assertEqual(self.codec.encode(0x8013, plain[19:83]), whole[19:83])

    def test_patch_addresses_are_exact(self):
        plain = b"\x00\x01\xfe\xff"
        patch = self.codec.encode_patch(0xF7FC, plain)
        self.assertEqual(set(patch), set(range(0xF7FC, 0xF800)))
        self.assertEqual(self.codec.decode(0xF7FC, bytes(patch.values())), plain)

    def test_first_word_tail_and_invalid_arguments_rejected(self):
        for address, data in [(0x4000,b"ab"), (0x4001,b"a"), (0xFFFF,b"ab"),
                              (0x10000,b"a"), (0x1F800,b"a"), (0x4002,b""),
                              (True,b"a"), (0x4002,"a")]:
            for operation in (self.codec.encode, self.codec.decode):
                with self.subTest(address=address, operation=operation.__name__):
                    with self.assertRaises(C.CodecError):
                        operation(address, data)

    def test_original_reconstruction_requires_full_pinned_transport(self):
        for data in [b"", bytes(C.END-C.BASE), b"\xff"*(C.END-C.BASE)]:
            with self.assertRaises(C.CodecError):
                self.codec.decode_original_bytes(data)
        with self.assertRaises(C.CodecError):
            self.codec.decode_original({0x4000: 0})


if __name__ == "__main__":
    unittest.main()
