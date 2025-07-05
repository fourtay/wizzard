# run_backtest.py
#!/usr/bin/env python3
"""
For every folder in children/, build a self-contained Lean project
(params.json + main.py + strategies/*), push it to the cloud project,
and store the resulting backtestId.

Env vars required (GitHub secrets):
  QC_API_TOKEN  – already set via lean login
  QC_PROJECT_ID – the cloud project to overwrite each time
"""

from __future__ import annotations
import json, os, pathlib, shutil, subprocess, sys, uuid

ROOT       = pathlib.Path(__file__).resolve().parent
CHILD_DIR  = ROOT / "children"
OUT_FILE   = ROOT / "backtests.json"
PROJECT_ID = os.getenv("QC_PROJECT_ID")

if not PROJECT_ID:
    sys.exit("QC_PROJECT_ID env var missing")

# files & dirs that must be present in every variant we push
ESSENTIALS = ["main.py", "strategies"]

records: dict[str, str] = {}

for child in CHILD_DIR.iterdir():
    if not child.is_dir():
        continue

    # 1️⃣  Make the child a self-contained Lean project
    for item in ESSENTIALS:
        src = ROOT / item
        dst = child / item
        if dst.exists():
            shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # 2️⃣  Kick off the back-test
    run_name = f"{child.name}-{uuid.uuid4().hex[:6]}"
    print(f"🚀  {run_name}")
    cmd = [
        "lean", "cloud", "backtest", PROJECT_ID,
        "--push",   str(child),
        "--name",   run_name,
        "--wait",
        "--output", str(child / "backtest.json"),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode:
        print(f"❌  {run_name}: {proc.stderr.strip() or 'unknown error'}")
        continue

    try:
        bt_id = json.loads((child / "backtest.json").read_text())["backtestId"]
    except Exception as exc:
        print(f"⚠️   Could not parse backtestId for {run_name}: {exc}")
        continue

    records[run_name] = bt_id
    print(f"✔   {run_name}  →  {bt_id}")

OUT_FILE.write_text(json.dumps(records, indent=2))
print(f"📝  Back-test IDs saved to {OUT_FILE.relative_to(ROOT)}")
