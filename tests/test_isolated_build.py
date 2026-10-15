# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Copy the minimal source closure to a fresh directory, build under Python -I.

An audit hook rejects file access outside the copy, explicit official input,
and Python's installation. Scratch directories are retained; no cleanup/delete.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
IMAGE_SHA = 'a6e6284c2186d557eff9049afa3c66ec78f09406586110702f94baaafacd9ef8'
EXE_SHA = 'f19ebc6152539745e456d0d4060a2bca6669f0897e81e9d1ed0f2a96ff1cdfed'
DRIVER = r'''
import os, pathlib, runpy, sys
root = pathlib.Path(sys.argv[1]).resolve()
original = pathlib.Path(sys.argv[2]).resolve()
python_root = pathlib.Path(sys.base_prefix).resolve()
def inside(path, base):
    return path == base or base in path.parents
def audit(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = pathlib.Path(os.fsdecode(args[0])).resolve()
        if not (inside(path, root) or path == original or inside(path, python_root)):
            raise RuntimeError('Outside isolated closure: ' + str(path))
sys.addaudithook(audit)
sys.argv = [str(root / 'build.py'), '--original', str(original), '--out', str(root / 'output')]
runpy.run_path(str(root / 'build.py'), run_name='__main__')
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    original = args.original.resolve()
    # Only these authored source/parameter folders are copied. No workspace,
    # vendor binary, generated recipe/image, historical P1/P3 or test reports.
    isolated = Path(tempfile.mkdtemp(prefix='air2_p8_isolated_'))
    shutil.copy2(ROOT / 'build.py', isolated / 'build.py')
    copied = ['build.py']
    for directory in ('source', 'tools', 'reference'):
        for path in (ROOT / directory).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                relative = path.relative_to(ROOT)
                target = isolated / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                copied.append(relative.as_posix())
    result = subprocess.run([sys.executable, '-I', '-B', '-c', DRIVER,
                             str(isolated), str(original)], cwd=isolated,
                            capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stdout + '\n' + result.stderr)
    image = (isolated / 'output/AIR2-P8-FIX1.base4000.partial.bin').read_bytes()
    exe = (isolated / 'output/AirRemote_TTL_C_C11_AIR2_P8_FIX1_Caimankekw_EXPERIMENTAL.exe').read_bytes()
    if sha(image) != IMAGE_SHA or sha(exe) != EXE_SHA:
        raise RuntimeError('Isolated output differs from pinned P8-FIX1')
    report = {'status': 'PASS_ISOLATED_SOURCE_BUILD', 'python_isolated_flag': True,
              'file_access_guard_active': True, 'workspace_dependency': False,
              'image_sha256': sha(image), 'exe_sha256': sha(exe),
              'external_inputs': ['explicit official C11 EXE'],
              'copied_files': sorted(copied), 'device_accessed': False,
              'scratch_retained': True}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_bytes((json.dumps(report, indent=2) + '\n').encode('utf-8'))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
