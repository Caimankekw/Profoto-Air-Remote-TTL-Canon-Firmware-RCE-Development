# AIR2-P8-FIX1 build sources

English | [简体中文](README.zh-CN.md)

Caimankekw's authored PIC18 patch assemblers and linker are licensed under AGPL-3.0-only. These are not Profoto's original C source or a replacement for the complete vendor application. Vendor instructions and other third-party material retain their rights; see [NOTICE](../NOTICE.md). Build commands are in the [repository README](../README.md).

| File | Responsibility |
| --- | --- |
| `hss_patch.py` | Build the existing HSS adapter from source and original C11 arithmetic bytes. |
| `ui_patch.py` | Six-group UI, key handling and FIX1 transactional AIR1 idle expiry. |
| `radio_patch.py` | Canonical six-group target/switch command construction. |
| `persistence_patch.py` | V4 settings journal and migration of earlier record formats. |
| `linker.py` | Resolve component calls in two passes; protect HSS/native ranges and reserved NVM pages. |
| `PROVENANCE.json` | Authored source hashes and portability edits. |

FIX1 retains an expired native AIR1 deadline while busy, then consumes it and clears all six relative values on one successful readiness path. It adds no RAM or timing period. Radio and persistence component bytes and protected HSS-P3 intervals remain unchanged.

`build.py` reads only the explicitly supplied official C11 EXE plus files in this repository. It decodes the supported application area with `reference/`, builds HSS-P1 and its corrected header checksum from source, then links P8-FIX1 components. No prebuilt P1/P3 image, P3 updater, device backup, recovery capture or frozen P8 patch recipe is used as input. The recipe is generated **after** the source build and replayed independently as a packaging check.

Frozen output hashes are mandatory release guards. Source edits that change the output fail those guards; publishing another revision requires independent validation and new expected hashes. Successful reproduction does not establish hardware, RF or timing compatibility. FIX1 has not been booted or tested with a camera on hardware.

The partial BIN has unknown first-word placeholders and is **not a direct flash file**. Packaging preserves the original encoded first word, tail, configuration and bytes outside the embedded firmware resource. The C11 header checksum formula covers `0x4002..0x4100` excluding `0x4050..0x4052`; this does not establish that all bootloader integrity mechanisms have been reconstructed.
