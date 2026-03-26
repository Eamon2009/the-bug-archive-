"""
=============================================================================
BUG ARCHIVE — Entry #6
Incident  : Knight Capital Group Trading Disaster
Date      : August 1, 2012
Root Cause: A deprecated feature flag ("SMARS") was repurposed in a new
            deployment. One of eight servers did not receive the update.
            On that server, the old flag activated an abandoned trading
            strategy ("Power Peg") that bought high and sold low at
            massive volume. ~$10 million lost per minute for 45 minutes.
Loss      : $440 million | Lives Lost: 0
=============================================================================

THE BUG EXPLAINED
-----------------
Knight Capital had old code (Power Peg) that was decommissioned.
Instead of deleting it, they left it in the codebase, guarded by a flag.

When deploying new code, they reused that same flag for new functionality.
Seven servers got the update. One didn't.

On the unpatched server:
  - New code  : flag OFF  →  new feature doesn't run (intended)
  - Old code  : flag ON   →  Power Peg activates (catastrophic)

Power Peg's strategy: accumulate large stock positions rapidly.
It was never meant to run in a live market unsupervised.

=============================================================================
"""

import random
import time

# ── Feature Flags ─────────────────────────────────────────────────────────────

REPURPOSED_FLAG = "SMARS"

# ── Trading Strategies ────────────────────────────────────────────────────────

class PowerPeg:
    """
    ABANDONED strategy. Should have been DELETED, not just disabled.
    Buys large blocks at market price (high), sells quickly (lower).
    In a live market, this creates losses on every cycle.
    """
    def __init__(self):
        self.name        = "Power Peg (DEPRECATED)"
        self.active      = False
        self.pnl         = 0.0
        self.trade_count = 0

    def execute(self, market_price: float):
        if not self.active:
            return

        # Buy high
        buy_price  = market_price * (1 + random.uniform(0.001, 0.003))
        qty        = random.randint(8_000, 15_000)

        # Sell immediately at slightly lower price (market impact)
        sell_price = buy_price  * (1 - random.uniform(0.002, 0.005))

        loss_per_trade = (sell_price - buy_price) * qty
        self.pnl       += loss_per_trade
        self.trade_count += 1

        print(f"    [PowerPeg] BUY {qty:>6} @ ${buy_price:.4f}  "
              f"→ SELL @ ${sell_price:.4f}  "
              f"P&L this trade: ${loss_per_trade:>10,.0f}")


class RetailLiquidityProvider:
    """
    NEW strategy — the intended deployment.
    Provides small, balanced liquidity. Profitable.
    """
    def __init__(self):
        self.name        = "Retail Liquidity Provider (NEW)"
        self.active      = False
        self.pnl         = 0.0
        self.trade_count = 0

    def execute(self, market_price: float):
        if not self.active:
            return

        spread      = random.uniform(0.0001, 0.0003)
        qty         = random.randint(100, 500)
        profit      = spread * qty * market_price
        self.pnl   += profit
        self.trade_count += 1

        print(f"    [RLP NEW ] SPREAD trade   qty={qty:<5}  "
              f"P&L this trade: +${profit:>8,.2f}")


# ── Server ────────────────────────────────────────────────────────────────────

class TradingServer:
    def __init__(self, server_id: int, received_update: bool):
        self.server_id       = server_id
        self.received_update = received_update

        self.power_peg = PowerPeg()
        self.rlp       = RetailLiquidityProvider()

        self._configure()

    def _configure(self):
        """
        Deployment logic.
        Updated servers: SMARS flag → activates new RLP strategy.
        Unpatched server: SMARS flag → still activates old Power Peg.
        """
        if self.received_update:
            # New code on this server
            # SMARS flag now means: "enable RLP"
            self.rlp.active       = True
            self.power_peg.active = False
        else:
            # Old code still running on this server
            # SMARS flag here means: "enable Power Peg" (the old meaning)
            self.power_peg.active = True
            self.rlp.active       = False

    def run_trading_cycle(self, market_price: float):
        self.power_peg.execute(market_price)
        self.rlp.execute(market_price)

    def total_pnl(self) -> float:
        return self.power_peg.pnl + self.rlp.pnl


# ── Simulation ────────────────────────────────────────────────────────────────

def simulate_deployment(num_servers: int, unpatched_count: int, cycles: int):
    print(f"\n{'='*65}")
    print(f"  KNIGHT CAPITAL DEPLOYMENT SIMULATION")
    print(f"  Servers: {num_servers}  |  Unpatched: {unpatched_count}  |  Trade cycles: {cycles}")
    print(f"{'='*65}\n")

    servers = []
    for i in range(1, num_servers + 1):
        patched = (i > unpatched_count)    # first N are unpatched
        servers.append(TradingServer(i, received_update=patched))
        status = "UPDATED" if patched else " NOT UPDATED — old code active"
        print(f"  Server {i}: {status}")

    print(f"\n  {'─'*63}")
    print(f"  Running {cycles} market cycles...\n")

    market_price = 10.00
    for cycle in range(1, cycles + 1):
        market_price *= (1 + random.uniform(-0.001, 0.001))   # slight drift
        if cycle <= 5 or cycle == cycles:
            print(f"  ── Cycle {cycle} | Market: ${market_price:.4f} ──")
        elif cycle == 6:
            print(f"  ... (continuing) ...\n")

        for server in servers:
            server.run_trading_cycle(market_price)

    print(f"\n  {'─'*63}")
    print(f"  {'Server':<10} {'Strategy':<30} {'P&L':>15}")
    print(f"  {'─'*63}")

    total = 0.0
    for s in servers:
        strategy = s.power_peg.name if s.power_peg.active else s.rlp.name
        pnl      = s.total_pnl()
        total   += pnl
        indicator = "⚠️ " if s.power_peg.active else "  "
        print(f"  {indicator}Server {s.server_id:<4}  {strategy:<30}  ${pnl:>12,.0f}")

    print(f"  {'─'*63}")
    print(f"  {'TOTAL P&L':>43}  ${total:>12,.0f}")

    if total < -1_000_000:
        rate_per_min = total / (cycles / 60) if cycles >= 60 else total
        print(f"\n   CATASTROPHIC LOSS: ${total:,.0f}")
        print(f"     Caused entirely by ONE unpatched server running dead code.")
        print(f"     At this rate: ${abs(total)*60/cycles:,.0f} per minute if running continuously.\n")
    else:
        print(f"\n   All servers profitable. Deployment was clean.\n")


if __name__ == "__main__":
    random.seed(99)
    print(__doc__)

    # Real scenario: 8 servers, 1 unpatched, 45 minutes at 40 trades/second
    simulate_deployment(num_servers=8, unpatched_count=1, cycles=300)

    print("─" * 65)
    print("  LESSON")
    print("─" * 65)
    print("""
  $440 million lost because of one thing: dead code that was
  never deleted. It sat in the codebase, waiting for the exact
  wrong configuration to bring it back to life.

  → DELETE dead code. Don't comment it out. Don't flag-guard it.
    Delete it. Version control remembers it if you ever need it back.
  → Deployments must be verified atomically across ALL nodes.
    "7 out of 8 servers updated" is a failed deployment.
  → Reusing feature flags for new purposes is dangerous.
    Old code may still respond to the old meaning of that flag.
  → Every trading system must have a kill switch that can halt
    all activity within seconds. Knight's took 45 minutes to trigger.
  → Staging environments must mirror production exactly —
    including server count and flag state.
""")