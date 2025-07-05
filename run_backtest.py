# run_backtest.py
#!/usr/bin/env python3
"""
Launch exactly one (NUM_CHILDREN = 1) cloud back-test.

Steps
  1. copy lean.json, main.py, strategies/ into children/* so each folder is a
     self-contained Lean project
  2. run `lean cloud backtest` from INSIDE that folder
  3. store {run_name: backtestId} in backtests.json (best-effort)

Requires QC_PROJECT_ID as an env-var (set via GitHub Secret).
"""

from __future__ import annotations
import json, os, pathlib, re, shutil, subprocess, sys, uuid

ROOT       = pathlib.Path(__file__).resolve().parent
CHILD_DIR  = ROOT / "children"
OUT_FILE   = ROOT / "backtests.json"
PROJECT_ID = os.getenv("QC_PROJECT_ID")

if not PROJECT_ID:
    sys.exit("QC_PROJECT_ID env var missing")

# ← added lean.json here
ESSENTIALS = ["lean.json", "main.py", "strategies"]
BACKTEST_RE = re.compile(r"backtest.*?id.*?([0-9a-f\-]{8,})", re.I)

records: dict[str, str] = {}

for child in CHILD_DIR.iterdir():
    if not child.is_dir():
        continue

    # 1️⃣  copy essentials so each child is a full Lean project
    for item in ESSENTIALS:
        src, dst = ROOT / item, child / item
        if dst.exists():
            shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
        shutil.copytree(src, dst) if src.is_dir() else shutil.copy2(src, dst)

    # 2️⃣  start back-test (CLI 1.x ⇒ no --wait / --json flags)
    run_name = f"{child.name}-{uuid.uuid4().hex[:6]}"
    print(f"🚀  {run_name}")
    cmd = [
        "lean", "cloud", "backtest", PROJECT_ID,
        "--push", "--name", run_name
    ]

    proc = subprocess.run(cmd, cwd=child, text=True,
                          capture_output=True, timeout=900)

    if proc.returncode:
        print(f"❌  {run_name}:\n{proc.stderr or proc.stdout}")
        continue

    # 3️⃣  best-effort scrape of the back-test ID
    match = BACKTEST_RE.search(proc.stdout)
    bt_id = match.group(1) if match else "unknown"
    records[run_name] = bt_id
    print(f"✔   {run_name}  →  {bt_id}")

# always write something so later steps know the script ran
OUT_FILE.write_text(json.dumps(records, indent=2))
print(f"📝  Back-test IDs saved to {OUT_FILE.relative_to(ROOT)}")
