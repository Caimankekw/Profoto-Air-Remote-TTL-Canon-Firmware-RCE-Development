# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Standalone source/transport boundary tests; explicit original EXE, no USB.

Test scratch directories are retained (never deleted by this script).
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tested_standalone_builder', ROOT / 'build.py')
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)
ORIGINAL = None


class SourceBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if ORIGINAL is None:
            raise unittest.SkipTest('Supply --original for complete source build tests')
        cls.exe = ORIGINAL.read_bytes()
        cls.artifacts = builder.prepare(cls.exe)
        container = builder.load('build_test_container', ROOT / 'tools/container.py').Container(cls.exe)
        cls.original, cls.mask = builder.load('build_test_codec', ROOT / 'tools/reference_codec.py').ReferenceCodec().decode_original(container.hex.memory)
        cls.image = cls.artifacts['AIR2-P8.base4000.partial.bin']
        cls.scratch = Path(tempfile.mkdtemp(prefix='air2_p8_build_tests_'))

    def test_source_image_and_exe_match_frozen_hashes(self):
        self.assertEqual(builder.sha(self.image), builder.EXPECTED_IMAGE_SHA)
        self.assertEqual(builder.sha(self.artifacts[builder.EXE_NAME]), builder.EXPECTED_EXE_SHA)
        report = json.loads(self.artifacts['manifest.json'])
        self.assertTrue(report['source_build_not_recipe_replay'])
        self.assertFalse(report['device_accessed'])

    def test_hss_is_built_from_source(self):
        firmware = builder.load('source_test_firmware', ROOT / 'tools/firmware.py')
        self.assertEqual(builder.sha(firmware.hss_build(self.original)[0]), firmware.P1_SHA)
        self.assertEqual(builder.sha(firmware.baseline_p3(self.original)), firmware.P3_SHA)

    def test_changed_original_exe_rejected(self):
        altered = bytearray(self.exe)
        altered[-1] ^= 1
        with self.assertRaises(ValueError):
            builder.prepare(bytes(altered))

    def test_truncated_original_rejected(self):
        with self.assertRaises(ValueError):
            builder.prepare(self.exe[:-1])

    def test_unknown_first_word_rejected(self):
        altered = bytearray(self.image)
        altered[0] ^= 1
        with self.assertRaisesRegex(ValueError, 'bounds'):
            builder.validate_image(self.original, self.mask, altered)

    def test_nvm_page_change_rejected(self):
        altered = bytearray(self.image)
        altered[0xF800 - builder.BASE] = 0
        with self.assertRaisesRegex(ValueError, 'bounds'):
            builder.validate_image(self.original, self.mask, altered)

    def test_tail_configuration_change_rejected(self):
        altered = bytearray(self.image)
        altered[0x1F800 - builder.BASE] = 0
        with self.assertRaisesRegex(ValueError, 'bounds'):
            builder.validate_image(self.original, self.mask, altered)

    def test_header_crc_change_rejected(self):
        altered = bytearray(self.image)
        altered[0x50] ^= 1
        with self.assertRaisesRegex(ValueError, 'checksum'):
            builder.validate_image(self.original, self.mask, altered)

    def test_known_mask_escalation_rejected(self):
        mask = bytearray(self.mask)
        mask[0] = 1
        with self.assertRaisesRegex(ValueError, 'Known-mask'):
            builder.validate_image(self.original, mask, self.image)

    def test_recipe_is_generated_and_independently_replays(self):
        recipe = json.loads(self.artifacts['reproduction_recipe.json'])
        tool = builder.load('build_test_recipe', ROOT / 'tools/rebuild_windows.py')
        result, report = tool.rebuild(self.exe, recipe)
        self.assertEqual(result, self.artifacts[builder.EXE_NAME])
        self.assertEqual(report['status'], 'PASS')

    def test_existing_output_is_not_overwritten(self):
        out = self.scratch / 'existing'
        out.mkdir()
        (out / 'second.bin').write_bytes(b'preserve')
        with self.assertRaisesRegex(ValueError, 'different existing'):
            builder.write_outputs({'first.bin': b'one', 'second.bin': b'two'}, out)
        self.assertFalse((out / 'first.bin').exists())
        self.assertEqual((out / 'second.bin').read_bytes(), b'preserve')

    def test_output_escape_rejected_before_creation(self):
        out = self.scratch / 'escaping_output'
        with self.assertRaisesRegex(ValueError, 'escapes'):
            builder.write_outputs({'../escape.bin': b'one'}, out)
        self.assertFalse(out.exists())

    def test_bad_input_cli_produces_no_output(self):
        invalid = self.scratch / 'invalid.exe'
        invalid.write_bytes(b'not the original firmware')
        out = self.scratch / 'bad_input_output'
        result = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'build.py'),
                                 '--original', str(invalid), '--out', str(out)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(out.exists())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path)
    args, extra = parser.parse_known_args()
    ORIGINAL = args.original.resolve() if args.original else None
    unittest.main(argv=[sys.argv[0]] + extra)
