; =============================================================================
; BUG ARCHIVE — Entry #2
; Incident  : Therac-25 Radiation Therapy Machine
; Date      : 1985–1987
; Language  : PDP-11 Assembly (DEC PDP-11/23, RT-11 OS)
; Root Cause: Shared variable DATENT used both as an input-ready flag
;             and as a mode-selection value. Race condition: if operator
;             typed fast enough, DATENT was read before mode was set,
;             leaving high-power XRAY beam armed in ELECTRON config.
; Loss      : Immeasurable | Lives Lost: 6 killed or seriously injured
; =============================================================================
;
; PDP-11 ASSEMBLY NOTES (authentic to era):
;   Registers: R0–R7. R6=SP (stack pointer), R7=PC (program counter)
;   MOV src, dst    — copy word
;   CMP a, b        — compare (sets flags)
;   BEQ label       — branch if equal (Z flag set)
;   BNE label       — branch if not equal
;   CLR dst         — clear (set to 0)
;   INC dst         — increment
;   JSR R7, sub     — jump to subroutine (PDP-11 style)
;   RTS R7          — return from subroutine
;   Octal literals  — PDP-11 uses octal: 012=LF, 015=CR
;
; Memory-mapped I/O and shared variables between the UI task and
; the treatment task ran under a cooperative (non-preemptive) scheduler.
; The race window was the gap between DATENT write and MODEFL read.
;
; =============================================================================

; ---  SHARED MEMORY LOCATIONS  -----------------------------------------------
;      (absolute addresses as used in the real Therac-25 memory map region)

DATENT  = 177564        ; shared: operator input ready flag AND edit value
                        ; 0 = no new input
                        ; 1 = data entered (UI sets this after keypress)
MODEFL  = 177566        ; treatment mode: 0=ELECTRON, 1=XRAY
BEAMHI  = 177570        ; beam power:     0=LOW,      1=HIGH
TGTPOS  = 177572        ; target/spreader: 0=OUT,     1=IN (armed)
SAFEOK  = 177574        ; safety interlock (SOFTWARE ONLY — no hardware backup)

; --- CONSTANTS ---------------------------------------------------------------
MODE_ELECTRON   = 0
MODE_XRAY       = 1
BEAM_LOW        = 0
BEAM_HIGH       = 1
TARGET_OUT      = 0
TARGET_IN       = 1
SAFE            = 1
UNSAFE          = 0
INPUT_READY     = 1
NO_INPUT        = 0

; =============================================================================
;  BUGGY UI TASK — runs in noncritical time slice
;     Problem: DATENT is set to INPUT_READY and MODEFL written,
;     but if the treatment task reads DATENT before MODEFL is stable,
;     it fires with the previous mode's hardware config.
; =============================================================================

UI_TASK_BUGGY:
        ; Operator pressed ENTER for XRAY mode
        MOV     #MODE_XRAY,  MODEFL          ; set mode = XRAY
        MOV     #BEAM_HIGH,  BEAMHI          ; arm high power beam
        MOV     #TARGET_IN,  TGTPOS          ; extend target into beam path
        MOV     #INPUT_READY, DATENT         ; ← signal that input is ready
        ;
        ; *** RACE WINDOW OPENS HERE ***
        ; If operator quickly edits to ELECTRON mode (within 8 seconds),
        ; the UI overwrites MODEFL and TGTPOS — but DATENT was ALREADY set.
        ; The treatment task may have already read DATENT=INPUT_READY
        ; and scheduled beam fire before the edit completes.
        ;
        ; Simulate fast operator edit to ELECTRON:
        MOV     #MODE_ELECTRON, MODEFL       ; operator changes mind
        MOV     #TARGET_OUT,    TGTPOS       ; retracts target
        ; NOTE: BEAMHI is NOT reset — still HIGH!
        ; NOTE: DATENT is NOT reset — still INPUT_READY!
        RTS     R7

; =============================================================================
;  BUGGY TREATMENT TASK — critical time slice
;     Reads DATENT and fires beam without verifying full state consistency.
; =============================================================================

