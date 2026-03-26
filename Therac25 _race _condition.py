"""
=============================================================================
BUG ARCHIVE — Entry #2
Incident  : Therac-25 Radiation Therapy Machine
Date      : 1985–1987
Root Cause: A race condition — if an operator typed fast enough, a shared
            state variable (mode) could be set to HIGH_POWER before the
            hardware safety flag was armed. The physical safety interlock
            had been removed and replaced with a software-only check.
            The software check could be bypassed by timing alone.
Loss      : Immeasurable | Lives Lost: 6 killed or permanently injured
=============================================================================

THE BUG EXPLAINED
-----------------
The machine had two modes:
  - X-RAY mode  : high-powered beam, requires physical beam spreader
  - ELECTRON mode: low-power direct beam, no spreader needed

The operator UI allowed edits. If an operator:
  1. Selected X-RAY mode     → machine begins preparing high-power beam
  2. Quickly changed to ELECTRON mode  (within ~8 seconds)
  3. Pressed ENTER to confirm

...the machine would fire a HIGH-POWER beam in ELECTRON configuration —
with NO spreader, NO physical shielding, delivering a dose 100x the prescription.

The bug: a shared `mode` variable was read by the hardware at a different
time than it was set by the UI thread. Classic TOCTOU (Time-of-Check
to Time-of-Use) race condition.

=============================================================================
"""

import threading
import time
import random

# ── Shared State (the dangerous global) ──────────────────────────────────────

class MachineState:
    def __init__(self):
        self.mode             = "ELECTRON"    # current mode
        self.spreader_armed   = False          # physical spreader status
        self.beam_power       = "LOW"          # beam power level
        self.lock             = threading.Lock()   # used in the FIXED version only


# ── BUGGY VERSION ─────────────────────────────────────────────────────────────

def buggy_operator_ui(state: MachineState, delay: float):
    """Operator types fast — changes mode after preparation starts."""
    print(f"  [UI]      Operator selects X-RAY mode")
    state.mode           = "XRAY"
    state.spreader_armed = True
    state.beam_power     = "HIGH"

    time.sleep(delay)                          # operator edits quickly

    print(f"  [UI]      Operator switches to ELECTRON mode (edit)")
    state.mode = "ELECTRON"                    # mode changed...
    # ...but spreader_armed and beam_power are NOT reset — race condition!


def buggy_hardware_fire(state: MachineState):
    """Hardware reads state and fires. No synchronisation."""
    time.sleep(0.01)                           # tiny delay, hardware reads mid-edit
    print(f"  [HW]      Hardware reads mode     : {state.mode}")
    print(f"  [HW]      Hardware reads power    : {state.beam_power}")
    print(f"  [HW]      Hardware reads spreader : {'ARMED' if state.spreader_armed else 'NOT ARMED'}")

    if state.mode == "ELECTRON" and state.beam_power == "HIGH":
        print("\n   FATAL: HIGH-POWER beam fired in ELECTRON mode!")
        print("           No spreader. Patient receives ~100x prescribed dose.")
        print("           This is what killed Therac-25 patients.\n")
    else:
        print("\n   Beam fired safely.\n")


def run_buggy_simulation(fast_typist: bool):
    state = MachineState()
    delay = 0.005 if fast_typist else 0.5      # fast vs slow operator

    label = "fast typist (dangerous)" if fast_typist else "slow typist (safe by accident)"
    print(f"\n{'='*60}")
    print(f"  BUGGY Therac-25 — {label}")
    print(f"{'='*60}")

    ui_thread = threading.Thread(target=buggy_operator_ui,  args=(state, delay))
    hw_thread = threading.Thread(target=buggy_hardware_fire, args=(state,))

    ui_thread.start()
    hw_thread.start()
    ui_thread.join()
    hw_thread.join()


# ── FIXED VERSION ─────────────────────────────────────────────────────────────

def fixed_operator_ui(state: MachineState, delay: float):
    """Operator selects mode — atomic update with lock."""
    with state.lock:
        print(f"  [UI]      Operator selects X-RAY mode (locked write)")
        state.mode           = "XRAY"
        state.spreader_armed = True
        state.beam_power     = "HIGH"

    time.sleep(delay)

    with state.lock:
        print(f"  [UI]      Operator switches to ELECTRON mode (locked write)")
        state.mode           = "ELECTRON"      # all three reset atomically
        state.spreader_armed = False
        state.beam_power     = "LOW"


def fixed_hardware_fire(state: MachineState):
    """Hardware reads state atomically — whole state is consistent."""
    time.sleep(0.01)
    with state.lock:
        mode    = state.mode
        power   = state.beam_power
        spreader = state.spreader_armed

    print(f"  [HW]      Hardware reads mode     : {mode}")
    print(f"  [HW]      Hardware reads power    : {power}")
    print(f"  [HW]      Hardware reads spreader : {'ARMED' if spreader else 'NOT ARMED'}")

    if mode == "ELECTRON" and power == "HIGH":
        print("\n   FATAL: Inconsistent state still detected — would refuse to fire.\n")
    else:
        print("\n   State consistent. Beam fired safely.\n")


def run_fixed_simulation(fast_typist: bool):
    state = MachineState()
    delay = 0.005 if fast_typist else 0.5

    label = "fast typist (now safe)"
    print(f"\n{'='*60}")
    print(f"   FIXED Therac-25 — {label}")
    print(f"{'='*60}")

    ui_thread = threading.Thread(target=fixed_operator_ui,  args=(state, delay))
    hw_thread = threading.Thread(target=fixed_hardware_fire, args=(state,))

    ui_thread.start()
    hw_thread.start()
    ui_thread.join()
    hw_thread.join()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(__doc__)

    # Buggy — slow operator is accidentally safe
    run_buggy_simulation(fast_typist=False)

    # Buggy — fast operator triggers the race condition
    run_buggy_simulation(fast_typist=True)

    # Fixed — fast operator is now safe
    run_fixed_simulation(fast_typist=True)

    print("─" * 60)
    print("  LESSON")
    print("─" * 60)
    print("""
  Race conditions are invisible under normal use. They only
  surface under specific timing — which is exactly why they
  survived testing and reached patients.

  → Shared mutable state accessed by multiple threads MUST
    be protected with locks or made atomic.
  → Safety-critical state transitions should be atomic:
    all fields update together or none do.
  → NEVER replace physical hardware interlocks with
    software-only checks. Software can be bypassed.
    Hardware cannot.
  → Medical software must be independently audited.
    "Works in testing" is not good enough.
""")