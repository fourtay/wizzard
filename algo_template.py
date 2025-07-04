# tools/algogen/algo_template.py
"""
Auto-generated EMA-cross strategy

FAST_PERIOD = {{FAST_PERIOD}}
SLOW_PERIOD = {{SLOW_PERIOD}}
SYMBOL = {{SYMBOL}}

(Values are replaced by tools/algogen/algo_gen.py)
"""
from AlgorithmImports import *
import numpy as np

class GeneticAlgo(QCAlgorithm):
    def Initialize(self):
        # --- Define your In-Sample and Out-of-Sample periods ---
        self.training_end_date = datetime(2024, 4, 30) # Adjusted for current date
        self.backtest_start_date = datetime(2023, 7, 1)
        self.backtest_end_date = datetime(2024, 7, 3) # Adjusted for current date
        # ---------------------------------------------------------

        self.SetStartDate(self.backtest_start_date)
        self.SetEndDate(self.backtest_end_date)
        self.SetCash(100000)

        # --- ADD THIS BLOCK FOR REALISM ---
        # Set a realistic brokerage model to account for commissions
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        # Set a slippage model to simulate the price impact of your trades
        # This prevents the backtest from assuming perfect execution
        self.SetSlippageModel(VolumeShareSlippageModel())
        # --- END BLOCK ---

        # The symbol is now a parameter passed from the template
        self.symbol = self.AddEquity("{{SYMBOL}}", Resolution.Daily).Symbol

        self.fast   = self.EMA(self.symbol, {{FAST_PERIOD}}, Resolution.Daily)
        self.slow   = self.EMA(self.symbol, {{SLOW_PERIOD}}, Resolution.Daily)

        # Ensure warmup period is an integer
        self.SetWarmUp(int({{SLOW_PERIOD}}))

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

    def OnEndOfAlgorithm(self):
        # This block calculates the performance on the Out-of-Sample (OOS) data
        all_trades = self.TradeBuilder.ClosedTrades
        oos_trades = [t for t in all_trades if t.ExitTime >= self.training_end_date]

        oos_profit = 0
        if oos_trades:
            for trade in oos_trades:
                oos_profit += trade.ProfitLoss

        # Log custom statistics for later evaluation
        self.SetStatistics("OOS Net Profit", f"{oos_profit:.2f}")

        self.Log(f"--- Out-of-Sample Results For {{SYMBOL}} ---")
        self.Log(f"OOS Trades: {len(oos_trades)}")
        self.Log(f"OOS Net Profit: ${oos_profit:.2f}")
        self.Log(f"-----------------------------")
