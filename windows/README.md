# AIR2-P8-FIX1 Windows wrapper source

[简体中文](README.zh-CN.md) · Copyright (C) 2026 **Caimankekw** · Authored code **AGPL-3.0-only** · **2026-10-16** · Tag `p8-fix1-20261016`

This directory builds a small NSIS self-extracting wrapper around the frozen AIR2-P8-FIX1 GUI. It does not patch firmware, implement a flasher, access USB or run the delivered updater/setup. License scope and experimental limitations are in the root LICENSE, NOTICE and bilingual disclaimers.

FIX1 retains an already-expired AIR1 display deadline while the native transaction is busy, allowing relative values to clear when readiness returns. Radio, persistence and HSS-P3 implementation remain unchanged from P8. **FIX1 has not been booted or camera-tested on hardware.** Historical P8 testing is not validation of this image.

Project source: [FIX1 release source](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/p8-fix1-20261016) · [Windows wrapper](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/p8-fix1-20261016/windows) · [original C11 reverse engineering on main](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/main).

The delivered package includes the exact corresponding source snapshot as `source.zip`. Its SHA256 is recorded in `package_manifest.json`, and `source_manifest.json` inside the archive records each source file. Use that bundled archive to reproduce this particular package; the release reference is tag `p8-fix1-20261016`.

## Inputs and build

Python 3.9+ uses only the standard library. Supply the exact complete NSIS 3.13 directory, 7-Zip 26.04 x64 `7z.exe` with adjacent `7z.dll`, the AIR2-P8-FIX1 GUI, original C11 GUI, and the project's final corresponding-source ZIP. [input_manifest.json](input_manifest.json) pins the updater and tools and records the expected firmware-image identity. The source ZIP has a separate required SHA256 argument, one `AirRemote_TTL_C_AIR2_P8_FIX1/` prefix and a `source_manifest.json` with name `AIR2-P8-FIX1` covering every other entry.

```powershell
python windows/build_package.py `
  --updater "C:\inputs\AirRemote_TTL_C_C11_AIR2_P8_FIX1_Caimankekw_EXPERIMENTAL.exe" `
  --original "C:\inputs\Air-Remote-TTL-C-Firmware-C11.exe" `
  --source-archive "C:\inputs\Profoto-AirRemote-TTL-C-AIR2-P8-FIX1-Source.zip" `
  --source-sha256 "REPLACE_WITH_SOURCE_ARCHIVE_SHA256" `
  --nsis-dir "C:\tools\nsis-3.13" `
  --seven-zip "C:\tools\7zip\7z.exe" `
  --output "C:\output\AIR2-P8-FIX1-new-build"
```

The destination must not exist. Without `--output`, a new UTC timestamp directory under `windows/build/` is used. Inputs are explicit; the script does not search for a private workspace or download files. It verifies the full NSIS tree, so use the complete unmodified distribution directory.

Create the source ZIP only after this source tree and root documents are final. It includes this directory but excludes `build/`, `dist/`, caches and generated releases. The builder checks each archive entry against its source manifest and compares the archived Windows sources/root license documents with the current files. Do not edit sources between creating the archive and packaging.

## Output and checks

Output includes `Profoto-AirRemote-TTL-C-AIR2-P8-FIX1-Custom-Updater.exe`, `AirRemote-TTL-C-AIR2-P8-FIX1-Windows-portable.zip`, extracted payload, logs, SHA256SUMS and `package_verification.json`. The payload contains the FIX1/original recovery GUIs, corresponding source.zip, user README documents, LICENSE, bilingual NOTICE, disclaimers, changelogs and manifests. No standalone HSS-P3 updater is included; the FIX1 image retains the existing HSS-P3 implementation.

The setup offers English/Chinese disclaimer and AGPL pages, extracts to a new user folder that does not already exist and leaves "open updater" unchecked by default. It does not silently update, install drivers, delete files or add an uninstall flow. The GUI retains the frozen SHA256 `f19ebc6152539745e456d0d4060a2bca6669f0897e81e9d1ed0f2a96ff1cdfed`.

The expected firmware image SHA256 is `a6e6284c2186d557eff9049afa3c66ec78f09406586110702f94baaafacd9ef8`. This builder verifies the frozen complete updater EXE; it does not rebuild, extract for flashing or independently replay the image.

The build invokes only the supplied compiler and archive extractor. It verifies PE identity/elevation, source ZIP and portable ZIP bytes, every extracted installer file and the exact extra NSIS plugins. The NSIS result is unsigned; byte-identical outer EXE reproduction is not claimed. Internal updater bytes and all payload files must match exactly. Static checks do not replace hardware or Windows UI testing.

Run offline validation helpers with `python -B windows/test_build_package.py`. `installer.nsi` and the two usage templates are the UI sources; UTF-16 display copies of disclaimer/license text are generated for NSIS while the original UTF-8 documents remain in the payload. Unmodified NSIS licensing text is in `vendor/NSIS-COPYING.txt`.
