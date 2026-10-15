# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Build the pinned AIR2-P8-FIX1 firmware from authored sources and an official C11 EXE.

Python 3.9+, standard library only. The vendor EXE is parsed, never executed.
No USB, updater launch, device reads/writes, network calls, or workspace inputs.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
BASE, END, PATCH_END = 0x4000, 0x1FC00, 0xF800
EXPECTED_IMAGE_SHA = 'a6e6284c2186d557eff9049afa3c66ec78f09406586110702f94baaafacd9ef8'
EXPECTED_EXE_SHA = 'f19ebc6152539745e456d0d4060a2bca6669f0897e81e9d1ed0f2a96ff1cdfed'
EXPECTED_HEX_SHA = '7f862508c314cad49b15096adf5e84e67879f851162abebf159a63cb88ccd67c'
EXE_NAME = 'AirRemote_TTL_C_C11_AIR2_P8_FIX1_Caimankekw_EXPERIMENTAL.exe'


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


def spans(addresses):
    result = []
    for address in sorted(set(addresses)):
        if result and address == result[-1][1]:
            result[-1][1] += 1
        else:
            result.append([address, address + 1])
    return result


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def validate_image(original, mask, image):
    """Hard bounds independent of the source linker and transport encoder."""
    need(len(original) == len(mask) == len(image) == END - BASE, 'Image dimensions changed')
    need(mask == b'\0\0' + b'\1' * (END - BASE - 2), 'Known-mask scope changed')
    changed = [BASE + i for i, (a, b) in enumerate(zip(original, image)) if a != b]
    need(changed and all(address in (0x4050, 0x4051) or 0x40A6 <= address < PATCH_END
                         for address in changed), 'Change outside code/checksum bounds')
    need(image[:0x50] == original[:0x50] and image[0x52:0xA6] == original[0x52:0xA6],
         'Original unknown prefix, startup or header metadata changed')
    need(image[0xB800:0xC000] == b'\xff' * 0x800, 'Runtime NVM pages are not erased')
    need(image[PATCH_END-BASE:] == original[PATCH_END-BASE:], 'Protected tail/settings changed')
    firmware = load('standalone_firmware_validation', ROOT / 'tools/firmware.py')
    need(firmware.apply_header_crc(image) == image, 'Header checksum does not match image')
    delta = firmware.crc16_linear(bytes(a ^ b for a, b in zip(
        firmware.crc_body(original), firmware.crc_body(image))))
    need(int.from_bytes(original[0x50:0x52], 'little') ^ delta ==
         int.from_bytes(image[0x50:0x52], 'little'), 'CRC affine/differential checks disagree')
    return changed


