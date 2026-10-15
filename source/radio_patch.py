#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 Caimankekw
"""P5 six-group radio adapter. Pure offline native PIC18 assembly.

The UI validates and commits canonical state before calling the public helpers.
radio_power_commit: W signed step +/-1,+/-10; RAM03 physical selector1..6/7ALL.
radio_switch_commit: W0Head/1Model; RAM03 same selector. All reads are canonical.
No USB, host writer, RF-ACK claim, or guessed no-change absolute value.
"""
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    'air2_p5_radio_asm', HERE / 'hss_patch.py')
_asm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_asm)
absolute = _asm.absolute


class Asm(_asm.Asm):
    """Conditional long branches keep layout independent of final placement."""
    def jump(self, name, kind='BRA'):
        if kind == 'BRA':
            return super().jump(name, kind)
        self.fixups.append((len(self.data), self.pc, name, 'LONG_' + kind))
        self.emit(bytes(6), kind + ' ' + name)

    def finalize(self):
        for off, pc, name, kind in self.fixups:
            dest = self.labels[name]
            if kind == 'CALL':
                self.data[off:off+4] = absolute(0xEC00, dest)
            elif kind.startswith('LONG_'):
                inverse = {'BZ':0xE100, 'BNZ':0xE000, 'BC':0xE300, 'BNC':0xE200}[kind[5:]]
                self.data[off:off+6] = (inverse | 2).to_bytes(2, 'little') + absolute(0xEF00, dest)
            else:
                delta = (dest - pc - 2) // 2
                if not -1024 <= delta <= 1023:
                    raise ValueError('BRA range ' + name)
                self.data[off:off+2] = (0xD000 | (delta & 2047)).to_bytes(2, 'little')
        return bytes(self.data)

TARGETS = (0x200, 0x201, 0x202, 0x260, 0x261, 0x262)
FEC = (0x263, 0x264, 0x265)
HEAD, MODEL, PAGE = 0x26F, 0x270, 0x271
MANUAL_KIND, DIRTY = 0x203, 0x204
STEP, SELECTOR, SWITCH_KIND, COMMAND = 0x280, 0x281, 0x284, 0x285
CODE_CAP = 0xF800


