#!/usr/bin/env python3
"""
wizard/mutate_params.py
Given a parent parameters.json, spit out a mutated copy.

Usage (from repo root):
    python wizard/mutate_params.py <parent_branch> <child_folder>

Env vars:
    MUTATION_SIGMA  - % of each value to use as std-dev (default 0.15 = ±15 %)
"""
import json, os, random, sys, pathlib, shutil, math, subprocess

SIGMA = float(os.getenv("MUTATION_SIGMA", 0.15))

if len(sys.argv) != 3:
    sys.exit("Args: <parent_branch> <child_folder>")

parent_branch, child_dir = sys.argv[1:]
child_path = pathlib.Path(child_dir)
child_path.mkdir(parents=True, exist_ok=True)

# --- grab parameters.json from the parent branch
tmp_dir = pathlib.Path(".tmp_params")
if tmp_dir.exists(): shutil.rmtree(tmp_dir)
subprocess.run(["git", "clone", "--depth=1", "-b", parent_branch,
                ".", str(tmp_dir)], check=True, stdout=subprocess.DEVNULL)
src_file = tmp_dir / "parameters.json"
if not src_file.exists():
    sys.exit(f"{src_file} not found in {parent_branch}")

with open(src_file) as f:
    params = json.load(f)

# --- mutate numeric leaf values
def mutate(val):
    if isinstance(val, (int, float)):
        delta = random.gauss(0, SIGMA) * val
        return type(val)(val + delta)
    return val

def walk(obj):
    if isinstance(obj, dict):
        return {k: walk(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [walk(v) for v in obj]
    return mutate(obj)

mutated = walk(params)

# --- write to child folder
with open(child_path / "parameters.json", "w") as f:
    json.dump(mutated, f, indent=2)
print("🧬  Wrote mutated parameters to", child_path / "parameters.json")
