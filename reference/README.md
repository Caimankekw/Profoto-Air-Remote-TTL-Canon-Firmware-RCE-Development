# C11 address-transform reference data

English | [简体中文](README.zh-CN.md)

Developer: Caimankekw. Authored tools use AGPL-3.0-only.

`c11_offset_transform.bin` holds address-transform parameters derived from recovered protocol behavior. It does not contain device serials, batches, dates, USB paths, device backups or original firmware plaintext. Offline tools use it to convert the original C11 updater's transport bytes to and from MCU bytes. Original firmware and updater rights remain with their respective owners.

The supported MCU byte-address range is exactly `[0x4002, 0x10000)`. The file contains 73,725 bytes: 49,150 XOR bytes followed by 24,575 packed mask bytes. A mask's low nibble applies to the lower address, and its high nibble to the next address. There is no file header. `codec_manifest.json` and tool constants pin the layout, range and SHA-256.

For plaintext byte `p`, XOR byte `k` and four-bit mask `m`:

```text
t = (p XOR (p >> 4)) AND m AND 0x0F
swap(p, m) = p XOR t XOR (t << 4)
encode(p) = swap(p, m) XOR k
decode(c) = swap(c XOR k, m)
```

Byte addresses do not move. Each mask bit controls exchange of a pair of bits four positions apart; the swap is its own inverse. The mapping was recovered with fixed-fill and fixed-instruction references. Device information and raw transactions used during recovery are not exported.

`tools/reference_codec.py` uses only the Python standard library. Its `encode`, `decode` and `encode_patch` methods reject out-of-range requests.

`decode_original_bytes()` accepts only the pinned complete original C11 application transport area and returns a 113,664-byte partial image based at `0x4000`, plus a known-byte mask. Addresses `0x4000–0x4001` remain unknown: their placeholder bytes and mask are zero. Those zeros must not be flashed as instructions. For this pinned C11 input, `0x10000–0x1FBFF` is confirmed FF fill and is filled only after validating the complete transport hash. This does not establish a general encoder for that range. Packaging must preserve the original transport bytes of the first word, tail, sparse gaps and configuration.

`codec_equivalence.json` records the original per-address comparison against the development decoder and checks the original plaintext/mask hashes. Run `python -B -m unittest discover -s tests -p test_reference_codec.py` for checks that need no vendor input. Reference equivalence does not replace physical boot, RF or lamp testing.
