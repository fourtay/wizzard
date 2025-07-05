# algo_gen.py
#!/usr/bin/env python3
"""
Generate N mutated parameter sets based on parameter_schema.json
Each set is placed in its own folder inside `children/` as params.json
"""

from __future__ import annotations
import argparse, hashlib, json, os, pathlib, random

ROOT   = pathlib.Path(__file__).resolve().parent
SCHEMA = json.load(open(ROOT / "parameter_schema.json"))

def random_value(field: str):
    spec = SCHEMA[field]
    if spec["type"] == "choice":
        return random.choice(spec["values"])
    if spec["type"] == "int":
        return random.randint(spec["min"], spec["max"])
    return round(random.uniform(spec["min"], spec["max"]), 4)

def mutate(parent: dict[str, object]) -> dict[str, object]:
    child = parent.copy()
    fields = random.sample(list(SCHEMA), k=max(1, int(0.3 * len(SCHEMA))))
    for f in fields:
        child[f] = random_value(f)
    return child

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent", default="parent_params.json")
    ap.add_argument("--num", type=int, default=int(os.getenv("NUM_CHILDREN", 5)))
    ap.add_argument("--outdir", default="children")
    args = ap.parse_args()

    # load parent or create one if it doesn't exist
    parent_path = ROOT / args.parent
    parent = (json.load(open(parent_path))
              if parent_path.exists()
              else {f: random_value(f) for f in SCHEMA})

    outdir = ROOT / args.outdir
    outdir.mkdir(exist_ok=True)

    for i in range(args.num):
        child = mutate(parent)
        hash8 = hashlib.md5(json.dumps(child, sort_keys=True)
                            .encode()).hexdigest()[:8]
        d = outdir / f"child_{i}_{hash8}"
        d.mkdir(exist_ok=True)
        json.dump(child, open(d / "params.json", "w"), indent=2)
        print(f"🧬  Wrote {d}")

if __name__ == "__main__":
    main()
