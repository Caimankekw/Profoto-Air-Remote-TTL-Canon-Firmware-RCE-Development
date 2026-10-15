#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 Caimankekw
"""Independent AIR2 settings journal. Offline PIC18 assembler, no device I/O.

Only pages F800/FC00 are written. Original 1F800 journal is not changed.
Application ownership of this allocation is checked separately; unknown
bootloader integrity behavior remains an experimental hardware limitation.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location('air2_p5_persist_asm', Path(__file__).with_name('ui_patch.py'))
_ui = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ui)
Asm = _ui.Asm

PAGES = (0xF800, 0xFC00)
CODE_CAP = 0xF800
RECORD_SIZE = 32
FORMAT_VERSION = 4


def construct(original, base=0xB800, imports=None):
    a = Asm(base)
    # Private bank2: best-valid/ptr/seq, current ptr, loops, CRC, scratch,
    # best targets/masks. Record340..35F; context330..33F never overlaps it.
    VALID, BESTL, BESTH, SEQL, SEQH = 0x20, 0x21, 0x22, 0x23, 0x24
    PL, PH, COUNT, N, CL, CH, BITS, TMP = 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C
    DL, DH, BLAST, WL, WH, WI, ERROR = 0x2D, 0x2E, 0x30, 0x32, 0x33, 0x34, 0x35
    BA, BB, BC, BMODE, BH, BM = 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D
    BD, BE, BF, BBANK, BVERSION = 0x40, 0x41, 0x42, 0x43, 0x44
    TARGETS = (0x200, 0x201, 0x202, 0x260, 0x261, 0x262)
    BEST_TARGETS = (BA, BB, BC, BD, BE, BF)
    contexts = ((0xFE0, 0x330), (0xFD9, 0x331), (0xFDA, 0x332),
                (0xFF6, 0x333), (0xFF7, 0x334), (0xFF8, 0x335),
                (0xFF5, 0x336))

    def bank2(): a.w(0x0102, 'MOVLB 2')
    def lit(v): a.w(0x0E00 | v, 'MOVLW %02X' % v)
    def setv(f, v): lit(v); a.w(0x6F00 | f, 'MOVWF 2%02X' % f)
    def get(f): a.w(0x5100 | f, 'MOVF 2%02X,W' % f)
    def put(f): a.w(0x6F00 | f, 'MOVWF 2%02X' % f)
    def zero(f): a.w(0x6B00 | f, 'CLRF 2%02X' % f)
    def inc(f): a.w(0x2B00 | f, 'INCF 2%02X,F' % f)
    def call(label): a.jump(label, 'CALL')
    def go(label): a.jump(label, 'GOTO')
    def ret(v=None): a.w(0x0012 if v is None else 0x0C00 | v, 'RETURN' if v is None else 'RETLW %d' % v)
    def get_abs(f): a.movff(f, 0xFE8); a.w(0x0900, 'IORLW 0')
    def set_abs(f, v): lit(v); a.movff(0xFE8, f)
    def fsr2(p): a.emit(_ui.words(0xEE20 | ((p >> 8) & 15), 0xF000 | (p & 255)), 'LFSR2 %03X' % p)
    def compare_buf(i, v, bad):
        get_abs(0x340 + i); a.w(0x0A00 | v, 'XORLW %02X' % v)
        skip = 'compare_ok_%X' % a.pc
        a.jump(skip, 'BZ'); go(bad); a.label(skip)
    def ptr_to_tbl(lo=PL, hi=PH):
        a.movff(0x200 + lo, 0xFF6); a.movff(0x200 + hi, 0xFF7)
        a.w(0x6AF8, 'CLRF TBLPTRU,ACCESS')
    def ptr_step(size=16):
        lit(size); a.w(0x2725, 'ADDWF 225,F')
        lit(0); a.w(0x2326, 'ADDWFC 226,F')
    def restore_context():
        for src, dst in reversed(contexts): a.movff(dst, src)
        ret()

    a.label('init')
    call('save_context'); bank2(); call('scan')
    for target in TARGETS: set_abs(target, 50)
    # First install preserves native ABC defaults and keeps DEF disabled.
    for dest, fields, on_zero in ((0x26F, (0x47, 0x46, 0x45), True), (0x270, (0x51, 0x50, 0x4F), False)):
        zero(TMP)
        for bit, field in enumerate(fields):
            get_abs(field); a.jump('default_%X_%d' % (dest, bit), 'BNZ' if on_zero else 'BZ')
            a.w(0x8100 | (bit << 9) | TMP, 'BSF ABC default mask')
            a.label('default_%X_%d' % (dest, bit))
        a.movff(0x22C, dest)
    set_abs(0x271, 0)
    set_abs(0x208, 0xFF)  # No V2/V3 mode: UI falls back to native saved mode.
    set_abs(0x209, 1)  # No historical MAN subtype: choose AIR1 deterministically.
    get(VALID); a.jump('init_defaults', 'BZ')
    a.movff(0x23B, 0x208)
    get(BLAST); a.w(0x0AFF); a.jump('init_last_v3', 'BNZ')
    # V2 can recover its MAN subtype from effective mode; TTL lacks history.
    get(BMODE); a.w(0x0A02); a.jump('init_last_ready', 'BNZ')
    set_abs(0x209, 2); a.jump('init_last_ready')
    a.label('init_last_v3'); a.movff(0x230, 0x209)
    a.label('init_last_ready')
    for source, target in zip(BEST_TARGETS, TARGETS):
        a.movff(0x200 + source, target)
    a.movff(0x23C, 0x26F); a.movff(0x23D, 0x270); a.movff(0x243, 0x271)
    # UI load_page projects canonical flags and derived44/7F after mode restore.
    a.label('init_defaults'); zero(5)  # 205 NVM dirty, not radio dirty204.
    go('restore_context')

    a.label('commit')
    call('save_context'); bank2(); get(5); a.jump('commit_enter', 'BNZ'); go('restore_context')
    a.label('commit_enter')
    # Complete key-release action only; wait for both native and A2 queues.
    for address in (0x77, 0x204, 0x206, 0x207, 0x7C, 0x7D):
        get_abs(address); a.jump('commit_idle_%X' % address, 'BZ'); go('restore_context')
        a.label('commit_idle_%X' % address)
    get_abs(0xF73); a.w(0x0B01, 'ANDLW 1 ; SSP1STAT.BF')
    a.jump('camera_rx_empty', 'BZ'); go('restore_context'); a.label('camera_rx_empty')
    for p, q in zip(range(0x67, 0x6B), range(0x6B, 0x6F)):
        get_abs(p); a.movff(0xFE8, 0x22C); get_abs(q)
        a.w(0x192C, 'XORWF 22C,W'); a.jump('queue_equal_%X' % p, 'BZ'); go('restore_context')
        a.label('queue_equal_%X' % p)
    call('scan'); call('capture')
    # Invalid application state must not become a durable record.
    call('validate_payload'); a.w(0x0900); a.jump('commit_payload_ok', 'BNZ'); go('restore_context')
    a.label('commit_payload_ok'); get(VALID); a.jump('commit_changed', 'BZ')
    get(BVERSION); a.w(0x0A04); a.jump('commit_changed', 'BNZ')
    for buf, old in ((3, BMODE), (15, BLAST), (6, BA), (7, BB), (8, BC), (9, BD), (10, BE), (11, BF), (12, BH), (13, BM), (14, BBANK)):
        get_abs(0x340 + buf); a.w(0x1900 | old, 'XORWF best,W'); a.jump('commit_changed', 'BNZ')
    zero(5); go('restore_context')
    a.label('commit_changed')
    get(VALID); a.jump('initial_page', 'BZ')
    get(BESTH); a.w(0x0BFC, 'ANDLW FC'); put(PH); zero(PL); a.jump('locate_slot')
    a.label('initial_page'); zero(PL); setv(PH, 0xF8)
    a.label('locate_slot'); call('find_erased'); a.w(0x0900); a.jump('slot_ready', 'BNZ')
    # Current page has no completely erased slot. Erase ONLY the other page.
    # BESTH is used, not the exhausted scan pointer which has advanced a page.
    get(VALID); a.jump('no_valid_page', 'BZ')
    get(BESTH); a.w(0x0BFC); a.w(0x0A04); put(PH); zero(PL); a.jump('erase_target')
    a.label('no_valid_page'); zero(PL); setv(PH, 0xF8)
    a.label('erase_target'); call('erase_page'); a.w(0x0900); a.jump('slot_ready', 'BNZ'); go('restore_context')
    a.label('slot_ready')
    a.movff(0x225, 0x232); a.movff(0x226, 0x233)
    call('capture')
    # Sequence starts at 0; wrap is ordered by a half-range modular compare.
    get(VALID); a.jump('sequence_initial', 'BZ')
    inc(SEQL); a.jump('sequence_ready', 'BNZ'); inc(SEQH); a.jump('sequence_ready')
    a.label('sequence_initial'); zero(SEQL); zero(SEQH)
    a.label('sequence_ready'); a.movff(0x223, 0x344); a.movff(0x224, 0x345)
    call('crc28'); a.movff(0x229, 0x35C); a.movff(0x22A, 0x35D)
    set_abs(0x35E, 0x5A); set_abs(0x35F, 0xA5)
    fsr2(0x340); setv(WI, 16)
    a.label('write_record_loop')
    call('write_word'); a.w(0x0900); a.jump('word_complete', 'BNZ'); go('restore_context')
    a.label('word_complete')
    lit(2); a.w(0x2732, 'ADDWF 232,F'); lit(0); a.w(0x2333, 'ADDWFC 233,F')
    a.w(0x2F34, 'DECFSZ 234,F'); a.jump('write_record_loop')
    # Last word is commit; each word was independently read back.
    zero(5); go('restore_context')

    a.label('save_context')
    for src, dst in contexts: a.movff(src, dst)
    ret()
    a.label('restore_context'); restore_context()

    a.label('scan')
    zero(VALID); zero(PL); setv(PH, 0xF8); setv(COUNT, 128)
    a.label('scan_loop')
    a.w(0x0004, 'CLRWDT'); call('read_record'); call('validate_record'); a.w(0x0900)
    a.jump('scan_next', 'BZ'); get(VALID); a.jump('scan_accept', 'BZ')
    get_abs(0x344); put(DL); get(SEQL); a.w(0x5F2D, 'SUBWF 22D,F')
    get_abs(0x345); put(DH); get(SEQH); a.w(0x5B2E, 'SUBWFB 22E,F')
    a.w(0xBF2E, 'BTFSC 22E,7'); a.jump('scan_next')
    get(DL); a.w(0x112E, 'IORWF 22E,W'); a.jump('scan_next', 'BZ')
    a.label('scan_accept')
    setv(VALID, 1); a.movff(0x225, 0x221); a.movff(0x226, 0x222)
    a.movff(0x344, 0x223); a.movff(0x345, 0x224)
    a.movff(0x342, 0x244)
    for src, dst in ((6, BA), (7, BB), (8, BC)):
        a.movff(0x340 + src, 0x200 + dst)
    get(BVERSION); a.w(0x0A04); a.jump('scan_accept_v4', 'BZ')
    for f in (BD, BE, BF): setv(f, 50)
    zero(BBANK); a.movff(0x34A, 0x23C); a.movff(0x34B, 0x23D)
    setv(BMODE, 0xFF); setv(BLAST, 0xFF)
    get_abs(0x342); a.w(0x0A01, 'XORLW 1 ; V1 has no mode'); a.jump('scan_next', 'BZ')
    a.movff(0x343, 0x23B)
    get_abs(0x342); a.w(0x0A03, 'XORLW 3 ; V3 has last MAN'); a.jump('scan_next', 'BNZ')
    a.movff(0x349, 0x230)
    a.jump('scan_next')
    a.label('scan_accept_v4')
    for src, dst in ((3, BMODE), (9, BD), (10, BE), (11, BF), (12, BH), (13, BM), (14, BBANK), (15, BLAST)):
        a.movff(0x340 + src, 0x200 + dst)
    a.label('scan_next'); ptr_step(); a.w(0x2F27, 'DECFSZ 227,F'); a.jump('scan_loop'); ret()

    a.label('read_record')
    ptr_to_tbl()
    for i in range(16):
        a.w(0x0009, 'TBLRD*+'); a.movff(0xFF5, 0x340 + i)
    # Legacy FFF0 is legal16B, but never fetch past the application boundary.
    get(PH); a.w(0x0AFF); a.jump('read_second_half', 'BNZ')
    get(PL); a.w(0x0AF0); a.jump('read_second_half', 'BNZ')
    for i in range(16, 32): set_abs(0x340 + i, 255)
    ret()
    a.label('read_second_half')
    for i in range(16, 32):
        a.w(0x0009, 'TBLRD*+'); a.movff(0xFF5, 0x340 + i)
    ret()

    a.label('validate_record')
    get_abs(0x342); a.w(0x0A04); a.jump('validate_record_v4', 'BZ')
    for i, value in ((0, 0x41), (1, 0x32), (14, 0x5A), (15, 0xA5)):
        compare_buf(i, value, 'record_bad')
    call('validate_legacy_payload'); a.w(0x0900); a.jump('record_bad', 'BZ')
    call('crc12'); get_abs(0x34C); a.w(0x1929); a.jump('record_bad', 'BNZ')
    get_abs(0x34D); a.w(0x192A); a.jump('record_bad', 'BNZ'); ret(1)
    a.label('record_bad'); ret(0)

    a.label('validate_record_v4')
    get(PL); a.w(0x0B1F); a.jump('record_v4_bad', 'BNZ')
    for i, value in ((0, 0x41), (1, 0x32), (30, 0x5A), (31, 0xA5)):
        compare_buf(i, value, 'record_v4_bad')
    call('validate_payload'); a.w(0x0900); a.jump('record_v4_bad', 'BZ')
    call('crc28'); get_abs(0x35C); a.w(0x1929); a.jump('record_v4_bad', 'BNZ')
    get_abs(0x35D); a.w(0x192A); a.jump('record_v4_bad', 'BNZ'); ret(1)
    a.label('record_v4_bad'); ret(0)

    a.label('validate_legacy_payload')
    get_abs(0x343); a.w(0x0802, 'SUBLW 2 ; mode0..2'); a.jump('payload_bad', 'BNC')
    get_abs(0x342); a.w(0x0A01); a.jump('validate_version_two', 'BNZ')
    compare_buf(3, 0, 'payload_bad'); compare_buf(9, 0, 'payload_bad'); a.jump('validate_payload_fields')
    a.label('validate_version_two'); get_abs(0x342); a.w(0x0A02); a.jump('validate_version_three', 'BNZ')
    compare_buf(9, 0, 'payload_bad'); a.jump('validate_payload_fields')
    a.label('validate_version_three'); compare_buf(2, 3, 'payload_bad')
    get_abs(0x349); a.jump('payload_bad', 'BZ'); a.w(0x0802); a.jump('payload_bad', 'BNC')
    get_abs(0x343); a.jump('validate_payload_fields', 'BZ')
    a.movff(0x349, 0x22C); get_abs(0x343); a.w(0x192C, 'XORWF last MAN,W'); a.jump('payload_bad', 'BNZ')
    a.label('validate_payload_fields')
    for i in (6, 7, 8):
        get_abs(0x340 + i); a.jump('payload_bad', 'BZ'); a.w(0x0864, 'SUBLW 100'); a.jump('payload_bad', 'BNC')
    for i in (10, 11):
        get_abs(0x340 + i); a.w(0x0BF8, 'ANDLW F8'); a.jump('payload_bad', 'BNZ')
    ret(1); a.label('payload_bad'); ret(0)

    a.label('validate_payload')
    compare_buf(2, FORMAT_VERSION, 'v4_payload_bad')
    get_abs(0x343); a.w(0x0802); a.jump('v4_payload_bad', 'BNC')
    get_abs(0x34F); a.jump('v4_payload_bad', 'BZ'); a.w(0x0802); a.jump('v4_payload_bad', 'BNC')
    get_abs(0x343); a.jump('validate_v4_targets', 'BZ')
    a.movff(0x34F, 0x22C); get_abs(0x343); a.w(0x192C); a.jump('v4_payload_bad', 'BNZ')
    a.label('validate_v4_targets')
    for i in range(6, 12):
        get_abs(0x340+i); a.jump('v4_payload_bad', 'BZ'); a.w(0x0864); a.jump('v4_payload_bad', 'BNC')
    for i in (12, 13):
        get_abs(0x340+i); a.w(0x0BC0); a.jump('v4_payload_bad', 'BNZ')
    get_abs(0x34E); a.w(0x0801); a.jump('v4_payload_bad', 'BNC')
    # Reserved trailing bytes must be zero, independently of CRC correctness.
    fsr2(0x350); setv(N, 12)
    a.label('validate_v4_reserved'); a.movff(0xFDE, 0xFE8); a.w(0x0900); a.jump('v4_payload_bad', 'BNZ')
    a.w(0x2F28); a.jump('validate_v4_reserved'); ret(1)
    a.label('v4_payload_bad'); ret(0)

    a.label('capture')
    for i, v in ((0, 0x41), (1, 0x32), (2, FORMAT_VERSION), (3, 0)):
        set_abs(0x340 + i, v)
    a.movff(0x203, 0x34F)  # Persist remembered MAN subtype even while TTL.
    get_abs(0x52); a.jump('capture_mode_ready', 'BNZ')
    a.movff(0x203, 0x343)
    a.label('capture_mode_ready')
    for i, target in enumerate(TARGETS): a.movff(target, 0x346+i)
    a.movff(0x26F, 0x34C); a.movff(0x270, 0x34D); a.movff(0x271, 0x34E)
    for i in range(16, 28): set_abs(0x340+i, 0)
    ret()

    a.label('crc12'); setv(N, 12); a.jump('crc_common')
    a.label('crc28'); setv(N, 28)
    a.label('crc_common'); setv(CL, 255); setv(CH, 255); fsr2(0x340)
    a.label('crc_byte'); a.movff(0xFDE, 0xFE8); a.w(0x1B2A, 'XORWF CRC hi,F'); setv(BITS, 8)
    a.label('crc_bit')
    a.w(0x90D8, 'BCF STATUS,C'); a.w(0x3729, 'RLCF CRC low,F'); a.w(0x372A, 'RLCF CRC high,F')
    a.jump('crc_no_xor', 'BNC'); lit(0x21); a.w(0x1B29); lit(0x10); a.w(0x1B2A)
    a.label('crc_no_xor'); a.w(0x2F2B); a.jump('crc_bit'); a.w(0x2F28); a.jump('crc_byte'); ret()

    a.label('is_erased')
    # Entire32B must be FF, including any legacy16B second half.
    fsr2(0x340); setv(N, 32)
    a.label('erased_loop'); a.movff(0xFDE, 0xFE8); a.w(0x0AFF); a.jump('not_erased', 'BNZ')
    a.w(0x2F28); a.jump('erased_loop')
    ret(1); a.label('not_erased'); ret(0)

    a.label('find_erased')
    setv(COUNT, 32)
    a.label('find_loop'); a.w(0x0004); call('read_record'); call('is_erased'); a.w(0x0900)
    a.jump('find_found', 'BNZ'); ptr_step(32); a.w(0x2F27); a.jump('find_loop'); ret(0)
    a.label('find_found'); ret(1)

    a.label('erase_page')
    # Fail closed on any corrupted address. Only two explicitly owned pages.
    get(PL); a.jump('erase_bad', 'BNZ'); get(PH); a.w(0x0AF8); a.jump('erase_address_ok', 'BZ')
    get(PH); a.w(0x0AFC); a.jump('erase_bad', 'BNZ')
    a.label('erase_address_ok'); ptr_to_tbl(); a.w(0x9AA6, 'BCF EECON1,WPROG')
    a.w(0x88A6, 'BSF EECON1,FREE'); call('flash_unlock')
    a.w(0xB6A6, 'BTFSC EECON1,WRERR'); a.jump('erase_bad')
    # Verify every byte of the erased page before choosing its first slot.
    ptr_to_tbl(); setv(N, 4); zero(BITS)
    a.label('erase_verify'); a.w(0x0004); a.w(0x0009); get_abs(0xFF5); a.w(0x0AFF); a.jump('erase_bad', 'BNZ')
    a.w(0x2F2B); a.jump('erase_verify'); a.w(0x2F28); a.jump('erase_verify'); ret(1)
    a.label('erase_bad'); ret(0)

    a.label('write_word')
    # Pointer must be even and within owned pages; never reach original journal.
    get(WH); a.w(0x0BF8); a.w(0x0AF8); a.jump('write_bad', 'BNZ')
    a.w(0xB132, 'BTFSC 232,0'); a.jump('write_bad')
    ptr_to_tbl(WL, WH)
    a.movff(0xFDE, 0xFF5); a.movff(0xFF5, 0x23E); a.w(0x000D, 'TBLWT*+')
    a.movff(0xFDE, 0xFF5); a.movff(0xFF5, 0x23F); a.w(0x000C, 'TBLWT*')
    a.w(0x98A6, 'BCF EECON1,FREE'); a.w(0x8AA6, 'BSF EECON1,WPROG'); call('flash_unlock')
    a.w(0xB6A6, 'BTFSC EECON1,WRERR'); a.jump('write_bad')
    ptr_to_tbl(WL, WH); a.w(0x0009); get_abs(0xFF5); a.w(0x193E); a.jump('write_bad', 'BNZ')
    a.w(0x0008); get_abs(0xFF5); a.w(0x193F); a.jump('write_bad', 'BNZ'); ret(1)
    a.label('write_bad'); ret(0)

    a.label('flash_unlock')
    # Follow 47J53 documented 55/AA sequence. Hardware stalls during WR.
    # Preserve caller IRQ enables; do not change priority mode or IRQ flags.
    a.movff(0xFF2, 0x339)
    a.w(0x9EF2, 'BCF INTCON,GIEH'); a.w(0x9CF2, 'BCF INTCON,GIEL')
    a.w(0x96A6, 'BCF EECON1,WRERR'); a.w(0x84A6, 'BSF EECON1,WREN'); a.w(0x0004, 'CLRWDT')
    lit(0x55); a.w(0x6EA7, 'MOVWF EECON2'); lit(0xAA); a.w(0x6EA7); a.w(0x82A6, 'BSF EECON1,WR')
    a.w(0x94A6, 'BCF EECON1,WREN'); a.w(0x98A6, 'BCF EECON1,FREE'); a.w(0x9AA6, 'BCF EECON1,WPROG')
    a.movff(0x339, 0x236)
    a.w(0xAD36, 'BTFSS saved GIEL'); a.jump('irq_low_done'); a.w(0x8CF2, 'BSF INTCON,GIEL')
    a.label('irq_low_done'); a.w(0xAF36, 'BTFSS saved GIEH'); a.jump('irq_high_done'); a.w(0x8EF2, 'BSF INTCON,GIEH')
    a.label('irq_high_done'); ret()

    a.finish()
    if a.pc > CODE_CAP:
        raise ValueError('persistence component crosses reserved NVM pages')
    metadata = {
        'exports': dict(a.labels), 'imports': {}, 'unresolved_imports': [],
        'tail_range': [base, a.pc], 'runtime_nvm_pages': [[0xF800, 0xFC00], [0xFC00, 0x10000]],
        'original_settings_journal': 'untouched 1F800..1FC00',
        'record': {'bytes': 32, 'slots_per_page': 32, 'alignment': 32, 'magic': '4132', 'version': FORMAT_VERSION,
                   'sequence': 'LE16 half-range', 'targets': 'bytes6..11 ABCDEF range1..100',
                   'mode': 'byte3:0TTL/1MAN-A1/2MAN-A2; read-only init token208',
                   'last_manual': 'byte15:1A1/2A2 even while TTL; MAN effective mode must equal this byte; init token209',
                   'headmask': 'byte12 bits0..5 ABCDEF,1enabled',
                   'modelmask': 'byte13 same bits, raw intent', 'display_bank': 'byte14:0ABC/1DEF',
                   'reserved_zero': list(range(16, 28)), 'crc': 'CCITT-FALSE first28 bytes,LE16 at28',
                   'legacy_V1': '16B/byte3=byte9=0; token208=FF/token209=1; migrate next dirty',
                   'legacy_V2': '16B/byte9=0; token209=mode if MAN else1; migrate next dirty',
                   'legacy_V3': '16B/mode3,lastMAN9; restore ABC and tokens; migrate next dirty',
                   'legacy_defaults': 'DEF targets50/headOFF/modelOFF/displayABC; scan16B but allocate only wholly erased aligned32B slots',
                   'commit_word_last': '5AA5 at30'},
        'ram': {'private': [0x220, 0x248], 'buffer': [0x340, 0x360], 'context': [0x330, 0x340],
                'canonical_targets': list(TARGETS), 'headmask': 0x26F, 'modelmask': 0x270, 'bank': 0x271, 'dirty': 0x205,
                'manual_kind_203': 'read only for every capture, required1/2 even TTL; never changed by NVM',
                'startup_mode_token_208': '0TTL/1A1/2A2 or FF for no V2/V3/V4; UI applies mode',
                'startup_last_manual_token_209': '1A1/2A2; legacy lacking subtype defaults1; UI applies203',
                'best_mode_23B': 'private scanner metadata, FF for V1',
                'best_last_manual_230': 'private scanner metadata, FF for V1/V2',
                'best_DEF_bank_version': [0x240, 0x245],
                'preserved': 'all low RAM; BSR,FSR2,TBLPTR,TABLAT; UI projects visible flags and44/7F from canonical after init'},
        'write_gate': '205 && !77 && !204 && !206 && !207(key_active) && !7C && !7D && !SSP1STAT.BF && equal native pending67..6A/6B..6E',
        'gc': 'erase other page only after current page full; old valid page retained until new record commit',
        'limits': ['Unknown bootloader integrity scope is not statically proven.',
                   'Firmware reinstall can erase these settings; they are not calibration data.',
                   'Latest completed commit survives modeled interrupted writes; an unfinished user action may be lost.',
                   'Known camera pending flags defer saving, but future camera traffic during hardware write stalls cannot be predicted.',
                   'Electrical retention/endurance and brownout behavior need hardware validation.'],
    }
    return a, [(base, a.code, 'six-group32B journal with16B legacy migration and isolated flash primitives')], metadata
