; =============================================================================
; BUG ARCHIVE — Entry #9
; Incident  : Intel Pentium FDIV Bug
; Date      : 1994
; Language  : x86 Assembly (Intel Pentium P5 microarchitecture)
;             The bug was in hardware, but demonstrated here in NASM x86
;             assembly to show the FPU instruction that triggered it.
; Root Cause: The Pentium FPU used the SRT (Sweeney-Robertson-Tocher)
;             division algorithm with a lookup table of 1,066 entries.
;             5 entries near the top were incorrectly left as 0 (should be +2).
;             This caused specific division operations to return wrong results.
; Loss      : ~$475 million in chip replacements | Lives Lost: 0
; =============================================================================
;
; NASM SYNTAX (x86 real/protected mode, 32-bit)
; The actual Pentium FPU instructions:
;   FLDZ   — push 0.0 onto FPU stack
;   FLD    — load float onto FPU stack
;   FDIV   — ST(0) = ST(0) / src
;   FMUL   — multiply
;   FSTP   — store and pop FPU stack
;   FCOM   — compare FPU registers
;
; The famous test (discovered by Dr. Thomas Nicely, Oct 30, 1994):
;   4195835.0 / 3145727.0
;   Correct : 1.333820449136241002
;   Pentium : 1.333739068902037589   ← wrong from 4th significant digit
;
; =============================================================================

