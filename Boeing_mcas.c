/**
 * =============================================================================
 * BUG ARCHIVE — Entry #8
 * Incident  : Boeing 737 MAX — MCAS System Failures
 * Date      : October 2018 & March 2019
 * Language  : C  (ARINC 653 / DO-178C compliant embedded flight software)
 *             Boeing flight control systems run on PowerPC processors
 *             using C under a real-time OS (VxWorks or INTEGRITY RTOS).
 *             Certification standard: DO-178C Level A (highest criticality).
 * Root Cause: MCAS read angle-of-attack from a SINGLE sensor with no
 *             cross-check or redundancy. A failed sensor produced a stuck
 *             reading of ~74°. MCAS activated repeatedly with no activation
 *             limit and no independent sensor fault detection.
 *             Pilots were not told MCAS existed.
 * Loss      : 346 lives | $20 billion+ | 20-month grounding
 * =============================================================================
 *
 * This reconstruction is based on:
 *   - JATR (Joint Authorities Technical Review) report, Oct 2019
 *   - Ethiopian Airlines ET302 Accident Investigation Report
 *   - Lion Air JT610 KNKT Final Report
 *   - Boeing MCAS description in the 737 MAX FCOM (flight crew ops manual)
 *
 * Variable names and logic match those described in these public documents.
 *
 * =============================================================================
 */

#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

/* ── Constants ───────────────────────────────────────────────────────────── */
#define STALL_AOA_THRESHOLD_DEG 15.0f /* above this → MCAS activates    */
#define MCAS_NOSE_DOWN_DEGREES 2.5f   /* nose-down pitch per activation  */
#define PILOT_MAX_NOSE_UP_DEG 1.8f    /* max pilot column back-pressure  */
#define AOA_DISAGREE_LIMIT_DEG 10.0f  /* sensors disagree threshold      */
#define SAFE_PITCH_LIMIT_DEG -20.0f   /* unrecoverable dive threshold    */
#define MCAS_SINGLE_ACTIVATION 1      /* fixed version: max 1 activation */

/* ── Sensor structure ────────────────────────────────────────────────────── */
typedef struct
{
       char id[8];
       float current_reading_deg;
       bool failed;
       float stuck_value; /* if failed=true, always returns this     */
} AoaSensor;

float sensor_read(const AoaSensor *sensor, float true_aoa)
{
       if (sensor->failed)
              return sensor->stuck_value; /* stuck sensor — always returns fault val */
       /* Real sensors: ±0.3° noise */
       float noise = ((float)rand() / RAND_MAX - 0.5f) * 0.6f;
       return true_aoa + noise;
}

/* =============================================================================
 * ❌  BUGGY MCAS — as certified and deployed on 737 MAX (pre-crash)
 *
 *  - Single AoA sensor input  (no cross-check with the other sensor)
 *  - No activation counter    (fires continuously until pilot disables)
 *  - No sensor fault detection
 *  - System existence not disclosed to pilots
 * ============================================================================= */

typedef struct
{
       int activation_count;
       bool inhibited;
} Mcas_State;

/**
 * ❌ BUGGY: single sensor, unlimited activations, no sensor validation
 *
 * @param sensor        Single AoA sensor (no redundancy)
 * @param true_aoa      Actual aircraft angle of attack
 * @param pilot_input   Pilot column input (+ve = nose up)
 * @param state         MCAS internal state
 * @return              Net pitch command (negative = nose down)
 */
float mcas_update_buggy(const AoaSensor *sensor,
                        float true_aoa,
                        float pilot_input,
                        Mcas_State *state)
{

       float sensed_aoa = sensor_read(sensor, true_aoa);

       /* ❌ No cross-check with second sensor                                    */
       /* ❌ No sensor validity check                                              */
       /* ❌ No activation limit                                                   */

       if (sensed_aoa >= STALL_AOA_THRESHOLD_DEG)
       {
              state->activation_count++;
              /* MCAS fires nose-down, pilot tries to pull up — MCAS wins           */
              return -MCAS_NOSE_DOWN_DEGREES + pilot_input;
       }
       return pilot_input;
}

/* =============================================================================
 * ✅  FIXED MCAS — redesigned after the crashes (737 MAX Software Update)
 *
 *  - Dual AoA sensors with cross-check (AoA Disagree alert)
 *  - Single-activation limit (requires pilot acknowledgement to fire again)
 *  - Pilot can always override with column force
 *  - AOA Disagree shown on flight deck display (previously optional $)
 * ============================================================================= */

/**
 * ✅ FIXED: dual sensor cross-check, activation limit, sensor fault detection
 *
 * @param left_sensor    Left AoA vane
 * @param right_sensor   Right AoA vane
 * @param true_aoa       Actual aircraft angle of attack
 * @param pilot_input    Pilot column input
 * @param state          MCAS internal state
 * @param alert_out      Output: alert string (NULL if none)
 * @return               Net pitch command
 */
