# wizard/algogen.py
"""
Generates a very simple QC algorithm file (C#) with
slightly-randomised parameters. Each call produces
a new variant, written to wizard/out/MyAlgo_<stamp>.cs
"""
from datetime import datetime
import random
from pathlib import Path

TEMPLATE = """
using QuantConnect.Algorithm;
public class AutoAlgo_{STAMP} : QCAlgorithm
{{
    public override void Initialize()
    {{
        SetStartDate(2020, 1, 1);
        SetEndDate(2024, 1, 1);
        SetCash(100000);
        var symbol = AddEquity("{TICKER}", Resolution.Daily).Symbol;
        var fast = {FAST};
        var slow = {SLOW};
        var emaFast = EMA(symbol, fast);
        var emaSlow = EMA(symbol, slow);
        PlotIndicator("EMA", emaFast, emaSlow);
    }}
}}
"""

def make_algo(out_dir: Path):
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    code = TEMPLATE.format(
        STAMP = stamp,
        TICKER = random.choice(["AAPL","SPY","QQQ"]),
        FAST   = random.randint(5, 30),
        SLOW   = random.randint(31, 200),
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"MyAlgo_{stamp}.cs"
    path.write_text(code)
    return path

if __name__ == "__main__":
    dst = make_algo(Path(__file__).parent / "out")
    print(f"✅ generated {dst}")
