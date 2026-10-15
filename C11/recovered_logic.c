/* SPDX-License-Identifier: AGPL-3.0-only
 * Copyright (c) 2026 Caimankekw
 *
 * MANUALLY AUTHORED REVERSE-ENGINEERING EXPLANATION -- NOT VENDOR SOURCE.
 * This is a partial, non-buildable model of selected ORIGINAL C11 behavior.
 * It omits register/stack ABI, peripheral setup and many error/cleanup paths.
 * It is neither the P8 implementation nor a replacement firmware.
 * Manufacturer machine code/resources retain their respective rights.
 * Addresses below are PIC18 BYTE addresses; recovered image base = 0x4000.
 */
#error "Documentation only: use the project patch generators, not this C model."

typedef unsigned char u8;
typedef unsigned short u16;

/* Abstract boundaries: no GPIO/ADC implementation is supplied here. */
extern u8 read_register(u16 address);
extern void original_delay_9226(u8 parameter);
extern u16 original_adc_conversion(unsigned selection_field);
extern void original_adc_enable(void);
extern void original_adc_disable(void);

enum original_key {
    KEY_NONE = 0, KEY_MODE = 1, KEY_2 = 2, KEY_3 = 3,
    KEY_MINUS = 4, KEY_PLUS = 5, KEY_MODEL = 6, KEY_HEAD = 7,
    KEY_A = 8, KEY_B = 9, KEY_C = 10, KEY_11 = 11
};

/* 6826/6844/684E/6858: inclusive original 10-bit ADC intervals.
 * Return names are explanatory, not original firmware identifiers.
 */
static unsigned voltage_band(u16 v)
{
    if (923 <= v && v <= 1023) return 1;
    if (412 <= v && v <= 612) return 2;
    if (60 <= v && v <= 260) return 3;
    return 0;
}

/* Original 674A..6824. This routine returns ONE priority-selected keycode.
 * A bouncing high-priority digital key skips the remaining digital checks
 * and falls through to ADC. A valid digital key skips both ADC selections.
 * 67AA..67B4 selects field1; 67E6..67EA selects field0.
 * ADC conversion waits are blocking in the original; no timeout is modeled.
 */
static u8 original_scan_674A(void)
{
    static const struct { u16 port; u8 bit, code; } digital[] = {
        {0xF81, 0, KEY_MINUS}, {0xF81, 1, KEY_PLUS},
        {0xF81, 7, KEY_MODE},  {0xF81, 6, KEY_11},
        {0xF80, 2, KEY_C}
    };
    static const u8 field1_codes[] = {KEY_NONE, KEY_A, KEY_2, KEY_B};
    static const u8 field0_codes[] = {KEY_NONE, KEY_MODEL, KEY_HEAD, KEY_3};
    unsigned i, band;
    u8 result;

    for (i = 0; i < 5; ++i) {
        if ((read_register(digital[i].port) & (1u << digital[i].bit)) == 0) {
            original_delay_9226(1); /* Native parameter, not a measured ms API. */
            if ((read_register(digital[i].port) & (1u << digital[i].bit)) == 0)
                return digital[i].code;
            break;
        }
    }
    original_adc_enable();
    band = voltage_band(original_adc_conversion(1));
    if (band != 0) result = field1_codes[band];
    else result = field0_codes[voltage_band(original_adc_conversion(0))];
    original_adc_disable();
    return result;
}

/* Original mode-bank sketch, 60EA..6136.
 * config is the object addressed through RAM42:43 (normally at0088).
 * The rest of the key's hold/settings/hardware tail is deliberately omitted.
 * A held MODE can enter settings and force TTL; this is not a full handler.
 */
extern u8 ram[];
extern u8 original_pending_96C4(void);
extern void original_clear_pending_885A(u8 value);
static void original_mode_bank_transition(u8 *config)
{
    if (original_pending_96C4() != 0) return;
    if (ram[0x52] != 0) {                 /* TTL -> MAN */
        ram[0x52] = 0;
        config[2] = ram[0x3F];
        config[3] = ram[0x40];
        config[4] = ram[0x41];
        ram[0x3F] = ram[0x40] = ram[0x41] = 0; /* 6230 */
        ram[0x03] = ram[0x4E];             /* 6236: selected pending slot */
        original_clear_pending_885A(0);
    } else {                             /* MAN -> TTL */
        ram[0x52] = 1;
        ram[0x3F] = config[2];
        ram[0x40] = config[3];
        ram[0x41] = config[4];
    }
    /* Continue at6136 for display/hold/settings. At6212..6224, AFTER that
     * tail, config[5] = (ram[0x52] == 0). Camera9188/91A4 performs the
     * inverse mapping ram[0x52] = (config[5] == 0).
     */
}

/* The remaining sections are an address index, not reconstructed C bodies.
 * Calls into the middle of these ranges are NOT safe function APIs.
 */
