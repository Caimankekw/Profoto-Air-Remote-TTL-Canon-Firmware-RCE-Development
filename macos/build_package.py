#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Package reviewed firmware in the stock Mac GUI. Never launch an updater."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import plistlib
import re
import shutil
import stat
import struct
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FORMAT = 'airremote-macos-package-v1'
LEGAL = ('LICENSE', 'NOTICE.md', 'NOTICE.zh-CN.md',
         'DISCLAIMER.md', 'DISCLAIMER.zh-CN.md')
MAX_ARCHIVE = 512 * 1024 * 1024


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(path):
    data = Path(path).read_bytes()
    return {'size': len(data), 'sha256': sha(data)}


def safe_path(value):
    need(isinstance(value, str) and value and '\\' not in value and ':' not in value,
         'Invalid relative path')
    path = PurePosixPath(value)
    need(not path.is_absolute() and str(path) == value and
         all(x not in ('', '.', '..') for x in value.split('/')) and
         not any(ord(c) < 32 for c in value), 'Unsafe path: ' + value)
    return path


def digest(value):
    need(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'Invalid SHA256')
    return value


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        need(key not in obj, 'Duplicate JSON key: ' + key)
        obj[key] = value
    return obj


def parse_json(data):
    obj = json.loads(data.decode('utf-8-sig'), object_pairs_hook=unique_object)
    need(isinstance(obj, dict), 'Expected JSON object')
    return obj


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def verify_file(path, expected):
    actual = fingerprint(path)
    need(actual['sha256'] == digest(expected['sha256']), 'SHA256 mismatch: ' + Path(path).name)
    if 'size' in expected:
        need(actual['size'] == expected['size'], 'Size mismatch: ' + Path(path).name)
    return actual


def validate_profile(profile):
    need(profile.get('schema') == FORMAT, 'Wrong Mac profile schema')
    need(profile.get('model') in ('C', 'N', 'S', 'F', 'O'), 'Unsupported model')
    need(profile.get('version') == ('AIR2-P8-FIX1' if profile['model'] == 'C' else 'AIR2-P8-M2'),
         'Unexpected firmware version')
    for key in ('brand', 'stock_revision', 'output_slug', 'volume_name', 'source_prefix'):
        need(isinstance(profile.get(key), str) and profile[key], 'Missing profile value: ' + key)
    need(re.fullmatch('[A-Za-z0-9_.-]+', profile['output_slug']), 'Unsafe output slug')
    need(len(profile['volume_name']) <= 80 and not any(c in profile['volume_name'] for c in '/\\:\n\r'),
         'Invalid volume name')
    safe_path(profile['source_prefix'])
    for entry in ('original', 'windows'):
        item = profile[entry]
        digest(item['sha256'])
        need(type(item['size']) is int and 0 < item['size'] <= MAX_ARCHIVE, 'Invalid archive size')
        need(len(safe_path(item['asset']).parts) == 1, 'Asset must be a filename')
    original = profile['original']
    for key in ('dmg', 'faq', 'notice'):
        safe_path(original[key + '_member'])
        digest(original[key + '_sha256'])
    for key in ('app_path', 'main_path', 'helper_path', 'firmware_path'):
        safe_path(original[key])
    need(original['app_path'].endswith('.app'), 'Expected original app bundle')
    need(original['firmware_path'] == 'Contents/Resources/RMRT%s_firmware.hex' % profile['model'],
         'Model and firmware resource differ')
    for key in ('main_sha256', 'helper_sha256', 'firmware_sha256'):
        digest(original[key])
    windows = profile['windows']
    safe_path(windows['updater_member'])
    digest(windows['updater_sha256'])
    digest(windows['custom_hex_sha256'])
    need(type(windows['hex_start']) is int and type(windows['hex_end']) is int and
         0 <= windows['hex_start'] < windows['hex_end'] <= MAX_ARCHIVE, 'Invalid HEX interval')
    digest(profile['expected_firmware_sha256'])
    for key in ('release_repository',):
        need(re.fullmatch('[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', profile[key]), 'Invalid repository')
    for key in ('release_tag',):
        need(re.fullmatch('[A-Za-z0-9_.-]+', profile[key]), 'Invalid release tag')
    for key in ('repository', 'tag'):
        if key in windows:
            pattern = '[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+' if key == 'repository' else '[A-Za-z0-9_.-]+'
            need(re.fullmatch(pattern, windows[key]), 'Invalid Windows asset location')
    return profile


