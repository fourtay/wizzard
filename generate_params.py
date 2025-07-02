#!/usr/bin/env python3
"""
generate_params.py
──────────────────
Spits out a JSON file full of random parameter sets so the CI workflow
can feed them into Lean Cloud back-tests.

How it works
------------
• You tell it how many sets you want (POP_SIZE env-var, default 10)
• It draws integers within the bounds you define in PARAM_BOUNDS
• It tags each set with a uuid and a generation number
• It writes everything to param_candidates.json
"""

import json
import os
import random
import uuid

# ── CONFIG ────────────────────────────────────────────────────────────────
POP_SIZE = int(os.getenv("POP_SIZE", 10))       # how many variants to make
GENERATION = int(os.getenv("GENERATION", 1))    # which “cycle” is this?
SEED = int(os.getenv("SEED", random.randrange(1_000_000)))  # reproducible runs

# Parameter names and their (low, high) integer bounds
PARAM_BOUNDS = {
    "fast": (5, 40),          # e.g. fast EMA length
    "slow": (20, 200),        # slow EMA length
    "rsi":  (5, 30),          # RSI period
}

# ── LOGIC ─────────────────────────────────────────────────────────────────
random.seed(SEED)
param_sets = []

for _ in range(POP_SIZE):
    param = {
        "id": str(uuid.uuid4()),
        "generation": GENERATION,
    }
    # pick a random integer in each bound range
    for name, (lo, hi) in PARAM_BOUNDS.items():
        param[name] = random.randint(lo, hi)
    param_sets.append(param)

outfile = "param_candidates.json"
with open(outfile, "w") as fp:
    json.dump(param_sets, fp, indent=2)

print(f"✅  Wrote {len(param_sets)} parameter sets to {outfile}")
print(f"    Seed used: {SEED}")
