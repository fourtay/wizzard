"""
Minimal Lean algorithm — just buys SPY when RSI crosses up.
⚠️  THIS IS ONLY A TEMPLATE.  The generator will clone and mutate it.
"""

from AlgorithmImports import *

# --- PARAMETERS THE GENERATOR WILL MUTATE ---
RSI_PERIOD = 14          # <- generator bumps this ±1-2 each iteration
RSI_BUY_THRESHOLD = 30
RSI_SELL_THRESHOLD = 70
# --------------------------------------------

class TemplateAlgo(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetCash(100_000)
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.rsi = self.RSI(self.symbol, RSI_PERIOD, MovingAverageType.Wilders)
        self.SetWarmUp(RSI_PERIOD + 1)

    def OnData(self, data):
        if self.IsWarmingUp: return

        if not self.Portfolio.Invested and self.rsi < RSI_BUY_THRESHOLD:
            self.SetHoldings(self.symbol, 1)
        elif self.Portfolio.Invested and self.rsi > RSI_SELL_THRESHOLD:
            self.Liquidate(self.symbol)
