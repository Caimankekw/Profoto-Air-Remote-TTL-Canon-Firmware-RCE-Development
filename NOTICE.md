# License scope

English | [简体中文](NOTICE.zh-CN.md)

Copyright (C) 2026 Caimankekw.

Repository: [Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development).

The `P8` branch contains the corresponding authored development source; `main` contains analysis of unmodified C11. The FIX1 release tag is `p8-fix1-20261016`. Release notes pin the exact source commit, and each Windows package includes its corresponding source archive.

Caimankekw's original patch generators, integration and packaging tools, tests and explanatory documentation are licensed under **AGPL-3.0-only**. See the complete, unmodified [LICENSE](LICENSE). The corresponding authored source is included in the source archive distributed with the Windows packages.

This grant applies only to material for which the developer can grant rights. Original Profoto firmware, copied or relocated original instructions, firmware resources, the original updater and loader, trademarks and other third-party material retain their respective rights. Recovered logic and reference parameters document observations of that firmware; including them does not grant additional rights to the original software. The mixed generated firmware/updater is not represented as wholly authored by Caimankekw or wholly relicensed under AGPL.

The source distribution excludes the original vendor EXE, device readbacks, USB captures, individual device configuration/identifiers and account data. The original EXE is a separately supplied, hash-checked build input; the Windows distribution includes an unmodified original recovery EXE. Reusing the vendor GUI or container does not imply approval or a valid vendor signature.

This integrated FIX1 release provides both an NSIS self-extracting wrapper and a portable Windows ZIP. NSIS, its runtime/plugins and 7-Zip keep their own licenses. The Windows build retains the NSIS copyright/license notice with its distributed runtime; 7-Zip is a separately supplied build verification tool. See [windows](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/blob/p8-fix1-20261016/windows/README.md) for inputs and packaging source. These package formats differ from the earlier frozen FIX1 candidate, which supplied a portable ZIP only.

The project license and disclaimers do not limit rights granted by applicable open-source licenses or non-excludable statutory rights.

The same file is included in the bundled Source.zip at windows/README.md.
