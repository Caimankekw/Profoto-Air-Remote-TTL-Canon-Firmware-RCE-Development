# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
#!/usr/bin/env python3
"""Bounded offline PIC18 standard instruction candidate listings (Python 3.9+).

Byte addresses, little-endian words; no execution, USB, or external dependencies.
Numeric file operands deliberately avoid assuming a particular MCU/SFR map.
This is a linear decoder, not a code/data classifier or a C decompiler.
"""
from dataclasses import dataclass

BASE = 0x4000
CODE_START, CODE_END = 0x40A6, 0x9780
PC_MASK = 0x1FFFFF

# Masks and fields cross-checked against the adjacent Ghidra reference .sinc.
FILE_DA = {
    0x0400: "DECF", 0x1000: "IORWF", 0x1400: "ANDWF", 0x1800: "XORWF",
    0x1C00: "COMF", 0x2000: "ADDWFC", 0x2400: "ADDWF", 0x2800: "INCF",
    0x2C00: "DECFSZ", 0x3000: "RRCF", 0x3400: "RLCF", 0x3800: "SWAPF",
    0x3C00: "INCFSZ", 0x4000: "RRNCF", 0x4400: "RLNCF", 0x4800: "INFSNZ",
    0x4C00: "DCFSNZ", 0x5000: "MOVF", 0x5400: "SUBFWB", 0x5800: "SUBWFB",
    0x5C00: "SUBWF",
}
FILE_A = {
    0x0200: "MULWF", 0x6000: "CPFSLT", 0x6200: "CPFSEQ", 0x6400: "CPFSGT",
    0x6600: "TSTFSZ", 0x6800: "SETF", 0x6A00: "CLRF", 0x6C00: "NEGF",
    0x6E00: "MOVWF",
}
LITERAL = {0x0800: "SUBLW", 0x0900: "IORLW", 0x0A00: "XORLW", 0x0B00: "ANDLW",
           0x0C00: "RETLW", 0x0D00: "MULLW", 0x0E00: "MOVLW", 0x0F00: "ADDLW"}
BIT = {0x7000: "BTG", 0x8000: "BSF", 0x9000: "BCF", 0xA000: "BTFSS", 0xB000: "BTFSC"}
BRANCH = {0xE000: "BZ", 0xE100: "BNZ", 0xE200: "BC", 0xE300: "BNC",
          0xE400: "BOV", 0xE500: "BNOV", 0xE600: "BN", 0xE700: "BNN"}
FIXED = {
    0x0000: "NOP", 0x0003: "SLEEP", 0x0004: "CLRWDT", 0x0005: "PUSH",
    0x0006: "POP", 0x0007: "DAW", 0x0008: "TBLRD*", 0x0009: "TBLRD*+",
    0x000A: "TBLRD*-", 0x000B: "TBLRD+*", 0x000C: "TBLWT*",
    0x000D: "TBLWT*+", 0x000E: "TBLWT*-", 0x000F: "TBLWT+*", 0x00FF: "RESET",
}
SKIPS = {"CPFSLT", "CPFSEQ", "CPFSGT", "TSTFSZ", "DECFSZ", "INCFSZ",
         "DCFSNZ", "INFSNZ", "BTFSS", "BTFSC"}


@dataclass
class Row:
    address: int
    length: int
    raw: str
    kind: str
    mnemonic: str
    operands: str = ""
    target: object = None
    note: str = ""


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def long_prefix(word):
    return ((word & 0xF000) == 0xC000 or (word & 0xFE00) == 0xEC00
            or (word & 0xFF00) == 0xEF00 or (word & 0xFFC0) == 0xEE00)