TREAT_TASK_BUGGY:
        ; Check if operator confirmed a setting
        CMP     #INPUT_READY, DATENT
        BNE     TREAT_IDLE              ; no input yet — wait

        ; Input is ready — read mode and fire
        CMP     #MODE_XRAY, MODEFL
        BEQ     FIRE_XRAY

        ; Must be ELECTRON mode — check safety (software-only check)
        ; BUG: BEAMHI may still be HIGH from previous XRAY selection
        ;         TGTPOS may be OUT (no spreader) yet BEAMHI=HIGH
        CMP     #BEAM_HIGH, BEAMHI
        BEQ     FIRE_UNSAFE             ; ← THIS PATH KILLS PATIENTS

        MOV     #SAFE, SAFEOK
        BR      FIRE_BEAM

FIRE_XRAY:
        MOV     #TARGET_IN, TGTPOS      ; spreader in place — safe for XRAY
        MOV     #SAFE, SAFEOK
        BR      FIRE_BEAM

FIRE_UNSAFE:
        ; High-power beam, ELECTRON config, NO spreader
        ; Patient receives ~100x prescribed dose
        MOV     #UNSAFE, SAFEOK
        ; System does NOT halt — fires anyway
        ; Error message displayed: "MALFUNCTION 54" (cryptic, alarming?)
        BR      FIRE_BEAM               ; ← FIRES. PATIENT HARMED.

FIRE_BEAM:
        CLR     DATENT                  ; clear input flag after reading
        ; ... beam fires ...
        RTS     R7

TREAT_IDLE:
        RTS     R7


; =============================================================================
;   FIXED UI TASK — atomic state update, DATENT set LAST
; =============================================================================

UI_TASK_FIXED:
        ; Operator confirms XRAY mode — write all state, THEN signal ready
        MOV     #MODE_XRAY,  MODEFL
        MOV     #BEAM_HIGH,  BEAMHI
        MOV     #TARGET_IN,  TGTPOS
        ;
        ; If operator fast-edits to ELECTRON, ALL fields reset atomically:
        MOV     #MODE_ELECTRON, MODEFL
        MOV     #BEAM_LOW,      BEAMHI         ;  power explicitly reset
        MOV     #TARGET_OUT,    TGTPOS         ;  target explicitly retracted
        ; DATENT is set ONLY after full state is consistent:
        MOV     #INPUT_READY, DATENT           ;  signal LAST, not first
        RTS     R7


; =============================================================================
;   FIXED TREATMENT TASK — validates full state before any beam fire
; =============================================================================

TREAT_TASK_FIXED:
        CMP     #INPUT_READY, DATENT
        BNE     TREAT_IDLE_F

        ;  FULL STATE CROSS-CHECK before firing
        CMP     #MODE_ELECTRON, MODEFL
        BNE     CHECK_XRAY_SAFE

        ; ELECTRON mode — verify power is LOW and target is OUT
        CMP     #BEAM_LOW, BEAMHI
        BNE     SAFETY_FAULT            ;  inconsistent — refuse to fire

        CMP     #TARGET_OUT, TGTPOS
        BNE     SAFETY_FAULT            ;  inconsistent — refuse to fire

        MOV     #SAFE, SAFEOK
        BR      FIRE_BEAM_SAFE

CHECK_XRAY_SAFE:
        ; XRAY mode — verify power is HIGH and target is IN
        CMP     #BEAM_HIGH, BEAMHI
        BNE     SAFETY_FAULT

        CMP     #TARGET_IN, TGTPOS
        BNE     SAFETY_FAULT

        MOV     #SAFE, SAFEOK
        BR      FIRE_BEAM_SAFE

SAFETY_FAULT:
        ;  Inconsistent state detected — HALT, alert operator, do NOT fire
        MOV     #UNSAFE, SAFEOK
        CLR     DATENT
        ; Trigger audible alarm + clear display error code
        ; (would write to terminal control registers here)
        HALT                            ; machine stops — patient protected
        RTS     R7

FIRE_BEAM_SAFE:
        CLR     DATENT
        ; ... beam fires safely ...
        RTS     R7

TREAT_IDLE_F:
        RTS     R7

; =============================================================================
; LESSON
; The race condition existed because DATENT served two purposes:
;   1. Flag: "operator has entered a value" (should be set LAST)
;   2. Value: implicitly tied to the mode/power state
;
; And because BEAMHI was never reset when the operator changed modes.
; The machine had no hardware interlock to catch this state.
; Only software stood between the patient and a lethal dose.
; The software had a timing gap of ~8 seconds.
; Six people entered that gap.
;
; → Shared flags must have clear, single ownership
; → Safety-critical state transitions must be atomic
; → NEVER remove hardware interlocks and trust software alone
; → A "Malfunction 54" message is not a safety response
; =============================================================================