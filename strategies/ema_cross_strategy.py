from AlgorithmImports import *

class EmaCrossStrategy(QCAlgorithm):
    """
    A strategy that trades based on the crossover of two Exponential Moving Averages.
    """
    def Initialize(self):
        # This method is now called by main.py, which passes in the parameters
        pass

    def OnWarmupFinished(self):
        # This is a custom method we'll call after parameters are set
        self.fast = self.EMA(self.symbol, self.fast_period, Resolution.Daily)
        self.slow = self.EMA(self.symbol, self.slow_period, Resolution.Daily)
        self.SetWarmUp(self.slow_period)

    def OnData(self, data):
        if self.IsWarmingUp:
            return

        # Only trade during the in-sample training period
        if self.Time < self.training_end_date:
            if not self.Portfolio.Invested and self.fast.Current.Value > self.slow.Current.Value:
                self.SetHoldings(self.symbol, 1.0)
            elif self.Portfolio.Invested and self.fast.Current.Value < self.slow.Current.Value:
                self.Liquidate()
