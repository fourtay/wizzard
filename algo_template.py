# tools/algogen/algo_template.py
"""
Auto-generated EMA-cross strategy
FAST_PERIOD  = {{FAST_PERIOD}}
SLOW_PERIOD  = {{SLOW_PERIOD}}
(Values are replaced by tools/algogen/algo_gen.py)
"""
from AlgorithmImports import *

class GeneticAlgo(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetEndDate(2024, 1, 1)
        self.SetCash(100000)

        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.fast   = self.EMA(self.symbol, {{FAST_PERIOD}}, Resolution.Daily)
        self.slow   = self.EMA(self.symbol, {{SLOW_PERIOD}}, Resolution.Daily)

        self.SetWarmUp({{SLOW_PERIOD}})

    def OnData(self, data):
        if self.IsWarmingUp:
            return

        # Cross-over logic
        if not self.Portfolio.Invested and self.fast.Current.Value > self.slow.Current.Value:
            self.SetHoldings(self.symbol, 1.0)

        if self.Portfolio.Invested and self.fast.Current.Value < self.slow.Current.Value:
            self.Liquidate()
