# Air Remote TTL-C · AIR2-P8

English | [简体中文](README.zh-CN.md)

Developer: [Caimankekw](https://github.com/Caimankekw) · Authored code: [AGPL-3.0-only](LICENSE)

Unofficial experimental firmware for **Profoto Air Remote TTL-C (Canon), C11**. This project builds AIR2-P8 from source and places it in the original C11 graphical updater. It is a reverse-engineering and binary-patch project, not the manufacturer's complete C source. It is not for Connect, Connect Pro, or other camera-mount versions.

Following the B10 REV5 release layout, the compact source project and Windows distribution are prepared separately. No previous development workspace or intermediate firmware release is required to build this version.

This is the **P8 development branch** of [Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development). The [main branch](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/main) contains analysis of the unmodified C11 firmware and offline analysis tools only. Download the Windows package and corresponding source from [Releases](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/releases). Release notes identify the exact source commit and file hashes.

## Features and controls

- MAN-AIR1: relative power control; numbers appear temporarily after an adjustment.
- MAN-AIR2: control lights using the displayed absolute targets; enabled groups on the current page remain visible.
- **C+HEAD**: change ABC / DEF pages in TTL or either manual mode.
- **C+MODEL**: switch AIR1 / AIR2 in MAN; ignored in TTL without changing the remembered manual type.
- A, B, plus and minus bypass the chord window and retain normal short/long-press steps.
- MODE toggles TTL / MAN and restores the last manual type.
- ALL affects six groups; six AIR2 targets, Head/Model switches, page and mode are remembered.
- The existing HSS-P3 runtime paths are retained.

**In TTL, ABC uses exposure compensation and DEF uses the remembered manual type. This is not six-group automatic TTL.** The fixed LCD ABC letters cannot become DEF; the DEF page hides them and briefly shows d/E/F when selected.

Only C, HEAD and MODEL wait for chord recognition. Their individual actions may therefore be delayed; release both keys after a chord. The former plus/minus and A-minus shortcuts are removed and follow native single-key priority. Synchronous sending, saving and scanning still limit input speed. Busy-state actions may be rejected rather than queued for later execution.

AIR2 targets span 0.1–10.0, but a light may have a higher minimum output. Displayed values are remote targets, not live feedback from the lights. DEF defaults to disabled at 5.0 on first installation or old-record migration. Reinstallation may reset added settings.

## Layout

| Path | Contents |
| --- | --- |
| [C11](C11/README.md) | Compact original-firmware analysis and recovered logic |
| `source/` | UI, six-group radio, persistence, HSS patches and linker |
| `tools/` | Container, codec, disassembly, reproduction and source packaging tools |
| `reference/` | Generic address transformation parameters and fingerprints; no device backup |
| [windows](windows/README.md) | Windows self-extracting package build source |
| `tests/` | Standalone build and input-boundary checks |
| [inputs](inputs/README.md) | Required user-supplied vendor input; vendor EXE excluded from source archive |

## Build from source

Use Python **3.9 or newer**. Firmware building needs only the standard library. Obtain the original `Air-Remote-TTL-C-Firmware-C11.exe` and run from this project root:

```powershell
python -B build.py --original "inputs\Air-Remote-TTL-C-Firmware-C11.exe"
```

The required original EXE SHA-256 is:

```text
e56b19080bd6330a5461dd4e3d614fc6d81dcc533e945e6090e7db63824bc240
```

The build decodes the original EXE, executes the HSS/AIR2 source generators, links the result, checks CRC/encoding and writes `build/`. It never runs an updater or accesses USB. The source archive excludes the original EXE; the unmodified recovery EXE in the Windows package can serve as this input.

This release must reproduce these frozen files:

```text
AIR2-P8.base4000.partial.bin
337120c7ed51954f4cdf0e60816e0289583a3c6b4ad400504d0cbef0a259f185

AirRemote_TTL_C_C11_AIR2_P8_Caimankekw_EXPERIMENTAL.exe
dec0660b9568713d36a13e44909741b2891d30680895f0ef3406a31e9cbebde1
```

The first two plaintext bytes of the analysis BIN remain unknown: **do not flash it directly**. Use the graphical EXE updater. Reconstruction retains the vendor GUI, loader, opaque first word and sparse tail. Modifying its firmware resource invalidates the original signature.

## Windows distribution

`Profoto-AirRemote-TTL-C-AIR2-P8-Custom-Updater.exe` follows REV5's NSIS self-extracting format. It contains the current updater, original recovery updater, bilingual instructions, license, disclaimers and corresponding source archive. The wrapper extracts to a user directory; its finish page can optionally open the GUI. Firmware writing still requires an action in the updater.

Using the package does not require Python. Building the wrapper needs NSIS and 7-Zip; see the [Windows build instructions](windows/README.md) for pinned versions and commands. Run `python -B tools/package_source.py` to create the source archive under `dist/`.

## Verification scope

The frozen P8 image passed 470 UI, 1,944 radio, 717 persistence, 333 integration and 966,339 HSS offline cases, plus 576 HSS sequences. This compact project additionally checks source reconstruction, container round trips, frozen output fingerprints and extracted installer contents. These do not replace device boot, RF delivery, exposure or power-loss tests.

After installation, first check five plus taps add 0.5 and five minus taps restore it, both chords leave Head/Model switches unchanged, and settings/mode survive a reboot. Check the display and actual light behavior separately. If needed, use the bundled original recovery GUI; its presence does not guarantee recovery.

Read the [English disclaimer](DISCLAIMER.md) or [中文免责声明](DISCLAIMER.zh-CN.md) before use. [NOTICE](NOTICE.md) separates authored work from vendor and third-party material; the mixed binaries are not wholly relicensed under AGPL.