def zip_inventory(archive):
    """Reject unsafe, ambiguous, enormous, linked, or duplicate archive members."""
    infos = archive.infolist()
    need(len(infos) <= 10000, 'Too many ZIP entries')
    seen = set()
    total = 0
    for info in infos:
        name = info.filename.rstrip('/') if info.is_dir() else info.filename
        safe_path(name)
        key = name.casefold()
        need(key not in seen, 'Duplicate/case-colliding ZIP entry: ' + name)
        seen.add(key)
        kind = stat.S_IFMT(info.external_attr >> 16)
        need(kind not in (stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFIFO, stat.S_IFSOCK),
             'Non-regular ZIP entry: ' + name)
        need(not info.flag_bits & 1, 'Encrypted ZIP entry')
        total += info.file_size
        need(total <= MAX_ARCHIVE, 'Expanded archive exceeds bound')
    need(archive.testzip() is None, 'ZIP CRC failure')
    return {info.filename: info for info in infos if not info.is_dir()}


def read_pinned_member(archive, name, expected_sha):
    members = zip_inventory(archive)
    need(name in members, 'Missing ZIP member: ' + name)
    data = archive.read(name)
    need(sha(data) == digest(expected_sha), 'ZIP member SHA256 mismatch: ' + name)
    return data


def extract_hex(path, profile):
    windows = profile['windows']
    verify_file(path, windows)
    with zipfile.ZipFile(path) as archive:
        exe = read_pinned_member(archive, windows['updater_member'], windows['updater_sha256'])
    need(windows['hex_end'] <= len(exe), 'HEX interval exceeds updater')
    data = exe[windows['hex_start']:windows['hex_end']]
    need(sha(data) == windows['custom_hex_sha256'], 'Custom transport HEX mismatch')
    parse_hex(data)
    return data


def parse_hex(data):
    """Validate record checksums, absolute address uniqueness, and terminal EOF."""
    need(isinstance(data, bytes) and data, 'Empty Intel HEX')
    try:
        lines = data.decode('ascii').splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError('Non-ASCII Intel HEX') from exc
    address_base = 0
    memory = {}
    ended = False
    for line in lines:
        need(not ended and re.fullmatch(':[0-9A-Fa-f]+', line), 'Invalid/after-EOF HEX record')
        raw = bytes.fromhex(line[1:])
        need(len(raw) >= 5 and len(raw) == raw[0] + 5 and sum(raw) % 256 == 0, 'HEX checksum/length error')
        count, address, kind = raw[0], int.from_bytes(raw[1:3], 'big'), raw[3]
        body = raw[4:-1]
        if kind == 0:
            need(address + count <= 0x10000, 'HEX record crosses segment')
            for i, byte in enumerate(body):
                absolute = address_base + address + i
                need(absolute not in memory, 'Overlapping HEX records')
                memory[absolute] = byte
        elif kind == 1:
            need(count == 0 and address == 0, 'Malformed EOF record')
            ended = True
        elif kind in (2, 4):
            need(count == 2 and address == 0, 'Malformed extended address')
            address_base = int.from_bytes(body, 'big') << (4 if kind == 2 else 16)
        elif kind in (3, 5):
            need(count == 4 and address == 0, 'Malformed execution address')
        else:
            raise ValueError('Unsupported Intel HEX record')
    need(ended and memory, 'Missing HEX EOF or data')
    return memory


