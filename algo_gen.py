"""
algo_gen.py
-----------
Very-first, bare-bones *algorithm generator*.

• Every call produces a new QCAlgorithm subclass with:
    – A randomly chosen ticker from a small universe
    – A random daily SMA crossover (fast / slow windows)
• The script writes the code into
      strategies/<uuid4>.py
  and prints that filename; evolve.py picks it up.

Later we’ll:
  • Add genetic / bayesian search
  • Inject constraints (asset class, leverage, etc.)
  • Use past winners as parents
"""

import random, uuid, pathlib, json, textwrap, os, datetime

UNIVERSE = ["SPY", "QQQ", "IWM", "TLT", "GLD"]
OUT_DIR  = pathlib.Path(__file__).with_suffix("").parent / "strategies"
OUT_DIR.mkdir(exist_ok=True)

def generate():
    sym   = random.choice(UNIVERSE)
    fast  = random.randint(5, 30)
    slow  = random.randint(fast + 5, fast + 60)
    class_name = f"SMA_{sym}_{fast}_{slow}_{uuid.uuid4().hex[:6]}"
    code = textwrap.dedent(f"""
        from AlgorithmImports import *

        class {class_name}(QCAlgorithm):
            def Initialize(self):
                self.SetStartDate(2017, 1, 1)
                self.SetEndDate(datetime.utcnow())
                self.SetCash(100000)
                self.symbol = self.AddEquity("{sym}", Resolution.Daily).Symbol
                self.fast = self.SMA(self.symbol, {fast}, Resolution.Daily)
                self.slow = self.SMA(self.symbol, {slow}, Resolution.Daily)
                self.previous = None

            def OnData(self, data):
                if not (self.fast.IsReady and self.slow.IsReady): return
                if self.previous == self.Time.date(): return
                self.previous = self.Time.date()

                if self.fast.Current.Value > self.slow.Current.Value and not self.Portfolio[self.symbol].IsLong:
                    self.SetHoldings(self.symbol, 1)
                elif self.fast.Current.Value < self.slow.Current.Value and self.Portfolio[self.symbol].IsLong:
                    self.Liquidate(self.symbol)
    """)
    file_path = OUT_DIR / f"{class_name}.py"
    file_path.write_text(code)
    meta = {
        "strategy_file": str(file_path),
        "symbol": sym,
        "fast": fast,
        "slow": slow,
        "created": datetime.datetime.utcnow().isoformat()
    }
    print(json.dumps(meta))          # evolve.py consumes stdout
    return file_path

if __name__ == "__main__":
    generate()
