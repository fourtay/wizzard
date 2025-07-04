#!/usr/bin/env python3
"""
Generate N children by mutating a parent param-dict using schema bounds.
Reads schema from parameter_schema.json.
Outputs each child params to stdout (and writes to tmp file for Lean).
"""

import json, random, os, argparse, pathlib, hashlib

SCHEMA = json.load(open(pathlib.Path(__file__).parent / "parameter_schema.json"))

def random_value(field):
    t, mn, mx = SCHEMA[field]["type"], SCHEMA[field]["min"], SCHEMA[field]["max"]
    if t == "int":
        return random.randint(mn, mx)
    return round(random.uniform(mn, mx), 4)

def mutate(parent):
    child = parent.copy()
    # mutate 30 % of fields
    for f in random.sample(list(SCHEMA.keys()), k=max(1, int(0.3*len(SCHEMA)))):
        child[f] = random_value(f)
    return child

def load_parent(pth):
    if not os.path.exists(pth):
        # bootstrap: random parent
        return {f: random_value(f) for f in SCHEMA}
    return json.load(open(pth))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", default="parent_params.json")
    ap.add_argument("--num", type=int, default=int(os.getenv("NUM_CHILDREN", 5)))
    ap.add_argument("--outdir", default="children")
    args = ap.parse_args()

    parent = load_parent(args.parent)
    os.makedirs(args.outdir, exist_ok=True)

    for i in range(args.num):
        child = mutate(parent)
        h = hashlib.md5(json.dumps(child, sort_keys=True).encode()).hexdigest()[:8]
        fn = f"{args.outdir}/child_{i}_{h}.json"
        json.dump(child, open(fn, "w"), indent=2)
        print(fn)
