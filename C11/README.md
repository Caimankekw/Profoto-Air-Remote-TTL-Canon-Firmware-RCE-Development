# Original C11 reverse-engineering notes

[简体中文](README.zh-CN.md) | Developer: **Caimankekw**

This is a compact explanation of selected **unmodified Air Remote TTL-C C11** behavior. [recovered_logic.c](recovered_logic.c) is manually authored pseudocode and an address index, with an intentional `#error`. It is not manufacturer source, a complete decompilation, a safe callable API or compilable firmware. Modified AIR2 implementation belongs to the separate [P8 branch](https://github.com/Caimankekw/Profoto-Air-Remote-TTL-Canon-Firmware-RCE-Development/tree/P8).

Addresses are PIC18 **byte addresses**; the recovered application starts at `0x4000`. The first two plaintext bytes remain unknown. The original analysis image SHA-256 is `7f2b7ef2625bacebafc526d0623ae91faa1f544e6062f2d4171635ed087f072a`; known-byte mask SHA-256 is `81fe4da4f8a15728c97bc6de35fae71572d44f39a927dce22a9ca300b5d2558b`. Those images are not included here, and an analysis `.partial.bin` would not be a directly flashable file.

| Area | Original byte-address evidence and limits |
|---|---|
| Keys | `674A` returns one priority-selected key. Digital minus/plus precede MODE, another digital key and C. A/B share ADC field 1; MODEL/HEAD share field 0. Inclusive ADC intervals are `923..1023`, `412..612`, `60..260` (`6826/6844/684E/6858`). This does not establish the voltage produced by simultaneous switches on one resistor ladder. |
| TTL / MAN | `60EA` switches RAM `52` (nonzero TTL, zero MAN). Visible FEC slots are `3F..41`; object `C+2..4` stores TTL FEC. `6212` writes the inverse boolean to `C+5`; camera path `9188/91A4` maps it back. The object pointer is in RAM `42:43`, normally addressing `0088`. |
| Display | `5DD4` selects native mode/display behavior; `84C2`, `8414`, `83BC` format the three rows. Fixed LCD labels are not an arbitrary character display. |
| Radio requests | `783E/79D8` send ASCII `RSGT1` plus a 16-byte binary body, without CR. `8930` sends a ROM string plus CR and optionally calls four-byte receive routine `8656`. `9636` writes UART TXREG; its return does not establish final-bit drain, radio completion or a light acknowledgement. |
| Relative power | `6B8E` consumes the native relative-adjustment queue, including prequery, response and timeout/fallback paths. It is separate from the camera energy command path. |
| Camera / HSS | `40A8` dispatches camera commands; B4 at `421C` classifies `19/23` as preflash and `25/2D/35/39/3D` as main-flash paths. `42DC/4308` and `43BC..4432` contain different output sequences and S/Q waits; `5F78` computes/formats energy under native mode/class conditions. These boundaries do not reconstruct the radio module's full state machine or prove optical HSS equivalence. |
| Software time | `931C` builds a deadline; `7724` tests it; `7F28` updates the software clock from timer observations. Native parameters are not automatically calibrated milliseconds. |
| Original settings | `54EE..550A` mirrors FEC into `C+2..4`. Soft power-off `8F38 -> 939E -> 662E` packs/compares the original four-byte journal record in the `1F800` region. This is not automatic per-edit Flash saving. |
| Radio channel | `9474/75FC` requests `RSGER0\r`; `64F8/8976` applies/writes channel commands, including `RSGEW00<channel>\r`. The journal field `C+6` is not identified as the channel. |

The notes follow recovered bytes and bounded offline examination. Register aliases do not prove every PCB wire, cold-start peripheral state, exact MCU variant or bootloader behavior. Linear decoding can interpret data as instructions. Use the [root inspection command](../README.md#inspect-original-c11) to generate candidates from your own pinned original EXE; no pre-generated firmware or complete listing is bundled.

Original material retains its rights. Authored explanations are covered by [LICENSE](../LICENSE), subject to the scope in [NOTICE](../NOTICE.md); see the [disclaimer](../DISCLAIMER.md).
