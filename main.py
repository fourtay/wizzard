# main.py
from AlgorithmImports import *

class BasicTemplateAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2022, 1, 1)
        self.SetEndDate(2024, 1, 1)
        self.SetCash(100000)
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol
        self.invested = False

    def OnData(self, data: Slice):
        if not self.invested:
            self.SetHoldings(self.spy, 1)
            self.invested = True
