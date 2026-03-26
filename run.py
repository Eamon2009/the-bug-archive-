"""
=============================================================================
  THE BUG ARCHIVE — Main Runner
  Run all bug simulations in sequence, or pick one to explore.
=============================================================================
"""

import subprocess
import sys
import os

BUGS = [
    {
        "id"      : 1,
        "title"   : "Mariner 1 — The Missing Hyphen (1962)",
        "file"    : "examples/mariner1_hyphen.py",
        "tags"    : ["formula", "transcription", "sensor", "space"],
        "loss"    : "$90 million",
        "lives"   : 0,
    },
    {
        "id"      : 2,
        "title"   : "Therac-25 — Race Condition Kills Patients (1985)",
        "file"    : "examples/therac25_race_condition.py",
        "tags"    : ["race condition", "concurrency", "medical", "threading"],
        "loss"    : "Immeasurable",
        "lives"   : 6,
    },
    {
        "id"      : 3,
        "title"   : "Ariane 5 — Integer Overflow (1996)",
        "file"    : "examples/ariane5_overflow.py",
        "tags"    : ["overflow", "type conversion", "space", "reused code"],
        "loss"    : "$370 million",
        "lives"   : 0,
    },
    {
        "id"      : 4,
        "title"   : "Mars Climate Orbiter — Unit Mismatch (1999)",
        "file"    : "examples/mars_orbiter_units.py",
        "tags"    : ["units", "interface", "space", "metric"],
        "loss"    : "$125 million",
        "lives"   : 0,
    },
    {
        "id"      : 5,
        "title"   : "Y2K — Two-Digit Year Assumption (2000)",
        "file"    : "examples/y2k_date_bug.py",
        "tags"    : ["date", "assumption", "legacy", "overflow"],
        "loss"    : "$300–600 billion",
        "lives"   : 0,
    },
    {
        "id"      : 6,
        "title"   : "Intel Pentium FDIV — Floating Point Error (1994)",
        "file"    : "examples/pentium_fdiv.py",
        "tags"    : ["floating point", "hardware", "lookup table", "precision"],
        "loss"    : "$475 million",
        "lives"   : 0,
    },
    {
        "id"      : 7,
        "title"   : "Knight Capital — Dead Code Triggered (2012)",
        "file"    : "examples/knight_capital_deadcode.py",
        "tags"    : ["dead code", "deployment", "trading", "flag"],
        "loss"    : "$440 million",
        "lives"   : 0,
    },
    {
        "id"      : 8,
        "title"   : "Northeast Blackout — Silent Alarm Failure (2003)",
        "file"    : "examples/northeast_blackout_silent_fail.py",
        "tags"    : ["silent failure", "watchdog", "race condition", "power grid"],
        "loss"    : "$6 billion",
        "lives"   : 100,
    },
    {
        "id"      : 9,
        "title"   : "Boeing 737 MAX — Single Point of Failure (2019)",
        "file"    : "examples/boeing_mcas_spof.py",
        "tags"    : ["single point of failure", "aviation", "sensor", "redundancy"],
        "loss"    : "$20 billion+",
        "lives"   : 346,
    },
]


def print_menu():
    print("\n" + "=" * 65)
    print(" THE BUG ARCHIVE — Interactive Runner")
    print("=" * 65)
    print(f"\n  {'#':<4} {'Title':<45} {'Lives'}")
    print(f"  {'─'*62}")
    for bug in BUGS:
        lives = f" {bug['lives']}" if bug["lives"] > 0 else "   0"
        print(f"  {bug['id']:<4} {bug['title']:<45} {lives}")
    print(f"\n  {'─'*62}")
    print(f"  [A] Run ALL simulations")
    print(f"  [Q] Quit")
    print()


def run_bug(bug: dict):
    script_path = os.path.join(os.path.dirname(__file__), bug["file"])
    if not os.path.exists(script_path):
        print(f"   File not found: {script_path}")
        return

    print(f"\n{'#'*65}")
    print(f"  Running: {bug['title']}")
    print(f"{'#'*65}\n")

    result = subprocess.run([sys.executable, script_path], capture_output=False)
    if result.returncode != 0:
        print(f"\n   Script exited with code {result.returncode}")


def run_all():
    total_lives = sum(b["lives"] for b in BUGS)
    print(f"\n  Running all {len(BUGS)} bug simulations...")
    print(f"  Combined lives lost across all incidents: {total_lives}\n")
    for bug in BUGS:
        run_bug(bug)
        print("\n" + "·" * 65 + "\n")


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip()
        if arg.isdigit():
            bug_id = int(arg)
            matches = [b for b in BUGS if b["id"] == bug_id]
            if matches:
                run_bug(matches[0])
            else:
                print(f"   No bug with ID {bug_id}. Valid range: 1–{len(BUGS)}")
            return
        elif arg.lower() == "all":
            run_all()
            return

    # Interactive menu
    while True:
        print_menu()
        choice = input("  Enter number (1–9), A for all, Q to quit: ").strip().upper()

        if choice == "Q":
            print("\n  Study the bugs. Write better code.\n")
            break
        elif choice == "A":
            run_all()
        elif choice.isdigit():
            bug_id  = int(choice)
            matches = [b for b in BUGS if b["id"] == bug_id]
            if matches:
                run_bug(matches[0])
            else:
                print(f"\n   Invalid choice. Enter 1–{len(BUGS)}, A, or Q.\n")
        else:
            print(f"\n   Invalid choice. Enter 1–{len(BUGS)}, A, or Q.\n")


if __name__ == "__main__":
    main()