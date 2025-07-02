#!/usr/bin/env python3
"""
Create <num> new algorithm folders under wizard/children/.

Each child folder contains:
  • main.py  – a QC Lean algorithm stub with random parameters
  • config.json – metadata we keep to trace the parameters used
"""
import argparse, os, json, random, shutil, datetime, pathlib

CHILD_DIR = pathlib.Path(__file__).parent / "children"
TEMPLATE   = pathlib.Path(__file__).parent / "template_algo.py"   # ← plain algo stub

def mutate():
    """Return a dict of randomly-mutated hyper-parameters."""
    return {
        "symbol": random.choice(["SPY", "QQQ", "TLT", "IWM"]),
        "sma_fast": random.randint(5, 30),
        "sma_slow": random.randint(40, 200),
        "rsi_period": random.randint(7, 21),
        "rsi_buy": random.randint(25, 40),
        "rsi_sell": random.randint(60, 75),
    }

def write_child(idx: int, params: dict):
    ts   = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    name = f"child_{ts}_{idx}"
    folder = CHILD_DIR / name
    folder.mkdir(parents=True, exist_ok=True)

    # copy template algo
    shutil.copy(TEMPLATE, folder / "main.py")

    # embed params in config.json
    with open(folder / "config.json", "w") as f:
        json.dump(params, f, indent=2)

    print(f"📦  created {folder}")
    return folder

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num", type=int, required=True)
    args = parser.parse_args()

    CHILD_DIR.mkdir(exist_ok=True)
    for i in range(args.num):
        write_child(i + 1, mutate())
