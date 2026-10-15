# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Caimankekw
"""Generate a bounded numeric original-C11 PIC18 listing from the official EXE."""
import argparse
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--start', type=lambda x: int(x, 0), default=0x4002)
    parser.add_argument('--end', type=lambda x: int(x, 0), default=0x9780)
    args = parser.parse_args()
    if not (0x4002 <= args.start < args.end <= 0x10000) or args.start % 2 or args.end % 2:
        raise ValueError('Require aligned bounds within recovered 0x4002..0x10000')
    if args.out.resolve() == args.original.resolve():
        raise ValueError('Listing output must not replace the original EXE')
    container = load('listing_container', 'container.py').Container(args.original.read_bytes())
    codec = load('listing_codec', 'reference_codec.py').ReferenceCodec()
    plain, mask = codec.decode_original(container.hex.memory)
    decoder = load('listing_decoder', 'pic18_listing.py')
    lines = ['; Original C11 numeric PIC18 linear listing; not vendor C source.',
             '; First word 0x4000..0x4001 is unknown and excluded.',
             '; Linear decoding does not prove code/data separation or reachable behavior.']
    regions = [(0x400A, 0x40A6, 'original header/padding; not opcode-decoded'),
               (0x9746, 0x974E, 'startup initializer data; not opcode-decoded')]
    lines += [decoder.format_row(row) for row in decoder.listing(
        plain, mask, args.start, args.end, data_regions=regions)]
    data = ('\n'.join(lines) + '\n').encode('utf-8')
    if args.out.exists() and args.out.read_bytes() != data:
        raise ValueError('Refusing to replace an existing different listing')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if not args.out.exists():
        with args.out.open('xb') as handle:
            handle.write(data)
    print('Original C11 listing generated: %d bytes; no device accessed.' % len(data))


if __name__ == '__main__':
    main()
