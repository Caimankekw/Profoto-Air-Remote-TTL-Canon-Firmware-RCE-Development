# Profoto Air Remote TTL Canon Firmware RCE Development

[简体中文](README.zh-CN.md) | Developer: **Caimankekw**

`main` contains research notes and offline inspection tools for the **unmodified Air Remote TTL-C C11 application**. It contains no firmware image, updater executable, device capture, USB writer or AIR2 patch generator. Studying an unmodified program does not mean that all of its source code has been recovered: the annotated logic is partial, manually reconstructed and deliberately non-buildable.

| Location | Purpose |
|---|---|
| `main` | Original C11 analysis, address index and reproducible numeric PIC18 listing tool |
| [P8 branch](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/P8) | AIR2-P8 experimental development source, verification and Windows packaging |
| [Releases](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/releases) | Separately published AIR2-P8 experimental packages; follow the matching P8 documentation |

AIR2-P8 is an unofficial modification. Offline checks do not establish complete hardware compatibility, radio timing or optical HSS performance. `main` has no installation or flashing procedure. See the [disclaimer](DISCLAIMER.md).

## Inspect original C11

Use Python **3.9 or newer**, with its standard library; no `pip` packages, Ghidra or compiler are required. Supply your own original Windows C11 updater as described in [inputs/README.md](inputs/README.md). The tool reads the EXE as data and does not execute it or connect to a device.

From the repository root:

```powershell
python -I -B tools/disassemble.py --original "C:\path\to\Air-Remote-TTL-C-Firmware-C11.exe" --out build/original_C11.listing.txt
python -I -B -m unittest discover -s tests -p test_reference_codec.py
```

The supported updater must have SHA-256 `e56b19080bd6330a5461dd4e3d614fc6d81dcc533e945e6090e7db63824bc240` and size **3,938,448 bytes**. Other inputs are rejected. The default listing interval is `[0x4002, 0x9780)` in PIC18 **byte addresses**; optional `--start` and `--end` accept even bounds within `[0x4002, 0x10000]`. An existing different output file is not overwritten.

The listing is a linear instruction-candidate view, not proof of code reachability or a full code/data separation. The first plaintext word at `0x4000–0x4001` remains unknown and is excluded. The codec's confirmed address range and original-only tail reconstruction are explained in [reference/README.md](reference/README.md).

## Contents

- [C11/](C11/README.md): original key scanner, TTL/MAN banks, radio request interface, camera/HSS boundaries and settings index; the C-like explanation is not manufacturer source.
- `tools/`: four standard-library modules for strict original-container parsing, byte transformation and candidate disassembly. The documented entry point only writes the requested text listing.
- [reference/](reference/README.md): derived address-transform parameters, format manifest and prior equivalence evidence. These are not a device backup or a firmware image.
- `tests/`: codec self-checks that need no vendor executable or device.

The six-file runtime dependency closure is the four files in `tools/`, `reference/codec_manifest.json` and `reference/c11_offset_transform.bin`. Keep `tools/` and `reference/` as siblings. The generic codec/container modules also expose in-memory transformation helpers; no P8 hooks, policy patches or firmware-building entry point are included here.

## Rights

Caimankekw's original explanations, tools and tests are licensed under [AGPL-3.0-only](LICENSE). Original firmware, recovered original instructions, manufacturer resources and third-party material retain their respective rights; this project does not relicense them. See [NOTICE.md](NOTICE.md). No official affiliation, approval or warranty is implied.
