/*
 * =============================================================================
 * BUG ARCHIVE — Entry #4
 * Incident  : Mars Climate Orbiter — Lost in Space
 * Date      : September 23, 1999
 * Language  : C  (Lockheed Martin ground navigation software — AMD29000 CPU)
 * Root Cause: angular_momentum() returned values in pound-force·seconds (lbf·s).
 *             The calling navigation system expected newton-seconds (N·s).
 *             No unit annotation in the function signature.
 *             No conversion at the interface boundary.
 *             $125 million spacecraft destroyed on Mars atmospheric entry.
 * Loss      : ~$125 million | Lives Lost: 0
 * =============================================================================
 *
 * C was the standard language for embedded ground systems at JPL/Lockheed
 * in the late 1990s. The navigation software AMD_MANEUVER.C produced
 * thruster data that was consumed by JPL's trajectory correction code.
 * The interface was a plain double — no unit information, no wrapper type,
 * no static analysis to catch the mismatch.
 *
 * =============================================================================
 */

#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/* ── Unit constants ────────────────────────────────────────────────────────── */
#define LBF_PER_NEWTON 0.224809  /* 1 N = 0.224809 lbf              */
#define NEWTON_PER_LBF 4.44822   /* 1 lbf = 4.44822 N               */
#define SPACECRAFT_MASS_KG 638.0 /* Mars Climate Orbiter dry mass   */
#define MISSION_DAYS 286         /* actual flight duration           */

/* ── Thruster spec (real MCO thruster: ~4.45 N hydrazine) ──────────────────── */
#define THRUSTER_FORCE_NEWTONS 4.45
#define THRUSTER_FORCE_LBF (THRUSTER_FORCE_NEWTONS * LBF_PER_NEWTON) /* ~1.0 lbf */

/* =============================================================================
 *   BUGGY LOCKHEED FUNCTION (AMD_MANEUVER.C)
 *
 * Returns thruster angular momentum in POUND-FORCE SECONDS.
 * Comment says nothing about units. The function name says nothing.
 * The return type is plain `double`.
 * JPL's nav software expected newton-seconds.
 * ============================================================================= */

/**
 * Compute thruster angular momentum for a burn.
 *
 * @param burn_duration_s  Duration of thruster burn in seconds
 * @return                 Angular momentum (units: UNDOCUMENTED — actually lbf·s)
 */
double angular_momentum(double burn_duration_s)
{
       /*  Returns lbf·s — but the comment and name give no indication */
       return THRUSTER_FORCE_LBF * burn_duration_s;
}

/* =============================================================================
 *   FIXED LOCKHEED FUNCTION — explicit unit in name and comment
 * ============================================================================= */

/**
 * Compute thruster angular momentum for a burn.
 *
 * @param burn_duration_s  Duration of thruster burn in seconds
 * @return                 Angular momentum in NEWTON-SECONDS (N·s)
 *
 * UNIT CONTRACT: caller must expect SI units (N·s).
 * Do NOT pass this value to any function expecting imperial units.
 */
double angular_momentum_newton_seconds(double burn_duration_s)
{
       /*  Converts to N·s explicitly before returning */
       double impulse_lbf_s = THRUSTER_FORCE_LBF * burn_duration_s;
       return impulse_lbf_s * NEWTON_PER_LBF; /* → N·s */
}

/* =============================================================================
 * JPL NAVIGATION SYSTEM — expects N·s, accumulates trajectory corrections
 * ============================================================================= */

typedef struct
{
       double total_impulse_ns;  /* accumulated impulse in N·s */
       double velocity_error_ms; /* velocity error in m/s      */
       double position_error_km; /* positional drift in km     */
} NavState;

void nav_apply_impulse(NavState *nav, double impulse_ns)
{
       /* Navigation math — assumes input is newton-seconds */
       nav->total_impulse_ns += impulse_ns;
       nav->velocity_error_ms = nav->total_impulse_ns / SPACECRAFT_MASS_KG;
       /* Error accumulates over 286 days of flight */
       nav->position_error_km = fabs(nav->velocity_error_ms) * MISSION_DAYS * 86400.0 / 1000.0;
}

void nav_print(const NavState *nav, const char *label)
{
       printf("\n  [%s]\n", label);
       printf("  Total impulse   : %10.4f N·s\n", nav->total_impulse_ns);
       printf("  Velocity error  : %10.6f m/s\n", nav->velocity_error_ms);
       printf("  Positional drift: %10.1f km  (after %d days of flight)\n",
              nav->position_error_km, MISSION_DAYS);

       if (nav->position_error_km > 80.0)
       {
              printf("  SAFE corridor   : ±80 km for orbital insertion\n");
              printf("  Required altitude: 150 km\n");
              printf("  Actual altitude  : ~%.0f km (inside atmosphere)\n",
                     150.0 - nav->position_error_km);
              printf("  💥 SPACECRAFT LOST — atmospheric entry at wrong angle.\n");
       }
       else
       {
              printf("   Within safe corridor. Orbital insertion nominal.\n");
       }
}

