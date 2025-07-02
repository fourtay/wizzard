# wizard/algo_gen.py
"""
Simple parameter-space “genetic” generator for QC algos.

Assumptions
-----------
* Each algorithm lives in its own sub-folder under `algos/`.
* Inside every algo folder there is a `params.json` file, e.g.
      {
        "ma_short": 10,
        "ma_long": 50,
        "stop_loss": 0.02
      }
* The trading logic (e.g. `main.py`) imports params.json at run-time,
  so mutating that file is enough to create a new variant.
"""

from __future__ import annotations
import json, random, shutil, time, pathlib, hashlib
from typing import Dict, List

ALGOS_DIR = pathlib.Path("algos")          # root that holds 1 folder per algo
PARAM_FILE = "params.json"                 # file we actually mutate


def _rand_key() -> str:
    """Return 8-char hash for unique folder names."""
    return hashlib.sha1(str(time.time_ns()).encode()).hexdigest()[:8]


def mutate(parent_params: Dict[str, float], std: float) -> Dict[str, float]:
    """Gaussian-jitter each numeric parameter by `std`."""
    child = {}
    for k, v in parent_params.items():
        if isinstance(v, (int, float)):
            jitter = random.gauss(0, std * abs(v or 1))
            child[k] = max(0, v + jitter)  # keep positive
        else:
            child[k] = v                   # non-numeric untouched
    return child


def generate_children(
    parent_algo: pathlib.Path,
    num_children: int = 5,
    mutation_std: float = 0.1,
) -> List[pathlib.Path]:
    """
    Create `num_children` mutated copies of `parent_algo`.

    Returns a list of new child-folder paths.
    """
    assert parent_algo.is_dir(), f"{parent_algo} not found"

    parent_params_path = parent_algo / PARAM_FILE
    with parent_params_path.open() as f:
        parent_params = json.load(f)

    children_paths: List[pathlib.Path] = []

    for _ in range(num_children):
        key     = _rand_key()
        child   = ALGOS_DIR / f"{parent_algo.name}_{key}"
        shutil.copytree(parent_algo, child)

        # write mutated param file
        new_params = mutate(parent_params, mutation_std)
        with (child / PARAM_FILE).open("w") as f:
            json.dump(new_params, f, indent=2)

        children_paths.append(child)

    return children_paths
