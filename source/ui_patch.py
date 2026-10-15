#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) 2026 Caimankekw
"""AIR2-P8 UI component. Pure offline PIC18 assembler; no device/USB access.

M targets are panel tenths 1..100, not claims about lamp minimum output.
Six-group canonical values are distinct from the three visible work slots.
Old 67..6E transactions may drain, but new edits use mapped radio imports.
"""

def need(ok, message):
    if not ok:
        raise ValueError(message)


def words(*values):
    return b''.join(v.to_bytes(2, 'little') for v in values)


def absolute(op, address):
    need(address % 2 == 0, 'unaligned target')
    return words(op | ((address // 2) & 255), 0xf000 | (address // 512))


class Asm:
    def __init__(self, base):
        self.base = base
        self.data = bytearray()
        self.labels = {}
        self.fixups = []
        self.notes = []

    @property
    def pc(self):
        return self.base + len(self.data)

    @property
    def code(self):
        return bytes(self.data)

    def emit(self, raw, note=''):
        self.notes.append((self.pc, note))
        self.data.extend(raw)

    def w(self, value, note=''):
        self.emit(words(value), note)

    def label(self, name):
        need(name not in self.labels, 'duplicate label')
        self.labels[name] = self.pc

    def call(self, address):
        self.emit(absolute(0xec00, address), 'CALL %04X' % address)

    def goto(self, address):
        self.emit(absolute(0xef00, address), 'GOTO %04X' % address)

    def movff(self, source, target):
        self.emit(words(0xc000 | source, 0xf000 | target), 'MOVFF %03X,%03X' % (source, target))

    def jump(self, label, kind='BRA'):
        self.fixups.append((len(self.data), self.pc, label, kind))
        self.emit(words(0, 0) if kind in ('CALL', 'GOTO') else words(0), kind + ' ' + label)

    def finish(self):
        for offset, pc, label, kind in self.fixups:
            target = self.labels[label]
            if kind in ('CALL', 'GOTO'):
                self.data[offset:offset + 4] = absolute(0xec00 if kind == 'CALL' else 0xef00, target)
            else:
                delta = (target - pc - 2) // 2
                need(-1024 <= delta <= 1023 if kind == 'BRA' else -128 <= delta <= 127, 'branch range ' + label)
                opcode = 0xd000 | (delta & 2047) if kind == 'BRA' else {'BZ': 0xe000, 'BNZ': 0xe100, 'BC': 0xe200, 'BNC': 0xe300}[kind] | (delta & 255)
                self.data[offset:offset + 2] = words(opcode)


def construct(original, base=0x99c8, imports=None):
    imports = imports or {}
    a = Asm(base)
    patches, hooks = [], []
    targets = (0x200,0x201,0x202,0x260,0x261,0x262)
    def bank0(): a.w(0x0100)
    def lit(v): a.w(0x0e00 | (v & 255))
    def mf(f):
        if f >= 0x100: a.movff(f,0xfe8);a.w(0x0900)
        else: a.w(0x5000|f|(0x100 if f>=0x60 else 0))
    def mw(f):
        if f >= 0x100:a.movff(0xfe8,f)
        else:a.w(0x6e00|f|(0x100 if f>=0x60 else 0))
    def cl(f):
        if f>=0x100:lit(0);mw(f)
        else:a.w(0x6a00|f|(0x100 if f>=0x60 else 0))
    def setv(f,v):lit(v);mw(f)
    def ret():a.w(0x0012)
    def call(label):a.jump(label,'CALL')
    def go(label,cond=None):
        if cond:
            # Inverse conditional skips one four-byte absolute GOTO.
            a.w({'BZ':0xe102,'BNZ':0xe002,'BC':0xe302,'BNC':0xe202}[cond])
        a.jump(label,'GOTO')
    def imp(name):a.call(imports.get(name,0x4000))
    def xor(v):a.w(0x0a00|v)
    def icon(code,on):setv(7,on);lit(code);a.call(0x55c8)
    def fec_copy(save):
        for i,f in enumerate((0x263,0x264,0x265),2):
            a.emit(words(0xee20,0xf000|i));a.call(0x6226)
            a.movff(f,0xfdf) if save else a.movff(0xfdf,f)
    def eligible(g, skip):
        mf(0x273);xor(7);go('eligible_%s_%d'%(skip,g),'BZ')
        mf(0x273);xor(g+1);go(skip,'BNZ')
        a.label('eligible_%s_%d'%(skip,g));mf(0x26f);a.w(0x0b00|(1<<g));go(skip,'BZ')

    # Cooperative first-key arbitration: native key service is called once per main loop.
    # No software-clock wait is performed inside a poll. 65:66 is the native fine clock.
    a.label('key_service');bank0();mf(0x2c0);go('pending_poll','BNZ')
    a.call(0x674a);mw(0x2b);a.w(0x0900);go('pending_return','BZ')
    for key in (6,7,10):mf(0x2b);xor(key);go('pending_begin','BZ')
    a.goto(0x8bce)
    a.label('pending_begin');setv(0x207,1);setv(0x2c0,1);cl(0x2cb)
    a.movff(0x2b,0x2c1)
    for src,dst in ((0x65,0x2c2),(0x66,0x2c3),(0x65,0x2ce),(0x66,0x2cf),
                    (0x52,0x2c7),(0x203,0x2c8),(0x271,0x2c9),(0x4e,0x2ca)):
        a.movff(src,dst)
    cl(0x2cc);cl(0x2cd);call('sample_chord_keys');mw(0x2c4);call('stable_stamp')
    for pattern in (6,7,0x80,255):mf(0x2c4);xor(pattern);go('pending_begin_cancel','BZ')
    mf(0x2c4);go('pending_begin_ready','BZ');call('first_key_mask');a.movff(0x2c4,4);a.w(0x1404);go('pending_begin_cancel','BZ')
    a.label('pending_begin_ready');call('ready_for_edit');a.w(0x0900);go('pending_begin_cancel','BZ')
    # Run the original backlight/idle/activity prefix once, then key_entry returns pending.
    a.goto(0x8bce)
    a.label('pending_begin_cancel');call('pending_cancel');a.goto(0x8bce)

    a.label('pending_poll');mf(0x2c0);xor(2);go('release_poll','BZ')
    # Any domain transition or old in-flight transaction invalidates this gesture.
    for src,saved in ((0x52,0x2c7),(0x203,0x2c8),(0x271,0x2c9),(0x4e,0x2ca)):
        a.movff(src,4);mf(saved);a.w(0x1804);go('pending_cancel','BNZ')
    call('ready_for_edit');a.w(0x0900);go('pending_cancel','BZ')
    call('pending_clock_watch');a.w(0x0900);go('pending_cancel','BZ')
    call('sample_chord_keys');mw(0x27a)
    for pattern in (6,7,0x80,255):mf(0x27a);xor(pattern);go('pending_cancel','BZ')
    a.movff(0x2c4,4);mf(0x27a);a.w(0x1804);go('pending_same','BZ')
    # A formed candidate cannot degrade into a single or change to another chord.
    for pattern in (3,5):mf(0x2c4);xor(pattern);go('pending_cancel','BZ')
    mf(0x27a);go('pending_new_candidate','BZ')
    for pattern in (3,5):mf(0x27a);xor(pattern);go('pending_new_chord','BZ')
    call('first_key_mask');a.movff(0x27a,4);a.w(0x1804);go('pending_cancel','BNZ')
    go('pending_new_candidate')
    a.label('pending_new_chord')
    call('first_key_mask');a.movff(0x27a,4);a.w(0x1404);go('pending_cancel','BZ')
    call('window_expired');a.w(0x0900);go('dispatch_held_single','BNZ')
    a.label('pending_new_candidate');a.movff(0x27a,0x2c4);call('stable_stamp');ret()
    a.label('pending_same');call('stable_elapsed');a.w(0x0900);go('pending_return','BZ')
    mf(0x27a);go('dispatch_released_single','BZ')
    for pattern in (3,5):mf(0x27a);xor(pattern);go('dispatch_chord','BZ')
    call('window_expired');a.w(0x0900);go('dispatch_held_single','BNZ');ret()

    a.label('dispatch_chord');setv(0x2c0,2);setv(0x267,1);setv(0x2c4,255)
    mf(0x27a);xor(3);go('dispatch_page_chord','BNZ');call('manual_toggle');ret()
    a.label('dispatch_page_chord');call('page_toggle');a.w(0x0900);go('pending_return','BZ');call('page_hint');ret()
    a.label('dispatch_released_single');setv(0x2cb,1);go('dispatch_single')
    a.label('dispatch_held_single');setv(0x2cb,2)
    a.label('dispatch_single');cl(0x2c0);cl(0x267);a.movff(0x2c1,0x2b);a.goto(0x8be4)

    a.label('pending_cancel');setv(0x2c0,2);setv(0x267,1);setv(0x2c4,255);ret()
    a.label('release_poll');call('sample_chord_keys');mw(0x27a);a.w(0x0900);go('release_not_zero','BNZ')
    mf(0x2c4);go('release_stable_zero','BZ');cl(0x2c4);call('stable_stamp');ret()
    a.label('release_stable_zero');call('stable_elapsed');a.w(0x0900);go('pending_return','BZ')
    cl(0x2c0);cl(0x267);cl(0x2cb);go('after_key')
    a.label('release_not_zero');setv(0x2c4,255)
    a.label('pending_return');ret()

    a.label('first_key_mask');mf(0x2c1);xor(10);go('first_not_c','BNZ');a.w(0x0c01)
    a.label('first_not_c');mf(0x2c1);xor(6);go('first_is_head','BNZ');a.w(0x0c02)
    a.label('first_is_head');a.w(0x0c04)
    a.label('stable_stamp');a.movff(0x65,0x2c5);a.movff(0x66,0x2c6);ret()
    # Elapsed is modulo 0x8000, matching the original deadline half-ring.
    for name,lo,threshold in (('window_expired',0x2c2,200),('stable_elapsed',0x2c5,10)):
        a.label(name);mf(lo);a.w(0x5d65);mw(4)
        mf(lo+1);a.w(0x5966);a.w(0x0b7f);go(name+'_yes','BNZ')
        lit(threshold);a.w(0x5c04);go(name+'_no','BNC')
        a.label(name+'_yes');a.w(0x0c01)
        a.label(name+'_no');a.w(0x0c00)
    a.label('pending_clock_watch')
    a.movff(0x65,4);mf(0x2ce);a.w(0x1804);go('pending_clock_advanced','BNZ')
    a.movff(0x66,4);mf(0x2cf);a.w(0x1804);go('pending_clock_advanced','BNZ')
    mf(0x2cc);a.w(0x0f01);mw(0x2cc);go('pending_clock_carry','BC');go('pending_clock_check')
    a.label('pending_clock_carry');mf(0x2cd);a.w(0x0f01);mw(0x2cd)
    a.label('pending_clock_check');mf(0x2cd);a.w(0x0bf0);go('pending_clock_stalled','BNZ');a.w(0x0c01)
    a.label('pending_clock_advanced');a.movff(0x65,0x2ce);a.movff(0x66,0x2cf);cl(0x2cc);cl(0x2cd);a.w(0x0c01)
    a.label('pending_clock_stalled');a.w(0x0c00)

    a.label('key_entry');bank0();setv(0x207,1)
    mf(0x2c0);go('pending_return','BNZ')
    go('key_dispatch')

    a.label('sample_chord_keys')
    # C is an independent digital input; MODEL and HEAD are different windows
    # of the SAME ADC field0. No claim is made about two-key analog aliases.
    a.movff(0xfc2,0x27b);a.w(0xb2c2);go('sample_fault')
    mf(0xf81);a.w(0x0bc3);xor(0xc3);go('sample_other_early','BNZ')
    mf(0xf80);a.w(0x0b04);mw(0x27c);cl(0x27d)
    mf(0x27c);go('sample_c_ready','BNZ');setv(0x27d,1)
    a.label('sample_c_ready');lit(0);call('convert_key_adc');a.w(0x0900);go('sample_fault_restore','BZ')
    call('classify_key_adc');xor(3);go('sample_other_restore','BZ')
    mf(4);xor(1);go('sample_not_model','BNZ');mf(0x27d);a.w(0x0902);mw(0x27d);go('sample_second_channel')
    a.label('sample_not_model');mf(4);xor(2);go('sample_second_channel','BNZ');mf(0x27d);a.w(0x0904);mw(0x27d)
    a.label('sample_second_channel');lit(4);call('convert_key_adc');a.w(0x0900);go('sample_fault_restore','BZ')
    call('classify_key_adc');a.w(0x0900);go('sample_other_restore','BNZ')
    # All other digital keys must remain released; C must not change mid-sample.
    mf(0xf81);a.w(0x0bc3);xor(0xc3);go('sample_other_restore','BNZ')
    a.movff(0x27c,4);mf(0xf80);a.w(0x0b04);a.w(0x1804);go('sample_other_restore','BNZ')
    mf(0x27d);mw(0x27f);go('sample_restore')
    a.label('sample_other_restore');setv(0x27f,0x80);go('sample_restore')
    a.label('sample_fault_restore');setv(0x27f,255)
    a.label('sample_restore');a.movff(0x27b,0xfc2);mf(0x27f);ret()
    a.label('sample_other_early');a.w(0x0c80)
    a.label('sample_fault');a.w(0x0cff)
    a.label('convert_key_adc');mw(4);mf(0x27b);a.w(0x0bc0);a.w(0x1004);a.w(0x0901);mw(0xfc2)
    a.w(0x82c2);cl(8);setv(9,0x40)
    a.label('adc_conversion_wait');a.w(0x0004);a.w(0xa2c2);go('adc_conversion_done')
    a.w(0x2e08);go('adc_conversion_wait');a.w(0x2e09);go('adc_conversion_wait');a.w(0x0c00)
    a.label('adc_conversion_done');a.w(0x0c01)
    a.label('classify_key_adc')
    # Original ADC windows: high923..1023 ->1, middle412..612 ->2, low60..260 ->3.
    a.call(0x6826);go('adc_class_middle','BNC');lit(4);a.w(0x5c06);go('adc_class_middle','BC');setv(4,1);a.w(0x0c01)
    a.label('adc_class_middle');a.call(0x684e);go('adc_class_low','BNC');a.call(0x6858);go('adc_class_middle_hit','BNC')
    a.label('adc_class_low');mf(6);go('adc_class_low_upper','BNZ');lit(60);a.w(0x5c05);go('adc_class_none','BNC')
    a.label('adc_class_low_upper');a.call(0x6844);go('adc_class_low_hit','BNC')
    a.label('adc_class_none');cl(4);a.w(0x0c00)
    a.label('adc_class_middle_hit');setv(4,2);a.w(0x0c02)
    a.label('adc_class_low_hit');setv(4,3);a.w(0x0c03)
    a.label('key_dispatch')
    for key,label in ((4,'power_key'),(5,'power_key'),(6,'model_key'),(7,'head_key'),(8,'select_1'),(9,'select_2'),(10,'select_3')):
        mf(0x1e);xor(key);go(label,'BZ')
    lit(1);mw(0x26);a.goto(0x4f7e)

    a.label('ready_to_switch');bank0();mf(0x77);go('switch_busy','BNZ')
    a.call(0x96c4);a.w(0x0900);go('switch_busy','BNZ');a.w(0x0c01)
    a.label('switch_busy');a.w(0x0c00)
    a.label('ready_for_edit');mf(0x206);go('switch_busy','BNZ');go('ready_to_switch')
    a.label('physical_selector');mf(0x4e);xor(7);go('selector_all','BZ')
    mf(0x4e);go('selector_bad','BZ');lit(3);a.w(0x644e);go('selector_valid');go('selector_bad')
    a.label('selector_valid');mf(0x271);go('selector_abc','BZ');mf(0x4e);a.w(0x0f03);ret()
    a.label('selector_abc');mf(0x4e);ret()
    a.label('selector_all');a.w(0x0c07)
    a.label('selector_bad');a.w(0x0c00)

    a.label('power_key');call('ready_for_edit');a.w(0x0900);go('key_release','BZ')
    call('physical_selector');mw(0x273);a.w(0x0900);go('key_release','BZ')
    # +/- never participate in combo pending; retain the original short/long detector.
    a.label('power_native_hold');lit(0x29);mw(7);a.movff(0x1e,8);cl(9);a.call(0x8acc);mw(0x2a)
    a.label('key_repeat_step');mf(0x2a);lit(1);mw(0x27);go('step_ready','BZ');setv(0x27,10)
    a.label('step_ready');cl(0x274)
    for g in range(6):
        skip='preflight_skip_%d'%g;eligible(g,skip);setv(0x274,1)
        call('get_%d'%g);call('adjust_value');mf(0x275);go('key_finish','BZ');a.label(skip)
    mf(0x274);go('key_finish','BZ')
    for g in range(6):
        skip='apply_skip_%d'%g;eligible(g,skip);call('get_%d'%g);call('adjust_value');call('put_%d'%g)
        if g<3:mf(0x52);go(skip,'BNZ')
        mf(0x203);xor(1);go(skip,'BNZ');mf(0x266);a.w(0x0900|(1<<g));mw(0x266)
        a.label(skip)
    call('sync_fec');setv(0x205,1);setv(0x204,1)
    # Canonical state is committed atomically before any RF request.
    a.movff(0x273,3);mf(0x1e);xor(4);go('power_up_parameter','BNZ')
    a.w(0x1c27,'COMF27,W');a.w(0x0f01);go('power_send')
    a.label('power_up_parameter');mf(0x27)
    a.label('power_send');imp('radio_power_commit');bank0();call('redraw_all')
    mf(0x2a);go('key_check_repeat','BZ')
    lit(0x29);mw(7);a.movff(0x1e,8);cl(9);a.call(0x8acc)
    a.label('key_check_repeat');mf(0x1e);a.w(0x1829);go('key_repeat_step','BZ')
    a.label('key_finish');a.call(0x9086);lit(1);a.goto(0x7ae4)
    a.label('key_release');a.goto(0x9086)

    a.label('adjust_value')
    # Bias maps signed FEC/relative and positive absolute domains to 0..max.
    a.w(0x2428);mw(0x272);mf(0x1e);xor(4);go('adjust_down','BZ')
    mf(0x27);a.movff(0x272,0x28);a.w(0x2428);go('adjust_check')
    a.label('adjust_down');mf(0x27);a.movff(0x272,0x28);a.w(0x5c28);go('adjust_bad','BNC')
    a.label('adjust_check');mw(0x272);a.movff(0x272,0x28);mf(0x26);a.w(0x6428);go('adjust_valid');go('adjust_bad')
    a.label('adjust_valid');setv(0x275,1);mf(0x276);a.movff(0x272,0x28);a.w(0x5c28);ret()
    a.label('adjust_bad');cl(0x275);ret()

    for g in range(6):
        a.label('get_%d'%g)
        if g<3:
            mf(0x52);go('get_manual_%d'%g,'BZ');setv(0x28,20);setv(0x276,20);setv(0x26,40);mf(0x263+g);ret()
            a.label('get_manual_%d'%g)
        mf(0x203);xor(2);go('get_relative_%d'%g,'BNZ')
        setv(0x28,255);setv(0x276,255);setv(0x26,99);mf(targets[g]);ret()
        a.label('get_relative_%d'%g);setv(0x28,99);setv(0x276,99);setv(0x26,198);mf(0x269+g);ret()
        a.label('put_%d'%g);mw(0x272)
        if g<3:
            mf(0x52);go('put_manual_%d'%g,'BZ');a.movff(0x272,0x263+g);ret();a.label('put_manual_%d'%g)
        mf(0x203);xor(2);go('put_relative_%d'%g,'BNZ');a.movff(0x272,targets[g]);ret()
        a.label('put_relative_%d'%g);a.movff(0x272,0x269+g);ret()

    a.label('head_key');cl(0x278);go('switch_key')
    a.label('model_key');setv(0x278,1)
    a.label('switch_key');call('ready_for_edit');a.w(0x0900);go('key_release','BZ')
    call('physical_selector');mw(0x273);a.w(0x0900);go('key_release','BZ')
    mf(0x278);go('switch_model_read','BNZ');a.movff(0x26f,0x272);go('switch_modify')
    a.label('switch_model_read');a.movff(0x270,0x272)
    a.label('switch_modify');mf(0x273);xor(7);go('switch_single','BNZ')
    mf(0x272);xor(63);lit(0);go('switch_store','BZ');lit(63);go('switch_store')
    a.label('switch_single')
    for g in range(6):
        mf(0x273);xor(g+1);go('switch_not_%d'%g,'BNZ');mf(0x272);xor(1<<g);go('switch_store');a.label('switch_not_%d'%g)
    go('key_release')
    a.label('switch_store');mw(0x272);mf(0x278);go('switch_model_store','BNZ');a.movff(0x272,0x26f);go('switch_submit')
    a.label('switch_model_store');a.movff(0x272,0x270)
    a.label('switch_submit');setv(0x205,1);a.movff(0x273,3);mf(0x278);imp('radio_switch_commit');bank0();call('redraw_all');a.goto(0x9086)

    a.label('page_key');go('select_1')
    a.label('page_toggle');call('ready_for_edit');a.w(0x0900);go('page_toggle_busy','BZ')
    mf(0x271);xor(1);mw(0x271);setv(0x205,1);call('load_page');a.w(0x0c01)
    a.label('page_toggle_busy');a.w(0x0c00)
    for row in (1,2,3):
        a.label('select_%d'%row);call('ready_for_edit');a.w(0x0900);go('key_release','BZ')
        mf(0x4e);xor(row);lit(7);go('select_store_%d'%row,'BZ');lit(row)
        a.label('select_store_%d'%row);mw(0x4e);call('is_relative_page');a.w(0x0900);go('selection_redraw_%d'%row,'BZ');call('clear_relative')
        a.label('selection_redraw_%d'%row);call('redraw_all');a.goto(0x9086)
    a.label('page_hint')
    for row in range(1,4):
        for c in (3*row+1,3*row+2):icon(c,0)
        cl(7);lit(row);a.call(0x7be6)
        mf(0x271);go('hint_abc_%d'%row,'BZ');lit(0x0c+row);go('hint_draw_%d'%row)
        a.label('hint_abc_%d'%row);lit(0x09+row)
        a.label('hint_draw_%d'%row);mw(4);lit(2*row-1);a.call(0x5bf8)
        setv(4,0x64);lit(2*row);a.call(0x5bf8)
    ret()

    a.label('reset_entered_a1');mf(0x52);go('reset_a1_return','BNZ');mf(0x203);xor(1);go('reset_a1_return','BNZ')
    call('clear_relative')
    a.label('reset_a1_return');ret()
    a.label('clear_relative');cl(0x266)
    for f in range(0x269,0x26f):cl(f)
    ret()
    a.label('mode_gate');call('ready_for_edit');a.w(0x0900);go('mode_return','BZ')
    mf(0x52);xor(1);mw(0x52);call('reset_entered_a1');setv(0x205,1);cl(0x204);call('load_page');a.goto(0x6136)
    a.label('mode_return');ret()
    a.label('manual_toggle');mf(0x52);go('mode_return','BNZ');call('ready_for_edit');a.w(0x0900);go('mode_return','BZ')
    mf(0x203);xor(3);mw(0x203);call('reset_entered_a1');cl(0x204);setv(0x205,1);go('redraw_all')
    a.label('settings_force_ttl');setv(0x52,1);setv(0x205,1);call('load_page');a.goto(0x6186)
    a.label('clear_or_load');call('load_page');a.movff(0x4e,3);a.w(0x0c00)
    a.label('relative_writer');a.w(0x0c00)
    a.label('idle_preserve_m');mf(0x203);xor(1);go('idle_return','BNZ')
    call('ready_for_edit');a.w(0x0900);go('idle_return','BZ')
    mf(0x266);go('idle_clear_relative','BNZ')
    for f in range(0x269,0x26f):mf(f);go('idle_clear_relative','BNZ')
    a.label('idle_return');ret()
    a.label('idle_clear_relative')
    call('clear_relative');go('redraw_all')
    a.label('idle_mode_gate');mf(0x52);go('idle_native_continue','BZ');mf(0x203);xor(1);go('idle_return','BNZ')
    a.label('idle_native_continue');a.goto(0x9372)

    a.label('camera_mode');mf(0x2c0);xor(1);go('camera_request_store','BNZ');call('pending_cancel')
    a.label('camera_request_store');setv(0x206,1);go('camera_retry')
    a.label('camera_retry');mf(0x206);go('camera_return','BZ');call('ready_to_switch');a.w(0x0900);go('camera_return','BZ')
    a.movff(0x52,0x279);a.emit(words(0xee20,0xf005));a.call(0x6226);a.call(0x91a4)
    mf(0x279);a.w(0x1852);go('camera_unchanged','BZ');call('reset_entered_a1');cl(0x204);setv(0x205,1)
    a.label('camera_unchanged');cl(0x206);call('redraw_all');mf(0x52);go('camera_return','BZ');imp('radio_fec_refresh');bank0()
    a.label('camera_return');ret()

    a.label('startup_targets');bank0();fec_copy(False)
    for f in range(0x269,0x26f):cl(f)
    for f in (0x44,0x45,0x46,0x47):cl(f)
    imp('persistence_init');bank0();setv(0x203,1)
    for f in (0x204,0x206,0x207,0x266,0x267)+tuple(range(0x2c0,0x2d0)):cl(f)
    mf(0x209);xor(2);go('startup_subtype_ready','BNZ');setv(0x203,2)
    a.label('startup_subtype_ready');mf(0x208);go('startup_saved_ttl','BZ');xor(1);go('startup_saved_a1','BZ')
    mf(0x208);xor(2);go('startup_bank_load','BNZ');setv(0x203,2);go('startup_saved_manual')
    a.label('startup_saved_a1');setv(0x203,1)
    a.label('startup_saved_manual');cl(0x52);go('startup_sync_mode')
    a.label('startup_saved_ttl');setv(0x52,1)
    a.label('startup_sync_mode');a.emit(words(0xee20,0xf005));a.call(0x6226)
    mf(0x52);lit(1);a.w(0xa4d8);lit(0);a.w(0x6edf)
    a.label('startup_bank_load');go('load_page')
    a.label('sync_fec');fec_copy(True);ret()
    a.label('fec_parameters');a.movff(0x264,4);a.movff(0x265,5);setv(6,0x25);mf(0x263);ret()

    a.label('load_page');bank0();mf(0x271);go('load_def','BNZ')
    for page in range(2):
        if page:a.label('load_def')
        for row in range(3):
            g=page*3+row;call('get_%d'%g);mw(0x3f+row)
            setv((0x47,0x46,0x45)[row],1);mf(0x26f);a.w(0x0b00|(1<<g));go('head_project_%d'%g,'BZ');cl((0x47,0x46,0x45)[row])
            a.label('head_project_%d'%g);cl((0x51,0x50,0x4f)[row]);mf(0x270);a.w(0x0b00|(1<<g));go('model_project_%d'%g,'BZ');setv((0x51,0x50,0x4f)[row],1)
            a.label('model_project_%d'%g)
        if not page:go('load_aggregate')
    a.label('load_aggregate');cl(0x44);mf(0x26f);go('aggregate_head_done','BNZ');setv(0x44,1)
    a.label('aggregate_head_done');cl(0x7f);mf(0x270);xor(63);go('aggregate_model_done','BNZ');setv(0x7f,1)
    a.label('aggregate_model_done');ret()

    a.label('after_key');mf(0x2c0);go('after_key_pending','BNZ');cl(0x207);cl(0x2cb);imp('persistence_commit');bank0();call('redraw_all')
    a.label('after_key_pending');a.goto(0x89bc)
    a.label('display_mode');go('redraw_all')
    a.label('redraw_all');call('load_page');mf(0x52);go('draw_native_man','BZ');a.call(0x5dd8);go('draw_values')
    a.label('draw_native_man');a.call(0x5e78)
    a.label('draw_values')
    for row,flag,f,entry in ((1,0x47,0x3f,0x84c2),(2,0x46,0x40,0x8414),(3,0x45,0x41,0x83bc)):
        mf(flag);go('draw_enabled_%d'%row,'BZ')
        for c in (3*row+1,3*row+2):icon(c,0)
        cl(7);lit(row);a.call(0x7be6)
        for pos in (2*row-1,2*row):setv(4,0x6b);lit(pos);a.call(0x5bf8)
        go('draw_next_%d'%row)
        a.label('draw_enabled_%d'%row);call('is_relative_page');a.w(0x0900);go('draw_numeric_%d'%row,'BZ')
        mf(0x271);go('visible_def_%d'%row,'BNZ');mf(0x266);a.w(0x0b00|(1<<(row-1)));go('visible_test_%d'%row)
        a.label('visible_def_%d'%row);mf(0x266);a.w(0x0b00|(1<<(row+2)))
        a.label('visible_test_%d'%row);go('draw_numeric_%d'%row,'BNZ')
        call('blank_relative_%d'%row)
        go('draw_next_%d'%row)
        a.label('draw_numeric_%d'%row);mf(f);a.call(entry)
        a.label('draw_next_%d'%row)
        # Model marks and selected row boxes are independently projected.
        cl(7);mf(flag);go('draw_model_%d'%row,'BNZ');mf((0x51,0x50,0x4f)[row-1]);mw(7)
        a.label('draw_model_%d'%row);lit((0x0e,0x10,0x11)[row-1]);a.call(0x55c8)
        cl(7);mf(0x4e);xor(7);go('box_on_%d'%row,'BZ');mf(0x4e);xor(row);go('box_draw_%d'%row,'BNZ')
        a.label('box_on_%d'%row);setv(7,1)
        a.label('box_draw_%d'%row);lit(row);a.call(0x55c8)
    for code in (0x65,0x66,0x67):
        mf(0x271);lit(1);a.w(0xa4d8);lit(0);mw(7);lit(code);a.call(0x55c8)
    ret()
    a.label('is_a2');mf(0x203);xor(2);go('not_a2','BNZ');mf(0x52);go('yes_a2','BZ');mf(0x271);go('not_a2','BZ')
    a.label('yes_a2');a.w(0x0c01)
    a.label('not_a2');a.w(0x0c00)
    a.label('is_relative_page');mf(0x203);xor(1);go('not_a2','BNZ');mf(0x52);go('yes_a2','BZ');mf(0x271);go('not_a2','BZ');go('yes_a2')
    for row,entry in ((1,0x84c2),(2,0x8414),(3,0x83bc)):
        a.label('format_%d'%row);mw(0x11);call('is_relative_page');a.w(0x0900);go('format_check_kind_%d'%row,'BZ')
        mf(0x271);go('format_visible_def_%d'%row,'BNZ');mf(0x266);a.w(0x0b00|(1<<(row-1)));go('format_visible_test_%d'%row)
        a.label('format_visible_def_%d'%row);mf(0x266);a.w(0x0b00|(1<<(row+2)))
        a.label('format_visible_test_%d'%row);go('blank_relative_%d'%row,'BZ')
        a.label('format_check_kind_%d'%row);call('is_a2');a.w(0x0900);go('format_absolute_%d'%row,'BNZ');cl(7);a.goto(entry+4)
        a.label('format_absolute_%d'%row)
        for c in (3*row+1,3*row+2):icon(c,0)
        mf(0x11);xor(100);go('format_fraction_%d'%row,'BNZ');setv(0x0b,10);cl(0x0c);go('format_output_%d'%row)
        a.label('format_fraction_%d'%row);a.movff(0x11,0x0b);setv(0x0c,1)
        a.label('format_output_%d'%row);lit(row);a.goto(0x7a5e)
        a.label('blank_relative_%d'%row)
        for c in (3*row+1,3*row+2):icon(c,0)
        cl(7);lit(row);a.call(0x7be6)
        for pos in (2*row-1,2*row):setv(4,0x64);lit(pos);a.call(0x5bf8)
        ret()

    a.finish()
    def hook(address, expected, label, reason):
        before=bytes.fromhex(expected)
        need(original[address-0x4000:address-0x4000+len(before)]==before,'hook preimage %04X'%address)
        after=absolute(0xef00,a.labels[label])+words(*([0]*((len(before)-4)//2)))
        patches.append((address,after,reason));hooks.append(dict(address=address,before_hex=before.hex(),after_hex=after.hex(),target=a.labels[label],reason=reason))
    for addr,old,label,reason in (
        (0x8bc2,'a5ec33f0','key_service','Cooperative first-key pending window before native activity dispatch'),
        (0x4f7a,'010e266e','key_entry','Six-group edit with C-HEAD paging/C-MODEL manual preference'),
        (0x60ea,'62ec4bf0','mode_gate','Binary mode with canonical bank and idle gate'),
        (0x6182,'010e526e','settings_force_ttl','Settings force TTL without losing manual preference'),
        (0x6230,'3f6a406a','clear_or_load','Retire projection clear; load canonical current page'),
        (0x9188,'20ee05f013ec31f009d8','camera_mode','Deferred camera mode and canonical FEC refresh'),
        (0x8d50,'476a466a','startup_targets','V4 canonical state restore then page projection'),
        (0x819c,'475008e1','idle_preserve_m','Native idle timing clears six relative canonical values only'),
        (0x936c,'5250d8a4','idle_mode_gate','Existing B1 idle deadline also hides TTL DEF AIR1 relative values'),
        (0x885a,'046e0350','relative_writer','Retire native pending writer; new power commits directly'),
        (0x8bf0,'deef44f0','after_key','Persist released edits and redraw current page'),
        (0x5dd4,'525050e0','display_mode','Canonical page rendering with true global mode label'),
        (0x5510,'40c004f0','fec_parameters','ABC FEC packet parameters never read DEF work window')):
        hook(addr,old,label,reason)
    for row,entry in ((1,0x84c2),(2,0x8414),(3,0x83bc)):
        hook(entry,'116e076a','format_%d'%row,'Effective page absolute/manual formatter')
    need(a.pc<=0xf800,'UI overlaps persistence pages')
    need(original[base-0x4000:a.pc-0x4000]==b'\xff'*len(a.code),'UI cave not erased')
    patches.append((base,a.code,'AIR2-P8 C-HEAD/C-MODEL combos and direct power keys'))
    names=('persistence_init','persistence_commit','radio_power_commit','radio_switch_commit','radio_fec_refresh')
    metadata=dict(version=8,status='EXPERIMENTAL_OFFLINE_COMPONENT',exports=dict(a.labels),hooks=hooks,imports={n:imports.get(n,0x4000) for n in names},
        ram={'A2_targets':list(targets),'ABC_FEC':[0x263,0x264,0x265],'relative_visible':0x266,'chord_latched':0x267,'A1_relative':list(range(0x269,0x26f)),'head_mask':0x26f,'model_mask':0x270,'page':0x271,'manual_kind':0x203,'sender_dirty':0x204,'nv_dirty':0x205,'camera_pending':0x206,'key_active':0x207,'startup_mode_token':0x208,'startup_last_manual_token':0x209,'pending_state':0x2c0,'pending_first_key':0x2c1,'pending_start':[0x2c2,0x2c3],'pending_candidate':0x2c4,'pending_stable_start':[0x2c5,0x2c6],'pending_domain':[0x2c7,0x2c8,0x2c9,0x2ca],'pending_dispatch':0x2cb,'pending_stall_count':[0x2cc,0x2cd],'pending_last_tick':[0x2ce,0x2cf],'scratch':list(range(0x272,0x280)),'mode':0x52,'active':[0x3f,0x40,0x41]},
        panel_range=[1,100],relative_range=[-99,99],fec_range=[-20,20],requires_radio_6B8E_replacement=True,source_dependencies=['ui_patch.py'],
        behavior=['All six canonical states are separate from the three-row projection','TTL ABC FEC; TTL DEF last-manual relative/absolute; mixed ALL is explicit new policy','Atomic bounds reject for all selected enabled groups','Only C/HEAD/MODEL enter200-fine pending; A/B/+/- take the direct original short/long key path', 'C+HEAD pages in every mode; C+MODEL toggles A1/A2 only in MAN and is swallowed without preference change in TTL', 'MODEL/HEAD share ADCfield0: their simultaneous analog alias is unknown, not a provable bitmask6/7', 'No C selection or Head/Model change before pending single/combination resolution','Combination/release stability needs repeated raw samples spanning at least 10 native fine counts; no millisecond calibration claim','A legal combination first seen before count200 may finish confirmation later; after timeout only the first single may dispatch','4096 consecutive polls without fine-clock progress cancel; domain change or queue/camera busy also cancels until stable release','Pending C/HEAD/MODEL returns to main; A/B/+/- have no combination window; native8ACC/9086 and synchronous TX limits remain','Chord latch clears only after stable all-released sampling; ADC busy/timeout fails closed','DEF hides fixed ABC glass labels; temporary d/E/F; true global TTL/MAN label retained','Head/Model six-group masks; ALL all-on unless already all-on','No MAN blinking; A2 values stay visible, A1 values only after adjustment until entry/selection/idle clear; Head OFF is --','Mode preserves last manual subtype; canonical ABC FEC continuously mirrors native object','Existing B1 idle timing clears A1 six relative values/visibility in MAN or TTL DEF without radio/NVM; old queue drains before edits','Radio TX/ACK are not RF-completion guarantees'])
    return a,patches,metadata