def decode(data, mask, address, base=BASE, end=None):
    """Decode one bounded candidate. Every nonzero mask byte means known.

    Malformed double-word prefixes consume only their first word so no bytes
    are silently hidden. Unknown/truncated continuation is marked incomplete.
    Standalone Fxxx is ambiguous (continuation/NOP/data), never asserted code.
    """
    if len(data) != len(mask):
        raise ValueError("image/mask lengths differ")
    end = min(base + len(data), end if end is not None else base + len(data))
    if address < base or address >= end or address % 2:
        raise ValueError("address must be aligned and inside the bounded image")
    i = address - base

    def row(length, kind, mnemonic, operands="", target=None, note=""):
        raw = " ".join(f"{data[j]:02X}" if mask[j] else "??"
                       for j in range(i, i + length))
        return Row(address, length, raw, kind, mnemonic, operands, target, note)

    remaining = end - address
    if remaining < 2:
        return row(remaining, "TRUNCATED", ".BYTE", note="incomplete word at region boundary")
    if not all(mask[i:i + 2]):
        return row(2, "UNKNOWN", ".UNKNOWN", note="mask marks unrecovered byte(s); placeholder bytes are not instructions")
    word = int.from_bytes(data[i:i + 2], "little")
    if word == 0xFFFF:
        return row(2, "FILL_FFFF", ".FILL", "0xFFFF", note="fill candidate; not treated as an executable NOP")

    if long_prefix(word):
        if remaining < 4:
            return row(remaining, "INCOMPLETE_DWORD", ".INCOMPLETE", note="double-word prefix crosses region boundary")
        if not all(mask[i + 2:i + 4]):
            return row(4, "INCOMPLETE_DWORD", ".INCOMPLETE", note="double-word continuation has unknown bytes")
        second = int.from_bytes(data[i + 2:i + 4], "little")
        is_lfsr = (word & 0xFFC0) == 0xEE00
        valid = ((second & 0xFF00) == 0xF000 if is_lfsr else (second & 0xF000) == 0xF000)
        if not valid or (is_lfsr and ((word >> 4) & 3) == 3):
            return row(2, "INVALID_DWORD", ".WORD", f"0x{word:04X}",
                       note="invalid continuation bits or reserved LFSR selector; next word retained separately")
        if (word & 0xF000) == 0xC000:
            return row(4, "CANDIDATE", "MOVFF", f"0x{word & 0xFFF:03X}, 0x{second & 0xFFF:03X}")
        if is_lfsr:
            return row(4, "CANDIDATE", "LFSR", f"FSR{(word >> 4) & 3}, 0x{((word & 15) << 8) | (second & 255):03X}")
        target = (((second & 0xFFF) << 8) | (word & 255)) << 1
        mnemonic = "GOTO" if word & 0xFF00 == 0xEF00 else "CALL"
        operands = f"0x{target:06X}" + (f", {(word >> 8) & 1}" if mnemonic == "CALL" else "")
        return row(4, "CANDIDATE", mnemonic, operands, target,
                   "absolute byte target = 2 * ((second[11:0] << 8) | first[7:0])")

    if (word & 0xF000) == 0xF000:
        return row(2, "CONTINUATION_OR_NOP", ".WORD", f"0x{word:04X}",
                   note="standalone Fxxx: continuation, architectural NOP, or data; XINST also unconfirmed")
    if word in FIXED:
        return row(2, "CANDIDATE", FIXED[word])
    if word in (0x0010, 0x0011, 0x0012, 0x0013):
        return row(2, "CANDIDATE", "RETFIE" if word < 0x0012 else "RETURN", str(word & 1))
    if word & 0xFF00 == 0x0100:
        if word & 0xF0:
            return row(2, "DEVICE_DEPENDENT_ENCODING", ".WORD", f"0x{word:04X}",
                       note="MOVLB k8 in supplied reference, outside classic 4-bit bank profile; exact MCU unconfirmed")
        return row(2, "CANDIDATE", "MOVLB", f"0x{word & 15:02X}")
    if word & 0xFF00 in LITERAL:
        return row(2, "CANDIDATE", LITERAL[word & 0xFF00], f"0x{word & 255:02X}")
    if word & 0xF800 in (0xD000, 0xD800) or word & 0xFF00 in BRANCH:
        wide = (word & 0xF800) in (0xD000, 0xD800)
        bits = 11 if wide else 8
        displacement = signed(word & ((1 << bits) - 1), bits)
        target = (address + 2 + 2 * displacement) & PC_MASK
        mnemonic = ("BRA" if (word & 0xF800) == 0xD000 else "RCALL") if wide else BRANCH[word & 0xFF00]
        return row(2, "CANDIDATE", mnemonic, f"0x{target:06X}", target,
                   f"relative {displacement:+d} words ({2 * displacement:+d} bytes), from PC+2")
    access = "BANKED" if word & 0x100 else "ACCESS"
    f = f"0x{word & 255:02X}"
    mnemonic, operands = None, ""
    if word & 0xF000 in BIT:
        mnemonic = BIT[word & 0xF000]
        operands = f"{f}, {(word >> 9) & 7}, {access}"
    elif word & 0xFC00 in FILE_DA:
        mnemonic = FILE_DA[word & 0xFC00]
        operands = f"{f}, {'F' if word & 0x200 else 'W'}, {access}"
    elif word & 0xFE00 in FILE_A:
        mnemonic = FILE_A[word & 0xFE00]
        operands = f"{f}, {access}"
    if mnemonic:
        note = ""
        if mnemonic in SKIPS:
            note = "conditional skip of following instruction; not a relative branch"
            if address + 4 <= end and all(mask[i + 2:i + 4]):
                next_word = int.from_bytes(data[i + 2:i + 4], "little")
                note += f"; next prefix implies skip resume 0x{address + (6 if long_prefix(next_word) else 4):06X}"
        return row(2, "CANDIDATE", mnemonic, operands, note=note)
    return row(2, "UNRECOGNIZED_STANDARD", ".WORD", f"0x{word:04X}",
               note="not decoded by standard-set rules; reserved, extended instruction, or data")


def listing(data, mask, start, end, base=BASE, data_regions=()):
    rows = []
    while start < end:
        data_region = next((region for region in data_regions if region[0] <= start < region[1]), None)
        next_boundary = min([end] + [region[0] for region in data_regions if region[0] > start])
        if data_region:
            length = min(2, data_region[1] - start, end - start)
            i = start - base
            raw = " ".join(f"{data[j]:02X}" if mask[j] else "??" for j in range(i, i + length))
            result = Row(start, length, raw, "DATA", ".BYTE", note=data_region[2])
        else:
            result = decode(data, mask, start, base, next_boundary)
        rows.append(result)
        start += result.length
    return rows


def format_row(row):
    text = f"{row.address:06X}  {row.length:1d}  {row.raw:<11}  {row.kind:<22} {row.mnemonic:<12} {row.operands}"
    return text.rstrip() + (" ; " + row.note if row.note else "")


def data_rows(data, mask, start, end, base=BASE):
    """Header bytes are deliberately listed as data, even if an opcode matches."""
    result = []
    for address in range(start, end, 8):
        i, length = address - base, min(8, end - address)
        raw = " ".join(f"{data[j]:02X}" if mask[j] else "??" for j in range(i, i + length))
        chars = "".join(chr(data[j]) if mask[j] and 32 <= data[j] < 127 else "." for j in range(i, i + length))
        result.append(f"{address:06X}  {length}  {raw:<23} DATA                   .BYTE ; {chars}")
    return result

