# Offline analysis-tool checks

[简体中文](README.zh-CN.md)

Run from the repository root with Python 3.9+; no third-party packages or device are needed:

```powershell
python -I -B tests/test_reference_codec.py -v
python -I -B tests/test_container.py -v
python -I -B tests/test_container.py --original "C:\path\to\Air-Remote-TTL-C-Firmware-C11.exe" -v
```

The codec suite has 7 tests. The container suite has 9 pure-memory tests and 4 optional original-input tests; the latter explicitly skip when `--original` is omitted. Synthetic modifications are confined to memory: no EXE is written or executed. Tests validate parsing, pinned input, format preservation and transformation boundaries, not device startup or RF behavior.

The disassembly command in the [root README](../README.md) is the separate end-to-end inspection check. Generated listings belong outside version control. No P8 firmware build or emulation suite is required by `main`.
