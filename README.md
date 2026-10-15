# Air Remote TTL-C · AIR2-P8-FIX1

English | [简体中文](README.zh-CN.md)

Developer: [Caimankekw](https://github.com/Caimankekw) · Authored code: [AGPL-3.0-only](LICENSE)

Unofficial experimental firmware for **Profoto Air Remote TTL-C (Canon), C11**. This reverse-engineering and binary-patch project builds AIR2-P8-FIX1 from source and places it in the original C11 graphical updater. It is not the manufacturer's complete C source and is not for Connect, Connect Pro or other camera-mount versions.

**FIX1 has not been booted or tested with a camera on hardware.** It is a separate fix candidate based on AIR2-P8; the earlier P8 files and release remain historical artifacts. Existing P8 users must download the new FIX1 updater, read the [disclaimer](DISCLAIMER.md), and manually perform the update in its GUI. Downloading or extracting the package does not update the device.

This is the **P8 development branch** of [Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development). The [main branch](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/main) contains analysis of the unmodified C11 firmware and offline analysis tools. The release tag is `p8-fix1-20261016`; see [Releases](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/releases) for packages, the exact source commit and hashes, and [CHANGELOG](CHANGELOG.md) for the [earlier P8 release](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/releases/tag/p8-20261015).

## FIX1 change

When AIR1 relative values expired during a radio transaction, camera-mode request or legacy transmit operation, P8 cleared the native display deadline before discovering the busy condition. Deferred cleanup then had no deadline left to retry, so digits could remain visible. FIX1 retains the already-expired deadline while busy and clears the six-group relative values once readiness returns. Readiness is checked once; consuming the deadline and clearing the values share one successful path.

No RAM or timing period is added. AIR2 persistent digits, TTL ABC exposure compensation, targets, switches and page/mode memory retain their existing implementation. The radio and persistence components and protected HSS-P3 intervals remain byte-identical to P8.

## Features and controls

- MAN-AIR1: relative power control; numbers appear temporarily after adjustment.
- MAN-AIR2: absolute targets; enabled groups on the current page remain visible.
- **C + HEAD**: change ABC / DEF pages in TTL or either manual mode.
- **C + MODEL**: switch AIR1 / AIR2 in MAN; ignored in TTL without changing the remembered manual type.
- A, B, plus and minus retain normal short/long-press paths and bypass the chord window.
- MODE toggles TTL / MAN and restores the last manual type.
- ALL affects six groups; six AIR2 targets, Head/Model switches, page and mode are remembered.
- The existing HSS-P3 runtime paths are retained.

**In TTL, ABC uses exposure compensation and DEF uses the remembered manual type. This is not six-group automatic TTL.** The fixed LCD ABC letters cannot become DEF; the DEF page hides them and briefly shows d/E/F when selected.

Only C, HEAD and MODEL wait for chord recognition, so individual actions may be delayed; release both keys after a chord. The former plus/minus and A-minus shortcuts are removed and follow native single-key priority. Synchronous sending, saving and scanning still limit input speed. Busy-state user actions may be rejected rather than queued.

AIR2 targets span 0.1–10.0, but a light may have a higher minimum output. Displayed targets are requests, not live light feedback. DEF defaults to disabled at 5.0 on first installation or old-record migration. Reinstallation may reset added settings.

## Layout

| Path | Contents |
| --- | --- |
| [C11](C11/README.md) | Compact original-firmware analysis and recovered logic |
| [source](source/README.md) | UI, six-group radio, persistence, HSS patches and linker |
| `tools/` | Container, codec, disassembly, reproduction and source packaging tools |
| [reference](reference/README.md) | Generic address-transform parameters and fingerprints; no device backup |
| [windows](windows/README.md) | Windows self-extracting package build source |
| [tests](tests/README.md) | Standalone build checks and separated FIX1/P8 verification records |
| [inputs](inputs/README.md) | Required user-supplied vendor input; vendor EXE excluded from source archive |

## Build from source

Use Python **3.9 or newer**. Firmware building uses only the standard library and needs no previous development workspace or intermediate release. Supply the unmodified `Air-Remote-TTL-C-Firmware-C11.exe` and run from this project root:

```powershell
python -B build.py --original "inputs\Air-Remote-TTL-C-Firmware-C11.exe"
python -I -B tests/test_build.py --original "inputs\Air-Remote-TTL-C-Firmware-C11.exe" -v
python -I -B tests/test_isolated_build.py --original "inputs\Air-Remote-TTL-C-Firmware-C11.exe"
python -B tools/package_source.py
```

The required original EXE SHA-256 is `e56b19080bd6330a5461dd4e3d614fc6d81dcc533e945e6090e7db63824bc240`.

The build decodes that input, executes the HSS/AIR2 source generators, links the result, checks CRC/encoding and writes `build/`. It never runs an updater or accesses USB. The source archive excludes the vendor EXE; the unchanged recovery EXE in the Windows package can serve as this input.

| Frozen firmware output | SHA-256 |
| --- | --- |
| `AIR2-P8-FIX1.base4000.partial.bin` | `a6e6284c2186d557eff9049afa3c66ec78f09406586110702f94baaafacd9ef8` |
| `AirRemote_TTL_C_C11_AIR2_P8_FIX1_Caimankekw_EXPERIMENTAL.exe` | `f19ebc6152539745e456d0d4060a2bca6669f0897e81e9d1ed0f2a96ff1cdfed` |

The first two plaintext bytes of the analysis BIN remain unknown: **do not flash the partial BIN directly**. Use the graphical EXE updater. Reconstruction preserves the vendor GUI, loader, opaque first word, sparse layout and tail. Modifying its firmware resource invalidates the original signature.

## Windows packages

The release provides:

- `Profoto-AirRemote-TTL-C-AIR2-P8-FIX1-Custom-Updater.exe`: the NSIS self-extracting wrapper.
- `AirRemote-TTL-C-AIR2-P8-FIX1-Windows-portable.zip`: the portable Windows package.
- `Profoto-AirRemote-TTL-C-AIR2-P8-FIX1-Source.zip`: the corresponding integrated source archive.

The Windows packages include the custom GUI updater, unchanged original recovery GUI, corresponding source, bilingual instructions, license and disclaimers. The NSIS wrapper extracts to a user directory; its finish page can optionally open the GUI. **Firmware writing requires a manual action in the updater.** Using the packages needs no Python. Building the wrapper needs NSIS and 7-Zip; see [Windows build instructions](windows/README.md).

This source archive includes the integrated repository documentation, the complete `C11/`, `windows/` and `inputs/` source/documentation directories, and `.gitignore` / `.gitattributes`; the vendor EXE remains excluded. It differs from the earlier frozen FIX1 input source ZIP, whose SHA-256 is `14649a975625fc3ed72b5ac0a9237ad5b622e76905fa0b831404c34962728141`. That hash identifies the input archive, not this release attachment. Release checksums identify the new attachments; the firmware hashes above remain fixed.

## Verification scope

The frozen FIX1 report records 77 actual native deadline cases, including 24 frozen-P8 failure controls, busy-to-idle recovery, a late busy change after the readiness check, wraparound and AIR2 negative controls. It also records UI 470, radio 1,944, persistence 717 and integration 333 regression cases, plus 13 source-build, 13 container and 7 reference-codec checks and an isolated rebuild. [tests/VERIFICATION.json](tests/VERIFICATION.json) preserves this report separately from the historical P8 result.

PIC18 replay uses bounded clock, UART, Flash and LCD models. These checks do not establish device boot, physical key-rate capacity, RF reception, exposure, power-loss behavior or new physical HSS measurements. Full behavioral replay requires the original development workspace; the compact source package supplies independent build and container tests.

After a manual update, check AIR1 expiry in MAN and TTL DEF, persistent AIR2 digits, five plus taps adding 0.5 and five minus taps restoring it, both chords leaving Head/Model switches unchanged, and settings/mode surviving reboot. Check the display and actual light behavior separately. The original recovery GUI does not guarantee recovery.

Read the [disclaimer](DISCLAIMER.md), [license scope](NOTICE.md) and [LICENSE](LICENSE) before use. AGPL-3.0-only covers the developer's original work; it does not wholly relicense vendor firmware, the updater or mixed binaries.
