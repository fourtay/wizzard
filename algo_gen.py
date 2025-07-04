# tools/algogen/algo_gen.py
"""
Generate N children strategies by mutating (or seeding) EMA parameters.
Each child is written to outputs/child_<idx>_f<fast>_s<slow>.py
A side-car JSON with the same params is written next to the .py file.
"""

import argparse
import json
import os
import random
from typing import Dict, Any, Optional

from google.cloud import firestore

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "algo_template.py")
OUTPUT_DIR    = "outputs"


# ────────────────────────── helpers ──────────────────────────
def load_template() -> str:
    with open(TEMPLATE_PATH, "r") as fh:
        return fh.read()


def mutate_params(base: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """Return a fresh FAST/SLOW dict – mutated from base if supplied."""
    if base:
        fast = max(3, int(base["FAST_PERIOD"] + random.randint(-2, 2)))
        slow = max(fast + 5, int(base["SLOW_PERIOD"] + random.randint(-5, 5)))
    else:
        fast = random.randint(5, 30)
        slow = random.randint(fast + 10, 120)
    return {"FAST_PERIOD": fast, "SLOW_PERIOD": slow}


def render(code: str, params: Dict[str, int]) -> str:
    for k, v in params.items():
        code = code.replace(f"{{{{{k}}}}}", str(v))
    return code


# ─────────────────────────── main ────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_children", type=int, default=5)
    parser.add_argument(
        "--inherit_from",
        help="Firestore doc path holding winner params (written by select_winner.py)",
    )
    args = parser.parse_args()

    # maybe pull parent params
    parent_params = None
    if args.inherit_from:
        try:
            snap = firestore.Client().document(args.inherit_from).get()
            parent_params = snap.to_dict().get("params")
            print(f"🔬  Base params from {args.inherit_from}: {parent_params}")
        except Exception as e:
            print(f"⚠️  Could not load parent params, falling back to random → {e}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    template = load_template()

    for i in range(args.num_children):
        params = mutate_params(parent_params)
        code   = render(template, params)

        stem = f"child_{i+1}_f{params['FAST_PERIOD']}_s{params['SLOW_PERIOD']}"
        py_path   = os.path.join(OUTPUT_DIR, stem + ".py")
        json_path = os.path.join(OUTPUT_DIR, stem + ".json")

        with open(py_path, "w") as fh:
            fh.write(code)
        with open(json_path, "w") as jh:
            json.dump(params, jh)

        print(f"✅  Wrote {py_path}")


if __name__ == "__main__":
    main()
