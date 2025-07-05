# run_backtest.py
#!/usr/bin/env python3
"""
Creates a self-contained Lean project for each folder in children/ (only one by
default) and launches a cloud back-test.  Stores the map {run_name: backtestId}
in backtests.json.

Needs QC_PROJECT_ID in environment (set via GitHub secret).
"""

from __future__ import annotations
import json, os, pathlib, shutil, subprocess, sys, uuid

ROOT       = pathlib.Path(__file__).resolve().parent
CHILD_DIR  = ROOT / "children"
OUT_FILE   = ROOT / "backtests.json"
PROJECT_ID = os.getenv("QC_PROJECT_ID")

if not PROJECT_ID:
    sys.exit("QC_PROJECT_ID env var missing")

ESSENTIALS = ["main.py", "strategies"]   # copied into each variant
records: dict[str, str] = {}

for child in CHILD_DIR.iterdir():
    if not child.is_dir():
        continue

    # 1️⃣ copy code into variant folder
    for item in ESSENTIALS:
        src, dst = ROOT / item, child / item
        if dst.exists():
            shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
        shutil.copytree(src, dst) if src.is_dir() else shutil.copy2(src, dst)

    # 2️⃣ start back-test (CLI v1.x ⇒ no --wait flag)
    run_name = f"{child.name}-{uuid.uuid4().hex[:6]}"
    print(f"🚀  {run_name}")
    cmd = [
        "lean", "cloud", "backtest", PROJECT_ID,
        "--push",
        "--name", run_name,
        "--json"          # makes stdout a JSON blob
    ]
    proc = subprocess.run(cmd, cwd=child, text=True,
                          capture_output=True, timeout=900)

    if proc.returncode:
        print(f"❌  {run_name}:\n{proc.stderr or proc.stdout}")
        continue

    try:
        result = json.loads(proc.stdout)
        bt_id  = result["backtestId"]
        records[run_name] = bt_id
        print(f"✔   {run_name}  →  {bt_id}")
    except Exception as exc:
        print(f"⚠️   {run_name}: couldn’t parse CLI JSON ({exc})")

# write (even if empty, so later steps know it ran)
OUT_FILE.write_text(json.dumps(records, indent=2))
print(f"📝  Back-test IDs saved to {OUT_FILE.relative_to(ROOT)}")
