# AIR2-P8 Windows updater package

[简体中文](README.zh-CN.md) · Developer: **Caimankekw**

This is experimental custom firmware for **Air Remote TTL-C (Canon)**, not an official Profoto release. Original custom code is AGPL-3.0-only; vendor firmware and updater retain their own terms. Read [DISCLAIMER](DISCLAIMER.md), [LICENSE](LICENSE) and [NOTICE](NOTICE.md) before use.

Source: [P8 firmware and tools](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/P8) · [Windows packaging code](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/P8/windows). The [main branch](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/main) contains original C11 reverse-engineering material separately.

The included `source.zip` is the exact source snapshot corresponding to this package. Its SHA256 is recorded in `package_manifest.json`; its internal `source_manifest.json` identifies every source file. Use this snapshot for reproduction, since the online P8 branch may receive later changes.

## Use

1. Run the setup EXE and choose English or Simplified Chinese. Read the disclaimer and license, then select a new destination folder that does not already exist. It defaults to `%LOCALAPPDATA%\Caimankekw\AirRemote-TTL-C\AIR2-P8`. The wrapper does not install drivers or flash a device.
2. Opening the updater on the finish page is optional and **unchecked by default**. Alternatively, open `AirRemote_TTL_C_C11_AIR2_P8_Caimankekw_EXPERIMENTAL.exe` from the extracted folder. With the portable ZIP, extract all files first.
3. Connect the intended Air Remote TTL-C and follow the original GUI's instructions. Check the identified device and manually click its update button. Keep the connection until it finishes.
4. Disconnect USB and start normally on batteries. Check startup, buttons and display before camera testing. If it shows `EC!`, use `restore_original/Air-Remote-TTL-C-Firmware-C11.exe` through its original GUI to restore C11.

The original GUI and loader remain unchanged outside the firmware resource. No alternate command-line flasher is included. The outer setup runs with user privileges; any requirements of the original updater remain its own. This package does not claim an official signature or manufacturer endorsement.

## P8 controls

- **C + HEAD:** switch ABC/DEF pages in TTL and MAN.
- **C + MODEL:** switch AIR1/AIR2 in MAN; TTL consumes the chord without changing the remembered manual subtype. Neither chord should also toggle flash/modeling switches.
- **A/B/plus/minus:** no added chord wait. Native scanning, short/held-key detection and pending radio transactions still limit response. A busy edit can be rejected rather than queued; release and press again.
- AIR1 values appear temporarily only after successful adjustments and clear after idle. Enabled AIR2 targets stay visible. TTL ABC remains FEC; DEF is manual using the remembered AIR1/AIR2 type, **not six-group automatic TTL**.

Away from the limits, check five short plus presses for +0.5 and five minus presses for −0.5, on both the display and actual light. Check DEF reception and triggering separately. The complete behavior and limitations are documented in `source.zip` under the root README and `C11/`.

## Included files and verification

- Frozen AIR2-P8 GUI, original C11 recovery GUI and corresponding `source.zip`.
- English/Chinese README and disclaimers, LICENSE, NOTICE and NSIS notices.
- `package_manifest.json` and `SHA256SUMS.txt` record exact extracted bytes.

AIR2-P8 updater SHA256: `dec0660b9568713d36a13e44909741b2891d30680895f0ef3406a31e9cbebde1`.

The wrapper does not modify this updater or firmware. Packaging checks input hashes, the source archive, PE resources, portable ZIP and the statically extracted NSIS payload; it does not execute the updater or setup or access USB. Offline checks do not establish hardware startup, RF reception or photographic performance. The completed package's report records which checks passed.

To rebuild the wrapper, extract `source.zip` and follow `windows/README.md`. No Python is needed to use the delivered updater. The full corresponding source is included; original tools and firmware-derived inputs keep their respective rights. The wrapper uses unmodified NSIS 3.13 components; see `NSIS-COPYING.txt` and [NSIS source](https://sourceforge.net/projects/nsis/files/NSIS%203/3.13/).
