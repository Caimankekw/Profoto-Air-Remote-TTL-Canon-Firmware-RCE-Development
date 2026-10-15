# Changelog

English | [简体中文](CHANGELOG.zh-CN.md)

## 2026-10-16 · AIR2-P8-FIX1

Release tag: `p8-fix1-20261016`. Developer: Caimankekw.

- Fixed AIR1 relative-value expiry when a radio transaction, camera-mode request or legacy transmit operation is busy. The expired native deadline is retained until readiness returns; deadline consumption and six-group cleanup then complete together after one readiness check.
- Added no RAM or timing period. AIR2 persistent targets, TTL ABC exposure compensation, six-group state and page/mode memory retain their implementation. Radio and persistence components and protected HSS-P3 intervals remain byte-identical to P8.
- Frozen offline evidence records 77 native deadline cases, including 24 P8 failure controls; UI 470, radio 1,944, persistence 717 and integration 333 regression cases; 13 build, 13 container and 7 codec checks; and an isolated source rebuild. See [verification](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/blob/p8-fix1-20261016/tests/VERIFICATION.json) for the copied FIX1 report and separately preserved P8 history.
- Integrated the Windows NSIS wrapper, portable ZIP, corresponding source, C11 original-firmware analysis and bilingual documentation. The release source ZIP differs from the earlier frozen FIX1 input ZIP; firmware and updater hashes remain fixed.
- **FIX1 has not been booted or tested with a camera on hardware.** Bounded offline replay does not establish RF reception, exposure, physical key-rate capacity or new HSS measurements. Existing P8 users must download the FIX1 updater, read the [disclaimer](DISCLAIMER.md), and update manually in the GUI.

Firmware SHA-256: `a6e6284c2186d557eff9049afa3c66ec78f09406586110702f94baaafacd9ef8`.

GUI updater SHA-256: `f19ebc6152539745e456d0d4060a2bca6669f0897e81e9d1ed0f2a96ff1cdfed`.

## 2026-10-15 · AIR2-P8

Historical release: [p8-20261015](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/releases/tag/p8-20261015).

- Published the P8 six-group AIR1/AIR2 development source and Windows packages, including C + HEAD page switching, C + MODEL manual-type switching, remembered targets/switches/page/mode and existing HSS-P3 paths.
- Historical offline evidence covered UI 470, radio 1,944, persistence 717, integration 333, HSS 966,339 cases and 576 HSS sequences. These HSS totals are historical P8 evidence, not a newly executed FIX1 suite.
- The old standalone verification report is retained under `historical_p8` in [tests/VERIFICATION.json](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/blob/p8-fix1-20261016/tests/VERIFICATION.json); its P8 hashes and source inventory do not describe the new FIX1 release.

Historical firmware SHA-256: `337120c7ed51954f4cdf0e60816e0289583a3c6b4ad400504d0cbef0a259f185`.

Historical GUI updater SHA-256: `dec0660b9568713d36a13e44909741b2891d30680895f0ef3406a31e9cbebde1`.

The same verification record is included in the bundled Source.zip at tests/VERIFICATION.json.
