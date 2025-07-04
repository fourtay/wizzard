#!/usr/bin/env python3
"""
Generate NUM_CHILDREN mutated parameter sets from champion.json.

Outputs: children/child_<n>.json
"""

import json, os, random, pathlib, math

NUM_CHILDREN = int(os.getenv("NUM_CHILDREN", 5))
CHAMPION_FILE = "champion.json"
OUT_DIR = pathlib.Path("children")
OUT_DIR.mkdir(exist_ok=True)

# ═══════════════  helpers  ════════════════
def mutate(value, scale=0.3, minimum=1e-6):
    """Gaussian mutate a float or int, keep >0."""
    noise = random.gauss(0, abs(value) * scale or 1)
    v = value + noise
    if isinstance(value, int):
        v = int(round(v))
    return max(v, minimum)

def bounded(val, lo=None, hi=None):
    if lo is not None:
        val = max(val, lo)
    if hi is not None:
        val = min(val, hi)
    return val

# ═══════════════  main  ═══════════════════
with open(CHAMPION_FILE) as f:
    champion = json.load(f)

params = champion["parameters"]  # e.g. {"lookback": 20, "threshold": 0.7, …}

print(f"Champion params: {params}")
children = []

for i in range(NUM_CHILDREN):
    child = {"parameters": {}}
    for k, v in params.items():
        if isinstance(v, (int, float)):
            nv = mutate(v)
            # clamp example ranges
            if k == "lookback":
                nv = bounded(int(nv), 5, 100)
            elif k == "threshold":
                nv = bounded(nv, 0.01, 0.99)
            child["parameters"][k] = nv
        else:
            # categorical? random pick
            child["parameters"][k] = random.choice([v, v])  # placeholder
    children.append(child)
    out_path = OUT_DIR / f"child_{i}.json"
    with open(out_path, "w") as f:
        json.dump(child, f, indent=2)
    print(f"▶︎ wrote {out_path}")

print(f"Generated {len(children)} children")
