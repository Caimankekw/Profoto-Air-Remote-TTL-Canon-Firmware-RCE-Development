#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (c) Caimankekw. Authored offline candidate builder.
"""Build a C11 native-backend policy EXPERIMENT. Does not access hardware.

Source-only assembler used by the standalone linker; it performs no file I/O.
Unknown first-word placeholders are preserved and are NEVER encodeable firmware.
Packaging must retain the official opaque first word. Boot/config are untouched.
"""
def require(ok, msg):
    if not ok:
        raise RuntimeError(msg)

def words(*values): return b''.join(x.to_bytes(2,'little') for x in values)
def absolute(op,address):
    require(address%2==0,'unaligned target')
    return words(op|((address//2)&255),0xf000|((address//2)>>8))

class Asm:
    def __init__(self,base): self.base=base; self.data=bytearray(); self.labels={}; self.fixups=[]; self.notes=[]
    @property
    def pc(self): return self.base+len(self.data)
    def label(self,name): require(name not in self.labels,'duplicate label'); self.labels[name]=self.pc
    def emit(self,raw,note): self.notes.append((self.pc,note,raw.hex(' '))); self.data.extend(raw)
    def w(self,value,note): self.emit(words(value),note)
    def call(self,address): self.emit(absolute(0xec00,address),'CALL %04X'%address)
    def goto(self,address): self.emit(absolute(0xef00,address),'GOTO %04X'%address)
    def movff(self,a,b): self.emit(words(0xc000|a,0xf000|b),'MOVFF %03X,%03X'%(a,b))
    def jump(self,name,kind='BRA'):
        self.fixups.append((len(self.data),self.pc,name,kind)); self.emit(words(0),kind+' '+name)
    def call_label(self,name):
        self.fixups.append((len(self.data),self.pc,name,'CALL')); self.emit(words(0,0),'CALL '+name)
    def finalize(self):
        for off,pc,name,kind in self.fixups:
            dest=self.labels[name]
            if kind=='CALL': self.data[off:off+4]=absolute(0xec00,dest)
            else:
                delta=(dest-(pc+2))//2
                if kind=='BRA': require(-1024<=delta<=1023,'BRA range'); op=0xd000|(delta&2047)
                else:
                    require(-128<=delta<=127,'conditional branch range')
                    op=({'BZ':0xe000,'BNZ':0xe100}[kind])|(delta&255)
                self.data[off:off+2]=words(op)
        return bytes(self.data)

def construct(original):
    a=Asm(0x9780)
    a.label('prepare')
    a.w(0x0100,'MOVLB 0')
    a.w(0x501f,'MOVF 1F,W'); a.call(0x730e); a.w(0x50df,'MOVF INDF2,W ; C5')
    a.jump('manual','BNZ')
    a.w(0x0e02,'MOVLW 2'); a.w(0x182a,'XORWF 2A,W'); a.jump('normal','BNZ')
    a.call(0x4f56); a.call(0x8930)
    a.w(0x0e01,'MOVLW 1'); a.w(0x6e17,'MOVWF 17 ; explicit HSS'); a.jump('energy')
    a.label('normal'); a.w(0x6a17,'CLRF 17 ; explicit normal')
    a.label('energy')
    for byte in b'RSUTM': a.w(0x0e00|byte,'MOVLW %02X'%byte); a.call(0x9636)
    a.movff(0x1e,0x14); a.movff(0x7a,0x15); a.movff(0x78,0x16); a.call_label('energy_clone')
    # Preserve the original parameter15 software guard. Its native clock domain
    # is intentionally neither called microseconds nor substituted with 5000.
    a.w(0x6a15,'CLRF 15'); a.w(0x0e0f,'MOVLW 15'); a.w(0x6e14,'MOVWF 14'); a.call(0x931c)
    a.movff(0x14,0xa4); a.movff(0x15,0xa5)
    a.label('guard_poll')
    a.w(0x0ea4,'MOVLW A4'); a.w(0x6e05,'MOVWF 05'); a.call(0x7724); a.w(0x0900,'IORLW 0')
    a.jump('guard_done','BNZ'); a.call(0x7f28); a.w(0x0004,'CLRWDT'); a.jump('guard_poll')
    a.label('guard_done')
    a.w(0x0100,'MOVLB 0'); a.w(0x6ba4,'CLRF A4,BANKED'); a.w(0x6ba5,'CLRF A5,BANKED')
    a.label('drain')
    a.w(0x0004,'CLRWDT'); a.w(0xa2ad,'BTFSS TXSTA1,TRMT'); a.jump('drain')
    a.w(0x0100,'MOVLB 0'); a.goto(0x43bc)
    a.label('manual')
    a.w(0x0100,'MOVLB 0'); a.w(0x517d,'MOVF 7D,W,BANKED'); a.goto(0x43aa)
    a.label('sample_commit')
    a.w(0x0100,'MOVLB 0'); a.w(0x517c,'MOVF 7C,W,BANKED'); a.jump('sample_done','BZ')
    a.movff(0x4a,0x7a); a.w(0x6b7c,'CLRF 7C,BANKED ; consume even equal/manual')
    a.label('sample_done')
    a.w(0x6ba4,'CLRF A4,BANKED'); a.w(0x6ba5,'CLRF A5,BANKED'); a.goto(0x4140)
    a.label('preflash_duration')
    a.w(0x501f,'MOVF 1F,W'); a.call(0x730e); a.w(0x50df,'MOVF INDF2,W ; C5')
    a.jump('preflash_done','BZ')
    a.call(0x4f56); a.call(0x8930); a.w(0x0e01,'MOVLW 1'); a.w(0x0100,'MOVLB 0'); a.w(0x6f7d,'MOVWF 7D,BANKED')
    a.label('preflash_done'); a.w(0x0100,'MOVLB 0'); a.goto(0x4320)
    a.label('b3_nonwhitelist')
    a.w(0x501e,'MOVF 1E,W'); a.call(0x4f24); a.w(0x0a25,'XORLW 25 ; camera class37')
    a.jump('b3_done','BNZ'); a.w(0x0100,'MOVLB 0'); a.w(0x6b7c,'CLRF 7C,BANKED')
    a.label('b3_done'); a.w(0x0100,'MOVLB 0'); a.goto(0x41e8)
    a.label('energy_clone')
    clone=bytearray(original[0x5f78-0x4000:0x60ea-0x4000])
    # Keep every relative branch position. Explicit HSS flag replaces mode2.
    clone[0x6000-0x5f78:0x6008-0x5f78]=words(0x5017,0xe04e,0,0)
    clone[0x6022-0x5f78:0x6024-0x5f78]=words(0)
    a.emit(clone,'Native 5F78..60E9 clone; explicit 17 gate; threshold branch removed')
    blob=a.finalize()
    changes=[(0x40e4,absolute(0xef00,a.labels['sample_commit']),'replace equal/C5/early-send policy with pending sample commit'),
             (0x41e4,absolute(0xef00,a.labels['b3_nonwhitelist']),'nonwhitelist B3 clears pending only for class37'),
             (0x4276,words(0x0e02),'first-payload B4 25 category=2; other mainflash category=1'),
             (0x4312,absolute(0xef00,a.labels['preflash_duration']),'TTL preflash no early duration; manual legacy behavior'),
             (0x4366,words(0),'retain persistent accepted energy_A across preflash'),
             (0x43a6,absolute(0xef00,a.labels['prepare']),'native B4 preparation policy'),
             (a.base,blob,'new native trampoline and copied arithmetic')]
    return a,changes
