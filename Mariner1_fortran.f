C=============================================================================
C  BUG ARCHIVE — Entry #1
C  Incident  : Mariner 1 Rocket Destruction
C  Date      : July 22, 1962
C  Language  : FORTRAN II (IBM 7090 / NASA guidance computers, 1962)
C  Root Cause: A handwritten overbar (R̄ = smoothed average) was missing
C              when transcribed to punched card code. The raw noisy radar
C              velocity R was used instead of the smoothed R̄, causing the
C              guidance system to overcorrect on normal sensor noise.
C  Loss      : ~$90 million | Lives Lost: 0 (unmanned)
C=============================================================================
C
C  FORTRAN II NOTES (authentic to 1962):
C  - Column 1    : 'C' = comment
C  - Columns 1-5 : statement label (numeric)
C  - Column 6    : continuation marker
C  - Columns 7-72: code
C  - No lowercase. No DO-WHILE. No IF-THEN-ELSE blocks.
C  - Arithmetic IF: IF (expr) neg, zero, pos  — branches on sign
C  - All variables REAL unless named I,J,K,L,M,N (then INTEGER)
C
C=============================================================================
C  THE BUG: MISSING OVERBAR IN VELOCITY SMOOTHING
C=============================================================================
C
C  The original formula used R̄ (R-bar), meaning smoothed average velocity.
C  Without the overbar, raw noisy sensor reading R was used directly.
C
C  BUGGY guidance (what was actually coded on the punched cards):
C
      SUBROUTINE GUIDBG(R, RTARGT, CORRCT)
C     R      = RAW RADAR VELOCITY (NOISY)
C     RTARGT = TARGET VELOCITY
C     CORRCT = STEERING CORRECTION OUTPUT
      REAL R, RTARGT, CORRCT, ERROR
C
C      BUG: R IS RAW SENSOR READING — NOT SMOOTHED
C     THE OVERBAR (R̄) WAS MISSING FROM THE PUNCHED CARD
      ERROR  = R - RTARGT
      CORRCT = ERROR * 2.5
C
C     AMPLIFIES NOISE DIRECTLY INTO STEERING — ROCKET DESTROYED
      RETURN
      END
C
C=============================================================================
C  THE FIX: AVERAGE MULTIPLE SAMPLES (WHAT R̄ MEANT)
C=============================================================================
C
      SUBROUTINE GUIDFX(RBUF, NBUF, RTARGT, CORRCT)
C     RBUF   = ARRAY OF RECENT VELOCITY READINGS (RING BUFFER)
C     NBUF   = NUMBER OF SAMPLES IN BUFFER
C     RTARGT = TARGET VELOCITY
C     CORRCT = STEERING CORRECTION OUTPUT
      REAL RBUF(10), RTARGT, CORRCT, RBAR, SUMR, ERROR
      INTEGER NBUF, I
C
C      FIX: COMPUTE R̄ — AVERAGE OF LAST NBUF SAMPLES
      SUMR = 0.0
      DO 10 I = 1, NBUF
   10 SUMR = SUMR + RBUF(I)
      RBAR = SUMR / FLOAT(NBUF)
C
C     NOISE AVERAGES OUT — ONLY REAL DEVIATIONS TRIGGER CORRECTION
      ERROR  = RBAR - RTARGT
      CORRCT = ERROR * 2.5
      RETURN
      END
C
C=============================================================================
C  SIMULATION DRIVER
C=============================================================================
C
      PROGRAM MARNER
      REAL RBUF(10), RTRUE, RTARGT, CORRCT, RNOISE
      INTEGER I, STEP
C
      RTRUE  = 1000.0
      RTARGT = 1000.0
      WRITE (6,100)
  100 FORMAT ('MARINER 1 GUIDANCE SIMULATION')
      WRITE (6,101) RTRUE, RTARGT
  101 FORMAT ('TRUE VELOCITY=',F8.1,'  TARGET=',F8.1)
C
C     --- BUGGY VERSION: USE RAW READING ---
      WRITE (6,102)
  102 FORMAT ('--- BUGGY: RAW SENSOR (NO OVERBAR) ---')
      DO 20 STEP = 1, 5
C       SIMULATE SENSOR NOISE (+/- 40 UNITS)
        RNOISE = -40.0 + FLOAT(STEP) * 18.3
        CALL GUIDBG(RTRUE + RNOISE, RTARGT, CORRCT)
        WRITE (6,103) STEP, RNOISE, CORRCT
  103   FORMAT ('  STEP',I2,'  NOISE=',F7.1,'  CORRECTION=',F9.2)
        IF (ABS(CORRCT) - 30.0) 20, 99, 99
   20 CONTINUE
      GO TO 30
C
   99 WRITE (6,104)
  104 FORMAT ('  *** OVER-CORRECTION DETECTED — SELF DESTRUCT ***')
C
C     --- FIXED VERSION: SMOOTHED AVERAGE ---
   30 WRITE (6,105)
  105 FORMAT ('--- FIXED: SMOOTHED AVERAGE (R-BAR) ---')
      DO 40 I = 1, 10
        RNOISE  = -40.0 + FLOAT(I) * 8.5
        RBUF(I) = RTRUE + RNOISE
   40 CONTINUE
      CALL GUIDFX(RBUF, 10, RTARGT, CORRCT)
      WRITE (6,106) CORRCT
  106 FORMAT ('  SMOOTHED CORRECTION=',F9.2,'  (WITHIN SAFE RANGE)')
C
      STOP
      END
C
C=============================================================================
C  LESSON
C  A single symbol — an overbar above the letter R — was the difference
C  between a stable guidance system and one that fought its own rocket.
C  When transcribing mathematics to code, every notation is semantic.
C  The missing R̄ was not a typo. It was a lost meaning.
C=============================================================================