# tools/algogen/algo_template.py
"""
Auto-generated EMA-cross strategy

FAST_PERIOD = {{FAST_PERIOD}}
SLOW_PERIOD = {{SLOW_PERIOD}}

(Values are replaced by tools/algogen/algo_gen.py)
"""
from AlgorithmImports import *
import numpy as np

class GeneticAlgo(QCAlgorithm):
    def Initialize(self):
        # --- Define your In-Sample and Out-of-Sample periods ---
        self.training_end_date = datetime(2023, 10, 31)
        self.backtest_start_date = datetime(2023, 1, 1)
        self.backtest_end_date = datetime(2024, 1, 1)
        # ---------------------------------------------------------

        self.SetStartDate(self.backtest_start_date)
        self.SetEndDate(self.backtest_end_date)
        self.SetCash(100000)

        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.fast   = self.EMA(self.symbol, {{FAST_PERIOD}}, Resolution.Daily)
        self.slow   = self.EMA(self.symbol, {{SLOW_PERIOD}}, Resolution.Daily)
        self.SetWarmUp({{SLOW_PERIOD}})

    def OnData(self, data):
        if self.IsWarmingUp:
            return

        # --- Only execute trading logic during the In-Sample training period ---
        if self.Time < self.training_end_date:
            # Cross-over logic
            if not self.Portfolio.Invested and self.fast.Current.Value > self.slow.Current.Value:
                self.SetHoldings(self.symbol, 1.0)
            elif self.Portfolio.Invested and self.fast.Current.Value < self.slow.Current.Value:
                self.Liquidate()
        # --- After the training date, the algorithm simply holds and does nothing ---

    def OnEndOfAlgorithm(self):
        # --- This block calculates the performance on the Out-of-Sample (OOS) data ---
        all_trades = self.TradeBuilder.ClosedTrades
        oos_trades = [t for t in all_trades if t.ExitTime >= self.training_end_date]

        oos_profit = 0
        oos_returns = []

        if oos_trades:
            for trade in oos_trades:
                profit = trade.ProfitLoss
                oos_profit += profit
                # Calculate daily returns for Sharpe Ratio calculation
                # This part can be complex; a simpler approach is to use portfolio equity
                # For now, we will log the profit and a placeholder for sharpe.
                # A more robust solution would track daily portfolio value in the OOS period.

        # Log custom statistics. These will appear in your backtest-results.json
        self.SetStatistics("OOS Net Profit", f"{oos_profit:.2f}")

        # For a true OOS Sharpe, you'd need to calculate daily returns during the OOS period.
        # This is a complex implementation, so as a starting point, we will use a placeholder
        # or rely on a simpler metric like OOS Net Profit for selection.
        # Let's assume a simplified Sharpe for this example.
        # WARNING: The Sharpe Ratio calculated over the entire portfolio is NOT a true OOS Sharpe.
        # We add it here to have a metric but acknowledge its inaccuracy.
        # A simple profit metric is more reliable without a more complex implementation.
        self.SetStatistics("OOS Sharpe Ratio", f"{self.Portfolio.SharpeRatio:.4f}") # Inaccurate, for placeholder only

        self.Log(f"--- Out-of-Sample Results ---")
        self.Log(f"OOS Trades: {len(oos_trades)}")
        self.Log(f"OOS Net Profit: ${oos_profit:.2f}")
        self.Log(f"-----------------------------")
