# run_backtest.py
#!/usr/bin/env python3
"""
Kick off a cloud back-test for every sub-folder in `children/`
and record the QC backtest IDs in backtests.json.
"""

from __future__ import annotations
import json, os, pathlib, subprocess, sys

ROOT       = pathlib.Path(__file__).resolve().parent
CHILD_DIR  = ROOT / "children"
OUT_FILE   = ROOT / "backtests.json"
QC_TOKEN   = os.getenv("QC_API_TOKEN")
PROJECT_ID = os.getenv("QC_PROJECT_ID")

if not (QC_TOKEN and PROJECT_ID):
    sys.exit("QC_API_TOKEN and/or QC_PROJECT_ID env vars are missing.")

records: dict[str, str] = {}

for child in CHILD_DIR.iterdir():
    if not child.is_dir():
        continue
    print(f"🚀  Launching back-test → {child.name}")
    cmd = [
        "lean", "cloud", "backtest", PROJECT_ID,
        "--push",   str(child),
        "--name",   child.name,
        "--wait",
        "--output", str(child / "backtest.json"),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode:
        print(f"❌  {child.name}: {proc.stderr.strip()}")
        continue

    try:
        bt_id = json.loads((child / "backtest.json").read_text())["backtestId"]
    except Exception as e:
        print(f"⚠️   Could not read backtestId for {child.name}: {e}")
        continue

    records[child.name] = bt_id
    print(f"✔   {child.name}  →  {bt_id}")

OUT_FILE.write_text(json.dumps(records, indent=2))
print(f"📝  Back-test IDs saved to {OUT_FILE.relative_to(ROOT)}")
