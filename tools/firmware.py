# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Pure source-built HSS baseline and C11 header checksum, no device I/O."""
import hashlib
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE, END = 0x4000, 0x1FC00
ORIGINAL_SHA = '7f2b7ef2625bacebafc526d0623ae91faa1f544e6062f2d4171635ed087f072a'
MASK_SHA = '81fe4da4f8a15728c97bc6de35fae71572d44f39a927dce22a9ca300b5d2558b'
P1_SHA = 'eb3a3d4cf5ae0ef7dfd2c12e78440411958eab58d9ef05e27d34a4e2849cf4e9'
P3_SHA = '7cfbb93db7a8ddf3c2212e355bdd439f809669f78466250d6911e4129ca15fb9'
P3_EXE_SHA = '592d69581d8f3062ee814c4072652db672f0c66d7fa99c736a781b1df7435129'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def crc16_linear(data):
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xA001 if crc & 1 else 0)
    return crc


def crc_body(image):
    need(len(image) == END - BASE, 'Incorrect dense image size')
    return image[2:0x50] + image[0x52:0x100]


def apply_header_crc(image):
    result = bytearray(image)
    result[0x50:0x52] = (crc16_linear(crc_body(image)) ^ 0x0B15).to_bytes(2, 'little')
    return bytes(result)


def hss_build(original):
    need(sha(original) == ORIGINAL_SHA, 'Unsupported original plaintext')
    need(crc16_linear(b'123456789') == 0xBB3D, 'CRC standard vector failed')
    need(apply_header_crc(original) == original, 'Original C11 header CRC failed')
    hss = load('portable_hss_baseline', ROOT / 'source/hss_patch.py')
    asm, changes = hss.construct(original)
    need(asm.base == 0x9780 and asm.pc == 0x99C8, 'HSS layout changed')
    image = bytearray(original)
    touched, rows = set(), []
    for address, after, reason in changes:
        end = address + len(after)
        need(address % 2 == 0 and len(after) % 2 == 0 and 0x40A6 <= address < end <= 0x99C8,
             'HSS patch outside allowed allocation')
        span = set(range(address, end))
        need(not span.intersection(touched), 'Overlapping HSS changes')
        touched.update(span)
        before = original[address-BASE:end-BASE]
        if address >= 0x9780:
            need(before == b'\xff' * len(after), 'HSS code cave is not erased')
        image[address-BASE:end-BASE] = after
        rows.append({'address': address, 'end_exclusive': end, 'reason': reason,
                     'expected_before_hex': before.hex(), 'after_hex': after.hex()})
    need(sha(image) == P1_SHA, 'Source-built HSS-P1 differs from frozen expected image')
    return bytes(image), {'patches': rows, 'tail_range': [asm.base, asm.pc]}


def p1_manifest(original):
    return hss_build(original)[1]


def baseline_p3(original):
    p1, _ = hss_build(original)
    p3 = apply_header_crc(p1)
    need(sha(p3) == P3_SHA, 'Source-built HSS-P3 differs from frozen expected image')
    need(all(a == b for i, (a, b) in enumerate(zip(p1, p3)) if i not in (0x50, 0x51)),
         'HSS-P3 correction escaped the checksum field')
    return p3