def run(command, cwd=None):
    result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    need(result.returncode == 0, 'Command failed: ' + command[0] + '\n' + result.stderr.decode('utf-8', 'replace'))
    return result.stdout


def verify_source(archive_path, expected_sha, profile, root, commit):
    verify_file(archive_path, {'sha256': expected_sha})
    need(re.fullmatch('[0-9a-f]{40}', commit), 'Expected complete Git source commit')
    actual_commit = run(['git', 'rev-parse', 'HEAD'], cwd=root).decode().strip()
    need(actual_commit == commit, 'Checkout differs from expected source commit')
    need(not run(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=root).strip(), 'Tracked source has local modifications')
    tracked = set(run(['git', 'ls-files', '-z'], cwd=root).decode('utf-8').rstrip('\0').split('\0'))
    prefix = profile['source_prefix'] + '/'
    with zipfile.ZipFile(archive_path) as archive:
        members = zip_inventory(archive)
        manifest_name = prefix + 'source_manifest.json'
        need(manifest_name in members, 'Source archive manifest missing')
        manifest = parse_json(archive.read(manifest_name))
        files = manifest.get('files')
        need(isinstance(files, dict) and files, 'Invalid source inventory')
        need(set(members) == {prefix + name for name in files} | {manifest_name}, 'Source ZIP inventory mismatch')
        need(set(files) == tracked - {'source_manifest.json'}, 'Source archive differs from tracked checkout inventory')
        for name, expected in files.items():
            safe_path(name)
            path = root.joinpath(*PurePosixPath(name).parts)
            need(path.is_file() and not path.is_symlink(), 'Missing/nonregular source file: ' + name)
            data = archive.read(prefix + name)
            need(expected == {'size': len(data), 'sha256': sha(data)}, 'Source inventory fingerprint mismatch: ' + name)
            need(path.read_bytes() == data, 'Source archive and checkout differ: ' + name)
        for required in LEGAL + ('macos/build_package.py', 'macos/model.json', '.github/workflows/build-macos.yml'):
            need(required in files, 'Required corresponding source missing: ' + required)
    return {'archive': archive_path.name, **fingerprint(archive_path), 'commit': commit, 'files': len(files)}


def bundle_inventory(bundle):
    result = {}
    for path in sorted(bundle.rglob('*')):
        name = path.relative_to(bundle).as_posix()
        if path.is_symlink():
            target = os.readlink(path)
            resolved = path.resolve()
            need(resolved == bundle.resolve() or bundle.resolve() in resolved.parents, 'Escaping app symlink: ' + name)
            result[name] = {'symlink': target}
        elif path.is_file():
            result[name] = {**fingerprint(path), 'mode': stat.S_IMODE(path.stat().st_mode)}
        else:
            need(path.is_dir(), 'Special app file: ' + name)
    return result