def construct(original, base, imports=None):
    imports = dict(imports or {})
    camera_retry = imports.get('ui_camera_retry', 0x4000)
    persistence_commit = imports.get('persistence_commit', 0x4000)
    if base & 1 or camera_retry & 1 or persistence_commit & 1:
        raise ValueError('unaligned code address')
    if original[0x6B8E - 0x4000:0x6B92 - 0x4000] != bytes.fromhex('49 c0 1a f0'):
        raise ValueError('6B8E preimage is not original/P3')
    a = Asm(base)

    def bank0(): a.w(0x0100, 'MOVLB 0')
    def lit(value): a.w(0x0E00 | value, 'MOVLW %02X' % value)
    def movf(address):
        if address >= 0x100:
            a.movff(address, 0xFE8); a.w(0x0900, 'IORLW 0')
        else:
            a.w(0x5000 | address | (0x100 if address >= 0x60 else 0), 'MOVF %02X,W' % address)
    def store(address):
        if address >= 0x100: a.movff(0xFE8, address)
        else: a.w(0x6E00 | address | (0x100 if address >= 0x60 else 0), 'MOVWF %02X' % address)
    def clear(address): lit(0); store(address)
    def serial_literal(value): lit(value); a.call(0x9636)
    def ret(): bank0(); a.w(0x0012, 'RETURN')
    def valid_selector(prefix):
        # BSR-independent MOVFF into W; range checks use private BANK2 RAM.
        a.w(0x0102, 'MOVLB 2'); lit(1); a.w(0x5D81, 'SUBWF81,W,BANKED')
        a.jump(prefix + '_valid_low', 'BC'); ret(); a.label(prefix + '_valid_low')
        lit(8); a.w(0x5D81, 'SUBWF81,W,BANKED')
        a.jump(prefix + '_valid_high', 'BNC'); ret(); a.label(prefix + '_valid_high'); bank0()
    def selected(group, skip, enabled=True):
        movf(SELECTOR); a.w(0x0A00 | group, 'XORLW group')
        a.jump(skip + '_selected', 'BZ')
        movf(SELECTOR); a.w(0x0A07, 'XORLW ALL7'); a.jump(skip, 'BNZ')
        a.label(skip + '_selected')
        if enabled:
            movf(HEAD); a.w(0x0B00 | (1 << (group - 1)), 'ANDLW canonical Head bit')
            a.jump(skip, 'BZ')
    def basic_packet(group):
        movf(COMMAND); store(0x0A); lit(group); a.call(0x783E)

    a.label('radio_service')
    bank0()
    # Retain the old complete state machine only to drain existing A1 work.
    a.movff(0x49, 0x1A); a.call(0x6B92)
    movf(0x77); a.jump('radio_return', 'BNZ')
    a.call(0x96C4); a.w(0x0900, 'IORLW 0'); a.jump('radio_return', 'BNZ')
    movf(DIRTY); a.jump('radio_return', 'BZ')
    movf(MANUAL_KIND); a.w(0x0A02, 'XORLW A2'); a.jump('radio_return', 'BNZ')
    a.call_label('radio_send_snapshot'); clear(DIRTY)
    a.label('radio_return'); a.label('radio_retry_camera')
    a.call(camera_retry); a.call(persistence_commit); ret()

    a.label('radio_power_commit')
    # High private scratch survives all original UART helpers.
    a.movff(0xFE8, STEP); a.movff(0x003, SELECTOR); bank0()
    valid_selector('power')
    for step, command in ((1,6),(255,7),(10,13),(246,14)):
        movf(STEP); a.w(0x0A00 | step, 'XORLW accepted step')
        a.jump('power_step_%d' % step, 'BZ')
    ret()
    for step, command in ((1,6),(255,7),(10,13),(246,14)):
        a.label('power_step_%d' % step); lit(command); store(COMMAND); a.jump('power_valid')
    a.label('power_valid')
    movf(0x52); a.jump('power_manual', 'BZ')
    for group in range(1,4):
        skip = 'power_fec_skip_%d' % group
        selected(group, skip)
        a.jump('power_send_fec')
        a.label(skip)
    a.jump('power_manual')
    a.label('power_send_fec')
    a.call_label('radio_send_fec')
    a.label('power_manual')
    movf(MANUAL_KIND); a.w(0x0A02, 'XORLW A2'); a.jump('power_absolute', 'BZ')
    movf(MANUAL_KIND); a.w(0x0A01, 'XORLW A1'); a.jump('power_done', 'BNZ')
    for group in range(1,7):
        skip = 'power_relative_skip_%d' % group
        if group <= 3:
            movf(0x52); a.jump(skip, 'BNZ')
        selected(group, skip); basic_packet(group); a.label(skip)
    a.jump('power_done')
    a.label('power_absolute')
    for group in range(1,7):
        skip = 'power_absolute_skip_%d' % group
        if group <= 3:
            movf(0x52); a.jump(skip, 'BNZ')
        selected(group, skip); a.jump('power_send_absolute'); a.label(skip)
    a.jump('power_done')
    a.label('power_send_absolute'); a.call_label('radio_send_snapshot')
    a.label('power_done'); clear(DIRTY); a.call_label('radio_drain'); ret()

    a.label('radio_switch_commit')
    a.movff(0xFE8, SWITCH_KIND); a.movff(0x003, SELECTOR); bank0()
    valid_selector('switch')
    movf(SWITCH_KIND); a.jump('switch_valid', 'BZ')
    a.w(0x0A01, 'XORLW Model1'); a.jump('switch_valid', 'BZ'); ret()
    a.label('switch_valid')
    for group in range(1,7):
        skip = 'switch_skip_%d' % group
        selected(group, skip, enabled=False)
        movf(SWITCH_KIND); a.jump('switch_model_%d' % group, 'BNZ')
        movf(HEAD); a.w(0x0B00 | (1 << (group - 1)), 'ANDLW Head bit')
        a.jump('switch_head_off_%d' % group, 'BZ')
        lit(0); a.jump('switch_command_%d' % group)
        a.label('switch_head_off_%d' % group); lit(1); a.jump('switch_command_%d' % group)
        a.label('switch_model_%d' % group)
        movf(MODEL); a.w(0x0B00 | (1 << (group - 1)), 'ANDLW Model bit')
        a.jump('switch_model_off_%d' % group, 'BZ')
        lit(2); a.jump('switch_command_%d' % group)
        a.label('switch_model_off_%d' % group); lit(3)
        a.label('switch_command_%d' % group); store(COMMAND); basic_packet(group)
        # B10 ignores Model commands while Head is off. Reassert both ON and
        # OFF intentions after enabling Head; otherwise cached UI intent can
        # disagree with the receiver's retained Model state.
        movf(SWITCH_KIND); a.jump(skip, 'BNZ')
        movf(HEAD); a.w(0x0B00 | (1 << (group - 1)), 'ANDLW newly enabled Head')
        a.jump(skip, 'BZ')
        movf(MODEL); a.w(0x0B00 | (1 << (group - 1)), 'ANDLW saved Model intent')
        a.jump('switch_restore_model_off_%d' % group, 'BZ')
        lit(2); a.jump('switch_restore_model_send_%d' % group)
        a.label('switch_restore_model_off_%d' % group); lit(3)
        a.label('switch_restore_model_send_%d' % group); store(COMMAND); basic_packet(group)
        a.label(skip)
    a.call_label('radio_drain'); ret()

    a.label('radio_fec_refresh')
    a.label('radio_send_fec')
    # Original 79D8 constructs exactly three signed FEC slots, not six.
    bank0(); a.movff(FEC[1],4); a.movff(FEC[2],5); lit(0x25); store(6)
    movf(FEC[0]); a.call(0x79D8); a.call_label('radio_drain'); ret()

    a.label('radio_send_snapshot')
    for byte in b'RSGT1' + bytes([0x27,0xFF,0xFF,0xFF,1,0x11]): serial_literal(byte)
    for address in TARGETS: movf(address); a.call(0x9636)
    for address in (HEAD,MODEL):
        movf(address); a.w(0x0B3F, 'ANDLW 3F ; six valid mask bits'); a.call(0x9636)
    serial_literal(0); serial_literal(0)
    a.call_label('radio_drain'); lit(3); a.call(0x9226); ret()
    a.label('radio_drain')
    a.w(0x0004, 'CLRWDT'); a.w(0xA2AD, 'BTFSS TXSTA1.TRMT')
    a.jump('radio_drain'); a.w(0x0012, 'RETURN')

    blob = a.finalize()
    if a.pc > CODE_CAP or original[base-0x4000:a.pc-0x4000] != b'\xff' * len(blob):
        raise ValueError('radio exceeds reserved cap or occupied cave')
    changes = [(0x6B8E, absolute(0xEF00,a.labels['radio_service']),
                'drain legacy pending, optional canonical A2 snapshot, then camera/NVM services'),
               (base,blob,'P5 canonical six-group radio helpers')]
    metadata = {
        'status':'P5_EXPERIMENTAL_SIX_GROUP_UART_CANDIDATE',
        'exports':dict(a.labels), 'imports':{'ui_camera_retry':camera_retry,'persistence_commit':persistence_commit},
        'unresolved_imports':[k for k in ('ui_camera_retry','persistence_commit') if k not in imports],
        'tail_range':[base,a.pc], 'code_cap':CODE_CAP,
        'ram_contract':{'A2_targets':list(TARGETS),'TTL_FEC_ABC':list(FEC),'head_mask':HEAD,'model_mask':MODEL,'page':PAGE,
                        'manual_kind':MANUAL_KIND,'A2_dirty':DIRTY,'scratch':[STEP,SELECTOR,SWITCH_KIND,COMMAND],
                        'native_pending_preserved':[0x67,0x6E],'native_transaction_phase':0x77},
        'helper_abi':{'radio_power_commit':'W=int8(+1,-1,+10,-10),03=numeric selector1..6/7ALL; canonical already committed',
                      'radio_switch_commit':'W=0Head/1Model,03=numeric selector1..6/7ALL; canonical committed; HeadON reasserts canonical Model state',
                      'radio_fec_refresh':'no input; read canonical263..265 and send ABC cmd25, never visible DEF work',
                      'preserved':['1D','1E','26..2A','272..27F','canonical groups','67..6E on direct commits'],
                      'clobbered':['W','STATUS','01..0D','FSR1/2','PRODL/H','radio private280,281,284,285'], 'return_BSR':0},
        'power_commands':{'relative':{'+1':6,'-1':7,'+10':13,'-10':14},'absolute':17,'TTL_FEC':37},
        'frame':'RSGT1|27 FF FF FF 01 11|ABCDEF targets|HEAD6 MODEL6|00 00',
        'all_behavior':'enabled ABCDEF; TTL ALL sends ABC FEC then DEF manual; project extension',
        'TTL_A2_boundary':'DEF absolute edit sends full source-style cmd11 including ABC current power fields; next valid TTL exposure command reassigns automatic energy; not ABC zero-impact',
        'requires':['UI commits only after native77==0 and96C4==0 and no camera_pending',
                    'numeric selectors1..6/7, not bit masks','no guessed zero/FF absolute no-change sentinel'],
        'not_proven':['RF application ACK','physical timing','TTL TEST/preflash/transient exposure behavior','all receiver firmware compatibility']}
    return a,changes,metadata