float mcas_update_fixed(const AoaSensor *left_sensor,
                        const AoaSensor *right_sensor,
                        float true_aoa,
                        float pilot_input,
                        Mcas_State *state,
                        const char **alert_out)
{
       *alert_out = NULL;

       float left_aoa = sensor_read(left_sensor, true_aoa);
       float right_aoa = sensor_read(right_sensor, true_aoa);
       float disagree = fabsf(left_aoa - right_aoa);

       /* ✅ Cross-check: if sensors disagree, inhibit MCAS and alert crew        */
       if (disagree > AOA_DISAGREE_LIMIT_DEG)
       {
              state->inhibited = true;
              *alert_out = "AOA DISAGREE — MCAS INHIBITED";
              return pilot_input; /* pilot has full authority */
       }

       if (state->inhibited)
              return pilot_input;

       /* ✅ Single activation limit                                               */
       if (state->activation_count >= MCAS_SINGLE_ACTIVATION)
              return pilot_input;

       float averaged_aoa = (left_aoa + right_aoa) * 0.5f;

       if (averaged_aoa >= STALL_AOA_THRESHOLD_DEG)
       {
              state->activation_count++;
              return -MCAS_NOSE_DOWN_DEGREES + pilot_input;
       }

       return pilot_input;
}

/* =============================================================================
 * FLIGHT SIMULATION
 * ============================================================================= */

void simulate_flight(const char *label, bool use_fixed,
                     bool left_sensor_fails_at_step_2)
{

       AoaSensor left = {"LEFT", 0.0f, false, 0.0f};
       AoaSensor right = {"RIGHT", 0.0f, false, 0.0f};

       Mcas_State state = {0, false};

       float true_aoa = 5.0f; /* normal climb: 5° */
       float cumulative_pitch = 0.0f;
       float pilot_input = +PILOT_MAX_NOSE_UP_DEG;

       printf("\n%s\n", label);
       printf("%-6s  %-9s  %-9s  %-8s  %-10s  %-11s  %s\n",
              "Step", "True AoA", "Sensed", "MCASFire", "PilotInput",
              "NetPitch", "Alert");
       printf("%s\n", "--------------------------------------------------------------"
                      "--------------------");

       for (int step = 1; step <= 12; step++)
       {

              if (step == 2 && left_sensor_fails_at_step_2)
              {
                     left.failed = true;
                     left.stuck_value = 74.0f; /* sensor jams at 74° — extreme stall */
              }

              float net_pitch;
              const char *alert = NULL;
              bool mcas_fired;

              if (use_fixed)
              {
                     float before = state.activation_count;
                     net_pitch = mcas_update_fixed(&left, &right,
                                                   true_aoa, pilot_input,
                                                   &state, &alert);
                     mcas_fired = (state.activation_count > (int)before);
              }
              else
              {
                     int before = state.activation_count;
                     net_pitch = mcas_update_buggy(&left, true_aoa,
                                                   pilot_input, &state);
                     mcas_fired = (state.activation_count > before);
              }

              cumulative_pitch += net_pitch;
              float sensed = sensor_read(&left, true_aoa);

              printf("%-6d  %+8.1f°  %+8.1f°  %-8s  %+9.1f°  %+10.1f°  %s\n",
                     step, true_aoa, sensed,
                     mcas_fired ? "🔴 YES" : "no",
                     pilot_input, net_pitch,
                     alert ? alert : (left.failed && step >= 2 ? "SENSOR FAIL" : ""));

              if (cumulative_pitch <= SAFE_PITCH_LIMIT_DEG)
              {
                     printf("\n  💥 UNRECOVERABLE DIVE  cumulative=%.1f°  "
                            "MCAS activations=%d\n\n",
                            cumulative_pitch, state.activation_count);
                     return;
              }
       }
       printf("\n  ✅ FLIGHT NOMINAL  final cumulative pitch=%.1f°\n\n",
              cumulative_pitch);
}

int main(void)
{
       srand(7);

       printf("=================================================================\n");
       printf("  BOEING 737 MAX MCAS — C Flight Software Reconstruction\n");
       printf("=================================================================\n");

       simulate_flight(
           "❌ BUGGY MCAS — Single sensor, sensor fails step 2",
           false, true);

       simulate_flight(
           "✅ FIXED MCAS — Dual sensor cross-check, sensor fails step 2",
           true, true);

       printf("=================================================================\n");
       printf("  LESSON\n");
       printf("=================================================================\n");
       printf(R"(
  DO-178C Level A requires the highest software assurance level
  for flight-critical systems. MCAS was certified Level A.

  Yet it relied on a single sensor. A single point of failure
  in a Level A system is a fundamental design violation.

  The certification process reviewed the code.
  It did not fully review the system architecture.
  It did not question the single-sensor assumption.
  It did not require pilots to be informed MCAS existed.

  346 people died because of design decisions, not code bugs.

  → Safety-critical = redundant sensors. Always. No exceptions.
  → Cross-check sensor inputs. Disagree = inhibit + alert.
  → Automatic overrides of pilot control must have hard limits.
  → Every system affecting flight path must be disclosed to pilots.
  → DO-178C reviews code. Engineers must also review architecture.
  → "Works on Ariane 4" and "works in testing" are not enough.
    Prove safety under every failure mode — including sensor failure.
)");

       return 0;
}

/*
 * =============================================================================
 * COMPILE:
 *   gcc -std=c11 -lm -o mcas boeing_mcas_c.c
 * RUN:
 *   ./mcas
 * =============================================================================
 */