def macho_signature_independent(data):
    """Normalize only code-signature allocation metadata; retain all other bytes.

    codesign can resize the signature and __LINKEDIT. Excluding the signature
    itself plus normalizing those four size/offset fields leaves executable
    code, every section, linkage data, and the other load commands checked.
    Existing signatures mean no new load command should be required.
    """
    magic = data[:4]
    if magic in (b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca', b'\xca\xfe\xba\xbf', b'\xbf\xba\xfe\xca'):
        endian = '>' if magic in (b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf') else '<'
        fat64 = magic in (b'\xca\xfe\xba\xbf', b'\xbf\xba\xfe\xca')
        count = struct.unpack_from(endian + 'I', data, 4)[0]
        need(0 < count <= 16, 'Invalid fat Mach-O count')
        entries = []
        width = 32 if fat64 else 20
        need(8 + width * count <= len(data), 'Truncated fat Mach-O')
        for i in range(count):
            start = 8 + i * width
            cpu, subtype = struct.unpack_from(endian + 'II', data, start)
            offset, size = struct.unpack_from(endian + ('QQ' if fat64 else 'II'), data, start + 8)
            need(offset + size <= len(data), 'Fat slice out of bounds')
            entries.append({'cpu': cpu, 'subtype': subtype, 'content': macho_signature_independent(data[offset:offset + size])})
        return {'fat': entries}
    thin = {b'\xcf\xfa\xed\xfe': ('<', True), b'\xfe\xed\xfa\xcf': ('>', True),
            b'\xce\xfa\xed\xfe': ('<', False), b'\xfe\xed\xfa\xce': ('>', False)}
    need(magic in thin, 'Not a recognized Mach-O executable')
    endian, is64 = thin[magic]
    header = 32 if is64 else 28
    need(len(data) >= header, 'Truncated Mach-O header')
    count, command_size = struct.unpack_from(endian + 'II', data, 16)
    need(count < 4096 and header + command_size <= len(data), 'Invalid Mach-O command table')
    normalized = bytearray(data)
    cursor, signatures = header, []
    for _ in range(count):
        need(cursor + 8 <= header + command_size, 'Truncated load command')
        command, size = struct.unpack_from(endian + 'II', data, cursor)
        need(size >= 8 and cursor + size <= header + command_size, 'Invalid load command size')
        if command == 0x1d:
            need(size == 16, 'Invalid code signature command')
            offset, length = struct.unpack_from(endian + 'II', data, cursor + 8)
            need(offset >= header + command_size and length > 0 and offset + length <= len(data), 'Invalid signature range')
            signatures.append((offset, length))
            normalized[cursor + 8:cursor + 16] = b'\0' * 8
        if command in (1, 0x19):
            need(size >= (72 if command == 0x19 else 56), 'Truncated segment command')
            segment = data[cursor + 8:cursor + 24].split(b'\0')[0]
            if segment == b'__LINKEDIT':
                for offset, width in ((32, 8), (48, 8)) if command == 0x19 else ((28, 4), (36, 4)):
                    normalized[cursor + offset:cursor + offset + width] = b'\0' * width
        cursor += size
    need(cursor == header + command_size and len(signatures) == 1, 'Expected one existing signature command')
    offset, length = signatures[0]
    need(not any(data[offset + length:]), 'Unexpected nonzero bytes after code signature')
    # A re-sign may change zero alignment padding immediately before the blob.
    # Preserve it: only a signature at the same offset passes comparison.
    return {'signature_offset': offset, 'payload_sha256': sha(bytes(normalized[:offset])), 'header_size': header}


@contextlib.contextmanager
def mounted(dmg, mountpoint):
    mountpoint.mkdir()
    output = run(['/usr/bin/hdiutil', 'attach', '-readonly', '-nobrowse', '-noautoopen',
                  '-plist', '-mountpoint', str(mountpoint), str(dmg)])
    info = plistlib.loads(output)
    entities = info.get('system-entities', [])
    device = next((x.get('dev-entry') for x in entities if x.get('mount-point') == str(mountpoint)), None)
    need(device, 'Mounted DMG did not report the requested mount point')
    try:
        yield mountpoint
    finally:
        run(['/usr/bin/hdiutil', 'detach', device])


def assert_stock_bundle(app, profile):
    original = profile['original']
    need(app.is_dir() and not app.is_symlink(), 'Original .app missing')
    for label in ('main', 'helper', 'firmware'):
        path = app / original[label + '_path']
        need(path.is_file() and not path.is_symlink(), 'Original bundle pin is not a regular file')
        verify_file(path, {'sha256': original[label + '_sha256']})
    run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(app)])
    plist = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
    need(plist.get('CFBundleExecutable') == PurePosixPath(original['main_path']).name, 'Main executable/Info.plist mismatch')
    need(str(plist.get('LSMinimumSystemVersion', '')) == '11.0', 'Unexpected stock minimum macOS version')
    return bundle_inventory(app)


