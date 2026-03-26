"""
=============================================================================
BUG ARCHIVE — Entry #5
Incident  : Y2K — The Year 2000 Bug
Date      : 1999–2000
Root Cause: Programmers in the 1960s–80s stored years as two digits to save
            memory (e.g., 1987 → "87"). When "00" arrived, many systems
            could not determine whether it meant 1900 or 2000 — potentially
            breaking date arithmetic, contracts, expiry checks, and
            safety-critical timers worldwide.
Loss      : $300–600 billion in remediation | Lives Lost: 0 (averted)
=============================================================================

THE BUG EXPLAINED
-----------------
Two-digit year storage was a deliberate optimisation in an era when
memory cost thousands of dollars per kilobyte. Storing "87" instead of
"1987" saved 2 bytes per date field — meaningful at scale in the 1960s.

The assumption baked in: "We won't still be using this code in 30 years."

They were wrong.

=============================================================================
"""

from datetime import date, timedelta


# ── Buggy Date System (2-digit year) ─────────────────────────────────────────

class BuggyDate:
    """
     Legacy system: stores only 2-digit year.
    Assumes all years are in the 1900s.
    """
    def __init__(self, day: int, month: int, year: int):
        self.day   = day
        self.month = month
        self.year_2digit = year % 100        # strip the century

    def full_year(self) -> int:
        """Always assumes 1900s — the Y2K assumption."""
        return 1900 + self.year_2digit

    def __str__(self):
        return f"{self.day:02d}/{self.month:02d}/{self.year_2digit:02d}"

    def days_until(self, other: "BuggyDate") -> int:
        """Calculate days between two BuggyDates — broken across century boundary."""
        d1 = date(self.full_year(),  self.month,  self.day)
        d2 = date(other.full_year(), other.month, other.day)
        return (d2 - d1).days


class FixedDate:
    """
    Fixed system: stores full 4-digit year.
    No century assumption.
    """
    def __init__(self, day: int, month: int, year: int):
        self.day   = day
        self.month = month
        self.year  = year

    def __str__(self):
        return f"{self.day:02d}/{self.month:02d}/{self.year:04d}"

    def days_until(self, other: "FixedDate") -> int:
        d1 = date(self.year,       self.month,  self.day)
        d2 = date(other.year,      other.month, other.day)
        return (d2 - d1).days


# ── Real-World Failure Scenarios ──────────────────────────────────────────────

def scenario_credit_card_expiry():
    """
    A credit card expires 12/00.
    Buggy system thinks it expired in 1900 — 100 years ago.
    """
    print("\n   Scenario 1: Credit Card Expiry Check")
    print("  " + "─" * 50)

    today_buggy = BuggyDate(1, 1, 2000)     # Jan 1, 2000
    expiry_buggy = BuggyDate(31, 12, 2000)  # Dec 31, 2000

    today_fixed  = FixedDate(1, 1, 2000)
    expiry_fixed = FixedDate(31, 12, 2000)

    buggy_days = today_buggy.days_until(expiry_buggy)
    fixed_days = today_fixed.days_until(expiry_fixed)

    print(f"  Card expiry date      : 31/12/00")
    print(f"  Today                 : 01/01/00")
    print()
    print(f"   Buggy system sees  : expiry = 1900, today = 1900 → {buggy_days} days")
    if buggy_days < 0:
        print(f"     Result: CARD DECLINED — system thinks card expired 100 years ago")
    print()
    print(f"   Fixed system sees  : expiry = 2000, today = 2000 → {fixed_days} days remaining")
    print(f"     Result: CARD APPROVED")


def scenario_loan_interest():
    """
    A bank calculates interest for a 10-year loan issued in 1995, due 2005.
    Buggy system computes the duration as negative (1905 - 1995 = -90 years).
    """
    print("\n  📋 Scenario 2: Loan Duration Calculation")
    print("  " + "─" * 50)

    issue_buggy = BuggyDate(1, 6, 1995)
    due_buggy   = BuggyDate(1, 6, 2005)

    issue_fixed = FixedDate(1, 6, 1995)
    due_fixed   = FixedDate(1, 6, 2005)

    buggy_years = due_buggy.days_until(issue_buggy) / 365.0    # intentionally reversed to show negative
    fixed_years = (due_fixed.days_until(issue_fixed)) / -365.0

    print(f"  Loan issued  : 01/06/1995")
    print(f"  Loan due     : 01/06/2005  (stored as '05')")
    print()
    print(f"   Buggy system computes duration : ~{due_buggy.full_year() - issue_buggy.full_year()} years")
    print(f"     '05' interpreted as 1905 — loan appears 90 years overdue")
    print(f"     Result: ACCOUNT FROZEN, penalty interest applied, customer harmed")
    print()
    print(f"   Fixed system computes duration : 10 years")
    print(f"     Result: Loan on track, no action required")


def scenario_safety_timer():
    """
    An industrial safety system checks if its last maintenance was within 1 year.
    Buggy: last maintenance stored as '99', today is '00'.
    System thinks it was maintained 99 years ago — triggers emergency shutdown.
    """
    print("\n   Scenario 3: Safety System Maintenance Timer")
    print("  " + "─" * 50)

    last_maintenance_buggy = BuggyDate(1, 1, 1999)
    today_buggy            = BuggyDate(1, 1, 2000)

    last_maintenance_fixed = FixedDate(1, 1, 1999)
    today_fixed            = FixedDate(1, 1, 2000)

    buggy_gap_days = last_maintenance_buggy.days_until(today_buggy)
    fixed_gap_days = last_maintenance_fixed.days_until(today_fixed)

    MAINTENANCE_WINDOW_DAYS = 365

    print(f"  Last maintenance : 01/01/1999 (stored as '99')")
    print(f"  Today            : 01/01/2000 (stored as '00')")
    print()

    print(f"  Buggy: 1900 - 1999 = {buggy_gap_days} days since maintenance")
    if buggy_gap_days < 0:
        print(f"     System sees negative time — wraps to enormous positive number")
        print(f"     Result: EMERGENCY SHUTDOWN triggered (false positive)")
    print()
    print(f"   Fixed: {fixed_gap_days} days since maintenance")
    status = "OVERDUE — schedule maintenance" if fixed_gap_days > MAINTENANCE_WINDOW_DAYS else "Within window — no action needed"
    print(f"     Result: {status}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(__doc__)

    print("=" * 60)
    print("  Y2K BUG — FAILURE SCENARIO DEMONSTRATIONS")
    print("=" * 60)

    scenario_credit_card_expiry()
    scenario_loan_interest()
    scenario_safety_timer()

    print("\n" + "─" * 60)
    print("  LESSON")
    print("─" * 60)
    print("""
  Y2K is sometimes dismissed as overblown — because it was fixed.
  What is forgotten is WHY it was fixed: $300–600 billion in
  emergency remediation by hundreds of thousands of engineers
  working around the clock before midnight, January 1, 2000.

  → Short-term memory optimisations can become long-term
    civilisational liabilities. Design for longevity.
  → "This code won't be around in 30 years" is a bet you
    will often lose. Write as if it will be.
  → Dates are hard. Use well-tested standard libraries
    (datetime, dateutil) and always store full 4-digit years.
  → Legacy systems outlive their assumptions. Audit old code
    for embedded assumptions before they become ticking clocks.
""")