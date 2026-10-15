#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Download three exact public release assets; verify pins before packaging."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from build_package import ROOT, digest, need, parse_json, safe_path, validate_profile, verify_file


def fetch(directory, repository, tag, asset):
    need(len(safe_path(asset).parts) == 1 and not any(c in asset for c in '*?[]'), 'Invalid exact asset name')
    target = directory / asset
    need(not target.exists(), 'Input asset already exists; use a new directory')
    subprocess.run(['gh', 'release', 'download', tag, '--repo', repository,
                    '--pattern', asset, '--dir', str(directory)], check=True)
    need(target.is_file() and not target.is_symlink(), 'Download did not produce a regular file')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, default=ROOT / 'macos/model.json')
    parser.add_argument('--source-asset', required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--github-env', type=Path)
    args = parser.parse_args()
    profile = validate_profile(parse_json(args.profile.read_bytes()))
    digest(args.source_sha256)
    directory = args.directory.resolve()
    need(not directory.exists(), 'Input directory must be new')
    directory.mkdir(parents=True)
    repo, tag = profile['release_repository'], profile['release_tag']
    original = fetch(directory, repo, tag, profile['original']['asset'])
    verify_file(original, profile['original'])
    windows = profile['windows']
    package = fetch(directory, windows.get('repository', repo), windows.get('tag', tag), windows['asset'])
    verify_file(package, windows)
    source = fetch(directory, repo, tag, args.source_asset)
    verify_file(source, {'sha256': args.source_sha256})
    paths = {'STOCK_MACZIP': str(original), 'WINDOWS_PACKAGE': str(package), 'SOURCE_ARCHIVE': str(source)}
    if args.github_env:
        need(str(args.github_env) == os.environ.get('GITHUB_ENV'), 'Only write the runner-provided environment file')
        with args.github_env.open('a', encoding='utf-8') as handle:
            for key, value in paths.items():
                need('\n' not in value and '\r' not in value, 'Invalid environment value')
                handle.write(key + '=' + value + '\n')
    print(json.dumps({'status': 'PASS', 'assets': [x.name for x in (original, package, source)]}, indent=2))


if __name__ == '__main__':
    main()