def compare_bundle(original, changed, profile, before_main, after_main):
    firmware = profile['original']['firmware_path']
    main = profile['original']['main_path']
    signature = 'Contents/_CodeSignature/'
    ordinary_before = {k: v for k, v in original.items() if k not in (firmware, main) and not k.startswith(signature)}
    ordinary_after = {k: v for k, v in changed.items() if k not in (firmware, main) and not k.startswith(signature)}
    need(ordinary_before == ordinary_after, 'A stock resource/helper/Info.plist/permission changed')
    need(firmware in changed and changed[firmware]['sha256'] == profile['windows']['custom_hex_sha256'], 'Packaged HEX pin differs')
    need(main in changed and original[main]['mode'] == changed[main]['mode'], 'Main executable mode changed')
    before = macho_signature_independent(before_main)
    after = macho_signature_independent(after_main)
    need(before == after, 'Executable changed outside the embedded code signature')
    return before


def readme(profile, chinese=False):
    name = 'Air Remote TTL-' + profile['model'] + ' ' + profile['version']
    if chinese:
        return f'''# {name} macOS 实验包\n\n开发者：Caimankekw。原创内容采用 AGPL-3.0-only，第三方内容见 NOTICE.zh-CN.md。\n\n保留原厂 macOS GUI 与 USB 更新流程，使用对应 Windows 发布版的完全相同固件 HEX。仅限 {profile['brand']} / TTL-{profile['model']}。此包不是 Profoto 官方发布。\n\n1. 先阅读 DISCLAIMER.zh-CN.md。挂载带 AIR2 名称的自定义 DMG，将其中的应用复制到本地新文件夹后打开。应用内部保留原厂名称以保持资源与更新逻辑一致；以外层 DMG 名称及附带 SHA256SUMS.txt 区分版本。\n2. 按原厂 GUI 提示连接设备、更新；不要同时运行其他更新器。构建流程本身不访问 USB，也不执行更新器。\n3. 更新结束后断开 USB，用电池验证开机、菜单、灯组与拍摄行为。恢复时使用 完整 ZIP 内 Recovery 文件夹中的原厂 DMG（单独的自定义 DMG 不包含恢复程序）；不保证所有异常均可恢复。\n\n要求 macOS 11 或更新版本。原厂 GUI 为 Intel x86_64，Apple Silicon 可能需要 Rosetta 2；helper 保留原厂架构。修改后的外层应用使用本地 ad-hoc 签名，没有开发者 ID 签名或公证，Gatekeeper 可能阻止运行。请仅在核对下载来源与 SHA256 后依照 macOS 的“隐私与安全性”提示处理；不建议全局关闭安全检查。原厂恢复 DMG 的签名未改动。\n\n已进行原生挂载、代码签名完整性及文件回读检查；没有执行 GUI、USB 刷写或实机验收。具体固件功能与限制见源代码中的 README.zh-CN.md。\n'''
    return f'''# {name} experimental macOS package\n\nDeveloper: Caimankekw. Authored material: AGPL-3.0-only. Third-party rights: NOTICE.md.\n\nThe stock macOS GUI and USB update flow are retained with exactly the reviewed Windows release transport HEX. Only for {profile['brand']} / TTL-{profile['model']}. This is not an official Profoto release.\n\n1. Read DISCLAIMER.md. Mount the custom DMG with AIR2 in its name, copy its app into a new local folder, and open that copy. The original internal app name is intentionally retained for resource/update compatibility; distinguish releases by the outer DMG filename and SHA256SUMS.txt.\n2. Follow the vendor GUI instructions. Close other updaters. The build process never runs the updater or accesses USB.\n3. After updating, disconnect USB and test battery startup, menus, groups and photographic behavior. The full ZIP is the recommended download. Recovery uses its unchanged stock DMG under Recovery; the standalone custom DMG does not contain recovery software. Recovery is not guaranteed.\n\nRequires macOS 11 or newer. The stock GUI is Intel x86_64, so Apple Silicon may require Rosetta 2; the helper retains its original architectures. The modified outer app is locally ad-hoc signed, without a Developer ID signature or notarization. Gatekeeper may block it. Verify origin and SHA256 first, then follow macOS Privacy & Security guidance; do not globally disable security checks. The recovery DMG signature is unchanged.\n\nNative mounting, signature integrity and file readback were checked. GUI execution, USB flashing and hardware acceptance were not tested. See the corresponding source README for firmware behavior and limitations.\n'''


