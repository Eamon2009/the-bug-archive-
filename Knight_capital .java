/**
 * =============================================================================
 * BUG ARCHIVE — Entry #6
 * Incident  : Knight Capital Group Trading Disaster
 * Date      : August 1, 2012
 * Language  : Java (Sun/Oracle JVM — standard for HFT order routers in 2012)
 *             SMARS (Smart Market Access Routing System) was Java-based.
 * Root Cause: A boolean feature flag (POWER_PEG_ENABLED) was repurposed
 *             as the RLP activation flag. One server was not redeployed.
 *             On that server the old code path (Power Peg) activated.
 *             Power Peg bought high and sold low at ~40 trades/second.
 *             $440 million lost in 45 minutes.
 * Loss      : $440 million | Lives Lost: 0
 * =============================================================================
 *
 * The actual SMARS system is proprietary. This reconstruction is based on
 * the SEC cease-and-desist order (Rel. No. 34-70694), the inquiry by
 * Nanex LLC, and engineering post-mortems by Doug Seven and others.
 * Variable names and structure match what was publicly described.
 *
 * =============================================================================
 */

import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicBoolean;

// =============================================================================
//     SMARS ORDER ROUTER — BUGGY VERSION (pre-deployment, server 8)
//     The flag POWER_PEG_ENABLED was repurposed: in new code it means "RLP on".
//     But server 8 was never updated — it still has the OLD code where
//     POWER_PEG_ENABLED means "run Power Peg".
// =============================================================================

class SMARS_Buggy {

    //  This flag was originally: "Power Peg strategy enabled"
    //    New code reused it to mean: "RLP (Retail Liquidity Program) enabled"
    //    Server 8 never received the update — flag still means Power Peg here.
    private static final boolean POWER_PEG_ENABLED = true;   // set by ops team

    // Dead code — should have been deleted in 2003. Never was.
    // Moved to a new entry point in 2005 during a refactor.
    // Tests for it were deleted in 2012 ("no one uses it").
    private static class PowerPegStrategy {
        private final AtomicLong totalLoss = new AtomicLong(0);
        private final AtomicLong tradeCount = new AtomicLong(0);

        /**
         * DEAD CODE — designed as an internal test tool.
         * Buys large blocks at market (or above), sells immediately lower.
         * Was NEVER intended for live production execution.
         * In a live market, every cycle loses money.
         */
        public void execute(String symbol, double marketPrice) {
            // Buy at slightly above market (aggressive taker)
            double buyPrice  = marketPrice * 1.002;
            int    quantity  = 10_000 + (int)(Math.random() * 5_000);

            // Sell immediately at market impact (below buy)
            double sellPrice = buyPrice * 0.997;

            long lossThisTrade = (long)((sellPrice - buyPrice) * quantity);
            totalLoss.addAndGet(lossThisTrade);
            tradeCount.incrementAndGet();

            System.out.printf("  [PowerPeg ] BUY  %s x%,d @ $%.4f%n",
                              symbol, quantity, buyPrice);
            System.out.printf("  [PowerPeg ] SELL %s x%,d @ $%.4f  "
                            + "  P&L: $%,d%n",
                              symbol, quantity, sellPrice, lossThisTrade);
        }

        public long getTotalLoss()  { return totalLoss.get(); }
        public long getTradeCount() { return tradeCount.get(); }
    }

    private static class RetailLiquidityProgram_NEW {
        /**
         * NEW STRATEGY — intended recipient of the repurposed flag.
         * Provides balanced liquidity. Profitable.
         */
        public void execute(String symbol, double marketPrice) {
            double spread  = 0.0002 * marketPrice;
            int    qty     = 200;
            long   profit  = (long)(spread * qty);
            System.out.printf("  [RLP new  ] SPREAD %s x%d  P&L: +$%d%n",
                              symbol, qty, profit);
        }
    }

    public static void run(int cycles) {
        PowerPegStrategy         powerPeg = new PowerPegStrategy();
        RetailLiquidityProgram_NEW rlp    = new RetailLiquidityProgram_NEW();
        double marketPrice = 45.00;

        System.out.println("\n  === BUGGY SERVER 8 (old code, flag = POWER_PEG) ===");

        for (int i = 0; i < cycles; i++) {
            marketPrice += (Math.random() - 0.5) * 0.05;

            //  POWER_PEG_ENABLED on this server still routes to old strategy
            if (POWER_PEG_ENABLED) {
                powerPeg.execute("NYSE:ACME", marketPrice);
            } else {
                rlp.execute("NYSE:ACME", marketPrice);
            }
        }

        long totalLoss    = powerPeg.getTotalLoss();
        long tradesPerMin = (long)(powerPeg.getTradeCount() / (cycles / 40.0));
        System.out.printf("%n  Trades executed : %,d%n", powerPeg.getTradeCount());
        System.out.printf("  Total P&L       : $%,d%n", totalLoss);
        System.out.printf("  Rate if continued: $%,d/minute%n",
                          totalLoss * 60 / cycles * 40);
        System.out.println("   At 45 minutes: ~$440,000,000 gone.");
    }
}


