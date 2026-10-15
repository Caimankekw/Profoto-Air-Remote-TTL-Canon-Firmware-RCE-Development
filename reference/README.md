# C11 address-transformation reference data

English | [简体中文](README.zh-CN.md)

Developer: Caimankekw. Authored tool source uses AGPL-3.0-only.

`c11_offset_transform.bin` contains address-specific transformation parameters recovered from protocol behavior. It contains no device serial number, batch, date, USB path, device program backup, or original program plaintext. Offline tools use it to convert between C11 updater transport bytes and MCU bytes. Original firmware and updater rights remain with their respective owners.

The supported MCU byte-address interval is strictly `[0x4002, 0x10000)`. The 73,725-byte file contains 49,150 XOR bytes followed by 24,575 packed mask bytes. The low nibble belongs to the lower address and the high nibble to the next address. There is no file header; `codec_manifest.json` and tool constants pin the range, format and SHA-256.

For plaintext byte `p`, XOR byte `k`, and four-bit mask `m`:

```text
t = (p XOR (p >> 4)) AND m AND 0x0F
swap(p, m) = p XOR t XOR (t << 4)
encode(p) = swap(p, m) XOR k
decode(c) = swap(c XOR k, m)
```

Addresses do not move. Each mask bit selects a pair of bits four positions apart in the same byte; the swap is its own inverse. The mapping was recovered using fixed-fill and fixed-instruction-word references. Device information and raw transactions from those reference reads are not distributed.

`tools/reference_codec.py` uses only Python's standard library. `ReferenceCodec().encode(address, plaintext)`, `decode(address, opaque)`, and `encode_patch(address, plaintext)` reject out-of-range requests.

`decode_original_bytes()` accepts only the SHA-256-pinned complete original C11 application transport region. It returns a 113,664-byte partial plaintext image based at `0x4000` and a known-byte mask. Plaintext bytes `0x4000–0x4001` remain unknown and are represented by zeros with mask zero; these zeros must not be flashed as real instructions. The confirmed FF fill at `0x10000–0x1FBFF` is supplied only after the complete original transport hash matches. This does not establish a generic encoder for that tail. Any rebuilt container must preserve the original opaque first word, tail, sparse gaps and configuration bytes.

`codec_equivalence.json` records comparison with the original workspace decoder at every address and the C11 plaintext/mask hash checks. Run `python -B -m unittest discover -s tests -p test_reference_codec.py` for a self-test that does not require the vendor EXE. Reference equivalence does not validate device boot, RF delivery or light behavior.
