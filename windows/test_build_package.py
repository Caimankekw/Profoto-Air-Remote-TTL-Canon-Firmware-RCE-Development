# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""In-memory boundary tests; no output files, compilers, installers or USB."""
import io
import json
import struct
import unittest
import warnings
import zipfile
import build_package as p


def zip_fixture(files=None, manifest_change=None, extra=None):
    files = dict(files or {name: (name + '\n').encode() for name in p.ROOT_DOCS})
    manifest = {'format': 'airremote-air2-source-v1', 'name': 'AIR2-P8-FIX1',
                'files': {name: p.record(blob) for name, blob in files.items()}}
    if manifest_change:
        manifest_change(manifest)
    entries = list(files.items()) + [('source_manifest.json', p.encoded(manifest))]
    if extra:
        entries += extra
    output = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        with zipfile.ZipFile(output, 'w') as zipped:
            for name, blob in entries:
                entry = zipfile.ZipInfo(p.SOURCE_ROOT + name)
                entry.external_attr = 0o100644 << 16
                zipped.writestr(entry, blob)
    return output.getvalue()


def version_node(key, value=b'', children=(), kind=1):
    result = bytearray(struct.pack('<HHH', 0, len(value) // (2 if kind else 1), kind))
    result += (key + '\0').encode('utf-16le')
    result += bytes((-len(result)) % 4)
    result += value
    for child in children:
        result += bytes((-len(result)) % 4)
        result += child
    struct.pack_into('<H', result, 0, len(result))
    return bytes(result)


def pe_fixture(company='Caimankekw', elevation='asInvoker'):
    strings = [version_node(k, (v + '\0').encode('utf-16le')) for k, v in (
        ('CompanyName', company), ('ProductName', 'Air Remote TTL-C AIR2-P8-FIX1 Custom Updater'))]
    version = version_node('VS_VERSION_INFO', bytes(52), [
        version_node('StringFileInfo', children=[version_node('040904b0', children=strings)])], kind=0)
    manifest = ('<assembly><trustInfo><security><requestedPrivileges><requestedExecutionLevel level="' +
                elevation + '" uiAccess="false"/></requestedPrivileges></security></trustInfo></assembly>').encode()
    output = bytearray(0xA00)
    output[:2] = b'MZ'
    struct.pack_into('<I', output, 0x3C, 0x80)
    output[0x80:0x84] = b'PE\0\0'
    struct.pack_into('<HHIIIHH', output, 0x84, 0x14C, 1, 0, 0, 0, 224, 0)
    struct.pack_into('<H', output, 0x98, 0x10B)
    struct.pack_into('<II', output, 0x98 + 96 + 16, 0x1000, 0x800)
    struct.pack_into('<8sIIIIIIHHI', output, 0x178, b'.rsrc\0\0\0', 0x800, 0x1000, 0x800, 0x200, 0, 0, 0, 0, 0)
    base = 0x200
    struct.pack_into('<HH', output, base + 12, 0, 2)
    struct.pack_into('<IIII', output, base + 16, 16, 0x80000020, 24, 0x80000038)
    for offset, next_offset in ((0x20, 0x50), (0x38, 0x68)):
        struct.pack_into('<HHII', output, base + offset + 12, 0, 1, 1, 0x80000000 | next_offset)
    for offset, leaf in ((0x50, 0x80), (0x68, 0x90)):
        struct.pack_into('<HHII', output, base + offset + 12, 0, 1, 1033, leaf)
    vpos = 0xA0
    mpos = (vpos + len(version) + 3) & ~3
    struct.pack_into('<IIII', output, base + 0x80, 0x1000 + vpos, len(version), 0, 0)
    struct.pack_into('<IIII', output, base + 0x90, 0x1000 + mpos, len(manifest), 0, 0)
    output[base + vpos:base + vpos + len(version)] = version
    output[base + mpos:base + mpos + len(manifest)] = manifest
    return bytes(output)


class PackageBoundaries(unittest.TestCase):
    def test_valid_source_zip(self):
        self.assertEqual(p.VERSION_NAME, 'AIR2-P8-FIX1')
        self.assertEqual(p.SOURCE_ROOT, 'AirRemote_TTL_C_AIR2_P8_FIX1/')
        self.assertTrue({'NOTICE.zh-CN.md', 'CHANGELOG.md', 'CHANGELOG.zh-CN.md'} <= set(p.ROOT_DOCS))
        pins = json.loads((p.HERE / 'input_manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(pins['name'], 'AIR2-P8-FIX1')
        self.assertEqual(pins['updater']['name'], 'AirRemote_TTL_C_C11_AIR2_P8_FIX1_Caimankekw_EXPERIMENTAL.exe')
        self.assertEqual(pins['updater']['sha256'], 'f19ebc6152539745e456d0d4060a2bca6669f0897e81e9d1ed0f2a96ff1cdfed')
        self.assertEqual(pins['firmware']['sha256'], 'a6e6284c2186d557eff9049afa3c66ec78f09406586110702f94baaafacd9ef8')
        data = zip_fixture()
        self.assertEqual(set(p.parse_source_archive(data, p.sha(data))), set(p.ROOT_DOCS) | {'source_manifest.json'})

    def test_wrong_source_sha(self):
        with self.assertRaises(ValueError):
            p.parse_source_archive(zip_fixture(), '0' * 64)

    def test_wrong_source_identity(self):
        data = zip_fixture(manifest_change=lambda m: m.update(name='AIR2-P8'))
        with self.assertRaises(ValueError):
            p.parse_source_archive(data, p.sha(data))

    def test_duplicate_source_entry(self):
        data = zip_fixture(extra=[('LICENSE', b'other')])
        with self.assertRaises(ValueError):
            p.parse_source_archive(data, p.sha(data))

    def test_undeclared_source_file(self):
        data = zip_fixture(extra=[('unexpected.py', b'pass\n')])
        with self.assertRaises(ValueError):
            p.parse_source_archive(data, p.sha(data))

    def test_source_manifest_mismatch(self):
        data = zip_fixture(manifest_change=lambda m: m['files']['LICENSE'].update(size=0))
        with self.assertRaises(ValueError):
            p.parse_source_archive(data, p.sha(data))

    def test_source_missing_legal_doc(self):
        data = zip_fixture(files={'LICENSE': b'x'})
        with self.assertRaises(ValueError):
            p.parse_source_archive(data, p.sha(data))

    def test_generated_and_escaping_source_paths(self):
        for name in ('../bad.py', '/bad.py', 'C:/bad.py', 'a\\bad.py', 'build/a.py', '.git/config', 'dist/a.zip'):
            with self.subTest(name=name):
                files = {doc: (doc + '\n').encode() for doc in p.ROOT_DOCS}
                files[name] = b'x'
                data = zip_fixture(files=files)
                with self.assertRaises(ValueError):
                    p.parse_source_archive(data, p.sha(data))

    def test_reference_wrapper_pe(self):
        result = p.verify_installer_pe(pe_fixture())
        self.assertTrue(result['as_invoker'])
        self.assertEqual(result['developer'], 'Caimankekw')

    def test_wrong_company(self):
        with self.assertRaises(ValueError):
            p.verify_installer_pe(pe_fixture(company='SomeoneElse'))

    def test_elevated_wrapper_rejected(self):
        with self.assertRaises(ValueError):
            p.verify_installer_pe(pe_fixture(elevation='requireAdministrator'))

    def test_malformed_pe_rejected(self):
        for data in (b'', b'MZ', bytes(0x100), pe_fixture()[:0x250]):
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                p.verify_installer_pe(data)

    def test_version_bounds_rejected(self):
        value = bytearray(version_node('VS_VERSION_INFO', bytes(52), kind=0))
        struct.pack_into('<H', value, 0, len(value) + 10)
        with self.assertRaises(ValueError):
            p.version_strings(value)

    def test_current_installer_controls(self):
        text = (p.HERE / 'installer.nsi').read_text(encoding='utf-8')
        self.assertIn('!define MUI_FINISHPAGE_RUN_NOTCHECKED', text)
        self.assertEqual(text.count('!insertmacro MUI_PAGE_LICENSE'), 2)
        self.assertIn('RequestExecutionLevel user', text)
        self.assertIn('SetOverwrite off', text)
        self.assertNotIn('WriteUninstaller', text)
        self.assertNotIn('Delete ', text)
        self.assertEqual(text.count("  Exec '"), 1)
        self.assertIn("  Exec '\"$INSTDIR\\AirRemote_TTL_C_C11_AIR2_P8_FIX1_Caimankekw_EXPERIMENTAL.exe\"'", text)
        self.assertIn('Name "Air Remote TTL-C AIR2-P8-FIX1 Custom Updater"', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
