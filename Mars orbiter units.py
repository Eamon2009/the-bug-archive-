"""
=============================================================================
BUG ARCHIVE — Entry #4
Incident  : Mars Climate Orbiter — Lost in Space
Date      : September 23, 1999
Root Cause: Lockheed Martin's ground software produced thruster force data
            in imperial units (pound-force seconds). NASA's navigation
            system expected metric units (newton-seconds). Nobody validated
            the interface contract. The spacecraft approached Mars at the
            wrong angle and was destroyed in the atmosphere.
Loss      : ~$125 million spacecraft | Lives Lost: 0
=============================================================================

THE BUG EXPLAINED
-----------------
One pound-force second  ≈ 4.448 newton-seconds

The navigation system received values ~4.45x too small.
It thought the thrusters were barely firing.
In reality they were firing normally.

Over 10 months of flight, small corrections accumulated.
By arrival at Mars, the trajectory was ~170 km too low.
At that altitude, atmospheric drag destroyed the spacecraft.

=============================================================================
"""

# ── Unit Constants ────────────────────────────────────────────────────────────

LBF_TO_NEWTON = 4.44822          # 1 pound-force = 4.44822 newtons


# ── Thruster Classes ──────────────────────────────────────────────────────────

class ThrusterSystemImperial:
    """
    Lockheed Martin's software — outputs in pound-force seconds.
    This is the CORRECT output from their system.
    """
    def get_momentum(self, burn_seconds: float) -> float:
        force_lbf = 4.45          # thruster force in pound-force
        return force_lbf * burn_seconds   # returns: lbf·s


class ThrusterSystemMetric:
    """
    If Lockheed had used metric — outputs in newton-seconds.
    This is what NASA's navigation expected.
    """
    def get_momentum(self, burn_seconds: float) -> float:
        force_newtons = 4.45 * LBF_TO_NEWTON   # ~19.79 N
        return force_newtons * burn_seconds      # returns: N·s


# ── Navigation System ─────────────────────────────────────────────────────────

class NavigationSystem:
    """NASA's navigation — assumes all momentum values are in newton-seconds."""

    def __init__(self, label: str):
        self.label            = label
        self.position_km      = 0.0
        self.velocity_ms      = 3_600.0      # ~3.6 km/s approach velocity
        self.total_impulse_ns = 0.0          # accumulated in N·s

    def apply_thruster_data(self, momentum_value: float, corrected: bool = False):
        """
        Receives momentum. Assumes it is in newton-seconds.
        If it is secretly in lbf·s, the navigation will be wrong.
        """
        if corrected:
            # Convert from lbf·s to N·s before applying
            momentum_ns = momentum_value * LBF_TO_NEWTON
        else:
            # Assume value is already N·s — no conversion
            momentum_ns = momentum_value

        self.total_impulse_ns += momentum_ns

    def compute_trajectory_adjustment(self) -> float:
        """
        Simplified: impulse / (spacecraft mass) = velocity change
        Spacecraft mass: ~638 kg
        """
        mass_kg = 638.0
        delta_v = self.total_impulse_ns / mass_kg
        return delta_v

    def simulate_approach(self, mission_days: int) -> float:
        """
        Returns final approach altitude error in km.
        A small velocity error * 10 months of flight = huge positional error.
        """
        delta_v      = self.compute_trajectory_adjustment()
        time_seconds = mission_days * 86_400
        # Positional drift = (error in delta_v) * time
        drift_km = abs(delta_v) * time_seconds / 1_000
        return drift_km


# ── Simulation ────────────────────────────────────────────────────────────────

def simulate_mission(label: str, burns: list, corrected: bool):
    nav = NavigationSystem(label)
    thruster = ThrusterSystemImperial()   # always outputs lbf·s

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Unit correction applied: {'YES — lbf·s → N·s' if corrected else 'NO  — raw lbf·s used as N·s'}")
    print(f"  {'Burn':<6} {'Raw Value':>14}  {'Used as':>16}")
    print(f"  {'─'*44}")

    for burn_s in burns:
        raw = thruster.get_momentum(burn_s)
        used = raw * LBF_TO_NEWTON if corrected else raw
        print(f"  {burn_s:<6.1f}s  {raw:>12.4f} lbf·s  {used:>14.4f} N·s")
        nav.apply_thruster_data(raw, corrected=corrected)

    drift = nav.simulate_approach(mission_days=286)   # actual mission duration
    safe_corridor = 80.0   # km — safe orbital insertion band

    print(f"\n  Accumulated positional drift: {drift:.1f} km")

    if drift > safe_corridor:
        print(f"  Required altitude: 150 km above surface")
        print(f"  Actual  altitude : ~{150 - drift:.0f} km (inside atmosphere)")
        print(f"\n  SPACECRAFT LOST — atmospheric entry at wrong angle.\n")
    else:
        print(f"\n   Trajectory within safe corridor. Orbital insertion nominal.\n")


if __name__ == "__main__":
    print(__doc__)

    # 20 short correction burns over the mission
    burns = [0.5, 1.0, 0.5, 2.0, 0.5, 1.5, 1.0, 0.5, 2.0, 1.0,
             0.5, 0.5, 1.0, 2.0, 0.5, 1.0, 1.5, 0.5, 1.0, 0.5]

    simulate_mission(" BUGGY  — No unit conversion (the actual mission)", burns, corrected=False)
    simulate_mission(" FIXED  — Correct unit conversion applied",          burns, corrected=True)

    print("─" * 60)
    print("  LESSON")
    print("─" * 60)
    print("""
  This is one of the most avoidable disasters in engineering history.
  Two teams. Two units. Zero validation. $125 million lost.

  → Every interface contract between software systems must
    explicitly specify units. "Force value" is not a contract.
    "Force value in newton-seconds" is.
  → Use typed unit wrappers in code where possible:
      newton_seconds(4.45) vs pound_force_seconds(4.45)
    A type mismatch becomes a compile error, not a crash.
  → Integration tests must include unit validation.
  → NASA now mandates metric for all space missions.
    This disaster is the reason.
""")