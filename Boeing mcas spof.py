"""
=============================================================================
BUG ARCHIVE — Entry #7
Incident  : Boeing 737 MAX — MCAS System Failures
Date      : October 2018 & March 2019
Root Cause: MCAS (Maneuvering Characteristics Augmentation System) relied
            on a single Angle of Attack (AoA) sensor with no redundancy.
            When that sensor malfunctioned, MCAS repeatedly forced the
            nose down. Pilots were not trained on MCAS and were not told
            it existed. They could not overcome the repeated inputs.
Loss      : 346 lives | $20 billion+ | Fleet grounded 20 months
=============================================================================

THE BUG EXPLAINED
-----------------
MCAS was designed to push the nose down when it detected a stall condition
(high angle of attack). This was a legitimate safety feature.

The engineering failures:
  1. MCAS used ONE AoA sensor. No redundancy. No voting between sensors.
  2. A failed/stuck sensor could permanently trigger MCAS.
  3. MCAS could override pilot input repeatedly with no automatic stop.
  4. Pilots were not informed MCAS existed in the aircraft they were flying.
  5. There was no independent warning to pilots if the AoA sensor failed.

Both crashes followed the same pattern:
  - Left AoA sensor failed on takeoff
  - MCAS activated repeatedly, forcing nose down
  - Pilots fought MCAS but could not prevent the dive
  - Aircraft crashed within minutes of takeoff

=============================================================================
"""

import random
import time


# ── Sensor Classes ────────────────────────────────────────────────────────────

class AngleOfAttackSensor:
    def __init__(self, sensor_id: str, failed: bool = False, stuck_at: float = None):
        self.sensor_id = sensor_id
        self.failed    = failed
        self.stuck_at  = stuck_at    # if stuck, always returns this value

    def read(self, true_aoa: float) -> float:
        if self.failed and self.stuck_at is not None:
            return self.stuck_at     # sensor is stuck — reports wrong value
        noise = random.uniform(-0.5, 0.5)
        return true_aoa + noise


# ── MCAS Variants ─────────────────────────────────────────────────────────────

class MCAS_Buggy:
    """
     Original MCAS — single sensor, no redundancy, no limit on activations.
    As installed on Lion Air Flight 610 and Ethiopian Airlines Flight 302.
    """
    STALL_THRESHOLD    = 15.0    # degrees AoA — above this, MCAS activates
    NOSE_DOWN_INPUT    = -2.5    # degrees per activation (forces nose down)
    MAX_ACTIVATIONS    = 999     # effectively unlimited

    def __init__(self, sensor: AngleOfAttackSensor):
        self.sensor      = sensor
        self.activations = 0
        self.name        = "MCAS (BUGGY — single sensor, unlimited activations)"

    def update(self, true_aoa: float, pilot_nose_up_input: float) -> dict:
        sensed_aoa = self.sensor.read(true_aoa)
        mcas_fires = sensed_aoa >= self.STALL_THRESHOLD
        net_pitch  = 0.0

        if mcas_fires:
            self.activations += 1
            net_pitch = self.NOSE_DOWN_INPUT + pilot_nose_up_input
        else:
            net_pitch = pilot_nose_up_input

        return {
            "sensed_aoa"  : sensed_aoa,
            "true_aoa"    : true_aoa,
            "mcas_fired"  : mcas_fires,
            "activations" : self.activations,
            "net_pitch"   : net_pitch,
            "sensor_ok"   : not self.sensor.failed,
        }


class MCAS_Fixed:
    """
     Corrected MCAS — dual sensors, cross-check, activation limit, pilot override.
    Implemented after the crashes following the grounding investigation.
    """
    STALL_THRESHOLD = 15.0
    NOSE_DOWN_INPUT = -2.5
    MAX_ACTIVATIONS = 1           # fires once, then requires pilot acknowledgement

    def __init__(self, sensor_left: AngleOfAttackSensor, sensor_right: AngleOfAttackSensor):
        self.sensor_left  = sensor_left
        self.sensor_right = sensor_right
        self.activations  = 0
        self.inhibited    = False
        self.name         = "MCAS (FIXED — dual sensor cross-check, activation limit)"

    def update(self, true_aoa: float, pilot_nose_up_input: float) -> dict:
        left_reading  = self.sensor_left.read(true_aoa)
        right_reading = self.sensor_right.read(true_aoa)
        disagreement  = abs(left_reading - right_reading)

        # Cross-check: if sensors disagree by >10°, inhibit MCAS & alert pilots
        if disagreement > 10.0:
            self.inhibited = True

        if self.inhibited:
            return {
                "sensed_aoa"  : left_reading,
                "true_aoa"    : true_aoa,
                "mcas_fired"  : False,
                "activations" : self.activations,
                "net_pitch"   : pilot_nose_up_input,
                "sensor_ok"   : False,
                "alert"       : f"  AoA DISAGREE — sensors differ by {disagreement:.1f}°. MCAS INHIBITED.",
            }

        # Use average of both sensors
        averaged_aoa = (left_reading + right_reading) / 2.0
        mcas_fires   = (averaged_aoa >= self.STALL_THRESHOLD
                        and self.activations < self.MAX_ACTIVATIONS)

        net_pitch = 0.0
        if mcas_fires:
            self.activations += 1
            net_pitch = self.NOSE_DOWN_INPUT + pilot_nose_up_input
            if self.activations >= self.MAX_ACTIVATIONS:
                self.inhibited = True   #  stops after one activation
        else:
            net_pitch = pilot_nose_up_input

        return {
            "sensed_aoa"  : averaged_aoa,
            "true_aoa"    : true_aoa,
            "mcas_fired"  : mcas_fires,
            "activations" : self.activations,
            "net_pitch"   : net_pitch,
            "sensor_ok"   : True,
        }


