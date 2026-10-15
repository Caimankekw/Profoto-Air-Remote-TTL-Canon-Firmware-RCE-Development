# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Link the AIR2 PIC18 components onto pinned HSS-P3; offline only.

The partial binary is an analysis artifact, never a direct flash image. The
separate package helper preserves the original unknown encoded first word.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE, END, TAIL = 0x4000, 0x1FC00, 0x99C8
CODE_END = 0xF800
NVM_PAGES = ((0xF800, 0xFC00), (0xFC00, 0x10000))


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


def declarations(before, after):
    """Exact byte runs; CRC is independently declared by the packager."""
    addresses = [i for i, (a, b) in enumerate(zip(before, after))
                 if a != b and i not in (0x50, 0x51)]
    runs = []
    for offset in addresses:
        if runs and offset == runs[-1][1]:
            runs[-1][1] += 1
        else:
            runs.append([offset, offset + 1])
    return [{'address': BASE + start, 'before_hex': before[start:end].hex(),
             'after_hex': after[start:end].hex()} for start, end in runs]


def construct(original, mask):
    package = load('portable_firmware', ROOT / 'tools/firmware.py')
    need(sha(original) == package.ORIGINAL_SHA and sha(mask) == package.MASK_SHA,
         'Pinned original or mask changed')
    p3 = package.baseline_p3(original)
    p1_manifest = package.p1_manifest(original)
    preserved = [(p['address'], p['end_exclusive']) for p in p1_manifest['patches']]
    need(p1_manifest['tail_range'][1] == TAIL, 'P3 tail end changed')
    image = bytearray(p3)
    used, components, changes = set(), {}, []
    # Pass one fixes every component address. Cross-component calls use
    # fixed-width PIC18 CALL instructions, so symbol resolution cannot change
    # sizes. Require identical labels in pass two; no guessed link addresses.
    cursor, layouts, modules, symbols = TAIL, {}, {}, {}
    for name in ('ui', 'radio', 'persistence'):
        path = HERE / (name + '_patch.py')
        module = load('air2_p8_component_' + name, path)
        asm, _, metadata = module.construct(original, cursor, imports={})
        need(asm.base == cursor and cursor <= asm.pc <= CODE_END,
             'Component crosses reserved NVM pages')
        layouts[name] = (cursor, asm.pc, dict(asm.labels))
        modules[name] = module
        symbols.update({name + '_' + label: address for label, address in asm.labels.items()})
        # Radio public labels already include their component qualifier. Keep
        # the historical prefixed symbols and expose the declared ABI names.
        for label, address in asm.labels.items():
            if label.startswith(name + '_'):
                need(label not in symbols or symbols[label] == address,
                     'Conflicting qualified public symbol: ' + label)
                symbols[label] = address
        cursor = asm.pc
    cursor = TAIL
    for name in ('ui', 'radio', 'persistence'):
        path = HERE / (name + '_patch.py')
        asm, patch_list, metadata = modules[name].construct(original, cursor, imports=symbols)
        need((asm.base, asm.pc, dict(asm.labels)) == layouts[name],
             'Linking changed component layout: ' + name)
        need(asm.base == cursor and cursor <= asm.pc <= CODE_END, 'Component tail outside code allocation')
        need(not metadata.get('unresolved_imports'),
             'Unresolved imports in final component: ' + name)
        for imported, address in metadata.get('imports', {}).items():
            need(symbols.get(imported) == address,
                 'Incorrect linked import: ' + name + '/' + imported)
        need(asm.pc % 2 == 0, 'Unaligned tail end')
        for address, after, reason in patch_list:
            stop = address + len(after)
            need(address % 2 == 0 and len(after) % 2 == 0, 'Unaligned code patch')
            need(0x40A6 <= address < stop <= CODE_END, 'Patch outside known code allocation')
            need(not any(address < hi and stop > lo for lo, hi in preserved),
                 'AIR2 patch overlaps protected P3 HSS bytes')
            span = set(range(address, stop))
            need(not used.intersection(span), 'Overlapping AIR2 patches')
            used.update(span)
            start = address - BASE
            need(all(mask[start:start+len(after)]), 'Patch includes unknown bytes')
            before = p3[start:start+len(after)]
            if address >= TAIL:
                need(before == b'\xff' * len(after), 'Code cave is not empty')
            image[start:start+len(after)] = after
            changes.append({'component': name, 'address': address,
                            'end_exclusive': stop, 'reason': reason,
                            'before_hex': before.hex(), 'after_hex': after.hex()})
        components[name] = {'base': asm.base, 'end_exclusive': asm.pc,
                            'labels': asm.labels, 'metadata': metadata,
                            'source_sha256': sha(path.read_bytes())}
        cursor = asm.pc
    image = package.apply_header_crc(bytes(image))
    for lo, hi in preserved:
        need(image[lo-BASE:hi-BASE] == p3[lo-BASE:hi-BASE], 'P3 HSS patch changed')
    need(image[:0x50] == p3[:0x50] and image[0x52:0xA6] == p3[0x52:0xA6]
         and image[0xC000:] == p3[0xC000:], 'Protected image region changed')
    need(image[0xB800:0xC000] == b'\xff' * 0x800,
         'Install image must leave both runtime settings pages erased')
    manifest = {
        'format': 'c11-air2-target-v1', 'developer': 'Caimankekw',
        'authored_source_license': 'AGPL-3.0-only',
        'license_scope': 'Authored patch/build sources only; vendor firmware and updater bytes retain their original rights and are not relicensed by this manifest.',
        'name': 'AIR2-P8',
        'status': 'SOURCE_REBUILT_EXPECTED_ARTIFACT', 'base_address': BASE,
        'image_end_exclusive': END, 'original_plaintext_sha256': package.ORIGINAL_SHA,
        'p3_plaintext_sha256': package.P3_SHA, 'p3_exe_sha256': package.P3_EXE_SHA,
        'known_mask_sha256': package.MASK_SHA, 'plaintext_sha256': sha(image),
        'relative_to_original': declarations(original, image),
        'relative_to_p3': declarations(p3, image), 'component_patches': changes,
        'components': components, 'tail_range': [TAIL, cursor],
        'linked_symbols': symbols, 'code_end_exclusive': CODE_END,
        'runtime_nvm_pages': [list(span) for span in NVM_PAGES],
        'original_settings_journal_unchanged': True,
        'header_crc_le16': int.from_bytes(image[0x50:0x52], 'little'),
        'p3_hss_patch_intervals_preserved': preserved,
        'device_accessed': False, 'hardware_boot_verified': False,
        'radio_absolute_power_verified_on_device': False,
        'scope': 'C+HEAD paging and C+MODEL manual subtype switching with only secondary keys deferred; A/B/plus/minus bypass the chord window; six-group UI, V4 persistence and HSS-P3 retained',
        'radio_scope': 'TTL uses ABC FEC and DEF manual control according to the remembered Air1/Air2 subtype; no claim of six-group automatic TTL metering or verified RF transport',
        'runtime_contract': {
            'a2_targets': [0x200, 0x201, 0x202, 0x260, 0x261, 0x262],
            'canonical_head_mask': 0x26F, 'canonical_model_mask': 0x270,
            'display_page': 0x271, 'all_scope': 'A-F regardless of display page',
            'page_gesture': 'C plus HEAD with deferred secondary-key commit; one toggle until all keys released',
            'manual_gesture': 'C plus MODEL in MAN; swallowed without mode change in TTL',
            'non_pending_keys': ['A', 'B', 'minus', 'plus'],
            'pending_key_state': [0x2C0, 0x2D0],
            'chord_window_native_fine_counts': 200,
            'chord_stability_native_fine_counts': 10,
            'chord_window_is_not_verified_milliseconds': True,
            'air1_relative_visible_mask': 0x266,
            'air1_display': 'temporary; blank on entry and native idle expiry',
            'air2_display': 'persistent absolute targets for enabled groups',
            'ttl_def': 'manual by remembered AIR1/AIR2 subtype',
            'ttl_all': 'ABC FEC plus DEF manual; project extension',
            'ttl_a2_frame': 'full six-target cmd11 also refreshes ABC manual target cache',
            'nvm_record_buffer': [0x340, 0x360], 'nvm_context': [0x330, 0x340],
        },
        'first_two_plaintext_bytes_unknown': True,
        'builder_sha256': sha(Path(__file__).read_bytes()),
    }
    return image, mask, manifest

