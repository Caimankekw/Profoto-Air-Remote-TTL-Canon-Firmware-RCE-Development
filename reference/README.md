# C11 address-transform reference

[简体中文](README.zh-CN.md) | Developer: Caimankekw

`c11_offset_transform.bin` contains derived byte-transform parameters for offline inspection of the original C11 updater. It contains no device serial number, USB path, original transaction log, device backup or vendor plaintext image. Original firmware and updater rights remain with their respective holders; see [NOTICE](../NOTICE.md).

The supported PIC18 byte-address interval is exactly `[0x4002, 0x10000)`. The **73,725-byte** table comprises **49,150 XOR bytes** followed by **24,575 packed mask bytes**. The low nibble describes the lower address; the high nibble describes the next address. There is no file header. `codec_manifest.json` and tool constants pin the format, range and SHA-256:

```text
7779d34181f9d302d2d122e9a2ed40f975a4128b738a40561f97fc86ac949303
```

For plaintext byte `p`, XOR key `k` and four-bit mask `m`:

```text
t = (p XOR (p >> 4)) AND m AND 0x0F
swap(p, m) = p XOR t XOR (t << 4)
encode(p) = swap(p, m) XOR k
decode(c) = swap(c XOR k, m)
```

The transform never moves addresses. Each mask bit exchanges two bits four positions apart, making `swap` its own inverse. The parameters were derived from fixed fill/instruction references; their raw transactions and device metadata are not distributed.

`tools/reference_codec.py` uses only the Python standard library. Its generic in-memory `encode`, `decode` and `encode_patch` methods reject out-of-range requests. Those methods are not an updater or a P8 patch implementation.

`decode_original_bytes()` accepts only the pinned original C11 application transport region. It returns a 113,664-byte analysis representation based at `0x4000`, plus a known-byte mask. Bytes `0x4000–0x4001` remain unknown: zero placeholders with a zero mask, not recovered instructions. The fixed original's confirmed `FF` tail at `[0x10000, 0x1FC00)` is reconstructed only after the complete original transport hash matches; no general decoder for that tail or boot/config region is claimed. This analysis representation must not be treated as a directly flashable file.

`codec_equivalence.json` retains prior per-address equivalence and original-image/mask hash evidence. It is evidence metadata, not an additional runtime dependency. The self-contained [tests](../tests/README.md) check the table and transform without a device or vendor EXE; these checks do not establish hardware, radio or optical behavior.
