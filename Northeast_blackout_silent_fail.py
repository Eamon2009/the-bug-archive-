"""
=============================================================================
BUG ARCHIVE — Entry #8
Incident  : Northeast Blackout — 55 Million Without Power
Date      : August 14, 2003
Root Cause: A race condition bug in the XA/21 alarm management software
            caused the alert system to silently stop processing alarms.
            Operators had no idea the system had failed — they saw a
            normal quiet dashboard while the grid was collapsing around them.
Loss      : ~$6 billion | Lives Lost: ~100
=============================================================================

THE BUG EXPLAINED
-----------------
The XA/21 energy management system used by FirstEnergy had a known bug:
under specific load conditions, a race condition would cause the alarm
processing thread to become stuck. The software did not detect or report
this failure — it simply stopped delivering alerts.

Operators watched a dashboard that showed normal conditions.
In reality: three transmission lines had failed. 507 generating units
tripped. Power cascaded across eight US states and Ontario.

The alarm system had failed 90 minutes before the cascade — silently.

=============================================================================
"""

import threading
import time
import random
from collections import deque
from datetime import datetime


# ── Grid Event Types ──────────────────────────────────────────────────────────

SEVERITY = {"INFO": 0, "WARNING": 1, "CRITICAL": 2, "EMERGENCY": 3}

SEVERITY_LABELS = {0: "INFO    ", 1: "WARNING ", 2: "CRITICAL", 3: "EMERGENCY"}


class GridEvent:
    def __init__(self, message: str, severity: int):
        self.message  = message
        self.severity = severity
        self.time     = datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def __repr__(self):
        return f"[{self.time}] [{SEVERITY_LABELS[self.severity]}] {self.message}"


# ── BUGGY Alarm System ────────────────────────────────────────────────────────

class BuggyAlarmSystem:
    """
    Silent failure — if the alarm thread crashes, no one knows.
    No watchdog. No heartbeat. No dead-man switch.
    """
    def __init__(self):
        self.event_queue  = deque()
        self._running     = False
        self._thread      = None
        self._thread_alive = True
        self.delivered    = []

    def _alarm_thread(self):
        """Processes alarms. Can silently die under load."""
        process_count = 0
        while self._running:
            if self.event_queue:
                event = self.event_queue.popleft()
                process_count += 1

                # BUG: race condition simulation — under load, thread freezes
                if process_count == 5 and random.random() > 0.2:
                    print(f"  [AlarmSys]   Internal thread hung (race condition). "
                          f"No more alarms will be delivered.\n")
                    self._thread_alive = False
                    return                   # thread dies silently — no notification

                self.delivered.append(event)
                print(f"  [AlarmSys]  {event}")
            time.sleep(0.05)

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._alarm_thread, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def raise_event(self, event: GridEvent):
        self.event_queue.append(event)

    def is_healthy(self) -> bool:
        # BUG: system reports healthy even when thread has died
        return True


# ── FIXED Alarm System ────────────────────────────────────────────────────────

class FixedAlarmSystem:
    """
    Self-monitoring alarm system.
    Watchdog detects thread death and raises its own EMERGENCY alert.
    Heartbeat confirms alarm thread is alive every second.
    """
    def __init__(self):
        self.event_queue    = deque()
        self._running       = False
        self._thread        = None
        self._last_heartbeat = time.time()
        self._thread_alive  = True
        self.delivered      = []
        self._watchdog_thread = None

    def _alarm_thread(self):
        process_count = 0
        while self._running:
            self._last_heartbeat = time.time()   #  heartbeat on every loop
            if self.event_queue:
                event = self.event_queue.popleft()
                process_count += 1

                # Same race condition — but now watchdog catches it
                if process_count == 5 and random.random() > 0.2:
                    print(f"  [AlarmSys]  Internal thread hung. "
                          f"Watchdog will detect this within 1 second.")
                    self._thread_alive = False
                    return

                self.delivered.append(event)
                print(f"  [AlarmSys]  {event}")
            time.sleep(0.05)

    def _watchdog(self):
        """ Monitors heartbeat. Raises EMERGENCY if alarm thread dies."""
        time.sleep(0.5)   # give thread time to start
        while self._running:
            gap = time.time() - self._last_heartbeat
            if gap > 1.0 and not self._thread_alive:
                emergency = GridEvent(
                    " ALARM SYSTEM FAILURE — thread is unresponsive. "
                    "OPERATORS: Do NOT trust the dashboard. Inspect grid manually.",
                    SEVERITY["EMERGENCY"],
                )
                print(f"\n  [WATCHDOG] {emergency}\n")
                self._running = False
                return
            time.sleep(0.2)

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._alarm_thread, daemon=True)
        self._watchdog_thread = threading.Thread(target=self._watchdog, daemon=True)
        self._thread.start()
        self._watchdog_thread.start()

    def stop(self):
        self._running = False

    def raise_event(self, event: GridEvent):
        self.event_queue.append(event)

    def is_healthy(self) -> bool:
        return self._thread_alive