struct function_note { u16 address; const char *role; };
static const struct function_note original_function_index[] = {
    {0x8B0C, "Application setup; main application entry63AA follows initialization"},
    {0x8BC2, "Scan674A; activity prefix8BCE; dispatch4F7A at8BEC"},
    {0x4F7A, "Single-key dispatch: MODEL6->6250, HEAD7->5962, MODE1->60EA"},
    {0x8ACC, "Blocking repeated674A hold detector; short/long classification"},
    {0x9086, "Blocking release wait using674A"},
    {0x60EA, "Local TTL/MAN transition; bank sketch above is incomplete"},
    {0x9188, "Camera-mode notification;91A4 maps C[5] to boolean RAM52"},
    {0x5DD4, "Native mode/display branch; fixed LCD labels are not arbitrary text"},
    {0x84C2, "RowA numeric formatter; rowB8414 and rowC83BC"},
    {0x783E, "UART RSGT1 plus16-byte binary body; no trailing CR"},
    {0x79D8, "UART RSGT1 body:27 FF FF FF 01 RAM06 W RAM04 RAM05 then7 zeros"},
    {0x8930, "ROM string selected by RAM0A; appendCR; optional8656 when0B!=0"},
    {0x8656, "Four-byte receive/timeout routine; not a proven RF-success boolean"},
    {0x9636, "UART TX-register write; return does not require final-bit drain"},
    {0x6B8E, "Original relative adjustment pending/prequery/fallback consumer"},
    {0x40A8, "Camera-command parser, includingB0/B2 samples and laterB4 handling"},
    {0x421C, "B4 first-payload classification:19/23 preflash;25/2D/35/39/3D mainflash"},
    {0x5F78, "Energy arithmetic and RSUTM formatting; native mode/class conditions apply"},
    {0x43BC, "Mainflash phase through4432: S/Q waits and P3 pulse ordering"},
    {0x931C, "Build native software deadline from14:15; not a generic milliseconds API"},
    {0x7724, "Test deadline at low-RAM address in05; no clock advancement here"},
    {0x7F28, "Native software-clock update from hardware timer observations"},
    {0x54EE, "Mirror visible TTL FEC3F..41 into C[2..4]; no Flash write here"},
    {0x8F38, "Soft-power-off chain; calls939E at8F40 then performs hardware shutdown"},
    {0x939E, "Read/pack C[2..6]; ultimately enter662E for original1F800 journal"},
    {0x9474, "Read radio channel via75FC and RSGER0 CR; validate ASCII1..8"},
    {0x64F8, "Apply channel; later8976 emits RSGEW00<channel> CR"}
};

/* Original radio interface examples (REQUEST bytes, not over-air payloads):
 * 783E(W, RAM0A): RSGT1 + [W FF FF FF 01 RAM0A W 00 00 00 00 00 00 00 00 00]
 * 79D8(W, RAM06, RAM04, RAM05): see index above.
 * 8930: ROM bytes + CR; optionally read four response bytes.
 * These helpers do not prove light ACK, RF start/finish, or module readiness.
 */

/* Camera/HSS boundary, ORIGINAL C11:
 * B4 payload19/23 takes preflash-phase code42xx;25/2D/35/39/3D takes43xx.
 * Original430A..431E and43A6..43B8 can send selected RSUTP03/05 + CR.
 * Original43BC..4432 changes P3 pulse order around Q according to mode2.
 * P3=ACCESS81.bit3, P5=ACCESS81.bit5, Q=ACCESS81.bit4,
 * S=ACCESS83.bit5, E=ACCESS84.bit2 are code-observed aliases, not a complete
 * verified board wiring map. The local camera reply80 is NOT by itself an
 * over-air preflash80. RSUU1/0 existence is NOT a proven RF-ready/cancel API.
 * The complete radio-module backend and optical timing are outside this model.
 */

/* Original persistence boundary:
 * FEC edit -> C[2..4] in RAM. Soft power-off8F38 ->939E ->8F68/74AE/959A
 * ->662E packs/compares a4-byte record and uses journal region1F800.
 * It is not a background autosave scan. Do not call8F38 as an edit-time save:
 * it continues into shutdown. Channel is separately requested through the
 * radio RSGER0/RSGEW path; the packed C[6] field is not identified as channel.
 */

/* PROJECT ADDITIONS -- NOT ORIGINAL C11:
 * HSS-P3 baseline patches sample lifetime/B4 energy preparation and retains
 * the native UART/GPIO backend. P8 preserves it; it is not a full RF port.
 * P8 adds six canonical manual targets, relative/FEC separation, C+HEAD and
 * C+MODEL arbitration, page display, mapped sender and separate extension
 * settings pagesF800..FFFF. New instruction code is generated belowF800.
 * Original67..6E pending transactions are drained; the six-group direct send
 * path does not reproduce the whole original prequery/fallback transaction.
 * Build ../source/ with the project tooling; do not compile this document.
 */
