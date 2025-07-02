#!/usr/bin/env python3
"""
Exit 0 (success) if metrics pass the gate; otherwise exit 1
so the workflow can decide to delete the branch.
"""

import json, sys, os, math

FILE = sys.argv[1] if len(sys.argv) == 2 else "backtest-results.json"

# -------- thresholds (tune as you wish) --------
MIN_SHARPE   = float(os.getenv("MIN_SHARPE",   "0.20"))
MAX_DRAWDOWN = float(os.getenv("MAX_DRAWDOWN", "0.15"))
# -----------------------------------------------

try:
    data = json.load(open(FILE))
except Exception as e:
    print(f"❌  Cannot open {FILE}: {e}")
    sys.exit(1)

stats = data.get("statistics") or data.get("results", {}).get("statistics")
if not stats:
    print("❌  stats block missing")
    sys.exit(1)

sharpe   = float(stats.get("sharpeRatio")           or 0)
drawdown = float(stats.get("drawdown")              or 0)
print(f"ℹ️  Sharpe={sharpe:.3f}  DrawDown={drawdown:.3f}")

if sharpe < MIN_SHARPE:
    print(f"❌  Sharpe {sharpe:.2f} < {MIN_SHARPE}")
    sys.exit(1)
if drawdown > MAX_DRAWDOWN:
    print(f"❌  Drawdown {drawdown:.2f} > {MAX_DRAWDOWN}")
    sys.exit(1)

print("✅  PASSED quality gate")
