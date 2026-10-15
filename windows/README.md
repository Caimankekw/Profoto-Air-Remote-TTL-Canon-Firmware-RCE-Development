# AIR2-P8 Windows wrapper source

[简体中文](README.zh-CN.md) · Copyright (C) 2026 **Caimankekw** · **AGPL-3.0-only**

This directory builds a small NSIS self-extracting wrapper around the frozen AIR2-P8 GUI. It does not patch firmware, implement a flasher, access USB or run the delivered updater/setup. License scope and experimental limitations are in the root LICENSE, NOTICE and bilingual disclaimers.

Project source: [P8 firmware development](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/P8) · [Windows wrapper](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/P8/windows) · [original C11 reverse engineering on main](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/main).

The delivered package includes the exact corresponding source snapshot as `source.zip`. Its SHA256 is recorded in `package_manifest.json`, and `source_manifest.json` inside the archive records each source file. Branches may advance; use that bundled archive to reproduce this particular package rather than assuming the current P8 branch is unchanged.

## Inputs and build

Python 3.9+ uses only the standard library. Supply the exact complete NSIS 3.13 directory, 7-Zip 26.04 x64 `7z.exe` with adjacent `7z.dll`, the AIR2-P8 GUI, original C11 GUI, and the project's final corresponding-source ZIP. [input_manifest.json](input_manifest.json) pins firmware/updater and tools. The source ZIP has a separate required SHA256 argument, one `AirRemote_TTL_C_AIR2_P8/` prefix and `source_manifest.json` covering every other entry.

```powershell
python windows/build_package.py `
  --updater "C:\inputs\AirRemote_TTL_C_C11_AIR2_P8_Caimankekw_EXPERIMENTAL.exe" `
  --original "C:\inputs\Air-Remote-TTL-C-Firmware-C11.exe" `
  --source-archive "C:\inputs\AirRemote_TTL_C_AIR2_P8-source.zip" `
  --source-sha256 "REPLACE_WITH_SOURCE_ARCHIVE_SHA256" `
  --nsis-dir "C:\tools\nsis-3.13" `
  --seven-zip "C:\tools\7zip\7z.exe" `
  --output "C:\output\AIR2-P8-new-build"
```

The destination must not exist. Without `--output`, a new UTC timestamp directory under `windows/build/` is used. Inputs are explicit; the script does not search for a private workspace or download files. It verifies the full NSIS tree, so use the complete unmodified distribution directory.

Create the source ZIP only after this source tree and root documents are final. It includes this directory but excludes `build/`, `dist/`, caches and generated releases. The builder checks each archive entry against its source manifest and compares the archived Windows sources/root license documents with the current files. Do not edit sources between creating the archive and packaging.

## Output and checks

Output includes `Profoto-AirRemote-TTL-C-AIR2-P8-Custom-Updater.exe`, a portable ZIP, extracted payload, logs, SHA256SUMS and `package_verification.json`. The payload contains only P8/original recovery GUIs, corresponding source.zip, user README documents, licenses, disclaimers and manifests. It does not contain HSS-P3 or other firmware versions.

The setup offers English/Chinese disclaimer and AGPL pages, extracts to a new user folder that does not already exist and leaves "open updater" unchecked by default. It does not silently update, install drivers, delete files or add an uninstall flow. The GUI retains the frozen SHA256 `dec0660b9568713d36a13e44909741b2891d30680895f0ef3406a31e9cbebde1`.

The build invokes only the supplied compiler and archive extractor. It verifies PE identity/elevation, source ZIP and portable ZIP bytes, every extracted installer file and the exact extra NSIS plugins. The NSIS result is unsigned; byte-identical outer EXE reproduction is not claimed. Internal updater bytes and all payload files must match exactly. Static checks do not replace hardware or Windows UI testing.

Run offline validation helpers with `python -B windows/test_build_package.py`. `installer.nsi` and the two usage templates are the UI sources; UTF-16 display copies of disclaimer/license text are generated for NSIS while the original UTF-8 documents remain in the payload. Unmodified NSIS licensing text is in `vendor/NSIS-COPYING.txt`.
