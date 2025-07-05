# main.py   (first half rewritten to enforce a 1-year back-test)
from AlgorithmImports import *
import json, importlib
from datetime import datetime, timedelta, timezone

class DynamicStrategyLoader(QCAlgorithm):
    """Loads the concrete strategy listed in params.json and limits the test to the last year."""

    TODAY  = datetime(2025, 7, 4, tzinfo=timezone.utc)      # ✅ pin so CI is deterministic
    START  = TODAY - timedelta(days=365)

    def Initialize(self):
        # ----- date window -----
        self.SetStartDate(self.START.year,  self.START.month,  self.START.day)
        self.SetEndDate  (self.TODAY.year,  self.TODAY.month,  self.TODAY.day)
        self.SetCash(100_000)

        # Out-of-sample: final 60 days
        self.training_end = self.TODAY - timedelta(days=60)

        # ----- load params.json -----
        try:
            with open("params.json") as fh:
                self.params = json.load(fh)
        except FileNotFoundError:
            self.Debug("params.json missing – using fallback defaults")
            self.params = {
                "STRATEGY_MODULE": "ema_cross_strategy",
                "SYMBOL": "SPY",
                "FAST_PERIOD": 10,
                "SLOW_PERIOD": 100,
            }

        # dynamic import of the chosen strategy
        mod_name = self.params["STRATEGY_MODULE"]
        strat_mod  = importlib.import_module(f"strategies.{mod_name}")
        strat_cls  = getattr(strat_mod,
                             "".join(p.title() for p in mod_name.split("_")))

        # mix-in concrete strategy, then call its Initialize
        self.__class__ = type("Algorithm",
                              (DynamicStrategyLoader, strat_cls), {})
        strat_cls.Initialize(self)

    def OnEndOfAlgorithm(self):
        oos_trades = [t for t in self.TradeBuilder.ClosedTrades
                      if t.ExitTime >= self.training_end]
        self.SetStatistics("OOS Net Profit",
                           f"{sum(t.ProfitLoss for t in oos_trades):.2f}")
