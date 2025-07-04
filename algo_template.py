# scripts/algo_template.py
from AlgorithmImports import *

class EvolvableAlgo(QCAlgorithm):

    def Initialize(self):
        # --- basic engine settings ---
        self.SetStartDate(2020, 1, 1)   # 5-year window for speed
        self.SetEndDate(datetime.utcnow())
        self.SetCash(100000)
        self.AddEquity("SPY", Resolution.Daily)
        self.symbol = self.Symbol("SPY")

        # --- pull genome from parameters ---
        p = self.GetParameter  # shortcut
        self.fast   = int(p("FastMA"))
        self.slow   = int(p("SlowMA"))
        self.rsiLen = int(p("RSI_len"))
        self.rsiHi  = int(p("RSI_hi"))
        self.rsiLo  = int(p("RSI_lo"))
        self.bbLen  = int(p("BB_len"))
        self.bbK    = float(p("BB_K"))
        self.volLB  = int(p("VolLookback"))
        self.atrLen = int(p("ATR_len"))
        self.positionFrac = float(p("PositionSize"))

        # --- indicators ---
        self.fastMA = self.SMA(self.symbol, self.fast, Resolution.Daily)
        self.slowMA = self.SMA(self.symbol, self.slow, Resolution.Daily)
        self.rsi    = self.RSI(self.symbol, self.rsiLen, MovingAverageType.Wilders)
        self.bb     = self.BB(self.symbol, self.bbLen, self.bbK, MovingAverageType.Simple)
        self.atr    = self.ATR(self.symbol, self.atrLen, MovingAverageType.Simple)

        # warm-up
        self.SetWarmUp(self.slow + self.bbLen)

    def OnData(self, data: Slice):
        if self.IsWarmingUp:   # wait for indicators
            return

        price = data[self.symbol].Close
        volume_ok = self.History(self.symbol, self.volLB, Resolution.Daily)["volume"].mean() < data[self.symbol].Volume

        long_signal  = (price > self.fastMA.Current.Value > self.slowMA.Current.Value) and self.rsi.Current.Value < self.rsiLo and price < self.bb.LowerBand.Current.Value and volume_ok
        flat_signal  = self.Portfolio[self.symbol].Invested and (self.rsi.Current.Value > self.rsiHi or price > self.bb.UpperBand.Current.Value)

        if long_signal and not self.Portfolio[self.symbol].Invested:
            qty = self.CalculateOrderQuantity(self.symbol, self.positionFrac)
            self.SetHoldings(self.symbol, self.positionFrac)
        elif flat_signal:
            self.Liquidate(self.symbol)
