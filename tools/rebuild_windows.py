# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Reproduce a pinned experimental Windows updater without USB or execution.

The recipe contains same-length edits to the embedded transport HEX resource.
It does not contain a device backup or the manufacturer's original executable.
Python 3.9+, standard library only. No subprocesses, networking or device I/O.
"""
import argparse
import hashlib
import json
from pathlib import Path


class BuildError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise BuildError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate_hex(data):
    """Check the complete transport HEX, including layout and overlapping data."""
    upper, ended, records = 0, False, 0
    occupied = set()
    for line in data.splitlines():
        require(not ended, 'Unexpected content after HEX EOF')
        require(line.startswith(b':'), 'Invalid HEX record prefix')
        try:
            raw = bytes.fromhex(line[1:].decode('ascii'))
        except (ValueError, UnicodeError) as exc:
            raise BuildError('Invalid HEX encoding') from exc
        require(len(raw) >= 5 and len(raw) == raw[0] + 5, 'Invalid HEX length')
        require(sum(raw) % 256 == 0, 'Invalid HEX line checksum')
        n, address, kind = raw[0], int.from_bytes(raw[1:3], 'big'), raw[3]
        if kind == 0:
            require(address + n <= 0x10000, 'HEX data crosses address segment')
            span = set(range(upper + address, upper + address + n))
            require(not occupied.intersection(span), 'Overlapping HEX data')
            occupied.update(span)
        elif kind in (2, 4):
            require(n == 2 and address == 0, 'Invalid extended address')
            upper = int.from_bytes(raw[4:6], 'big') << (4 if kind == 2 else 16)
        elif kind == 1:
            require(n == 0 and address == 0, 'Invalid EOF')
            ended = True
        else:
            raise BuildError('Unsupported HEX record type')
        records += 1
    require(ended and occupied, 'Missing EOF or firmware data')
    return records


def rebuild(original, recipe):
    require(recipe.get('format') == 'c11-windows-reproduction-v1', 'Unknown recipe format')
    require(len(original) == recipe['original_size'], 'Original executable size mismatch')
    require(digest(original) == recipe['original_sha256'], 'Original executable fingerprint mismatch')
    start, end = recipe['hex_resource_range']
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(original),
            'Invalid embedded HEX bounds')
    require(digest(original[start:end]) == recipe['original_hex_sha256'], 'Original HEX mismatch')
    validate_hex(original[start:end])
    result = bytearray(original)
    previous_end, total = start, 0
    require(bool(recipe['edits']), 'No-op recipe is not custom firmware')
    for edit in recipe['edits']:
        offset = edit['offset']
        before, after = bytes.fromhex(edit['before']), bytes.fromhex(edit['after'])
        require(type(offset) is int and bool(before) and len(before) == len(after), 'Invalid edit')
        require(previous_end <= offset < offset + len(before) <= end,
                'Edit overlaps, is unordered, or lies outside the firmware resource')
        require(before != after and original[offset:offset + len(before)] == before,
                'Expected bytes mismatch or no-op edit')
        result[offset:offset + len(before)] = after
        previous_end = offset + len(before)
        total += len(before)
    result = bytes(result)
    require(result[:start] == original[:start] and result[end:] == original[end:],
            'Unexpected executable code or resource metadata edit')
    require(digest(result) == recipe['result_sha256'], 'Rebuilt executable fingerprint mismatch')
    require(digest(result[start:end]) == recipe['result_hex_sha256'], 'Rebuilt HEX fingerprint mismatch')
    records = validate_hex(result[start:end])
    return result, {'status': 'PASS', 'sha256': digest(result), 'changed_span_bytes': total,
                    'hex_records': records, 'device_accessed': False,
                    'device_write_or_boot_verified': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original', type=Path, required=True)
    p.add_argument('--recipe', type=Path, required=True)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--out', type=Path)
    mode.add_argument('--verify-only', action='store_true')
    a = p.parse_args()
    recipe = json.loads(a.recipe.read_text(encoding='utf-8'))
    result, report = rebuild(a.original.read_bytes(), recipe)
    if a.out:
        with a.out.open('xb') as handle:
            handle.write(result)
        report['output'] = str(a.out.resolve())
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
