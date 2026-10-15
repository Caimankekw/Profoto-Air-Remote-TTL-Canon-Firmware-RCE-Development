# AIR2-P8 build sources

These are Caimankekw's authored PIC18 patch assemblers and linker, licensed under
AGPL-3.0-only. They are not Profoto's original C source or a replacement for the
complete vendor application. Build instructions are in the repository README.

| File | Responsibility |
| --- | --- |
| `hss_patch.py` | Build the existing HSS adapter from source and original C11 arithmetic bytes. |
| `ui_patch.py` | Six-group UI, C+HEAD paging, C+MODEL manual subtype and secondary-key arbitration. |
| `radio_patch.py` | Canonical six-group target/switch command construction. |
| `persistence_patch.py` | V4 settings journal and migration of earlier record formats. |
| `linker.py` | Resolve component calls in two passes, protect HSS/native ranges and reserved NVM pages. |
| `PROVENANCE.json` | Original authored source hashes and portability edits. |

`build.py` reads only the explicitly supplied official C11 EXE plus files in this
repository. It decodes the supported application area with `reference/`, builds
HSS-P1 and its corrected header checksum from source, then links P8 components.
No prebuilt P1/P3 image, P3 updater, device backup, recovery capture, or frozen P8
patch recipe is used as a build input. The recipe is generated **after** the
source build, then replayed independently as a packaging check.

The frozen output hashes are mandatory release guards. Editing source that
changes the output will fail these guards; deliberately publishing a new revision
requires independent validation and new expected hashes. A successful rebuild
does not establish hardware, RF, or timing compatibility.

The partial BIN has unknown first-word placeholders and is **not a direct flash
file**. Packaging preserves the original encoded first word, the original tail,
configuration, and all bytes outside the embedded firmware resource. The C11
header checksum formula covers `0x4002..0x4100` excluding `0x4050..0x4052`; it is
not a claim that all bootloader integrity mechanisms have been reconstructed.
