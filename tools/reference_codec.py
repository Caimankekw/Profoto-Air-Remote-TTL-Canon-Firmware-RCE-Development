# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Offline, standard-library C11 byte transform. No USB or executable launch.

The reference table contains an address-indexed XOR byte and four bit-pair
swap controls, not device identity, a firmware image, or a device backup.
It is bounded to absolute MCU byte addresses [0x4002, 0x10000).
"""
from pathlib import Path
import hashlib
import json

BASE, END = 0x4000, 0x1FC00
ENCODABLE_START, ENCODABLE_END = 0x4002, 0x10000
TABLE_SIZE = 73725
TABLE_SHA256 = "7779d34181f9d302d2d122e9a2ed40f975a4128b738a40561f97fc86ac949303"
ORIGINAL_OPAQUE_SHA256 = "2fe896b4b23544e9bdde79a0266adac5162c13aeb3f64543ff18a347f5af75ee"
ORIGINAL_PLAIN_SHA256 = "7f2b7ef2625bacebafc526d0623ae91faa1f544e6062f2d4171635ed087f072a"
KNOWN_MASK_SHA256 = "81fe4da4f8a15728c97bc6de35fae71572d44f39a927dce22a9ca300b5d2558b"
REFERENCE_DIR = Path(__file__).resolve().parents[1] / "reference"


class CodecError(ValueError):
    pass


def swap_pairs(value, mask):
    """Swap bit n with n+4 when control bit n is set; an involution."""
    temporary = (value ^ (value >> 4)) & mask & 15
    return value ^ temporary ^ (temporary << 4)


class ReferenceCodec:
    def __init__(self, reference_dir=None):
        directory = Path(reference_dir) if reference_dir is not None else REFERENCE_DIR
        manifest = json.loads((directory / "codec_manifest.json").read_text(encoding="utf-8"))
        expected = {
            "format": "c11-offset-transform-v1",
            "file": "c11_offset_transform.bin",
            "start": ENCODABLE_START,
            "end_exclusive": ENCODABLE_END,
            "key_bytes": ENCODABLE_END - ENCODABLE_START,
            "packed_mask_bytes": (ENCODABLE_END - ENCODABLE_START) // 2,
            "packed_mask_order": "first-address-in-low-nibble",
            "size": TABLE_SIZE,
            "sha256": TABLE_SHA256,
        }
        for key, value in expected.items():
            if manifest.get(key) != value:
                raise CodecError("Reference manifest mismatch: " + key)
        raw = (directory / "c11_offset_transform.bin").read_bytes()
        if len(raw) != TABLE_SIZE or hashlib.sha256(raw).hexdigest() != TABLE_SHA256:
            raise CodecError("Reference transform fingerprint mismatch")
        count = ENCODABLE_END - ENCODABLE_START
        self._keys = raw[:count]
        packed = raw[count:]
        self._masks = bytes((packed[i // 2] >> (4 * (i & 1))) & 15 for i in range(count))
        self.encodable_range = (ENCODABLE_START, ENCODABLE_END)

    def _range(self, address, data):
        if type(address) is not int or not isinstance(data, (bytes, bytearray)) or not data:
            raise CodecError("Nonempty bytes and an integer absolute address are required")
        if not ENCODABLE_START <= address < address + len(data) <= ENCODABLE_END:
            raise CodecError("Requested interval is outside [0x4002, 0x10000)")
        return address - ENCODABLE_START

    def encode(self, address, plaintext):
        offset = self._range(address, plaintext)
        return bytes(swap_pairs(value, self._masks[i]) ^ self._keys[i]
                     for i, value in enumerate(plaintext, offset))

    def decode(self, address, opaque):
        offset = self._range(address, opaque)
        return bytes(swap_pairs(value ^ self._keys[i], self._masks[i])
                     for i, value in enumerate(opaque, offset))

    def encode_patch(self, address, plaintext):
        return {address + i: value for i, value in enumerate(self.encode(address, plaintext))}

    def decode_original_bytes(self, opaque):
        """Recover pinned C11 application and known mask, both based at 0x4000.

        This is intentionally NOT a decoder for an arbitrary full application.
        [0x4000,0x4002) remains unknown and is represented by zero placeholders.
        [0x10000,0x1FC00) is original C11 FF fill, admitted only after matching
        the entire original transport fingerprint. No tail transform is claimed.
        Actual output packaging must preserve original opaque bytes outside
        explicitly authored patches, including first word, tail and config.
        """
        if not isinstance(opaque, (bytes, bytearray)) or len(opaque) != END - BASE:
            raise CodecError("Expected the dense original [0x4000,0x1FC00) transport")
        if hashlib.sha256(opaque).hexdigest() != ORIGINAL_OPAQUE_SHA256:
            raise CodecError("Original C11 application transport fingerprint mismatch")
        plain = (b"\x00\x00" + self.decode(ENCODABLE_START, opaque[2:ENCODABLE_END - BASE])
                 + b"\xff" * (END - ENCODABLE_END))
        known = b"\x00\x00" + b"\x01" * (END - BASE - 2)
        if hashlib.sha256(plain).hexdigest() != ORIGINAL_PLAIN_SHA256:
            raise CodecError("Recovered original plaintext fingerprint mismatch")
        if hashlib.sha256(known).hexdigest() != KNOWN_MASK_SHA256:
            raise CodecError("Known-mask fingerprint mismatch")
        return plain, known

    def decode_original(self, memory):
        """Read an absolute-address -> opaque-byte mapping; never mutate it."""
        try:
            opaque = bytes(memory[address] for address in range(BASE, END))
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise CodecError("Original application transport is incomplete or invalid") from exc
        return self.decode_original_bytes(opaque)


# The alias eases migration from the prior workspace-only helper.
ExtendedReferenceCodec = ReferenceCodec
