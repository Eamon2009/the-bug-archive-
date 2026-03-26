"""
=============================================================================
BUG ARCHIVE — Entry #9
Incident  : Intel Pentium FDIV Bug
Date      : 1994
Root Cause: The Pentium's floating-point division unit used a lookup table
            (SRT division algorithm) with 1,066 entries. Due to a coding
            error, 5 of those entries were incorrectly left as zero.
            This caused rare but incorrect division results.
Loss      : ~$475 million in chip replacements | Lives Lost: 0
=============================================================================

THE BUG EXPLAINED
-----------------
The Pentium used the SRT (Sweeney, Robertson, Tocher) division algorithm.
It relies on a precomputed lookup table to estimate partial quotients
during iterative division.

Five entries near the top of the table were mistakenly left as 0
instead of +2 due to a transcription error.

The bug only affected specific numerator/denominator combinations.
For affected values, the error was small — but in financial or
scientific calculations requiring high precision, even small errors
compound catastrophically.

Famous example (discovered by Dr. Thomas Nicely):
  4195835.0 / 3145727.0

  Correct answer : 1.333820449136241002
  Pentium answer : 1.333739068902037589   ← wrong at 4th significant digit

=============================================================================
"""

from decimal import Decimal, getcontext

getcontext().prec = 50    # high-precision arithmetic for comparison


# ── Simulate the Pentium lookup table ────────────────────────────────────────

# A simplified SRT partial quotient table.
# Real Pentium had 1066 entries; we use 20 for illustration.
# Entries at index 7 and 13 are "buggy" (should be +2, are 0).

CORRECT_TABLE = [+2, +2, +2, +2, +2, +2, +2, +2, +2, +2,
                 +2, +2, +2, +2, +2, +2, +2, +2, +2, +2]

BUGGY_TABLE   = [+2, +2, +2, +2, +2, +2, +2,  0, +2, +2,
                 +2, +2, +2,  0, +2, +2, +2, +2, +2, +2]
#                                       ↑                 ↑
#                               index 7 = 0        index 13 = 0


def srt_divide_simplified(numerator: float, denominator: float, table: list) -> float:
    """
    Simplified SRT-style iterative division using a partial quotient table.
    This is a didactic approximation of the real algorithm.
    The key point: a wrong table entry causes an accumulated error.
    """
    if denominator == 0:
        raise ZeroDivisionError

    quotient   = 0.0
    remainder  = float(numerator)
    place      = 1.0

    for i in range(len(table)):
        # Estimate partial quotient from table
        partial_q = table[i % len(table)]

        # Adjust remainder
        remainder -= partial_q * denominator * place
        quotient  += partial_q * place
        place     /= 10.0

        if abs(remainder) < 1e-15:
            break

    # Final: add remaining fraction
    if denominator != 0:
        quotient += remainder / denominator

    return quotient


def true_divide(numerator: float, denominator: float) -> Decimal:
    """High-precision reference division using Python's Decimal."""
    return Decimal(str(numerator)) / Decimal(str(denominator))


# ── Test Cases ────────────────────────────────────────────────────────────────

TEST_CASES = [
    # (numerator, denominator, description)
    (4_195_835.0,  3_145_727.0, "Famous Nicely test case (discovered the bug)"),
    (5_505_001.0,  294_911.0,   "Variation known to trigger FDIV error"),
    (100.0,        4.0,         "Simple division — should be unaffected"),
    (1_000_000.0,  3.0,         "Common financial calculation"),
    (355.0,        113.0,       "Pi approximation"),
]


def run_fdiv_test():
    print(f"\n{'='*72}")
    print(f"  INTEL PENTIUM FDIV BUG — Division Accuracy Comparison")
    print(f"{'='*72}\n")
    print(f"  {'Test Case':<42} {'Correct':>20} {'Pentium (Buggy)':>20}  {'Match?'}")
    print(f"  {'─'*70}")

    for num, den, desc in TEST_CASES:
        correct_val = true_divide(num, den)
        buggy_val   = srt_divide_simplified(num, den, BUGGY_TABLE)
        correct_val_f = srt_divide_simplified(num, den, CORRECT_TABLE)

        error     = abs(float(correct_val) - buggy_val)
        match     = "true" if error < 1e-6 else f" ERROR: {error:.2e}"

        print(f"  {desc:<42} {float(correct_val):>20.15f}")
        print(f"  {'':42} {'Buggy result:':>20} {buggy_val:>20.15f}  {match}")
        print()


def demonstrate_compounding_error():
    """
    In financial or scientific applications, small division errors
    accumulate over repeated calculations.
    """
    print(f"\n{'='*72}")
    print(f"  COMPOUNDING ERROR — 1000 Repeated Calculations")
    print(f"{'='*72}\n")
    print(f"  Scenario: Bank calculates interest 1000 times using division.")
    print(f"  Each individual error: tiny. Cumulative error: significant.\n")

    principal     = 1_000_000.0   # $1 million
    rate_divisor  = 3_145_727.0   # arbitrary divisor (triggers Pentium bug)

    buggy_total   = principal
    correct_total = principal

    for i in range(1000):
        buggy_interest   = srt_divide_simplified(buggy_total,   rate_divisor, BUGGY_TABLE)
        correct_interest = srt_divide_simplified(correct_total, rate_divisor, CORRECT_TABLE)
        buggy_total   += buggy_interest
        correct_total += correct_interest

    discrepancy = abs(correct_total - buggy_total)
    print(f"  Starting principal  : ${principal:>18,.2f}")
    print(f"  Correct final value : ${correct_total:>18,.2f}")
    print(f"  Buggy   final value : ${buggy_total:>18,.2f}")
    print(f"  Discrepancy         : ${discrepancy:>18,.2f}")

    if discrepancy > 100:
        print(f"\n   A ${discrepancy:,.2f} error from tiny per-operation rounding.")
        print(f"     Across millions of bank accounts: catastrophic.\n")
    else:
        print(f"\n   Error within acceptable tolerance.\n")


if __name__ == "__main__":
    print(__doc__)
    run_fdiv_test()
    demonstrate_compounding_error()

    print("─" * 72)
    print("  LESSON")
    print("─" * 72)
    print("""
  Intel initially claimed the error would affect an average user
  only once every 27,000 years of use. Mathematicians and scientists
  who used floating-point division in professional work disagreed —
  loudly. The bug affected specific, commonly used values.

  → Pre-computed lookup tables must be exhaustively validated.
    A missing code review caught a missing table entry.
  → "The error is small" is not an acceptable response when
    the calculation is financial, medical, or scientific.
  → Hardware bugs are essentially unacceptable. Billions of
    units cannot be patched with a software update.
  → When users report a reproducible discrepancy, listen.
    Dr. Nicely reported the bug. Intel dismissed it.
    Public pressure forced a $475 million recall.
  → Floating-point arithmetic has known limitations.
    Use arbitrary-precision libraries (Python Decimal, Java BigDecimal)
    for financial calculations where exactness is required.
""")