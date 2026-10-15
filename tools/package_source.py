#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Make a compact, deterministic source archive. No firmware execution or USB."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'AirRemote_TTL_C_AIR2_P8'
NAME = 'Profoto-AirRemote-TTL-C-AIR2-P8-Source.zip'
EXCLUDED = {'.git', '.venv', '__pycache__', 'build', 'dist', '.tmp', '.pytest_cache'}
SUFFIXES = {'.py', '.md', '.txt', '.json', '.c', '.h', '.nsi', '.bin'}
REQUIRED = {'build.py', 'README.md', 'README.zh-CN.md', 'LICENSE', 'NOTICE.md',
            'DISCLAIMER.md', 'DISCLAIMER.zh-CN.md', 'source/ui_patch.py',
            'source/radio_patch.py', 'source/persistence_patch.py', 'source/hss_patch.py',
            'windows/build_package.py', 'windows/installer.nsi',
            'tools/reference_codec.py', 'tools/package_source.py'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory():
    files = {}
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if EXCLUDED.intersection(relative.parts) or relative.as_posix() == 'source_manifest.json':
            continue
        if relative.parts[0] == 'inputs' and path.name not in ('README.md', 'README.zh-CN.md'):
            continue
        need(not path.is_symlink(), 'Source tree contains a symbolic link: ' + str(relative))
        if not path.is_file():
            continue
        need(path.suffix.lower() in SUFFIXES or path.name in ('LICENSE', '.gitignore', '.gitattributes'),
             'Unexpected source file type: ' + str(relative))
        need(path.suffix.lower() != '.bin' or relative.parts[0] == 'reference',
             'Only generic reference parameters may be binary source inputs: ' + str(relative))
        data = path.read_bytes()
        if path.suffix.lower() != '.bin':
            text = data.decode('utf-8-sig')
            for private in (str(ROOT), str(Path.home()), str(ROOT).replace('\\', '/')):
                need(private not in text, 'Local absolute path in source: ' + str(relative))
        files[relative.as_posix()] = data
    need(REQUIRED.issubset(files), 'Missing required source files: ' + str(sorted(REQUIRED - files.keys())))
    return files


def source_manifest(files):
    return {
        'format': 'airremote-air2-source-v1', 'name': 'AIR2-P8', 'developer': 'Caimankekw',
        'license': 'AGPL-3.0-only; authored material only; see NOTICE.md',
        'original_updater_sha256': 'e56b19080bd6330a5461dd4e3d614fc6d81dcc533e945e6090e7db63824bc240',
        'firmware_sha256': '337120c7ed51954f4cdf0e60816e0289583a3c6b4ad400504d0cbef0a259f185',
        'updater_sha256': 'dec0660b9568713d36a13e44909741b2891d30680895f0ef3406a31e9cbebde1',
        'files': {name: {'size': len(data), 'sha256': sha(data)} for name, data in sorted(files.items())},
        'scope': 'Source and generic reference parameters; no vendor EXE, device capture, build output or historical releases.',
    }


def verify(archive):
    with zipfile.ZipFile(archive) as zipped:
        names = zipped.namelist()
        need(len(names) == len(set(names)) and zipped.testzip() is None, 'Duplicate names or ZIP CRC failure')
        for name in names:
            parts = PurePosixPath(name)
            need(not parts.is_absolute() and parts.parts[0] == PREFIX and '..' not in parts.parts and '\\' not in name,
                 'Unexpected ZIP path')
        manifest_name = PREFIX + '/source_manifest.json'
        manifest = json.loads(zipped.read(manifest_name))
        need(manifest['format'] == 'airremote-air2-source-v1' and manifest['name'] == 'AIR2-P8', 'Wrong source manifest')
        expected = {PREFIX + '/' + name for name in manifest['files']} | {manifest_name}
        need(set(names) == expected, 'Source inventory mismatch')
        for name, entry in manifest['files'].items():
            data = zipped.read(PREFIX + '/' + name)
            need(len(data) == entry['size'] and sha(data) == entry['sha256'], 'Source fingerprint mismatch: ' + name)
    return {'status': 'PASS', 'archive': archive.name, 'size': archive.stat().st_size,
            'sha256': sha(archive.read_bytes()), 'source_files': len(manifest['files']),
            'vendor_executable_included': False, 'device_accessed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'dist')
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify(args.verify), indent=2))
        return
    files = inventory()
    manifest = source_manifest(files)
    encoded = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    output = args.out.resolve()
    archive = output / NAME
    report_path = output / 'source_package_verification.json'
    need(not archive.exists() and not report_path.exists(), 'Source output already exists; choose a new --out directory')
    output.mkdir(parents=True, exist_ok=True)
    (ROOT / 'source_manifest.json').write_bytes(encoded)
    files['source_manifest.json'] = encoded
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(PREFIX + '/' + name, (2026, 10, 15, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            zipped.writestr(entry, data)
    result = verify(archive)
    with zipfile.ZipFile(archive) as zipped:
        need(all(zipped.read(PREFIX + '/' + name) == data for name, data in files.items()), 'ZIP byte comparison failed')
    result['all_files_match_sources'] = True
    report_path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
