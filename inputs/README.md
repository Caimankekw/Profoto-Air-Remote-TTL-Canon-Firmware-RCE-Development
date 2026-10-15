# External original input

[简体中文](README.zh-CN.md)

Provide the original **Air-Remote-TTL-C-Firmware-C11.exe** separately. This repository does not distribute it. Supported input:

- Size: `3938448` bytes.
- SHA-256: `e56b19080bd6330a5461dd4e3d614fc6d81dcc533e945e6090e7db63824bc240`.

The name is descriptive; content fingerprints are authoritative. Pass its path with `--original` to `tools/disassemble.py`. It can remain outside the repository. The tool reads it as data, never launches it, and needs no device, account, device readback or USB capture. Do not commit vendor EXEs, generated firmware or personal device data to `main`.

See the [root instructions](../README.md#inspect-original-c11). Modified inputs are rejected rather than treated as original C11.