/* =============================================================================
 * SIMULATION
 * ============================================================================= */

int main(void)
{

       /* Typical correction burns over a 9-month mission */
       double burns[] = {0.5, 1.0, 0.5, 2.0, 0.5, 1.5, 1.0,
                         0.5, 2.0, 1.0, 0.5, 0.5, 1.0, 2.0,
                         0.5, 1.0, 1.5, 0.5, 1.0, 0.5};
       int n_burns = sizeof(burns) / sizeof(burns[0]);

       printf("=============================================================\n");
       printf("  MARS CLIMATE ORBITER — Unit Mismatch Simulation\n");
       printf("=============================================================\n");
       printf("\n  Thruster force (actual): %.2f N  = %.4f lbf\n",
              THRUSTER_FORCE_NEWTONS, THRUSTER_FORCE_LBF);
       printf("  Unit conversion factor : 1 lbf·s = %.5f N·s\n", NEWTON_PER_LBF);
       printf("  Error multiplier       : %.1fx too small when lbf passed as N·s\n\n",
              NEWTON_PER_LBF);

       /* --- BUGGY: lbf·s values fed into N·s nav system --- */
       NavState nav_buggy = {0.0, 0.0, 0.0};
       printf("   BUGGY — angular_momentum() returns lbf·s,\n"
              "     nav system consumes as N·s (no conversion)\n");
       printf("  %-6s  %-14s  %-14s\n", "Burn", "lbf·s (actual)", "Used as N·s");
       printf("  %-6s  %-14s  %-14s\n", "------", "--------------", "------------");

       for (int i = 0; i < n_burns; i++)
       {
              double lbf_s = angular_momentum(burns[i]); /* returns lbf·s */
              nav_apply_impulse(&nav_buggy, lbf_s);      /* consumed as N·s */
              if (i < 4 || i == n_burns - 1)
                     printf("  %.1fs    %10.5f lbf·s   %10.5f (wrong unit)\n",
                            burns[i], lbf_s, lbf_s);
       }
       nav_print(&nav_buggy, "BUGGY RESULT");

       /* --- FIXED: N·s values used correctly --- */
       NavState nav_fixed = {0.0, 0.0, 0.0};
       printf("\n\n   FIXED — angular_momentum_newton_seconds() returns N·s\n");

       for (int i = 0; i < n_burns; i++)
       {
              double ns = angular_momentum_newton_seconds(burns[i]); /* returns N·s */
              nav_apply_impulse(&nav_fixed, ns);
       }
       nav_print(&nav_fixed, "FIXED RESULT");

       /* --- Show the real interface problem --- */
       printf("\n\n=============================================================\n");
       printf("  THE REAL BUG: C function signatures carry no unit info\n");
       printf("=============================================================\n\n");

       printf("   Buggy interface:\n");
       printf("     double angular_momentum(double burn_s);\n");
       printf("     // Returns: ??? Nobody knows without reading the body.\n\n");

       printf("   Fixed interface options:\n");
       printf("     double angular_momentum_newton_seconds(double burn_s);\n");
       printf("     // OR use a typedef:\n");
       printf("     typedef double Newton_Seconds;\n");
       printf("     Newton_Seconds angular_momentum(double burn_s);\n");
       printf("     // OR in C11+, use _Generic or tagged struct:\n");
       printf("     typedef struct { double value; } Newton_Seconds;\n");
       printf("     Newton_Seconds angular_momentum(double burn_s);\n");
       printf("     // Compiler now catches unit mismatches at the call site.\n\n");

       printf("  LESSON:\n");
       printf("  In C, a double is a double. It carries no semantic meaning.\n");
       printf("  Name your functions and types to include units.\n");
       printf("  Document the unit contract in the function header.\n");
       printf("  At system boundaries between teams, validate units explicitly.\n");
       printf("  $125 million is a lot to pay for a missing comment.\n\n");

       return 0;
}

/*
 * =============================================================================
 * LESSON
 * The Lockheed engineer who wrote angular_momentum() was correct.
 * The function did exactly what it was designed to do: compute lbf·s.
 * JPL's navigation code was correct: it consumed the value it was given.
 * The bug lived in the interface — the invisible contract between two
 * teams, expressed only in the name "angular_momentum", which says
 * nothing about whether the result is in SI or imperial units.
 *
 * This is a failure of interface design, not implementation.
 *
 * → Name functions with units when they return physical quantities.
 * → Use wrapper types to make unit mismatches into compiler errors.
 * → At inter-team interfaces, write explicit unit contracts in headers.
 * → Integration tests must verify unit consistency across subsystems.
 * → NASA now mandates metric (SI) for all space missions. This bug
 *   is the reason that policy exists.
 * =============================================================================
 */