def prepare(original_exe):
    container_mod = load('standalone_container', ROOT / 'tools/container.py')
    codec_mod = load('standalone_reference_codec', ROOT / 'tools/reference_codec.py')
    linker = load('standalone_linker', ROOT / 'source/linker.py')
    original_container = container_mod.Container(original_exe)
    codec = codec_mod.ReferenceCodec()
    original, mask = codec.decode_original(original_container.hex.memory)
    image, built_mask, manifest = linker.construct(original, mask)
    need(built_mask == mask, 'Linker changed known mask')
    changed = validate_image(original, mask, image)
    need(sha(image) == EXPECTED_IMAGE_SHA, 'Source-built image differs from pinned AIR2-P8-FIX1')
    replacements = {}
    for start, end in spans(changed):
        replacements.update(codec.encode_patch(start, image[start-BASE:end-BASE]))
    need(set(replacements) == set(changed), 'Encoded replacement range escaped source edits')
    encoded = original_container.hex.replace_opaque_bytes(replacements)
    executable = original_container.replace_hex(encoded)
    reopened = container_mod.Container(executable, require_vendor_pin=False)
    need(reopened.hex.text == encoded.text, 'EXE re-extraction mismatch')
    need(reopened.hex.spans() == original_container.hex.spans(), 'Sparse HEX layout changed')
    need(set(reopened.hex.memory) == set(original_container.hex.memory), 'HEX addresses changed')
    for address, value in original_container.hex.memory.items():
        if address not in replacements:
            need(reopened.hex.memory[address] == value, 'Protected opaque byte changed')
    opaque = bytes(reopened.hex.memory[a] for a in range(0x4002, 0x10000))
    need(codec.decode(0x4002, opaque) == image[2:0xC000], 'Output decode does not match linked image')
    need(sha(executable) == EXPECTED_EXE_SHA and sha(encoded.text) == EXPECTED_HEX_SHA,
         'Packaged EXE or embedded HEX differs from pinned AIR2-P8-FIX1')
    start, end = original_container.start, original_container.end
    need(executable[:start] == original_exe[:start] and executable[end:] == original_exe[end:],
         'Vendor GUI/loader/resource metadata changed outside embedded firmware')
    recipe = {'format': 'c11-windows-reproduction-v1', 'developer': 'Caimankekw',
              'original_size': len(original_exe), 'original_sha256': sha(original_exe),
              'result_sha256': sha(executable), 'hex_resource_range': [start, end],
              'original_hex_sha256': sha(original_container.hex_bytes),
              'result_hex_sha256': sha(encoded.text),
              'edits': [{'offset': a, 'before': original_exe[a:b].hex(), 'after': executable[a:b].hex()}
                        for a, b in spans(i for i, (x, y) in enumerate(zip(original_exe, executable)) if x != y)]}
    recipe_builder = load('standalone_recipe_verify', ROOT / 'tools/rebuild_windows.py')
    rebuilt, reproduction = recipe_builder.rebuild(original_exe, recipe)
    need(rebuilt == executable, 'Independent recipe reconstruction failed')
    sources = sorted(p for folder in ('source', 'tools', 'reference')
                     for p in (ROOT / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    sources.append(Path(__file__).resolve())
    manifest.update({
        'status': 'PASS_STANDALONE_SOURCE_BUILD', 'source_build_not_recipe_replay': True,
        'original_exe_sha256': sha(original_exe), 'output_exe_sha256': sha(executable),
        'output_hex_sha256': sha(encoded.text), 'outside_hex_same_as_original': True,
        'unknown_first_word_opaque_preserved': True, 'runtime_pages_install_erased': True,
        'original_tail_and_configuration_opaque_preserved': True,
        'device_accessed': False, 'device_flashed': False,
        'this_build_establishes_hardware_validation': False,
        'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sources},
        'recipe_reproduction': reproduction,
        'plaintext_file': 'AIR2-P8-FIX1.base4000.partial.bin', 'output_exe_file': EXE_NAME,
        'partial_image_is_not_a_direct_flash_file': True,
    })
    return {'AIR2-P8-FIX1.base4000.partial.bin': image, 'known_mask.bin': mask,
            EXE_NAME: executable, 'manifest.json': json_bytes(manifest),
            'reproduction_recipe.json': json_bytes(recipe)}


def write_outputs(artifacts, out, original_path=None):
    out = Path(out).resolve()
    need(not out.exists() or out.is_dir(), 'Output is not a directory')
    if original_path is not None:
        original_path = Path(original_path).resolve()
    # Validate every output before writing any file. Re-running identical output
    # is allowed; a different existing file is retained and causes a failure.
    for name, data in artifacts.items():
        need(Path(name).name == name, 'Artifact filename escapes output directory')
        path = out / name
        need(path.resolve().parent == out and path.resolve() != original_path, 'Output escapes directory or aliases original EXE')
        need(not path.exists() or path.is_file() and path.read_bytes() == data,
             'Refusing to replace a different existing output: ' + name)
    out.mkdir(parents=True, exist_ok=True)
    for name, data in artifacts.items():
        path = out / name
        if not path.exists():
            with path.open('xb') as handle:
                handle.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, required=True, help='Unmodified official Windows C11 EXE')
    parser.add_argument('--out', type=Path, default=ROOT / 'build')
    parser.add_argument('--verify-only', action='store_true', help='Run the full source build in memory without writing outputs')
    args = parser.parse_args()
    result = prepare(args.original.read_bytes())
    if not args.verify_only:
        write_outputs(result, args.out, args.original)
    manifest = json.loads(result['manifest.json'])
    print(json.dumps({'status': manifest['status'], 'image_sha256': manifest['plaintext_sha256'],
                      'exe_sha256': manifest['output_exe_sha256'], 'device_accessed': False,
                      'output_written': not args.verify_only}, indent=2))


if __name__ == '__main__':
    main()