// =============================================================================
//     SMARS ORDER ROUTER — FIXED VERSION
//     Dead code deleted. New flag has an unambiguous name.
//     Deployment verified across all nodes before enabling.
// =============================================================================

class SMARS_Fixed {

    //    Flag name matches exactly what it does. No ambiguity.
    //    Old POWER_PEG_ENABLED flag was DELETED, not reused.
    private static final boolean RLP_ENABLED = true;

    //    PowerPeg class DELETED entirely (not just disabled).
    //    It exists in version control history if anyone needs it.
    //    It does not exist in any production binary.

    private static class RetailLiquidityProgram {
        private final AtomicLong totalProfit = new AtomicLong(0);

        public void execute(String symbol, double marketPrice) {
            double spread  = 0.0002 * marketPrice;
            int    qty     = 200;
            long   profit  = (long)(spread * qty);
            totalProfit.addAndGet(profit);
            System.out.printf("  [RLP      ] SPREAD %s x%d  P&L: +$%,d%n",
                              symbol, qty, profit);
        }

        public long getTotalProfit() { return totalProfit.get(); }
    }

    // Deployment verification — checked atomically before any trades
    private static boolean verifyDeployment(String[] serverVersions,
                                            String   expectedVersion) {
        System.out.println("\n  Verifying deployment across all servers...");
        boolean allGood = true;
        for (int i = 0; i < serverVersions.length; i++) {
            boolean ok = serverVersions[i].equals(expectedVersion);
            System.out.printf("  Server %d: %s %s%n",
                              i + 1, serverVersions[i],
                              ok ? "true" : " MISMATCH — HALT DEPLOYMENT");
            if (!ok) allGood = false;
        }
        return allGood;
    }

    public static void run(int cycles) {
        System.out.println("\n  === FIXED: Deployment verification ===");

        String[] serverVersions = {
            "SMARS-2.4.1", "SMARS-2.4.1", "SMARS-2.4.1", "SMARS-2.4.1",
            "SMARS-2.4.1", "SMARS-2.4.1", "SMARS-2.4.1", "SMARS-2.4.1"
            // All eight servers are the same version
            // If any were "SMARS-2.3.0" here, run() would abort
        };

        if (!verifyDeployment(serverVersions, "SMARS-2.4.1")) {
            System.out.println("\n  DEPLOYMENT ABORTED — version mismatch detected.");
            System.out.println("     No trades processed. Engineering alerted.");
            return;
        }

        System.out.println("\n   All servers verified. Starting RLP trading.\n");

        RetailLiquidityProgram rlp = new RetailLiquidityProgram();
        double marketPrice = 45.00;

        for (int i = 0; i < cycles; i++) {
            marketPrice += (Math.random() - 0.5) * 0.05;
            if (RLP_ENABLED) {
                rlp.execute("NYSE:ACME", marketPrice);
            }
        }

        System.out.printf("%n  Total profit: +$%,d%n", rlp.getTotalProfit());
        System.out.println("   Trading session complete. No incidents.");
    }
}


// =============================================================================
// MAIN
// =============================================================================

public class KnightCapital {

    public static void main(String[] args) {
        System.out.println("=".repeat(62));
        System.out.println("  KNIGHT CAPITAL — SMARS RECONSTRUCTION");
        System.out.println("=".repeat(62));

        System.out.println("\n  Bug: boolean flag POWER_PEG_ENABLED reused for RLP.");
        System.out.println("  Server 8 not updated. Old Power Peg code still active.");
        System.out.println("  Dead code (PowerPegStrategy) never deleted.");
        System.out.println("  Deployment script silently failed on 1 of 8 servers.");

        SMARS_Buggy.run(20);    // 20 cycles ≈ half a second in real SMARS

        System.out.println("\n" + "-".repeat(62));
        System.out.println("  FIXED: dead code deleted, new flag name, deploy check");
        System.out.println("-".repeat(62));

        SMARS_Fixed.run(20);

        System.out.println("\n" + "=".repeat(62));
        System.out.println("  LESSON");
        System.out.println("=".repeat(62));
        System.out.println("""
  1. DELETE dead code. Don't comment it, don't guard it.
     Delete it. Git remembers it if you ever need it back.

  2. Never reuse feature flags for new functionality.
     Old binaries on unpatched servers still respond to
     the OLD meaning of the flag.

  3. Deployment must be ATOMIC and VERIFIED.
     7/8 servers updated is not a successful deployment.
     Write a check. Fail loud if any node mismatches.

  4. An automated kill switch must exist and must be tested.
     Knight's took 45 minutes to trigger.
     A working kill switch would have taken 45 seconds.

  5. Dead code in production is a loaded gun.
     Someone, someday, will pull the trigger by accident.
        """);
    }
}

/*
 * =============================================================================
 * COMPILE AND RUN:
 *   javac KnightCapital.java
 *   java  KnightCapital
 * =============================================================================
 */