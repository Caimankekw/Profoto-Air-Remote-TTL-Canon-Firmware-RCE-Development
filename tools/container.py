# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Pinned C11 Windows container and strict Intel HEX editing, stdlib only.

Adapted from the project's authored c11_container_roundtrip.py. The original
updater is read as data and never executed. Fixed resource coordinates are
valid only for the fingerprint below. Neither this parser nor a successful
roundtrip establishes device acceptance, bootability, or vendor endorsement.
"""
from dataclasses import dataclass
import hashlib
import json
import re


SOURCE_SHA256 = "e56b19080bd6330a5461dd4e3d614fc6d81dcc533e945e6090e7db63824bc240"
SOURCE_SIZE = 3938448
HEX_START = 2125444
HEX_END = 2438152
HEX_SHA256 = "fc61cbd275e075acab29e6df356ed0b05f731901e3ab16f303f920b237dc451e"
LAYOUT_SHA256 = "59e18b8641506461cfe137ab5103cf7e1fa5c6b2c9a706b365117a94740a71bb"
OUTSIDE_SHA256 = "d266f0e3561bcf9651b3eae60144e88fbf95f31123b737df9d45bcb3dd20e0d3"
SPANS = [(0x4000, 0x1FC10), (0x1FFF0, 0x20000)]


class RepackError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise RepackError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Record:
    index: int
    offset: int
    original: bytes
    ending: bytes
    raw: bytes
    kind: int
    address: int
    absolute: object

    @property
    def count(self):
        return self.raw[0]

    @property
    def payload(self):
        return self.raw[4:-1]


class HexImage:
    """Retain sparse addresses, record order, spelling and line endings."""

    def __init__(self, text):
        require(isinstance(text, bytes), "HEX input must be bytes")
        require(bool(text), "Empty HEX")
        self.text = text
        self.records = []
        self.memory = {}
        upper, offset, eof = 0, 0, False
        for number, line in enumerate(text.splitlines(keepends=True), 1):
            require(not eof, "Record or extra line after EOF")
            ending = b"\r\n" if line.endswith(b"\r\n") else b"\n" if line.endswith(b"\n") else b""
            content = line[:-len(ending)] if ending else line
            require(re.fullmatch(rb":[0-9a-fA-F]+", content) is not None,
                    "Invalid HEX spelling at line %d" % number)
            require((len(content) - 1) % 2 == 0, "Odd HEX digit count")
            raw = bytes.fromhex(content[1:].decode("ascii"))
            require(len(raw) >= 5 and len(raw) == raw[0] + 5, "Wrong HEX byte count")
            require(sum(raw) % 256 == 0, "Bad HEX checksum at line %d" % number)
            count, address, kind = raw[0], int.from_bytes(raw[1:3], "big"), raw[3]
            payload, absolute = raw[4:-1], None
            if kind == 0:
                require(address + count <= 0x10000, "Data record crosses 64 KiB boundary")
                absolute = upper + address
                for i, value in enumerate(payload):
                    require(absolute + i not in self.memory, "Overlapping HEX address")
                    self.memory[absolute + i] = value
            elif kind in (2, 4):
                require(count == 2 and address == 0, "Invalid extended-address record")
                upper = int.from_bytes(payload, "big") << (4 if kind == 2 else 16)
            elif kind == 1:
                require(count == 0 and address == 0, "Invalid EOF record")
                eof = True
            else:
                raise RepackError("Unsupported HEX type %d; not silently discarded" % kind)
            self.records.append(Record(number, offset, line, ending, raw, kind, address, absolute))
            offset += len(line)
        require(eof, "Missing EOF")
        require(bool(self.memory), "HEX contains no data")

    def layout(self):
        return [(r.kind, r.address, r.count, r.absolute, r.ending,
                 r.payload if r.kind != 0 else None) for r in self.records]

    def layout_sha256(self):
        rows = [[r.kind, r.address, r.count, r.absolute, r.ending.hex(),
                 r.payload.hex() if r.kind else None] for r in self.records]
        return sha(json.dumps(rows, separators=(",", ":")).encode("ascii"))

    def spans(self):
        ordered = sorted(self.memory)
        start = last = ordered[0]
        result = []
        for address in ordered[1:]:
            if address != last + 1:
                result.append((start, last + 1))
                start = address
            last = address
        result.append((start, last + 1))
        return result

    def replace_opaque_bytes(self, replacements):
        """Replace existing transport bytes without filling gaps or reordering."""
        for address, value in replacements.items():
            require(type(address) is int and address in self.memory,
                    "Patch address is absent, in a gap or outside original HEX")
            require(type(value) is int and 0 <= value <= 255, "Patch value is not a byte")
        lines = []
        for record in self.records:
            raw = bytearray(record.raw)
            line = bytearray(record.original)
            changed = False
            if record.kind == 0:
                for i in range(record.count):
                    address = record.absolute + i
                    if address in replacements and replacements[address] != raw[4 + i]:
                        raw[4 + i] = replacements[address]
                        pos = 1 + 2 * (4 + i)
                        line[pos:pos + 2] = ("%02X" % raw[4 + i]).encode("ascii")
                        changed = True
            if changed:
                raw[-1] = (-sum(raw[:-1])) & 255
                pos = 1 + 2 * (len(raw) - 1)
                line[pos:pos + 2] = ("%02X" % raw[-1]).encode("ascii")
            lines.append(bytes(line))
        result = HexImage(b"".join(lines))
        require(result.layout() == self.layout(), "Internal error: changed HEX layout")
        require(len(result.text) == len(self.text), "Internal error: changed HEX size")
        expected = dict(self.memory)
        expected.update(replacements)
        require(result.memory == expected, "Internal error: replacement changed other bytes")
        return result


class Container:
    """Access the one pinned resource; never search an arbitrary executable.

    require_vendor_pin=False is for checking a patched result. It still requires
    the original file size, every byte outside the HEX resource (by SHA-256),
    and the complete original HEX address/record/line-ending layout.
    """

    def __init__(self, outer, require_vendor_pin=True):
        require(isinstance(outer, bytes), "Container input must be bytes")
        require(len(outer) == SOURCE_SIZE, "C11 executable size mismatch")
        if require_vendor_pin:
            require(sha(outer) == SOURCE_SHA256, "Source is not pinned original C11 EXE")
        self.outer = outer
        self.start, self.end = HEX_START, HEX_END
        self.hex_size = self.end - self.start
        require(sha(outer[:self.start] + outer[self.end:]) == OUTSIDE_SHA256,
                "Executable bytes outside the firmware resource changed")
        self.hex_bytes = outer[self.start:self.end]
        if require_vendor_pin:
            require(sha(self.hex_bytes) == HEX_SHA256, "Original HEX fingerprint mismatch")
        self.hex = HexImage(self.hex_bytes)
        require(self.hex.layout_sha256() == LAYOUT_SHA256, "C11 HEX layout mismatch")
        require(self.hex.spans() == SPANS, "C11 HEX sparse address spans mismatch")

    def replace_hex(self, replacement):
        require(isinstance(replacement, HexImage), "Replacement must be validated HexImage")
        require(len(replacement.text) == self.hex_size, "HEX resource size change refused")
        require(replacement.layout() == self.hex.layout(), "HEX layout/address/EOL change refused")
        result = self.outer[:self.start] + replacement.text + self.outer[self.end:]
        require(len(result) == len(self.outer), "Container size change refused")
        require(result[:self.start] == self.outer[:self.start] and result[self.end:] == self.outer[self.end:],
                "Unexpected edit outside the firmware resource")
        parsed = Container(result, require_vendor_pin=False)
        require(parsed.hex_bytes == replacement.text, "Re-extraction mismatch")
        return result

    # Compatibility with the original authored parser's method name.
    replace_opaque_hex_in_memory = replace_hex