# ── Flight Simulation ─────────────────────────────────────────────────────────

def simulate_flight(label: str, mcas, steps: int = 12):
    print(f"\n{'='*68}")
    print(f"  {label}")
    print(f"  System: {mcas.name}")
    print(f"{'='*68}")
    print(f"  {'Step':<5} {'True AoA':>9} {'Sensed':>9} {'MCAS':>7} {'Pilot':>8} {'Net Pitch':>10}  Alert")
    print(f"  {'─'*65}")

    CRITICAL_DIVE_ANGLE = -20.0
    cumulative_pitch    = 0.0
    true_aoa            = 5.0      # normal climb: 5° AoA
    PILOT_INPUT         = +2.0     # pilot is pulling back (nose up)

    # Sensor fails on step 2 (as in both crashes)
    FAILURE_STEP = 2

    for step in range(1, steps + 1):
        # Simulate sensor failure at step 2
        if step == FAILURE_STEP:
            if hasattr(mcas, "sensor"):
                mcas.sensor.failed   = True
                mcas.sensor.stuck_at = 40.0     # reports 40° AoA — extreme stall signal
            elif hasattr(mcas, "sensor_left"):
                mcas.sensor_left.failed   = True
                mcas.sensor_left.stuck_at = 40.0

        result         = mcas.update(true_aoa, PILOT_INPUT)
        cumulative_pitch += result["net_pitch"]
        alert          = result.get("alert", "")
        mcas_flag      = " YES" if result["mcas_fired"] else "   no"
        sensor_flag    = "" if result["sensor_ok"] else "SENSOR FAIL"

        print(f"  {step:<5} {result['true_aoa']:>+8.1f}° {result['sensed_aoa']:>+8.1f}° "
              f" {mcas_flag}  {PILOT_INPUT:>+7.1f}° {result['net_pitch']:>+9.1f}°  "
              f"{alert or sensor_flag}")

        if cumulative_pitch <= CRITICAL_DIVE_ANGLE:
            print(f"\n   AIRCRAFT IN UNRECOVERABLE DIVE")
            print(f"     Cumulative pitch: {cumulative_pitch:.1f}°")
            print(f"     MCAS activated {result['activations']} time(s).")
            print(f"     Pilots could not overcome repeated MCAS inputs.\n")
            return

    status = " FLIGHT NOMINAL" if cumulative_pitch > CRITICAL_DIVE_ANGLE else "💥 CRASH"
    print(f"\n  Final cumulative pitch: {cumulative_pitch:.1f}°  →  {status}\n")


if __name__ == "__main__":
    random.seed(7)
    print(__doc__)

    # ── Buggy MCAS — single failing sensor ───────────────────────────────────
    left_sensor_failed = AngleOfAttackSensor("LEFT", failed=False)   # starts OK

    simulate_flight(
        " BUGGY MCAS — Single sensor, sensor fails at step 2",
        MCAS_Buggy(left_sensor_failed),
    )

    # ── Fixed MCAS — dual sensors, cross-check catches the failure ────────────
    left_fixed  = AngleOfAttackSensor("LEFT",  failed=False)
    right_fixed = AngleOfAttackSensor("RIGHT", failed=False)    # healthy

    simulate_flight(
        " FIXED MCAS — Dual sensors, AoA disagree alert, activation limit",
        MCAS_Fixed(left_fixed, right_fixed),
    )

    print("─" * 68)
    print("  LESSON")
    print("─" * 68)
    print("""
  346 people died because a safety system had no redundancy,
  no activation limit, and was never disclosed to pilots.

  → Safety-critical systems MUST have redundant sensors.
    One sensor is a single point of failure. Always.
  → Cross-check sensor disagreement and alert operators
    BEFORE acting on potentially corrupt data.
  → Automatic systems that override human control must have
    hard limits on how many times they can override.
  → Pilots must be trained on every automatic system in
    the aircraft they fly. Hiding MCAS was an ethical failure.
  → "The software works as designed" is not acceptable
    if the design itself is unsafe.
  → When a system can kill people, the standard is not
    "passes our tests." It is "fails safely under every
    foreseeable failure mode — including ones we didn't foresee."
""")