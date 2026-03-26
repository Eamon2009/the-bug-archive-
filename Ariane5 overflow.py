"""
=============================================================================
BUG ARCHIVE — Entry #3
Incident  : Ariane 5 Rocket — Flight 501
Date      : June 4, 1996
Root Cause: A 64-bit floating-point number (horizontal velocity) exceeded
            the maximum value of a 16-bit signed integer. The conversion
            caused an Operand Overflow exception. The software — reused
            from Ariane 4 without re-validation — passed the exception
            code as flight data to the guidance system, which interpreted
            it as a real trajectory reading and steered the rocket to
            destruction.
Loss      : ~$370 million | Lives Lost: 0 (unmanned)
=============================================================================

THE BUG EXPLAINED
-----------------
Ariane 5 was faster and more powerful than Ariane 4.
The horizontal velocity value it generated during flight
was larger than anything Ariane 4 ever produced.

The variable storing it was a 16-bit signed integer:
  max value = 32,767

Ariane 5's actual horizontal velocity (as a float): ~37,000+

When 37,000 was cast to int16, the result was a garbage number
(or an exception). That exception code — treated as flight data —
told the rocket it was wildly off course. It self-corrected.
Then self-destructed.

=============================================================================
"""

import struct

INT16_MAX =  32_767
INT16_MIN = -32_768


# ── Type-Safe Conversion ──────────────────────────────────────────────────────

def safe_int16(value: float) -> int:
    """
    SAFE conversion: clamps and warns before overflow occurs.
    """
    if value > INT16_MAX or value < INT16_MIN:
        raise OverflowError(
            f"Value {value:.1f} cannot fit in int16 "
            f"(range {INT16_MIN} to {INT16_MAX}). "
            f"Refusing conversion — check your data types."
        )
    return int(value)


def unsafe_int16(value: float) -> int:
    """
    UNSAFE conversion: silently wraps around (C-style behaviour).
    This is what the Ariane 5 software did.
    """
    packed   = struct.pack(">f", value)          # float to bytes
    as_int   = struct.unpack(">I", packed)[0]    # bytes to unsigned int
    truncated = as_int & 0xFFFF                  # keep only 16 bits
    # re-interpret as signed
    if truncated >= 0x8000:
        truncated -= 0x10000
    return truncated


# ── Flight Simulator ──────────────────────────────────────────────────────────

def simulate_guidance(label: str, velocity: float, convert_fn):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  True horizontal velocity (float64) : {velocity:.2f} m/s")
    print(f"  int16 safe range                   : {INT16_MIN} to {INT16_MAX}")
    print()

    try:
        converted = convert_fn(velocity)
        print(f"  Converted int16 value              : {converted}")

        # The guidance system uses this value to calculate correction
        expected_correction = 0.0                # we're on course — no correction needed
        actual_correction   = (converted - velocity) * 0.01

        print(f"  Expected steering correction       : {expected_correction:.4f}°")
        print(f"  Actual  steering correction        : {actual_correction:.4f}°")

        if abs(actual_correction) > 5.0:
            print(f"\n   FATAL: Guidance system issued a {actual_correction:.1f}° correction.")
            print(f"           Rocket veered off trajectory.")
            print(f"           Self-destruct sequence initiated.\n")
        else:
            print(f"\n   Correction within safe range. Flight nominal.\n")

    except OverflowError as e:
        print(f"  OverflowError caught: {e}")
        print(f"\n Safe conversion refused the operation.")
        print(f"     Engineers are alerted. Rocket does NOT receive corrupt data.\n")


# ── Ariane 4 vs Ariane 5 velocities ──────────────────────────────────────────

ARIANE4_MAX_HORIZONTAL_VELOCITY = 20_000.0   # safely within int16 range
ARIANE5_HORIZONTAL_VELOCITY     = 37_000.0   # exceeds int16 max (32,767)


if __name__ == "__main__":
    print(__doc__)

    # Ariane 4 — the reused code was valid for this rocket
    simulate_guidance(
        "Ariane 4 velocity — code was valid here",
        ARIANE4_MAX_HORIZONTAL_VELOCITY,
        unsafe_int16,
    )

    # Ariane 5 — same code, new rocket, overflow
    simulate_guidance(
        "Ariane 5 — BUGGY (unsafe int16 cast, Ariane 4 code reused)",
        ARIANE5_HORIZONTAL_VELOCITY,
        unsafe_int16,
    )

    # Ariane 5 — fixed with safe conversion
    simulate_guidance(
        "Ariane 5 — FIXED (safe int16 with overflow guard)",
        ARIANE5_HORIZONTAL_VELOCITY,
        safe_int16,
    )

    print("─" * 60)
    print("  LESSON")
    print("─" * 60)
    print("""
  The Ariane 5 team reused working, tested code from Ariane 4.
  The assumption was: if it worked before, it will work again.

  That assumption cost $370 million in 37 seconds.

  → Integer overflow is silent in many languages (C, Ada).
    Always use range-checked conversions in safety-critical code.
  → Reused code must be re-validated for the new environment.
    A function valid for Ariane 4's velocities is NOT
    automatically valid for Ariane 5's.
  → Data flowing between subsystems should carry type metadata.
    A float64 should never silently become an int16 at a
    system boundary.
  → Exception codes must NEVER be forwarded as sensor data.
    Error channels and data channels must be strictly separated.
""")