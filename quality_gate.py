#!/usr/bin/env python3
"""
wizard/quality_gate.py
-------------------------------------------------------
Evaluates back-test results dumped by QuantConnect.

Invoked by the workflow as:
    python wizard/quality_gate.py backtest-results.json
• Exits 0  → child passes
• Exits 1  → child fails (workflow step shows “failure” and culls branch)
-------------------------------------------------------
"""

import json, sys, pathlib, math, textwrap, os

MIN_SHARPE   = float(os.getenv("MIN_SHARPE",   "0.20"))
MAX_DRAWDOWN = float(os.getenv("MAX_DRAWDOWN", "0.15"))

def load(path: str) -> dict:
    try:
        with open(path, "r") as fh:
            return json.load(fh)
    except Exception as exc:
        sys.stderr.write(f"‼️  Could not read {path}: {exc}\n")
        sys.exit(1)

def extract(stats: dict[str, str], key: str, default: float = math.nan) -> float:
    try:
        return float(stats[key])
    except (KeyError, ValueError):
        return default

def run(path: str) -> None:
    data   = load(path)
    stats  = data.get("statistics") or data.get("results", {}).get("statistics") or {}
    name   = data.get("name", "unknown-run")

    sharpe     = extract(stats, "sharpeRatio")
    drawdown   = extract(stats, "drawdown")

    # Fail-safe: if numbers are missing treat as fail
    if math.isnan(sharpe) or math.isnan(drawdown):
        sys.stderr.write("‼️  Missing sharpeRatio or drawdown—failing gate.\n")
        sys.exit(1)

    ok = (sharpe >= MIN_SHARPE) and (drawdown <= MAX_DRAWDOWN)

    print(textwrap.dedent(f"""
        ╔══════════════════════════════════════════════╗
        ║   Quality Gate for:  {name}                  ║
        ║   Sharpe   : {sharpe:6.3f} (>= {MIN_SHARPE})          ║
        ║   Drawdown : {drawdown:6.3f} (<= {MAX_DRAWDOWN})       ║
        ╚══════════════════════════════════════════════╝
    """).strip())

    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: quality_gate.py <backtest-results.json>", file=sys.stderr)
        sys.exit(1)
    run(sys.argv[1])
