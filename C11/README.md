# C11 reverse-engineering notes

[简体中文](README.zh-CN.md) · Developer: **Caimankekw**

This folder is a compact explanation of the **original Air Remote TTL-C C11 application**, with an index of the functions reused or replaced by AIR2-P8. It is **not manufacturer source code, a complete decompilation, or a standalone firmware project**. [recovered_logic.c](recovered_logic.c) is deliberately non-buildable pseudocode and an address index. The actual patch generators are in [../source/](../source/).

The original machine code, firmware resources and tools retain their respective rights. The explanations and manually authored pseudocode here are licensed under [AGPL-3.0-only](../LICENSE). This does not relicense manufacturer material; see [NOTICE](../NOTICE.md) and [DISCLAIMER](../DISCLAIMER.md).

## Address and evidence conventions

Addresses are **PIC18 byte addresses**, not file offsets; the recovered application image has base `0x4000`. Only its first two plaintext bytes remain unknown. A `.partial.bin` is an analysis representation, not a file to flash directly. The original recovered-image SHA256 is `7f2b7ef2625bacebafc526d0623ae91faa1f544e6062f2d4171635ed087f072a`; the accompanying known-byte mask SHA256 is `81fe4da4f8a15728c97bc6de35fae71572d44f39a927dce22a9ca300b5d2558b`.

The descriptions below follow recovered instruction bytes and bounded offline replays. Peripheral names describe the observed register interface; they do not prove every PCB connection, bootloader behavior or physical timing. Linear PIC18 decoding can also interpret data as instructions, so the generated listing remains a candidate listing.

From the project root, generate a listing when needed using your original C11 Windows updater:

```powershell
python tools/disassemble.py --original "C:\path\to\official_C11.exe" --out build/original_C11.listing.txt
```

The default range is `0x4002..0x9780`. Optional `--start` and `--end` select byte-address bounds. This is an offline operation; it does not access a device. The project pins the supported original input. No full listing, personal device capture or firmware from another product is included in this folder.

## Original C11 versus AIR2-P8

| Area | Original C11 evidence | AIR2-P8 change or retained boundary |
|---|---|---|
| Keys | `674A` returns one priority-selected key. Minus/plus are digital inputs; A/B share ADC field1; MODEL/HEAD share ADC field0; C is a separate digital input. | C+HEAD pages; C+MODEL switches the remembered MAN subtype. Only these secondary keys wait for a chord. A/B/plus/minus take the direct key path. A shared ADC does not provide two independent MODEL/HEAD bits. |
| TTL / MAN | `60EA` toggles RAM `52`: nonzero TTL, zero MAN. TTL compensation uses visible slots `3F..41` and configuration object `C+2..4`. `6212` writes the inverse mode boolean to `C+5`; `9188/91A4` processes the camera-side boolean. | Separate six-group state and the last MAN subtype are added. TTL ABC FEC remains distinct from manual targets. DEF is manual control even while the global mode is TTL. |
| Radio interface | `783E/79D8` send ASCII `RSGT1` plus a 16-byte binary body. `8930` sends a ROM string plus CR and can call `8656` for a four-byte response. `9636` writes the UART. | The six-group sender constructs new requests through this existing module interface. UART completion or a local response is not proof of RF reception, light execution or equivalent radio timing. |
| Camera / HSS | `40A8` dispatches camera commands. `421C` handles B4; `42DC/4308` and `43BC..4432` contain distinct preflash/main-flash output sequences. The latter changes pulse order around the Q input according to the native mode. `5F78` handles energy arithmetic/formatting. | P8 retains the project's HSS-P3 policy patch and original backend. That patch moves energy preparation to the B4 main-flash phase; it is not unmodified C11 and is not a complete transplant of another transmitter's RF backend. |
| Settings | `54EE..550A` mirrors FEC into `C+2..4`. The original journal is committed on the soft-power-off chain `8F38 -> 939E -> 662E`, using the region at `1F800`. | P8 uses separate runtime pages `F800..FFFF` for extension records: six A2 targets, Head/Model intentions, page and mode memory. Temporary A1 offsets are not persisted. Original FEC persistence timing remains separate. |
| Channel | `9474/75FC` reads `RSGER0\r`; `64F8/8976` applies/writes channel commands, including `RSGEW00<channel>\r`. | This is a radio-module parameter path. Do not label the original journal's `C+6` field as the channel. |

## Important limits

- The original scanner and key handlers contain blocking debounce/hold/release paths (`9226`, `8ACC`, `9086`). Removing a chord delay does not promise lossless input at every tapping rate.
- The original software deadline units (`931C/7724`, clock update `7F28`) are not automatically milliseconds. The full hardware and sampling conditions matter.
- Original camera code includes S/Q waits and output pulses. Their existence does not establish the radio module's internal state machine, an RF-ready callback or optical HSS uniformity.
- Writing new settings, reconstructing bytes and reproducing an updater are separate checks. None alone establishes successful startup or hardware acceptance. Use the project-level build, verification and update instructions rather than compiling this folder.

