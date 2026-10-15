# AIR2-P8-FIX1 Windows updater package

[简体中文](README.zh-CN.md) · Developer: **Caimankekw** · **2026-10-16** · Tag `p8-fix1-20261016`

This is experimental custom firmware for **Air Remote TTL-C (Canon)**, not an official Profoto release. Original custom code is AGPL-3.0-only; vendor firmware and updater retain their own terms. Read [DISCLAIMER](DISCLAIMER.md), [LICENSE](LICENSE) and [NOTICE](NOTICE.md) before use.

**FIX1 has not been booted or camera-tested on hardware.** It fixes AIR1 relative digits remaining visible when their deadline expires during a busy native transaction: the expired deadline is retained until readiness returns, then the relative values are cleared. Radio, persistence and HSS-P3 remain unchanged from P8. Historical P8 hardware results do not validate this new image. See [CHANGELOG](CHANGELOG.md).

Source: [FIX1 firmware and tools](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/p8-fix1-20261016) · [Windows packaging code](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/p8-fix1-20261016/windows). The [main branch](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/main) contains original C11 reverse-engineering material separately.

The included `source.zip` is the exact source snapshot corresponding to this package. Its SHA256 is recorded in `package_manifest.json`; its internal `source_manifest.json` identifies every source file. Use this snapshot for reproduction; the release reference is tag `p8-fix1-20261016`.

## Use

1. Run the setup EXE and choose English or Simplified Chinese. Read the disclaimer and license, then select a new destination folder that does not already exist. It defaults to `%LOCALAPPDATA%\Caimankekw\AirRemote-TTL-C\AIR2-P8-FIX1`. The wrapper does not install drivers or flash a device.
2. Opening the updater on the finish page is optional and **unchecked by default**. Alternatively, open `AirRemote_TTL_C_C11_AIR2_P8_FIX1_Caimankekw_EXPERIMENTAL.exe` from the extracted folder. With the portable ZIP, extract all files first.
3. Connect the intended Air Remote TTL-C and follow the original GUI's instructions. Check the identified device and manually click its update button. Keep the connection until it finishes.
4. Disconnect USB and start normally on batteries. Check startup, buttons and display before camera testing. If it shows `EC!` and the original GUI can still communicate, use `restore_original/Air-Remote-TTL-C-Firmware-C11.exe` to attempt restoring C11. Recovery is not guaranteed.

The original GUI and loader remain unchanged outside the firmware resource. No alternate command-line flasher is included. The outer setup runs with user privileges; any requirements of the original updater remain its own. The modified updater's original vendor signature is invalid; the wrapper is unsigned. This package does not claim manufacturer endorsement.

## FIX1 controls

- **C + HEAD:** switch ABC/DEF pages in TTL and MAN.
- **C + MODEL:** switch AIR1/AIR2 in MAN; TTL consumes the chord without changing the remembered manual subtype. Neither chord should also toggle flash/modeling switches.
- **A/B/plus/minus:** no added chord wait. Native scanning, short/held-key detection and pending radio transactions still limit response. A busy edit can be rejected rather than queued; release and press again.
- AIR1 values appear temporarily only after successful adjustments. If their deadline expires while busy, FIX1 retains that deadline and clears the values when readiness returns. Enabled AIR2 targets stay visible. TTL ABC remains FEC; DEF is manual using the remembered AIR1/AIR2 type, **not six-group automatic TTL**.

After choosing to test this candidate, check AIR1 expiry and busy-to-idle recovery in MAN and TTL DEF, and persistent AIR2 values. Away from the limits, check five short plus presses for +0.5 and five minus presses for −0.5, on both the display and actual light. Check both key combinations, DEF reception and triggering separately. The complete behavior and limitations are documented in `source.zip` under the root README and `C11/`.

## Included files and verification

- Frozen AIR2-P8-FIX1 GUI, original C11 recovery GUI and corresponding `source.zip`.
- English/Chinese README, disclaimers, NOTICE and changelogs, LICENSE and NSIS notices.
- `package_manifest.json` and `SHA256SUMS.txt` record exact extracted bytes.

AIR2-P8-FIX1 updater SHA256: `f19ebc6152539745e456d0d4060a2bca6669f0897e81e9d1ed0f2a96ff1cdfed`.

Expected firmware image SHA256: `a6e6284c2186d557eff9049afa3c66ec78f09406586110702f94baaafacd9ef8`. The partial BIN is a build/research artifact and must not be flashed directly.

The wrapper does not modify this updater or firmware. Packaging checks input hashes, the source archive, PE resources, portable ZIP and the statically extracted NSIS payload; it does not execute the updater or setup or access USB. Offline checks do not establish hardware startup, RF reception or photographic performance. The completed package's report records which checks passed.

To rebuild the wrapper, extract `source.zip` and follow `windows/README.md`. No Python is needed to use the delivered updater. The full corresponding source is included; original tools and firmware-derived inputs keep their respective rights. The wrapper uses unmodified NSIS 3.13 components; see `NSIS-COPYING.txt` and [NSIS source](https://sourceforge.net/projects/nsis/files/NSIS%203/3.13/).