def make_zip(directory, destination, prefix):
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(directory.rglob('*')):
            need(not path.is_symlink(), 'Final ZIP cannot include symlinks')
            if path.is_file():
                info = zipfile.ZipInfo(prefix + '/' + path.relative_to(directory).as_posix(), (2026, 10, 16, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(info, path.read_bytes())


def build(args):
    profile = validate_profile(parse_json(args.profile.read_bytes()))
    root = args.profile.resolve().parents[1]
    source = verify_source(args.source_archive, args.source_sha256, profile, root, args.source_commit)
    verify_file(args.stock_maczip, profile['original'])
    custom_hex = extract_hex(args.windows_package, profile)
    need(platform.system() == 'Darwin', 'Native build requires macOS; verification is not emulated')
    output = args.output.resolve()
    need(not output.exists(), 'Output must be a new directory; nothing is deleted/overwritten')
    output.mkdir(parents=True)
    work = output / 'work'
    work.mkdir()
    original = profile['original']
    with zipfile.ZipFile(args.stock_maczip) as archive:
        for key in ('dmg', 'faq', 'notice'):
            data = read_pinned_member(archive, original[key + '_member'], original[key + '_sha256'])
            (work / (key + Path(original[key + '_member']).suffix)).write_bytes(data)
    stock_dmg = work / 'dmg.dmg'
    payload = work / 'custom-volume'
    payload.mkdir()
    app = payload / Path(original['app_path']).name
    with mounted(stock_dmg, work / 'stock-mount') as mount:
        stock_app = mount.joinpath(*PurePosixPath(original['app_path']).parts)
        before = assert_stock_bundle(stock_app, profile)
        before_main = (stock_app / original['main_path']).read_bytes()
        run(['/usr/bin/ditto', str(stock_app), str(app)])
    need(bundle_inventory(app) == before, 'ditto did not preserve the original bundle')
    (app / original['firmware_path']).write_bytes(custom_hex)
    # Preserve original entitlement XML and hardened-runtime flags, but never
    # preserve a vendor designated requirement/authority for changed resources.
    entitlements = run(['/usr/bin/codesign', '--display', '--entitlements', ':-', str(app)])
    ent_path = work / 'stock-entitlements.plist'
    sign = ['/usr/bin/codesign', '--force', '--sign', '-', '--timestamp=none',
            '--preserve-metadata=identifier,flags,runtime']
    if entitlements.strip():
        plistlib.loads(entitlements)
        ent_path.write_bytes(entitlements)
        sign += ['--entitlements', str(ent_path)]
    sign += [str(app)]
    run(sign)
    run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(app)])
    changed = bundle_inventory(app)
    code = compare_bundle(before, changed, profile, before_main, (app / original['main_path']).read_bytes())
    (payload / 'README.md').write_text(readme(profile), encoding='utf-8')
    (payload / 'README.zh-CN.md').write_text(readme(profile, True), encoding='utf-8')
    for name in LEGAL:
        shutil.copyfile(root / name, payload / name)
    shutil.copyfile(work / 'faq.pdf', payload / Path(original['faq_member']).name)
    shutil.copyfile(work / 'notice.txt', payload / Path(original['notice_member']).name)
    deliverables = output / 'release'
    deliverables.mkdir()
    dmg = deliverables / (profile['output_slug'] + '.dmg')
    run(['/usr/bin/hdiutil', 'create', '-format', 'UDZO', '-fs', 'APFS', '-volname',
         profile['volume_name'], '-srcfolder', str(payload), str(dmg)])
    run(['/usr/bin/hdiutil', 'verify', str(dmg)])
    with mounted(dmg, work / 'final-mount') as mount:
        checked_app = mount / app.name
        run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(checked_app)])
        need(bundle_inventory(checked_app) == changed, 'Final DMG bundle readback mismatch')
        compare_bundle(before, bundle_inventory(checked_app), profile, before_main,
                       (checked_app / original['main_path']).read_bytes())
        for name in LEGAL + ('README.md', 'README.zh-CN.md',
                             Path(original['faq_member']).name, Path(original['notice_member']).name):
            need((mount / name).read_bytes() == (payload / name).read_bytes(), 'Final DMG document differs')
    recovery = deliverables / 'Recovery'
    recovery.mkdir()
    shutil.copyfile(stock_dmg, recovery / Path(original['dmg_member']).name)
    shutil.copyfile(work / 'faq.pdf', deliverables / Path(original['faq_member']).name)
    shutil.copyfile(work / 'notice.txt', deliverables / Path(original['notice_member']).name)
    shutil.copyfile(args.source_archive, deliverables / args.source_archive.name)
    for name in LEGAL + ('README.md', 'README.zh-CN.md'):
        shutil.copyfile(payload / name, deliverables / name)
    verification = {
        'schema': 'airremote-macos-verification-v1', 'status': 'PASS', 'model': profile['model'],
        'version': profile['version'], 'developer': 'Caimankekw', 'source': source,
        'original_mac_zip': fingerprint(args.stock_maczip), 'windows_package': fingerprint(args.windows_package),
        'custom_dmg': fingerprint(dmg), 'stock_firmware_hex_sha256': original['firmware_sha256'],
        'custom_firmware_hex_sha256': sha(custom_hex), 'reviewed_firmware_image_sha256': profile['expected_firmware_sha256'],
        'main_code_outside_signature': code, 'helper_sha256': original['helper_sha256'],
        'stock_bundle': before, 'custom_bundle': changed,
        'checks': {'original_signature': True, 'custom_ad_hoc_signature': True,
                   'final_dmg_native_mount_and_readback': True, 'helper_exact': True,
                   'other_resources_and_info_plist_exact': True, 'source_matches_checkout': True,
                   'updater_launched': False, 'usb_accessed': False, 'hardware_validated': False,
                   'developer_id_signed': False, 'notarized': False},
        'build_platform': {'system': platform.system(), 'release': platform.release(), 'machine': platform.machine()},
    }
    write_json(deliverables / 'verification.json', verification)
    checksums = []
    for path in sorted(deliverables.rglob('*')):
        if path.is_file():
            checksums.append(sha(path.read_bytes()) + '  ' + path.relative_to(deliverables).as_posix())
    (deliverables / 'SHA256SUMS.txt').write_text('\n'.join(checksums) + '\n', encoding='utf-8')
    final_zip = output / (profile['output_slug'] + '.zip')
    make_zip(deliverables, final_zip, profile['output_slug'])
    with zipfile.ZipFile(final_zip) as archive:
        zip_inventory(archive)
        for path in deliverables.rglob('*'):
            if path.is_file():
                name = profile['output_slug'] + '/' + path.relative_to(deliverables).as_posix()
                need(archive.read(name) == path.read_bytes(), 'Final ZIP readback mismatch')
    summary = {'status': 'PASS', 'zip': {'name': final_zip.name, **fingerprint(final_zip)},
               'dmg': {'name': dmg.name, **fingerprint(dmg)}, 'source_commit': args.source_commit,
               'model': profile['model'], 'updater_launched': False, 'usb_accessed': False}
    write_json(output / 'build_summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, default=ROOT / 'macos/model.json')
    parser.add_argument('--stock-maczip', type=Path, required=True)
    parser.add_argument('--windows-package', type=Path, required=True)
    parser.add_argument('--source-archive', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args())


if __name__ == '__main__':
    main()
