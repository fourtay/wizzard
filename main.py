from AlgorithmImports import *
import json
import importlib

class DynamicStrategyLoader(QCAlgorithm):
    """
    This algorithm acts as a loader. It reads parameters from params.json,
    dynamically imports the specified strategy module, and runs it.
    """
    def Initialize(self):
        # --- Default Settings ---
        self.SetStartDate(2023, 7, 1)
        self.SetEndDate(2025, 7, 4)
        self.SetCash(100000)
        self.training_end_date = datetime(2025, 4, 30)

        # --- Load Strategy Configuration ---
        try:
            # Read the parameters for this specific backtest run
            with open("params.json", "r") as f:
                self.params = json.load(f)
        except FileNotFoundError:
            self.Log("ERROR: params.json not found. Using default fallback.")
            # Fallback to a default if running locally without a params file
            self.params = {
                "STRATEGY_MODULE": "ema_cross_strategy",
                "SYMBOL": "SPY",
                "FAST_PERIOD": 10,
                "SLOW_PERIOD": 100
            }

        self.Log(f"Loaded parameters: {self.params}")

        # --- Dynamically Load and Initialize the Chosen Strategy ---
        strategy_module_name = self.params.get("STRATEGY_MODULE")
        if not strategy_module_name:
            raise Exception("STRATEGY_MODULE not defined in params.json")

        # Dynamically import the strategy from the /strategies/ folder
        self.Log(f"Importing strategy: strategies.{strategy_module_name}")
        strategy_module = importlib.import_module(f"strategies.{strategy_module_name}")

        # Get the class from the module (assuming class name is PascalCase version of file name)
        strategy_class_name = "".join([s.capitalize() for s in strategy_module_name.split('_')])
        StrategyClass = getattr(strategy_module, strategy_class_name)

        # "Mix-in" the strategy's methods into this loader class
        self.__class__ = type("CombinedAlgorithm", (DynamicStrategyLoader, StrategyClass), {})
        self.Initialize() # Re-initialize to run the strategy's Initialize

        # --- Set Parameters on the Strategy Instance ---
        self.symbol_name = self.params.get("SYMBOL", "SPY")
        self.symbol = self.AddEquity(self.symbol_name, Resolution.Daily).Symbol
        self.fast_period = int(self.params.get("FAST_PERIOD"))
        self.slow_period = int(self.params.get("SLOW_PERIOD"))

        # Set realistic brokerage and slippage models
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)
        self.SetSlippageModel(VolumeShareSlippageModel())

        # Call the custom warmup method if it exists
        if hasattr(self, 'OnWarmupFinished'):
            self.OnWarmupFinished()

    def OnEndOfAlgorithm(self):
        # This logic remains here to standardize OOS reporting
        all_trades = self.TradeBuilder.ClosedTrades
        oos_trades = [t for t in all_trades if t.ExitTime >= self.training_end_date]
        oos_profit = sum(t.ProfitLoss for t in oos_trades) if oos_trades else 0

        self.SetStatistics("OOS Net Profit", f"{oos_profit:.2f}")
        self.Log(f"--- Out-of-Sample Results For {self.symbol_name} ---")
        self.Log(f"OOS Net Profit: ${oos_profit:.2f}")