section .data

    ; ── Test values (Dr. Nicely's exact discovery values) ─────────────────
    numerator_1     dd  4195835.0           ; 32-bit float
    denominator_1   dd  3145727.0
    expected_1      dq  1.333820449136241   ; 64-bit double (correct)

    ; ── Additional known-bad values ────────────────────────────────────────
    numerator_2     dd  5505001.0
    denominator_2   dd  294911.0
    expected_2      dq  18.666655...        ; approximate correct value

    ; ── Simple division (unaffected by bug) ────────────────────────────────
    numerator_3     dd  100.0
    denominator_3   dd  4.0
    expected_3      dq  25.0               ; exact

    ; ── String messages ────────────────────────────────────────────────────
    msg_title       db  'INTEL PENTIUM FDIV BUG - x86 FPU DEMONSTRATION', 0Ah, 0
    msg_test1       db  'Test: 4195835.0 / 3145727.0', 0Ah, 0
    msg_expected    db  'Expected: 1.333820449136241002', 0Ah, 0
    msg_pentium     db  'Pentium:  1.333739068902037589  <-- WRONG at digit 4', 0Ah, 0
    msg_separator   db  '-----------------------------------------------', 0Ah, 0

    ; ── The SRT lookup table (simplified, 20 entries) ──────────────────────
    ; Real Pentium: 1,066 entries. Bug: 5 entries zeroed that should be +2.
    ; Here we show the structure with the zero entries marked.
    ;
    ; Format: each entry is a 2-bit partial quotient digit: -2, -1, 0, +1, +2
    ; Represented as signed bytes here for clarity.
    ;
    correct_table:
        db  2, 2, 2, 2, 2, 2, 2, 2, 2, 2   ; entries 0-9
        db  2, 2, 2, 2, 2, 2, 2, 2, 2, 2   ; entries 10-19
        ; ... all entries are +2 or appropriate values in correct version

    buggy_table:
        db  2, 2, 2, 2, 2, 2, 2, 0, 2, 2   ; entry 7 = 0 (should be 2) 
        db  2, 2, 2, 0, 2, 2, 2, 2, 2, 2   ; entry 13 = 0 (should be 2) 
        ;                  ↑                        ↑
        ;           index 7 wrong           index 13 wrong


section .bss
    result_buffer   resq 1      ; 8 bytes for 64-bit float result
    error_buffer    resq 1      ; to hold error magnitude


section .text
    global _start

; =============================================================================
; THE FDIV INSTRUCTION — the one that triggered the bug
; On a real Pentium (pre-fix), this specific operation produced wrong results.
; On a fixed Pentium or any other x86: result is correct.
; =============================================================================

_start:

    ; ── Load numerator and denominator ─────────────────────────────────────
    ;    FPU stack grows downward: ST(0) is top
    ;
    fld     dword [denominator_1]   ; ST(0) = 3145727.0
    fld     dword [numerator_1]     ; ST(0) = 4195835.0   ST(1) = 3145727.0
    ;
    ; On pre-errata Pentium P5 (stepping B1):
    ;    FDIV reads the SRT lookup table for partial quotient estimation.
    ;    For this specific numerator/denominator pair, the flawed entry
    ;    (index 7 = 0 instead of 2) is consulted during the 19-step
    ;    iterative division. The partial quotient is underestimated.
    ;    The accumulated error propagates to the final result.
    ;
    fdiv    st0, st1                 ; ST(0) = ST(0) / ST(1)
                                     ; ← THE INSTRUCTION THAT CAUSED $475M RECALL
    ;
    fstp    qword [result_buffer]   ; store result as 64-bit double
    ;
    ; At this point on a buggy Pentium:
    ;   [result_buffer] = 1.333739068902037589   (WRONG)
    ;
    ; On a corrected Pentium or any modern x86:
    ;   [result_buffer] = 1.333820449136241002   (CORRECT)


    ; ── Demonstrate the financial compounding effect ────────────────────────
    ;    Interest calculation: principal * (1 + rate/divisions)^iterations
    ;    Each small error multiplies with every iteration.

    fld1                            ; ST(0) = 1.0
    fldpi                           ; ST(0) = pi (~3.14159), ST(1) = 1.0
                                    ; pi chosen because FDIV of pi-related
                                    ; values hit the buggy table entries
    fdiv    st0, st1                ; ST(0) = pi / 1.0 = pi
                                    ; ← small error on buggy Pentium
    fmul    st0, st0               ; ST(0) = (pi/1.0)^2 — error compounds
    fmul    st0, st0               ; ST(0) = ((pi/1.0)^2)^2 — more compounding
    fstp    qword [error_buffer]   ; store compounded result

    ; On a financial system doing millions of such operations:
    ; The accumulated error is measurable and significant.


    ; ── Safe exit ──────────────────────────────────────────────────────────
    mov     eax, 1                  ; syscall: exit
    xor     ebx, ebx                ; exit code 0
    int     0x80


; =============================================================================
; APPENDIX: What the SRT algorithm looks like in pseudocode
;
; The Pentium's SRT division iteratively computes partial quotients.
; At each step it looks up a partial quotient digit (-2,-1,0,+1,+2)
; from a table indexed by the current partial remainder and divisor.
;
; PSEUDOCODE (NOT assembly — for educational clarity):
;
;   function srt_divide(numerator, denominator):
;       quotient  = 0
;       remainder = numerator
;       place     = 1.0
;
;       for step in range(19):       ; Pentium used 19 iterations
;           index = lookup_index(remainder, denominator)
;
;           ; BUG: for certain (remainder, denominator) pairs,
;           ;         the table returns 0 when it should return +2.
;           ;         The quotient is underestimated.
;           ;         The remainder is NOT fully reduced.
;           ;         The error carries forward to all subsequent steps.
;
;           partial_q  = TABLE[index]     ; should be +2, was 0 for bug entries
;           remainder -= partial_q * denominator * place
;           quotient  += partial_q * place
;           place     /= radix            ; radix = 4 for Pentium SRT
;
;       return quotient + remainder/denominator
;
; The correct table has entries from {-2, -1, 0, +1, +2}.
; The buggy table had 5 entries that were 0 instead of +2.
; The table was built from a mathematical derivation.
; The derivation was correct, but 5 entries were missed when
; transcribing the computed values into the ROM lookup table.
;
; =============================================================================
;
; LESSON
; Intel's initial response was to say the error would affect users
; "once every 27,000 years of use on average."
; This was statistically true for general arithmetic.
; It was catastrophically false for scientists and financial analysts
; who used specific division patterns daily.
;
; Dr. Thomas Nicely discovered the bug by noticing inconsistencies
; in his reciprocals of prime numbers. He reported it. Intel dismissed it.
; The Internet amplified it. Intel recalled 5 million chips.
;
; → Hardware bugs are real. Do not assume the FPU is always correct.
; → For financial systems, use integer arithmetic or arbitrary
;   precision libraries — not floating-point.
; → Pre-computed lookup tables must be exhaustively validated.
;   Every entry. Not "the logic that generated them."
; → When a user reports a reproducible numerical discrepancy,
;   investigate it seriously. Nicely was right. Intel was wrong.
;
; =============================================================================
;
; ASSEMBLE AND LINK (Linux 32-bit or with -m32):
;   nasm -f elf32 pentium_fdiv_x86.asm -o pentium_fdiv.o
;   ld -m elf_i386 pentium_fdiv.o -o pentium_fdiv
;   ./pentium_fdiv
;
; To verify the FDIV result on your system:
;   python3 -c "print(f'{4195835.0 / 3145727.0:.18f}')"
;   # Should print: 1.333820449136241002 (correct on any modern CPU)
; =============================================================================