# ── Grid Failure Sequence ─────────────────────────────────────────────────────

GRID_EVENTS = [
    GridEvent("Transmission line Stuart–Atlanta trips offline",              SEVERITY["WARNING"]),
    GridEvent("Voltage sag detected in Ohio region",                         SEVERITY["WARNING"]),
    GridEvent("Transmission line Harding–Chamberlin trips offline",          SEVERITY["CRITICAL"]),
    GridEvent("Generation unit 4 in Toledo offline — load imbalance",        SEVERITY["CRITICAL"]),
    GridEvent("Transmission line Hanna–Juniper trips offline",               SEVERITY["CRITICAL"]),
    GridEvent("CASCADE: Ohio grid separating from eastern interconnect",     SEVERITY["EMERGENCY"]),
    GridEvent("CASCADE: Michigan, Pennsylvania grids tripping",              SEVERITY["EMERGENCY"]),
    GridEvent("CASCADE: New York, Ontario grids tripping",                   SEVERITY["EMERGENCY"]),
    GridEvent("BLACKOUT: 55 million customers without power",                SEVERITY["EMERGENCY"]),
]


def simulate_grid_failure(label: str, alarm_system):
    print(f"\n{'='*65}")
    print(f"  {label}")
    print(f"{'='*65}\n")
    print(f"  Alarm system starting...\n")
    alarm_system.start()
    time.sleep(0.1)

    for event in GRID_EVENTS:
        alarm_system.raise_event(event)
        time.sleep(0.15)

    time.sleep(1.5)
    alarm_system.stop()

    delivered_count = len(alarm_system.delivered)
    total_count     = len(GRID_EVENTS)
    critical_missed = sum(
        1 for e in GRID_EVENTS
        if e.severity >= SEVERITY["CRITICAL"] and e not in alarm_system.delivered
    )

    print(f"\n  {'─'*63}")
    print(f"  Events generated : {total_count}")
    print(f"  Events delivered : {delivered_count}")
    print(f"  Critical/Emergency events missed: {critical_missed}")

    if critical_missed > 0:
        print(f"\n   OPERATORS FLEW BLIND")
        print(f"     {critical_missed} critical alerts never reached operators.")
        print(f"     The grid collapsed without anyone knowing it was happening.\n")
    else:
        print(f"\n   All critical events delivered. Operators informed.\n")


if __name__ == "__main__":
    random.seed(3)
    print(__doc__)

    simulate_grid_failure("❌ BUGGY — Silent alarm failure (no watchdog)", BuggyAlarmSystem())
    simulate_grid_failure(" FIXED — Watchdog detects failure, raises emergency", FixedAlarmSystem())

    print("─" * 65)
    print("  LESSON")
    print("─" * 65)
    print("""
  The most dangerous failure is the one no one knows happened.
  A working dashboard showing wrong data is more dangerous
  than a dashboard that shows an error.

  → Every critical subsystem must monitor itself and report
    failure loudly. Silent death is unacceptable.
  → Watchdog timers / heartbeats are mandatory for threads
    that handle safety or operational alerts.
  → "The system looks normal" must mean "the system IS normal"
    — not "the system's monitoring has failed."
  → Operators should be trained to question silence.
    No alarms during a known high-risk period is itself
    an alarm — not a green light.
  → Test your monitoring system by deliberately breaking it.
    If you can't observe its failure, you can't trust it.
""")