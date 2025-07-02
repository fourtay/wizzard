"""
wizard/algogen.py
Create K random child-algorithms each time it is run.

The generated .cs files are saved into wizard/out/
and picked up automatically by the evolve.yml workflow.
"""

from pathlib import Path
import os
import random
import string

# ---------------------------------------------------------------------------
# configurable -- change this to make more or fewer children per run
NUM_CHILDREN = int(os.getenv("NUM_CHILDREN", "5"))
# ---------------------------------------------------------------------------

# ---- import your existing generator helper --------------------------------
# make_algo(out_path: Path) → Path to newly-created .cs file
from wizard.generator import make_algo   # <-- same helper you already use
# ---------------------------------------------------------------------------


def _ensure_out_dir() -> Path:
    """Make sure wizard/out exists and return its Path."""
    out_dir = Path(__file__).parent / "out"
    out_dir.mkdir(exist_ok=True)
    return out_dir


def _random_tag(n: int = 6) -> str:
    """Handy little random suffix for filenames / strategy names."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def main() -> None:
    out_dir = _ensure_out_dir()

    for i in range(NUM_CHILDREN):
        child_path = make_algo(out_dir)
        # Optionally rename with a random tag so they’re always unique
        new_name = child_path.with_stem(f"{child_path.stem}_{_random_tag()}")
        child_path.rename(new_name)
        print(f"[{i+1}/{NUM_CHILDREN}] generated → {new_name.relative_to(out_dir.parent)}")

    print(f"✅  Finished – {NUM_CHILDREN} children ready for back-testing.")


if __name__ == "__main__":
    main()
