*> ==========================================================================
      *> BUG ARCHIVE — Entry #5
      *> Incident  : Y2K — The Year 2000 Bug
      *> Date      : 1999–2000
      *> Language  : COBOL-74 / COBOL-85 (the primary language of affected systems)
      *>             COBOL ran ~95% of all business transactions worldwide in 1999.
      *>             Banks, insurance, government, pensions — all COBOL.
      *> Root Cause: Year fields defined as PIC 99 (2 digits) instead of PIC 9999.
      *>             On 01/01/2000, "00" was interpreted as 1900 not 2000.
      *>             Date arithmetic, expiry checks, and interest calculations broke.
      *> Loss      : $300–600 billion in remediation | Lives Lost: 0 (averted)
      *> ==========================================================================
      *>
      *> COBOL NOTES (authentic to era):
      *>   PIC 99      = 2-digit numeric field  (0–99)
      *>   PIC 9999    = 4-digit numeric field  (0–9999)
      *>   PIC 99/99/99 = date with 2-digit year (THE BUG)
      *>   COMPUTE      = arithmetic operation
      *>   EVALUATE     = switch/case
      *>   88-level     = condition name (boolean alias for a value)
      *>   MOVE         = assignment
      *>   DISPLAY      = print to screen
      *>
      *> ==========================================================================

       IDENTIFICATION DIVISION.
       PROGRAM-ID. Y2K-BUG-DEMO.
       AUTHOR.     BUG-ARCHIVE.
       DATE-WRITTEN. 1985 (typical for affected systems).

      *> ==========================================================================
      *> DATA DIVISION — where the Y2K bug was born
      *> ==========================================================================
       DATA DIVISION.
       WORKING-STORAGE SECTION.

      *>  BUGGY DATE STRUCTURES (as written in the 1960s–1980s)
      *>    Saved 2 bytes per date. Seemed clever. Was catastrophic.

       01  WS-BUGGY-DATE.
           05  WS-DAY-B          PIC 99.          *> day   (2 digits)
           05  FILLER            PIC X VALUE '/'.
           05  WS-MONTH-B        PIC 99.          *> month (2 digits)
           05  FILLER            PIC X VALUE '/'.
           05  WS-YEAR-B         PIC 99.          *>  year  (2 DIGITS ONLY)
                                                  *>    1987 stored as 87
                                                  *>    2000 stored as 00
                                                  *>    Indistinguishable from 1900

       01  WS-BUGGY-EXPIRY.
           05  WS-EXP-MONTH-B    PIC 99.
           05  FILLER            PIC X VALUE '/'.
           05  WS-EXP-YEAR-B     PIC 99.          *>  expiry year (2 digits)

      *>  FIXED DATE STRUCTURES (Y2K-remediated)
       01  WS-FIXED-DATE.
           05  WS-DAY-F          PIC 99.
           05  FILLER            PIC X VALUE '/'.
           05  WS-MONTH-F        PIC 99.
           05  FILLER            PIC X VALUE '/'.
           05  WS-YEAR-F         PIC 9999.        *>  4-digit year

       01  WS-FIXED-EXPIRY.
           05  WS-EXP-MONTH-F    PIC 99.
           05  FILLER            PIC X VALUE '/'.
           05  WS-EXP-YEAR-F     PIC 9999.        *>  4-digit year

      *> Computed fields
       01  WS-TODAY-YEAR-B       PIC 99   VALUE 00.   *> "00" = Jan 1, 2000
       01  WS-TODAY-YEAR-F       PIC 9999 VALUE 2000.
       01  WS-LOAN-ISSUE-YEAR-B  PIC 99   VALUE 95.   *> 1995
       01  WS-LOAN-DUE-YEAR-B    PIC 99   VALUE 05.   *> should be 2005
       01  WS-LOAN-DUE-YEAR-F    PIC 9999 VALUE 2005.
       01  WS-LOAN-ISSUE-YEAR-F  PIC 9999 VALUE 1995.

       01  WS-DURATION-B         PIC S9(5).    *> signed — can go negative!
       01  WS-DURATION-F         PIC 9(5).

       01  WS-PENSION-YEAR-B     PIC 99   VALUE 40.   *> 1940 birth year
       01  WS-PENSION-YEAR-F     PIC 9999 VALUE 1940.
       01  WS-AGE-B              PIC S9(3).    *> signed — will compute wrong
       01  WS-AGE-F              PIC 9(3).

       01  WS-INTEREST-RATE      PIC 99V99 VALUE 05.50. *> 5.50% annual
       01  WS-PRINCIPAL          PIC 9(9)V99 VALUE 100000.00.
       01  WS-INTEREST-B         PIC S9(9)V99.   *> buggy interest
       01  WS-INTEREST-F         PIC 9(9)V99.    *> fixed interest

       01  WS-SEPARATOR          PIC X(60)
           VALUE '------------------------------------------------------------'.

       88  LOAN-OVERDUE-B        VALUE NEGATIVE.   *> condition name on WS-DURATION-B

      *> ==========================================================================
      *> PROCEDURE DIVISION
      *> ==========================================================================
       PROCEDURE DIVISION.
       MAIN-PARA.

           DISPLAY ' '
           DISPLAY 'Y2K BUG ARCHIVE — COBOL DEMONSTRATION'
           DISPLAY WS-SEPARATOR

      *>  -----------------------------------------------------------------------
      *>  SCENARIO 1: CREDIT CARD EXPIRY CHECK
      *>  Card expires 12/00 — does it mean December 1900 or December 2000?
      *>  -----------------------------------------------------------------------
           DISPLAY ' '
           DISPLAY 'SCENARIO 1: CREDIT CARD EXPIRY'
           DISPLAY WS-SEPARATOR

           MOVE 12 TO WS-EXP-MONTH-B
           MOVE 00 TO WS-EXP-YEAR-B       *> "00" — is this 1900 or 2000?
           MOVE 01 TO WS-TODAY-YEAR-B      *> January 2000 = "00"... same!

      *>   BUGGY: Two-digit comparison — "00" vs "00" = expired?
           DISPLAY '  BUGGY  Card expiry year (stored): ' WS-EXP-YEAR-B
           DISPLAY '  BUGGY  Today year       (stored): ' WS-TODAY-YEAR-B

           EVALUATE TRUE
               WHEN WS-EXP-YEAR-B < WS-TODAY-YEAR-B
                   DISPLAY '   RESULT: CARD DECLINED — system thinks'
                   DISPLAY '            card expired in 1900 (100 yrs ago)'
               WHEN WS-EXP-YEAR-B = WS-TODAY-YEAR-B
                   DISPLAY '  ? RESULT: AMBIGUOUS — 1900 or 2000?'
               WHEN OTHER
                   DISPLAY '  CARD VALID'
           END-EVALUATE

      *>   FIXED: Four-digit year — no ambiguity
           MOVE 12   TO WS-EXP-MONTH-F
           MOVE 2000 TO WS-EXP-YEAR-F
           MOVE 2000 TO WS-TODAY-YEAR-F
           DISPLAY '  FIXED  Card expiry year (stored): ' WS-EXP-YEAR-F
           DISPLAY '  FIXED  Today year       (stored): ' WS-TODAY-YEAR-F
           EVALUATE TRUE
               WHEN WS-EXP-YEAR-F < WS-TODAY-YEAR-F
                   DISPLAY '  CARD DECLINED (genuinely expired)'
               WHEN OTHER
                   DISPLAY '   RESULT: CARD VALID — expires this year'
           END-EVALUATE

      *>  -----------------------------------------------------------------------
      *>  SCENARIO 2: LOAN DURATION CALCULATION
      *>  Loan issued 1995, due 2005. Buggy system: 05 - 95 = -90 years!
      *>  -----------------------------------------------------------------------
           DISPLAY ' '
           DISPLAY 'SCENARIO 2: LOAN DURATION'
           DISPLAY WS-SEPARATOR

      *>   BUGGY: 05 - 95 = -90 (COBOL signed arithmetic)
           COMPUTE WS-DURATION-B =
               WS-LOAN-DUE-YEAR-B - WS-LOAN-ISSUE-YEAR-B

           DISPLAY '  BUGGY  Loan issued year : ' WS-LOAN-ISSUE-YEAR-B
           DISPLAY '  BUGGY  Loan due year    : ' WS-LOAN-DUE-YEAR-B
           DISPLAY '  BUGGY  Computed duration: ' WS-DURATION-B ' years'
           IF WS-DURATION-B < 0
               DISPLAY '   RESULT: NEGATIVE DURATION — loan appears 90'
               DISPLAY '            years OVERDUE. Account frozen.'
               DISPLAY '            Penalty interest applied.'
           END-IF

      *>   FIXED: 2005 - 1995 = 10 (correct)
           COMPUTE WS-DURATION-F =
               WS-LOAN-DUE-YEAR-F - WS-LOAN-ISSUE-YEAR-F

           DISPLAY '  FIXED  Loan issued year : ' WS-LOAN-ISSUE-YEAR-F
           DISPLAY '  FIXED  Loan due year    : ' WS-LOAN-DUE-YEAR-F
           DISPLAY '  FIXED  Computed duration: ' WS-DURATION-F ' years'
           DISPLAY '   RESULT: 10-year loan on track. No action required.'

      *>  -----------------------------------------------------------------------
      *>  SCENARIO 3: PENSION AGE CALCULATION
      *>  Born in 1940. Today 2000. Buggy: 00 - 40 = -40 years old!
      *>  -----------------------------------------------------------------------
           DISPLAY ' '
           DISPLAY 'SCENARIO 3: PENSION ELIGIBILITY'
           DISPLAY WS-SEPARATOR

      *>   BUGGY: 00 - 40 = -40 (negative age)
           COMPUTE WS-AGE-B =
               WS-TODAY-YEAR-B - WS-PENSION-YEAR-B

           DISPLAY '  BUGGY  Birth year : ' WS-PENSION-YEAR-B
           DISPLAY '  BUGGY  Today year : ' WS-TODAY-YEAR-B
           DISPLAY '  BUGGY  Computed age: ' WS-AGE-B
           IF WS-AGE-B < 0
               DISPLAY '   RESULT: NEGATIVE AGE — pension payments STOPPED'
               DISPLAY '            9 million UK pensioners affected.'
               DISPLAY '            System believes they have not been born yet.'
           END-IF

      *>   FIXED
           COMPUTE WS-AGE-F =
               WS-TODAY-YEAR-F - WS-PENSION-YEAR-F

           DISPLAY '  FIXED  Birth year : ' WS-PENSION-YEAR-F
           DISPLAY '  FIXED  Today year : ' WS-TODAY-YEAR-F
           DISPLAY '  FIXED  Computed age: ' WS-AGE-F
           DISPLAY '   RESULT: Age 60 — eligible for pension. Payments continue.'

      *>  -----------------------------------------------------------------------
      *>  THE LESSON IN COBOL TERMS
      *>  -----------------------------------------------------------------------
           DISPLAY ' '
           DISPLAY WS-SEPARATOR
           DISPLAY 'THE Y2K FIX IN COBOL:'
           DISPLAY WS-SEPARATOR
           DISPLAY ' '
           DISPLAY '   BUGGY (1960s–1980s):'
           DISPLAY '     05  WS-YEAR   PIC 99.'
           DISPLAY '     Saves 2 bytes. Breaks at year 2000.'
           DISPLAY ' '
           DISPLAY '   FIXED (Y2K remediation):'
           DISPLAY '     05  WS-YEAR   PIC 9999.'
           DISPLAY '     Uses 2 more bytes. Works for 8,000 more years.'
           DISPLAY ' '
           DISPLAY '  The world spent $300-600 billion remediating this.'
           DISPLAY '  The original choice saved perhaps $0.002 per record.'
           DISPLAY '  At scale, across billions of records, it felt important.'
           DISPLAY '  In hindsight, it was the most expensive optimisation'
           DISPLAY '  in computing history.'

           STOP RUN.

      *> ==========================================================================
      *> LESSON
      *> COBOL programmers in the 1960s were not foolish. Memory cost thousands
      *> of dollars per kilobyte. Saving 2 bytes per date field — multiplied
      *> across millions of records on magnetic tape — was a real, legitimate
      *> engineering trade-off. The mistake was not the decision. The mistake
      *> was the assumption that the code would be rewritten before 2000.
      *>
      *> It was not. Code does not retire. Systems outlive their assumptions.
      *>
      *> → Design for the full lifecycle of your data, not just today's needs.
      *> → Two-digit years: never. Four-digit years: always.
      *> → "We'll fix it later" is a debt that compounds with interest.
      *> → Test your date arithmetic at boundary years: 1999→2000, 2099→2100.
      *> ==========================================================================