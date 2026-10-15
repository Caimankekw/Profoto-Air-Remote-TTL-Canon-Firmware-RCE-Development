# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Portable input/parser tests. These never emulate native signing success."""
import copy
import io
import json
from pathlib import Path
import stat
import struct
import tempfile
import unittest
import zipfile

import build_package as b


def record(address, kind, body=b''):
    raw = bytes([len(body)]) + address.to_bytes(2, 'big') + bytes([kind]) + body
    return ':' + (raw + bytes([-sum(raw) & 255])).hex().upper()


def hex_fixture():
    return (record(0, 4, b'\x00\x00') + '\r\n' + record(0x4000, 0, b'\x00\x00\x12\x34') +
            '\r\n' + record(0, 1) + '\r\n').encode('ascii')


def profile_fixture():
    zero = '0' * 64
    return {'schema': b.FORMAT, 'model': 'N', 'brand': 'Nikon', 'version': 'AIR2-P8-M2',
            'stock_revision': 'C5', 'release_repository': 'Caimankekw/Test', 'release_tag': 'test-mac',
            'output_slug': 'AirRemote-N-Mac', 'volume_name': 'AIR2 N Caimankekw', 'source_prefix': 'Source',
            'original': {'asset': 'stock.zip', 'size': 100, 'sha256': zero,
                         'dmg_member': 'stock.dmg', 'dmg_sha256': zero,
                         'faq_member': 'FAQ.pdf', 'faq_sha256': zero,
                         'notice_member': 'license.txt', 'notice_sha256': zero,
                         'app_path': 'Stock.app', 'main_path': 'Contents/MacOS/Stock', 'main_sha256': zero,
                         'helper_path': 'Contents/Resources/Helper', 'helper_sha256': zero,
                         'firmware_path': 'Contents/Resources/RMRTN_firmware.hex', 'firmware_sha256': zero},
            'windows': {'asset': 'windows.zip', 'size': 100, 'sha256': zero,
                        'updater_member': 'Portable/custom.exe', 'updater_sha256': zero,
                        'hex_start': 16, 'hex_end': 100, 'custom_hex_sha256': zero},
            'expected_firmware_sha256': zero}


def macho_fixture(signature=b'S' * 32, code=b'CODE'):
    header = struct.pack('<IIIIIIII', 0xfeedfacf, 0x1000007, 3, 2, 2, 88, 0, 0)
    offset = 160
    segment = struct.pack('<II16sQQQQIIII', 0x19, 72, b'__LINKEDIT\0\0\0\0\0\0',
                          0x1000, len(signature), offset, len(signature), 7, 1, 0, 0)
    signature_command = struct.pack('<IIII', 0x1d, 16, offset, len(signature))
    payload = header + segment + signature_command + code
    return payload.ljust(offset, b'\0') + signature


class InputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Retained intentionally: the publication workflow never deletes files.
        cls.work = Path(tempfile.mkdtemp(prefix='airremote-mac-tests-'))

    def test_valid_profile(self):
        self.assertEqual(b.validate_profile(profile_fixture())['model'], 'N')

    def test_wrong_model_resource_rejected(self):
        p = profile_fixture()
        p['model'] = 'S'
        with self.assertRaisesRegex(ValueError, 'Model and firmware'):
            b.validate_profile(p)

    def test_wrong_model_version_rejected(self):
        p = profile_fixture()
        p['model'] = 'C'
        with self.assertRaisesRegex(ValueError, 'version'):
            b.validate_profile(p)

    def test_unsafe_paths(self):
        for value in ('../x', '/x', 'a//b', 'a/./b', 'a\\b', 'C:x', 'x\ny', 'x/'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                b.safe_path(value)

    def test_duplicate_json_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            b.parse_json(b'{"model":"N","model":"C"}')

    def test_case_colliding_zip_rejected(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('A.txt', b'a')
            archive.writestr('a.txt', b'a')
        with zipfile.ZipFile(io.BytesIO(data.getvalue())) as archive:
            with self.assertRaisesRegex(ValueError, 'case-colliding'):
                b.zip_inventory(archive)

    def test_symlink_zip_rejected(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            entry = zipfile.ZipInfo('link')
            entry.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(entry, b'../../outside')
        with zipfile.ZipFile(io.BytesIO(data.getvalue())) as archive:
            with self.assertRaisesRegex(ValueError, 'Non-regular'):
                b.zip_inventory(archive)

    def test_intel_hex_checksum_and_addresses(self):
        self.assertEqual(b.parse_hex(hex_fixture()), {0x4000: 0, 0x4001: 0, 0x4002: 0x12, 0x4003: 0x34})

    def test_intel_hex_corruption(self):
        with self.assertRaises(ValueError):
            b.parse_hex(hex_fixture().replace(b'1234', b'1235'))

    def test_intel_hex_duplicate_address_rejected(self):
        text = record(0x4000, 0, b'\1') + '\n' + record(0x4000, 0, b'\2') + '\n' + record(0, 1)
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            b.parse_hex(text.encode())

    def test_intel_hex_extra_data_after_eof_rejected(self):
        with self.assertRaisesRegex(ValueError, 'after-EOF'):
            b.parse_hex(hex_fixture() + (record(0x4000, 0, b'\1') + '\n').encode())

    def test_extract_exact_pinned_windows_hex(self):
        p = profile_fixture()
        text = hex_fixture()
        exe = b'MZ' + b'\0' * 14 + text + b'END'
        package = self.work / 'fixture-portable.zip'
        if not package.exists():
            with zipfile.ZipFile(package, 'w') as archive:
                archive.writestr('Portable/custom.exe', exe)
        p['windows'].update(b.fingerprint(package))
        p['windows'].update(updater_sha256=b.sha(exe), hex_end=16 + len(text), custom_hex_sha256=b.sha(text))
        self.assertEqual(b.extract_hex(package, p), text)
        for key in ('sha256', 'updater_sha256', 'custom_hex_sha256'):
            bad = copy.deepcopy(p)
            bad['windows'][key] = '0' * 64
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'mismatch'):
                b.extract_hex(package, bad)

    def test_macho_signature_resize_allowed(self):
        self.assertEqual(b.macho_signature_independent(macho_fixture()),
                         b.macho_signature_independent(macho_fixture(b'NEW SIGNATURE' * 15)))

    def test_macho_code_modification_detected(self):
        self.assertNotEqual(b.macho_signature_independent(macho_fixture()),
                            b.macho_signature_independent(macho_fixture(code=b'EVIL')))

    def test_macho_load_command_modification_detected(self):
        changed = bytearray(macho_fixture())
        struct.pack_into('<I', changed, 24, 0x200000)
        self.assertNotEqual(b.macho_signature_independent(macho_fixture()), b.macho_signature_independent(bytes(changed)))

    def test_macho_appended_payload_rejected(self):
        with self.assertRaisesRegex(ValueError, 'after code signature'):
            b.macho_signature_independent(macho_fixture() + b'UNEXPECTED')

    def test_bundle_comparison_preserves_helper_and_plist(self):
        p = profile_fixture()
        main, firmware, helper = [p['original'][k + '_path'] for k in ('main', 'firmware', 'helper')]
        before = {main: {'sha256': 'old', 'mode': 0o755}, firmware: {'sha256': 'stock', 'mode': 0o644},
                  helper: {'sha256': 'helper', 'mode': 0o755}, 'Contents/Info.plist': {'sha256': 'plist', 'mode': 0o644}}
        after = copy.deepcopy(before)
        after[firmware]['sha256'] = p['windows']['custom_hex_sha256']
        after[main]['sha256'] = 'new-signed'
        after['Contents/_CodeSignature/CodeResources'] = {'sha256': 'new'}
        b.compare_bundle(before, after, p, macho_fixture(), macho_fixture(b'NEW' * 20))
        after[helper]['sha256'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'resource/helper'):
            b.compare_bundle(before, after, p, macho_fixture(), macho_fixture())

    def test_readme_declares_signature_and_hardware_limits(self):
        text = b.readme(profile_fixture())
        self.assertIn('ad-hoc', text)
        self.assertIn('full ZIP', text)
        self.assertIn('not tested', text)


if __name__ == '__main__':
    unittest.main()
